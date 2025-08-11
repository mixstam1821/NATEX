from bokeh.io import curdoc
from bokeh.models import TabPanel, Tabs, Div
from bokeh.layouts import column
import os, re, glob, warnings
from collections import defaultdict, OrderedDict
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from PIL import Image

from satpy import Scene
from pyresample import create_area_def

import cartopy.feature as cfeature
import shapely.ops as sops
from shapely.geometry import (
    box, LineString, MultiLineString, Polygon, MultiPolygon,
    GeometryCollection, LinearRing
)

from pyproj import Transformer

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource, Button, Slider, Div, TextInput, Select,
    ColorPicker, Spinner, RadioButtonGroup,InlineStyleSheet,GlobalInlineStyleSheet
)
from bokeh.plotting import figure

warnings.filterwarnings("ignore", category=UserWarning)
curdoc().theme = "dark_minimal"
base_variables = """ :host { /* CSS Custom Properties for easy theming */ --primary-color: #8b5cf6; --secondary-color: #06b6d4; --background-color: #1f2937; --surface-color: #343838; --text-color: #f9fafb; --accent-color: #f59e0b; --danger-color: #ef4444; --success-color: #10b981; --border-color: #4b5563; --hover-color: #6366f1; background: none !important; } """

wait_html = """ <div class="spin-wrapper"> <img src="https://raw.githubusercontent.com/mixstam1821/bokeh_showcases/refs/heads/main/assets0/2784386.png" class="spinner-img"> <p class="loader-msg">⏳ Loading... Stand by.</p> </div> <style> .spin-wrapper { height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; } .spinner-img { width: 100px; height: 100px; animation: spin-fast 2.5s linear infinite; filter: drop-shadow(0 0 6px #1a73e8); } @keyframes spin-fast { 0%   { transform: rotate(0deg); } 100% { transform: rotate(360deg); } } .loader-msg { margin-top: 16px; font-size: 18px; color: #ccc; font-family: 'Segoe UI', sans-serif; } </style> """
wait_html_div = Div(text="", width=600, height=200)
tabs_style = InlineStyleSheet(css=""" /* Main tabs container */ :host { background: #2d2d2d !important; border-radius: 14px !important; padding: 8px !important; margin: 10px !important; box-shadow: 0 6px 20px #00ffe055, 0 2px 10px rgba(0, 0, 0, 0.3) !important; border: 1px solid rgba(0, 191, 255, 0.3) !important; } /* Tab navigation bar */ :host .bk-tabs-header { background: transparent !important; border-bottom: 2px solid #00bfff !important; margin-bottom: 8px !important; } /* Individual tab buttons */ :host .bk-tab { background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%) !important; color: #00bfff !important; border: 1px solid #555 !important; border-radius: 8px 8px 0 0 !important; padding: 12px 20px !important; margin-right: 4px !important; font-family: 'Arial', sans-serif !important; font-weight: 600 !important; font-size: 0.95em !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; position: relative !important; overflow: hidden !important; } /* Tab hover effect */ :host .bk-tab:hover { background: linear-gradient(135deg, #dc1cdd 0%, #ff1493 100%) !important; color: #ffffff !important; border-color: #dc1cdd !important; box-shadow: 0 4px 15px rgba(220, 28, 221, 0.5) !important; transform: translateY(-2px) !important; } /* Active tab styling */ :host .bk-tab.bk-active { background: linear-gradient(135deg, #00bfff 0%, #0080ff 100%) !important; color: #000000 !important; border-color: #00bfff !important; box-shadow: 0 4px 20px rgba(0, 191, 255, 0.6), inset 0 2px 0 rgba(255, 255, 255, 0.3) !important; transform: translateY(-1px) !important; font-weight: 700 !important; } /* Active tab glow effect */ :host .bk-tab.bk-active::before { content: '' !important; position: absolute !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%) !important; animation: shimmer 2s infinite !important; } @keyframes shimmer { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } } /* Tab content area */ :host .bk-tab-content { background: transparent !important; padding: 16px !important; border-radius: 0 0 10px 10px !important; } /* Focus states for accessibility */ :host .bk-tab:focus { outline: 2px solid #00bfff !important; outline-offset: 2px !important; } /* Disabled tab state */ :host .bk-tab:disabled { background: #1a1a1a !important; color: #666 !important; cursor: not-allowed !important; opacity: 0.5 !important; } """)
fancy_div_style = InlineStyleSheet(css=""" :host { position: relative; background: #21233a; color: #fff; border-radius: 12px; padding: 18px 28px; text-align: center; overflow: hidden; box-shadow: 0 6px 10px rgba(197, 153, 10, 0.2); } :host::after { content: ''; position: absolute; top: 0; left: -80%; width: 200%; height: 100%; background: linear-gradient(120deg, transparent 40%, rgba(255, 252, 71, 0.416) 50%, transparent 60%); animation: shimmer 2.2s infinite; pointer-events: none; border-radius: inherit; } @keyframes shimmer { 0%   { left: -80%; } 100% { left: 100%; } } """)
gstyle = GlobalInlineStyleSheet(css=""" html, body, .bk, .bk-root {background-color: #343838; margin: 0; padding: 0; height: 100%; color: white; font-family: 'Consolas', 'Courier New', monospace; } .bk { color: white; } .bk-input, .bk-btn, .bk-select, .bk-slider-title, .bk-headers, .bk-label, .bk-title, .bk-legend, .bk-axis-label { color: white !important; } .bk-input::placeholder { color: #aaaaaa !important; } """)
textarea_style  = InlineStyleSheet(css=base_variables + """ :host textarea { background: var(--surface-color) !important; color: var(--text-color) !important; border: 1px solid var(--border-color) !important; border-radius: 6px !important; padding: 10px 12px !important; font-size: 14px !important; font-family: inherit !important; transition: all 0.2s ease !important; resize: vertical !important; } :host textarea:focus { outline: none !important; border-color: var(--primary-color) !important; box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important; } :host textarea::placeholder { color: #9ca3af !important; opacity: 0.7 !important; } """)
slider_style = InlineStyleSheet(css=""" /* Host slider container */ :host { background: none !important; } /* Full track: set dark grey, but filled part will override with .noUi-connect */ :host .noUi-base, :host .noUi-target { background: #bfbfbf !important; } /* Highlighted portion of track */ :host .noUi-connect { background: #00ffe0; } /* Slider handle */ :host .noUi-handle { background: #343838; border: 2px solid #00ffe0; border-radius: 50%; width: 20px; height: 20px; } /* Handle hover/focus */ :host .noUi-handle:hover, :host .noUi-handle:focus { border-color: #ff2a68; box-shadow: 0 0 10px #ff2a6890; } /* Tooltip stepping value */ :host .noUi-tooltip { background: #343838; color: #00ffe0; font-family: 'Consolas', monospace; border-radius: 6px; border: 1px solid #00ffe0; } /* Filled (active) slider track */ :host .noUi-connect { background: linear-gradient(90deg, #ffea31 20%, #d810f7 100%) !important; /* greenish-cyan fade */ box-shadow: 0 0 10px #00ffe099 !important; } """)
style = InlineStyleSheet(css=""" .bk-btn { background-color: #00ffe0; color: #1e1e2e; font-weight: bold; border: 10px solid #00ffe0; border-radius: 6px; transform: rotate(0deg); box-shadow: none; transition: all 0.3s ease-in-out; } /* 🟦 Hover: #1e1e2e + rotate */ .bk-btn:hover { background-color: #1e1e2e; border-color: #1e1e2e; color: #00ffe0; transform: rotate(3deg); box-shadow: 0 0 15px 3px #00ffe0; } /* 🔴 Active (click hold): red + stronger rotate */ .bk-btn:active { background-color: red; border-color: red; transform: rotate(6deg); box-shadow: 0 0 15px 3px red; } """)
style2 = InlineStyleSheet(css=""" .bk-input { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1px solid #3c3c3c; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } /* Input Hover */ .bk-input:hover { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232;        /* Red border */ box-shadow: 0 0 9px 2px #ff3232cc;  /* Red glow */ border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } /* Input Focus */ .bk-input:focus { background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232; box-shadow: 0 0 11px 3px #ff3232dd; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } .bk-input:active { outline: none; background-color: #1e1e1e; color: #d4d4d4; font-weight: 500; border: 1.5px solid #ff3232; box-shadow: 0 0 14px 3px #ff3232; border-radius: 5px; padding: 6px 10px; font-family: 'Consolas', 'Courier New', monospace; transition: all 0.2s ease; } .bk-input:-webkit-autofill { background-color: #1e1e1e !important; color: #d4d4d4 !important; -webkit-box-shadow: 0 0 0px 1000px #1e1e1e inset !important; -webkit-text-fill-color: #d4d4d4 !important; } """)
button_style = InlineStyleSheet(css=base_variables + """ :host button { background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important; color: white !important; border: none !important; border-radius: 6px !important; padding: 10px 20px !important; font-size: 14px !important; font-weight: 600 !important; cursor: pointer !important; transition: all 0.2s ease !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; } :host button:hover { transform: translateY(-1px) !important; box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important; background: linear-gradient(135deg, var(--hover-color), var(--primary-color)) !important; } :host button:active { transform: translateY(0) !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; } :host button:disabled { background: #6b7280 !important; cursor: not-allowed !important; transform: none !important; box-shadow: none !important; } """)
radio_style = InlineStyleSheet(css=""" /* Outer container */ :host { background: #2F2F2F !important; border-radius: 6px !important; padding: 0px !important; max-width: 1600px !important; } /* Title */ :host .bk-input-group label, :host .bk-radiobuttongroup-title { color: #f59e0b !important; font-size: 1em !important; font-family: 'Fira Code', monospace; font-weight: bold !important; margin-bottom: 8px !important; text-shadow: 0 1px 6px #f59e0b99; letter-spacing: 0.5px; } /* Button group: wrap on small screens */ :host .bk-btn-group { display: flex !important; gap: 6px !important; flex-wrap: wrap !important; justify-content: flex-start; margin-bottom: 4px; } /* Each radio button - compact style */ :host button.bk-btn { background: #23233c !important; color: #f9fafb !important; border: 1.8px solid #f59e0b !important; border-radius: 8px !important; padding: 0.3em 1em !important; min-width: 48px !important; font-size: 0.85em !important; font-family: 'Fira Code', monospace; font-weight: 500 !important; transition: border 0.13s, box-shadow 0.14s, color 0.12s, background 0.13s; box-shadow: 0 1px 4px #0002 !important; cursor: pointer !important; outline: none !important; white-space: nowrap !important; overflow: visible !important; text-overflow: unset !important; } /* Orange glow on hover */ :host button.bk-btn:hover:not(.bk-active) { border-color: #ffa733 !important; color: #ffa733 !important; box-shadow: 0 0 0 1px #ffa73399, 0 0 6px #ffa73388 !important; background: #2e2937 !important; } /* Red glow on active/focus */ :host button.bk-btn:focus, :host button.bk-btn.bk-active { border-color: #ff3049 !important; color: #ff3049 !important; background: #322d36 !important; box-shadow: 0 0 0 1px #ff304999, 0 0 9px #ff304988 !important; } /* Remove focus outline */ :host button.bk-btn:focus { outline: none !important; } """)

airmass = """ <div class="airmass"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .airmass { height: 300px;width: 300px;} </style> """
airmass_div = Div(text=airmass)

cloudConve = """ <div class="cloudConve"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/refs/heads/main/assets0/cloudConve.png?token=GHSAT0AAAAAADC5NF4GPK2ATGJG6P2RWCLI2EZB2OA"> <style> .cloudConve { height: 300px;width: 300px;} </style> """
cloudConve_div = Div(text=cloudConve)


convectionStorms = """ <div class="convectionStorms"> <img src=""> <style> .convectionStorms { height: 300px;width: 300px;} </style> """
convectionStorms_div = Div(text=convectionStorms)


dayMicro = """ <div class="dayMicro"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .dayMicro { height: 300px;width: 300px;} </style> """
dayMicro_div = Div(text=dayMicro)


dayMicro2 = """ <div class="dayMicro2"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .dayMicro2 { height: 300px;width: 300px;} </style> """
dayMicro2_div = Div(text=dayMicro2)


dust = """ <div class="dust"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .dust { height: 300px;width: 300px;} </style> """
dust_div = Div(text=dust)


naturalColor = """ <div class="naturalColor"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .naturalColor { height: 300px;width: 300px;} </style> """
naturalColor_div = Div(text=naturalColor)


nightMicro = """ <div class="nightMicro"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .nightMicro { height: 300px;width: 300px;} </style> """
nightMicro_div = Div(text=nightMicro)


severeStorm = """ <div class="severeStorm"> <img src="https://raw.githubusercontent.com/mixstam1821/NATEX/8ef9173df3a727cc574696b1e9d403749c194888/assets0/airmass.png?token=GHSAT0AAAAAADC5NF4H2KIVYLZXRFJLXT4M2EZBD4Q"> <style> .severeStorm { height: 300px;width: 300px;} </style> """
severeStorm_div = Div(text=severeStorm)

# --- composites list (UI shows all; we validate availability on rebuild) ---
ALL_COMPOSITES = [
    "24h_microphysics","airmass","ash","cloud_phase_distinction","cloud_phase_distinction_raw",
    "cloudtop","cloudtop_daytime","colorized_ir_clouds","convection","day_microphysics",
    "day_microphysics_winter","day_severe_storms","day_severe_storms_tropical","dust","fog",
    "green_snow","hrv_clouds","hrv_fog","hrv_severe_storms","hrv_severe_storms_masked",
    "ir108_3d","ir_cloud_day","ir_overview","ir_sandwich","natural_color","natural_color_nocorr",
    "natural_color_raw","natural_color_raw_with_night_ir","natural_color_with_night_ir",
    "natural_color_with_night_ir_hires","natural_enh","natural_enh_with_night_ir",
    "natural_enh_with_night_ir_hires","natural_with_night_fog","night_fog","night_ir_alpha",
    "night_ir_with_background","night_ir_with_background_hires","night_microphysics",
    "night_microphysics_tropical","overshooting_tops","overview","overview_raw","realistic_colors",
    "rocket_plume_day","rocket_plume_night","snow","vis_sharpened_ir"
]
# Map composites to preview Divs
HELP_IMAGES_MAP = {
    "airmass": airmass_div,
    "convection": cloudConve_div,
    "day_microphysics": dayMicro_div,
    "dust": dust_div,
    "natural_color": naturalColor_div,
    "night_microphysics": nightMicro_div,
    "day_severe_storms": severeStorm_div,
    # Add more as you prepare them
}

# ---------------- Widgets ----------------
w_data_glob = TextInput(title="Data glob (*.nat)", value="/home/michael/downloads_nat/*.nat", stylesheets = [style2], width = 350)
w_reader    = TextInput(title="Reader", value="seviri_l1b_native", stylesheets = [style2])
w_composite = Select(title="Composite", value="day_microphysics", options=ALL_COMPOSITES, stylesheets = [style2])
w_resampler = Select(title="Resampler (Plate Carrée only)", value="kd_tree", options=["nearest", "kd_tree"], stylesheets = [style2])
w_scale     = Select(title="Natural Earth scale", value="50m", options=["110m", "50m", "10m"], stylesheets = [style2])
w_coast     = ColorPicker(title="Coastlines color", color="#ffffff", width = 80)

# Projection toggle: 0=Plate Carrée, 1=Geostationary (native)
w_projection = RadioButtonGroup(labels=["Plate Carrée (EPSG:4326)", "Geostationary (native)"], active=0, stylesheets = [radio_style])

w_lon_min   = TextInput(title="lon_min", value="-180.0", stylesheets = [style2], width = 100)
w_lat_min   = TextInput(title="lat_min", value="-90.0", stylesheets = [style2], width = 100)
w_lon_max   = TextInput(title="lon_max", value="180.0", stylesheets = [style2], width = 100)
w_lat_max   = TextInput(title="lat_max", value="90.0", stylesheets = [style2], width = 100)

w_width     = Spinner(title="Target width (px, Plate Carrée)", value=3600, step=100, low=200, high=12000, stylesheets = [style2])
w_height    = Spinner(title="Target height (px, Plate Carrée)", value=1800, step=100, low=100, high=8000, stylesheets = [style2])
w_roi       = Spinner(title="KD-tree radius (m, Plate Carrée)", value=20000, step=1000, low=1000, high=100000, stylesheets = [style2])

btn_apply   = Button(label="Apply", button_type="primary", width=100, stylesheets = [button_style])
slider      = Slider(start=0, end=1, step=1, value=0, title="Frame", disabled=True, stylesheets = [slider_style])
btn_play    = Button(label="▶ Play", width=80, disabled=True, stylesheets = [button_style])
info        = Div(text="", width=520)
# New Div for showing current date/time from the plot title
current_datetime_div = Div(
    text="<p style='font-size:18px; color:#00ffe0; font-family:Consolas;'>—</p>",
    width=500
)


# ---------------- Globals / caches ----------------
frames: list[np.ndarray] = []         # each is (H,W) uint32 packed RGBA (flipped for bokeh)
titles: list[str] = []
period_ms = 500
ticker = {"handle": None}

# caches
OVERLAY_CACHE = {}    # key -> {"xs":..., "ys":...}
GROUP_CACHE   = {"glob": None, "groups": OrderedDict()}
FRAME_CACHE   = {}    # key -> (frames, titles, extent, overlay_key_used)

# ---------------- Geometry helpers ----------------
def _split_antimeridian(x, y):
    segs_x, segs_y = [], []
    if not x:
        return segs_x, segs_y
    cx, cy = [x[0]], [y[0]]
    for i in range(1, len(x)):
        cx.append(x[i]); cy.append(y[i])
        if abs(x[i] - x[i-1]) > 180:
            segs_x.append(cx[:-1]); segs_y.append(cy[:-1])
            cx, cy = [x[i-1]], [y[i-1]]
    segs_x.append(cx); segs_y.append(cy)
    return segs_x, segs_y

def _iter_lines(geom):
    if isinstance(geom, (LineString, LinearRing)):
        yield geom
    elif isinstance(geom, MultiLineString):
        for g in geom.geoms:
            yield g
    elif isinstance(geom, Polygon):
        yield geom.exterior
        for ring in geom.interiors:
            yield ring
    elif isinstance(geom, (MultiPolygon, GeometryCollection)):
        for g in geom.geoms:
            yield from _iter_lines(g)

def lonlat_feature_to_xsys_clipped(feature, clip_poly_lonlat):
    """For Plate Carrée: clip in lon/lat and return xs,ys lists."""
    xs_all, ys_all = [], []
    for geom in feature.geometries():
        for line in _iter_lines(geom):
            inter = line.intersection(clip_poly_lonlat)
            if inter.is_empty:
                continue
            for seg in _iter_lines(inter):
                x, y = seg.xy
                segx, segy = _split_antimeridian(list(x), list(y))
                xs_all.extend(segx); ys_all.extend(segy)
    return xs_all, ys_all

from pyproj import Transformer
import numpy as np

def _split_on_mask(x, y, mask):
    """Split sequences into contiguous segments where mask==True."""
    xs, ys = [], []
    if len(x) == 0:
        return xs, ys
    # find run boundaries
    idx = np.where(~mask)[0]
    start = 0
    for k in idx:
        if k - start >= 2:
            xs.append(x[start:k].tolist())
            ys.append(y[start:k].tolist())
        start = k + 1
    # tail
    if len(x) - start >= 2:
        xs.append(x[start:].tolist())
        ys.append(y[start:].tolist())
    return xs, ys
import numpy as np

def shift_xsys(xs, ys, dx=0.0, dy=0.0):
    # translate each segment by (dx, dy)
    xs2 = [list(np.asarray(seg, float) + dx) for seg in xs]
    ys2 = [list(np.asarray(seg, float) + dy) for seg in ys]
    return xs2, ys2

from pyproj import CRS, Transformer

def projected_feature_to_xsys(feature, area, extent_proj):
    x0, y0, x1, y1 = extent_proj
    xmin, xmax = (x0, x1) if x0 <= x1 else (x1, x0)
    ymin, ymax = (y0, y1) if y0 <= y1 else (y1, y0)

    proj_crs = CRS.from_proj4(area.proj_str)
    to_proj = Transformer.from_crs("EPSG:4326", proj_crs, always_xy=True)

    xs_all, ys_all = [], []
    def _split_on_mask(X, Y, mask):
        xs, ys = [], []
        if X.size == 0: return xs, ys
        idx = np.where(~mask)[0]; start = 0
        for k in idx:
            if k - start >= 2:
                xs.append(X[start:k].tolist()); ys.append(Y[start:k].tolist())
            start = k + 1
        if X.size - start >= 2:
            xs.append(X[start:].tolist()); ys.append(Y[start:].tolist())
        return xs, ys

    for geom in feature.geometries():
        for line in _iter_lines(geom):
            lon, lat = map(lambda z: np.asarray(z, float), line.xy)
            X, Y = to_proj.transform(lon, lat)
            X = np.asarray(X, float); Y = np.asarray(Y, float)
            valid = np.isfinite(X) & np.isfinite(Y) & (X>=xmin) & (X<=xmax) & (Y>=ymin) & (Y<=ymax)
            segx, segy = _split_on_mask(X, Y, valid)
            xs_all.extend(segx); ys_all.extend(segy)
    return xs_all, ys_all


# ---------------- Utils ----------------
def slot_key(p):
    m = re.search(r"(\d{8}\d{6})", Path(p).name)
    return m.group(1) if m else None

def parse_float(s, default):
    try:
        return float(str(s).strip())
    except Exception:
        return default

def frame_cache_key(groups, reader, composite, proj_mode, area_def_pc, resampler, roi):
    all_files = tuple(tuple(sorted(v)) for _, v in groups.items())
    if proj_mode == "pc":
        key = (
            all_files, reader, composite, proj_mode,
            area_def_pc.width, area_def_pc.height, area_def_pc.area_extent,
            resampler, roi
        )
    else:  # native geo
        key = (all_files, reader, composite, proj_mode)  # native extent/size dictated by data
    return key

def overlay_cache_key(proj_mode, extent, scale, proj_dict=None):
    if proj_mode == "pc":
        return ("pc", extent, scale)
    else:
        # sort proj_dict for stable key
        proj_items = tuple(sorted((k, str(v)) for k, v in proj_dict.items()))
        return ("geo", extent, scale, proj_items)

# ---------------- Satpy enhancement (no disk if possible) ----------------
try:
    from satpy.writers import get_enhanced_image
    HAVE_GET_ENH = True
except Exception:
    HAVE_GET_ENH = False

def enhance_to_rgba_uint32(xr_da):
    """Return (H,W) uint32 for Bokeh from enhanced dataset. Uses memory path when possible."""
    if HAVE_GET_ENH:
        xrimg = get_enhanced_image(xr_da)
        pil = (xrimg.pil_image() if hasattr(xrimg, "pil_image") else xrimg.to_pil()).convert("RGBA")
    else:
        # Last-ditch fallback: write tiny temp PNG (rare path)
        with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        from satpy import Scene  # (we assume caller can save dataset to tmp if needed)
        xr_da.to_pil().save(tmp_path)  # not always available; encourage upgrading Satpy if hit
        pil = Image.open(tmp_path).convert("RGBA")
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
    rgba8 = np.asarray(pil, dtype=np.uint8)
    if rgba8.shape[-1] == 3:
        alpha = np.full(rgba8.shape[:2] + (1,), 255, np.uint8)
        rgba8 = np.concatenate([rgba8, alpha], axis=-1)
    r, g, b, a = [rgba8[..., i].astype(np.uint32) for i in range(4)]
    return np.flipud((r << 24) | (g << 16) | (b << 8) | a)

# ---------------- Build a single frame ----------------
def build_frame(files, reader, composite, proj_mode, area_def_pc, resampler, roi):
    scn = Scene(reader=reader, filenames=files)
    scn.load([composite])
    # We'll take the first .nat file path to decide where to save
    nat_file = Path(files[0])
    png_path = nat_file.with_name(f"{nat_file.stem}_{composite}.png")

    if proj_mode == "pc":
        rs = scn.resample(area_def_pc, resampler=resampler,
                        radius_of_influence=roi if resampler == "kd_tree" else None)
        da = rs[composite]
        rs.save_dataset(composite, filename=str(png_path), writer="simple_image")

    else:
        da = scn[composite]
        scn.save_dataset(composite, filename=str(png_path), writer="simple_image")




    pil = Image.open(png_path).convert("RGBA")
    rgba = np.array(pil)
    view = rgba.view(np.uint32).reshape(rgba.shape[0], rgba.shape[1])
    view = np.flipud(view)

    area = da.attrs["area"]
    extent = tuple(area.area_extent)
    title = Path(files[0]).name
    return view, title, extent, area

def flip_overlays_xy(xs, ys, x0, x1, y0, y1):
    """Flip overlays vertically and horizontally within [x0,x1]×[y0,y1]."""
    inv_x = x0 + x1  # x' = (x0+x1) - x
    inv_y = y0 + y1  # y' = (y0+y1) - y
    new_xs, new_ys = [], []
    for segx, segy in zip(xs, ys):
        new_xs.append([inv_x - vx for vx in segx])
        new_ys.append([inv_y - vy for vy in segy])
    return new_xs, new_ys


# ---------------- Rebuild pipeline ----------------


def rebuild(event=None):


    wait_html_div.visible = True
    wait_html_div.text = wait_html  # clear before first progress update

    global frames, titles

    # stop any running animation
    if ticker["handle"] is not None:
        curdoc().remove_periodic_callback(ticker["handle"])
        ticker["handle"] = None
    btn_play.label = "▶ Play"; btn_play.disabled = True
    slider.disabled = True
    info.text = "Rebuilding…"

    # read UI values
    data_glob = w_data_glob.value
    reader    = w_reader.value.strip()
    composite = w_composite.value.strip()
    resampler = w_resampler.value
    roi       = int(w_roi.value)
    proj_mode = "pc" if w_projection.active == 0 else "geo"
    lon_min = parse_float(w_lon_min.value, -180.0)
    lat_min = parse_float(w_lat_min.value,  -90.0)
    lon_max = parse_float(w_lon_max.value,  180.0)
    lat_max = parse_float(w_lat_max.value,   90.0)
    width   = int(w_width.value)
    height  = int(w_height.value)
    scale   = w_scale.value

    # group files (cache by glob)
    if GROUP_CACHE["glob"] != data_glob:
        all_nat = glob.glob(data_glob)
        by_time = defaultdict(list)
        for f in all_nat:
            k = slot_key(f)
            if k:
                by_time[k].append(f)
        GROUP_CACHE["glob"] = data_glob
        GROUP_CACHE["groups"] = OrderedDict(sorted(by_time.items()))
    groups = GROUP_CACHE["groups"]

    if not groups:
        info.text = "No .nat files found for this pattern."
        slider.start = 0; slider.end = 1; slider.value = 0
        return

    # Plate Carrée target area
    area_def_pc = None
    if proj_mode == "pc":
        area_def_pc = create_area_def(
            area_id="pc_user", proj_id="pc_user",
            description="Plate Carrée (EPSG:4326)",
            projection={"proj": "longlat", "datum": "WGS84", "no_defs": None},
            width=width, height=height,
            area_extent=(lon_min, lat_min, lon_max, lat_max)
        )

    # Validate composite availability
    first_files = next(iter(groups.values()))
    try:
        tmp = Scene(reader=reader, filenames=first_files)
        av = set(tmp.available_composite_names())
        if composite not in av:
            info.text = (f"Composite '{composite}' not available. "
                        f"Pick: {', '.join(sorted(av)) or 'none'} and Apply.")
            slider.start = 0; slider.end = 1; slider.value = 0
            return
    except Exception as e:
        info.text = f"Could not inspect composites: {e}"
        slider.start = 0; slider.end = 1; slider.value = 0
        return

    # Cache key
    key = frame_cache_key(groups, reader, composite, proj_mode, area_def_pc, resampler, roi)

    if key in FRAME_CACHE:
        frames, titles, extent, overlay_key_used, first_area = FRAME_CACHE[key]
        finish_rebuild(extent, overlay_key_used, first_area, scale, proj_mode, composite, resampler)
        return

    # Prepare vars shared between callbacks
    frames, titles = [], []
    extent = None
    first_area = None
    overlay_key_used = None
    total_frames = len(groups)
    frame_iter = iter(groups.items())

    def process_next(idx=1):
        nonlocal extent, first_area, overlay_key_used

        try:
            t, files = next(frame_iter)
        except StopIteration:
            # All frames processed
            overlay_key_used = overlay_cache_key(
                proj_mode,
                extent,
                scale,
                (first_area.proj_dict if proj_mode == "geo" else None),
            )
            FRAME_CACHE[key] = (frames, titles, extent, overlay_key_used, first_area)

            # Hide the waiting div so it doesn't take space
            wait_html_div.visible = False

            finish_rebuild(extent, overlay_key_used, first_area, scale, proj_mode, composite, resampler)
            return

        # Update wait text
        wait_html_div.text = f"""
        <div class="spin-wrapper">
            <img src="https://raw.githubusercontent.com/mixstam1821/bokeh_showcases/refs/heads/main/assets0/2784386.png" class="spinner-img">
            <p class="loader-msg">⏳ Loading... Please wait<br>Processing frame {idx}/{total_frames}</p>
        </div>
        <style>
            .spin-wrapper {{ height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
            .spinner-img {{ width: 100px; height: 100px; animation: spin-fast 2.5s linear infinite; filter: drop-shadow(0 0 6px #1a73e8); }}
            @keyframes spin-fast {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .loader-msg {{ margin-top: 16px; font-size: 18px; color: #ccc; font-family: 'Segoe UI', sans-serif; text-align: center; }}
        </style>
        """

        # Process one frame
        v, ttl, ext, area = build_frame(files, reader, composite, proj_mode, area_def_pc, resampler, roi)
        frames.append(v)
        titles.append(ttl)

        if idx == 1:
            extent = ext
            first_area = area

        # Schedule next frame
        curdoc().add_next_tick_callback(lambda: process_next(idx + 1))

    def finish_rebuild(extent, overlay_key_used, first_area, scale, proj_mode, composite, resampler):
        # Build overlays if needed
        x0, y0, x1, y1 = extent
        if overlay_key_used not in OVERLAY_CACHE:
            coast_feat = cfeature.NaturalEarthFeature("physical", "coastline", scale, facecolor="none")
            bord_feat  = cfeature.NaturalEarthFeature("cultural", "admin_0_boundary_lines_land", scale, facecolor="none")

            if proj_mode == "pc":
                clip_box_ll = box(x0, y0, x1, y1)
                cx, cy = lonlat_feature_to_xsys_clipped(coast_feat, clip_box_ll)
                bx, by = lonlat_feature_to_xsys_clipped(bord_feat, clip_box_ll)
            else:
                cx, cy = projected_feature_to_xsys(coast_feat, first_area, (x0, y0, x1, y1))
                bx, by = projected_feature_to_xsys(bord_feat,  first_area, (x0, y0, x1, y1))
                cx, cy = flip_overlays_xy(cx, cy, x0, x1, y0, y1)
                bx, by = flip_overlays_xy(bx, by, x0, x1, y0, y1)
                cx, cy = shift_xsys(cx, cy, +1.1139e7, +1.1139e7)
                bx, by = shift_xsys(bx, by, +1.1139e7, +1.1139e7)

            OVERLAY_CACHE[overlay_key_used] = {"coast_xs": cx, "coast_ys": cy, "bord_xs": bx, "bord_ys": by}

        ov = OVERLAY_CACHE[overlay_key_used]
        coast_src.data.update(xs=ov["coast_xs"], ys=ov["coast_ys"])
        bord_src.data.update(xs=ov["bord_xs"],  ys=ov["bord_ys"])

        # Update plot
        img_source.data.update(image=[frames[0]], x=[x0], y=[y0], dw=[x1 - x0], dh=[y1 - y0])
        
        
        if proj_mode == "pc":
            p.x_range.start, p.x_range.end = x0, x1
            p.y_range.start, p.y_range.end = y0, y1
        else:
            p.x_range.start, p.x_range.end = 2e7,3e6
            p.y_range.start, p.y_range.end = y0+1.1139e7, y1+1.1139e7


        n = len(frames)
        slider.start = 0
        slider.end   = max(1, n - 1)
        slider.value = 0
        slider.disabled = (n < 2)
        btn_play.disabled = (n < 2)
        btn_play.label = "▶ Play"

        p.title.text = f"{composite} — {titles[0]} ({'PC' if proj_mode=='pc' else 'Native'})"
        info.text = f"{n} frames | {composite} | {'PC' if proj_mode=='pc' else 'Geo'} | scale={scale} | resampler={resampler if proj_mode=='pc' else 'native'}"

    # Start incremental processing
    process_next()



# ---------------- Animation helpers ----------------
def show_frame(i):
    if not frames:
        return
    i = int(i)
    img_source.data.update(image=[frames[i]])
    p.title.text = f"{w_composite.value} — {titles[i]} ({'PC' if w_projection.active==0 else 'Native'})"

def tick():
    if len(frames) < 2:
        return
    slider.value = (slider.value + 1) % len(frames)

def on_play():
    if len(frames) < 2:
        return
    if ticker["handle"] is None:
        ticker["handle"] = curdoc().add_periodic_callback(tick, period_ms)
        btn_play.label = "⏸ Pause"
    else:
        curdoc().remove_periodic_callback(ticker["handle"])
        ticker["handle"] = None
        btn_play.label = "▶ Play"

def on_slider(attr, old, new):
    show_frame(new)

# ---------------- Wire callbacks ----------------
def start_rebuild():
    wait_html_div.text = wait_html
    curdoc().add_next_tick_callback(rebuild)  # schedule rebuild in next event loop

btn_apply.on_click(start_rebuild)
btn_play.on_click(on_play)
slider.on_change("value", on_slider)

# ---------------- Initial figure ----------------
# Start with Plate Carrée world extents (will update on rebuild)
X0 = float(w_lon_min.value); Y0 = float(w_lat_min.value)
X1 = float(w_lon_max.value); Y1 = float(w_lat_max.value)

img_source = ColumnDataSource(data=dict(
    image=[np.zeros((2, 2), dtype=np.uint32)],
    x=[X0], y=[Y0], dw=[X1 - X0], dh=[Y1 - Y0]
))
coast_src = ColumnDataSource(data=dict(xs=[], ys=[]))
bord_src  = ColumnDataSource(data=dict(xs=[], ys=[]))

# Time series plot for color swatches
timeseries_src = ColumnDataSource(data=dict(frame_idx=[], color=[]))

ts_plot = figure(width=1480, height=120, title="Pixel Color Timeline",
                x_axis_label="Frame Index", y_axis_label=None,border_fill_color="#343838",
                y_range=(0, 1),  # fixed range (all bars same height)
                toolbar_location=None, tools="")

# Bar glyph with variable fill_color
ts_plot.vbar(x="frame_idx", top=1, width=0.9, color="color", source=timeseries_src)
ts_plot.yaxis.visible = False


p = figure(width=1480, height=700, match_aspect=True,
        x_range=(X0, X1), y_range=(Y0, Y1),
        output_backend="webgl",border_fill_color="#343838",
        title="Ready. Choose options, then click 'Apply'.")

p.image_rgba(image="image", x="x", y="y", dw="dw", dh="dh", source=img_source)
coast_r = p.multi_line(xs="xs", ys="ys", source=coast_src,
                    line_color=w_coast.color, line_width=1.2)
bord_r  = p.multi_line(xs="xs", ys="ys", source=bord_src,
                    line_color=w_coast.color, line_width=1.2)

def update_colors(attr, old, new):
    coast_r.glyph.line_color = w_coast.color
    bord_r.glyph.line_color = w_coast.color

w_coast.on_change("color", update_colors)

# Replace the existing packed_to_hex function with this:
def packed_to_hex(rgba_val):
    """Convert packed uint32 to hex color string - ABGR order."""
    a = (rgba_val >> 24) & 0xFF
    b = (rgba_val >> 16) & 0xFF
    g = (rgba_val >> 8) & 0xFF
    r = rgba_val & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"

# Replace the existing on_tap_callback function with this:
def on_tap_callback(event):
    if not frames:
        return
    
    x, y = event.x, event.y
    img_x0, img_y0 = img_source.data['x'][0], img_source.data['y'][0]
    dw, dh = img_source.data['dw'][0], img_source.data['dh'][0]
    H, W = frames[0].shape

    col = int((x - img_x0) / dw * W)
    row = int((y - img_y0) / dh * H)  # Direct mapping since image is already flipped
    
    # Clamp to valid bounds
    col = max(0, min(col, W - 1))
    row = max(0, min(row, H - 1))
    
    if 0 <= row < H and 0 <= col < W:
        frame_colors = []
        for fr in frames:
            rgba_val = fr[row, col]
            
            # Extract colors using ABGR order
            a = (rgba_val >> 24) & 0xFF
            b = (rgba_val >> 16) & 0xFF
            g = (rgba_val >> 8) & 0xFF
            r = rgba_val & 0xFF
            
            # Apply alpha blending against black background to match what you see
            alpha_factor = a / 255.0
            r_blended = int(r * alpha_factor)
            g_blended = int(g * alpha_factor)  
            b_blended = int(b * alpha_factor)
            
            frame_colors.append(f"#{r_blended:02x}{g_blended:02x}{b_blended:02x}")
            
            # Debug: show alpha values
            if len(frame_colors) == 1:  # Only print for first frame
                print(f"Pixel ({row},{col}): r={r} g={g} b={b} a={a} -> blended: #{r_blended:02x}{g_blended:02x}{b_blended:02x}")
        
        timeseries_src.data = dict(
            frame_idx=list(range(len(frames))),
            color=frame_colors
        )
# Attach tap tool event
p.on_event('tap', on_tap_callback)


HELP_IMAGE_CONTAINER = column(Div(text="<p style='color:gray;'>Select a composite to see a preview</p>"))

def update_help_image(attr, old, new):
    new = new.strip()
    if new in HELP_IMAGES_MAP:
        HELP_IMAGE_CONTAINER.children = [HELP_IMAGES_MAP[new]]
    else:
        HELP_IMAGE_CONTAINER.children = [Div(text="<p style='color:gray;'>No preview available</p>")]

w_composite.on_change("value", update_help_image)

def show_frame(i):
    if not frames:
        return
    i = int(i)
    img_source.data.update(image=[frames[i]])
    title_text = f"{w_composite.value} — {titles[i]} ({'PC' if w_projection.active==0 else 'Native'})"
    p.title.text = title_text

    # Extract datetime portion from title and update Div
    if "—" in title_text:
        dt_part0 = title_text.split("—")[1].split("(")[0].strip()
        dt_part = title_text.split(".")[0]
        current_datetime_div.text = f"<p style='font-size:18px; color:#00ffe0; font-family:Consolas;'>{dt_part[-14:-10]}-{dt_part[-10:-8]}-{dt_part[-8:-6]}  {dt_part[-6:-4]}:{dt_part[-4:-2]}:{dt_part[-2:]}</p> <br> <p style='font-size:18px; color:#c004ff; font-family:Consolas;'>{dt_part0}</p>"




# ---------------- Layout ----------------

w_composite.value.strip()
HELP_IMAGE = airmass_div
title = Div(text="<h2>Main Plot</h2>")

merged_div = Div(
    text="""
    <div style="
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
        text-align: center;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    ">
        <div style="font-size: 46px; font-weight: bold; color: deepskyblue; letter-spacing: 2px;">
            NATEX
        </div>
        <div style="font-size: 18px; color: #f4b400; margin-top: -6px; font-weight: 500;">
            A simple .nat explorer
        </div>
    </div>
    """,
    width=220,
)

about_div = Div( text=""" <div style="text-align:center; color:#00ffe0; font-size:1.07em; font-family:Consolas, monospace;"> Developed with <span style="color:#ff4c4c;">&#10084;&#65039;</span> by <a href="https://github.com/mixstam1821" target="_blank" style="color:#ffb031; font-weight:bold; text-decoration:none;"> mixstam1821 </a> </div> """, width=420, height=38, styles={"margin-top": "10px"} )

controls_row1 = column(w_data_glob, w_reader, w_composite, w_projection)
controls_row2 = column(row(w_lon_min,w_lon_max), row(w_lat_min, w_lat_max))
controls_row3 = column(row(w_coast,btn_apply, btn_play), slider,wait_html_div,current_datetime_div, info)
L1 = row(column(merged_div,controls_row1, controls_row2, controls_row3,about_div,
                            styles = {'background': 'linear-gradient(135deg, #262627 60%, #0a4431 100%)', 'box-shadow': '0 8px 36px hsla(152, 90%, 68%, 0.333)', 'border-radius': '18px', 'margin-left': '2px', 'margin-top': '10px', 'margin-bottom': '5px', 'width': '400px', 'height': '1000px', 'position': 'relative', 'z-index': '10','padding': '20px', },
stylesheets=[gstyle]

                            
                            ), column(p,ts_plot,HELP_IMAGE_CONTAINER),stylesheets=[gstyle],)
    
    # return L1  # Replace with your actual layout

# def make_downloader():
# Your downloader UI here

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from threading import Thread

import eumdac
from bokeh.io import curdoc
from bokeh.layouts import column, row, Spacer
from bokeh.models import Button, TextInput, Div, Select, PreText

from datetime import datetime, timezone
from pathlib import Path
import shutil, zipfile
import eumdac

from bokeh.io import curdoc
from bokeh.layouts import column, row, Spacer
from bokeh.models import Button, TextInput, Div, Select, PreText

# ------------------ EUMETSAT connection ------------------
consumer_key = '2nqAxmdR7vCBGShDjJGALAod_4wa'
consumer_secret = '4139hOZgSHKgXvMsxIwUtTDqVfEa'

try:
    token = eumdac.AccessToken((consumer_key, consumer_secret))
    datastore = eumdac.DataStore(token)
    connection_status = "✅ Connected to EUMETSAT"
except Exception as e:
    datastore = None
    connection_status = f"❌ Connection failed: {e}"

# ------------------ UI Elements ------------------
title_div = Div(text="<h1>🛰️ EUMETSAT Data Downloader</h1>", width=820)
status_div = Div(text=connection_status, width=820)

collection_select = Select(
    title="Collection ID:",
    value="EO:EUM:DAT:MSG:HRSEVIRI",
    options=[
        ("EO:EUM:DAT:MSG:HRSEVIRI", "HRSEVIRI (SEVIRI native)"),
        ("EO:EUM:DAT:MSG:MSG15-RSS", "MSG15 RSS"),
        ("EO:EUM:DAT:MSG:HRIT-SEVIRI", "HRIT SEVIRI"),
        ("EO:EUM:DAT:METOP:ASCAT", "ASCAT Wind Product"),
    ],
    width=360, stylesheets = [style2]
)
custom_collection = TextInput(title="Or enter custom Collection ID:", width=360, placeholder="e.g., EO:EUM:DAT:MSG:HRSEVIRI", stylesheets = [style2],)

start_date_input = TextInput(title="Start Date (YYYY-MM-DD)", value="2025-08-10", width=160, stylesheets = [style2])
start_hour_input = TextInput(title="Start Hour (0–23)", value="0", width=120, stylesheets = [style2])
start_min_input = TextInput(title="Start Minute (0–59)", value="0", width=120, stylesheets = [style2])

end_date_input = TextInput(title="End Date (YYYY-MM-DD)", value="2025-08-10", width=160, stylesheets = [style2])
end_hour_input = TextInput(title="End Hour (0–23)", value="2", width=120, stylesheets = [style2])
end_min_input = TextInput(title="End Minute (0–59)", value="0", width=120, stylesheets = [style2])

output_dir_input = TextInput(title="Output Directory:", value="downloads_nat", width=240, stylesheets = [style2])

download_button = Button(label="🔽 Download Files", button_type="primary", width=180)
unzip_button = Button(label="📦 Unzip Files", button_type="success", width=180)
clear_log_button = Button(label="🗑️ Clear Log", width=120)
delete_button = Button(label="🗑 Delete Zips & Extracted", button_type="danger", width=250)

log_display = PreText(text="Ready to download...\n", width=820, height=300)

current_downloads = []


# ------------------ Helpers ------------------
def log_message(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    log_display.text += f"[{ts}] {msg}\n"


# ------------------ Actions ------------------
def download_files():
    global current_downloads
    if not datastore:
        log_message("❌ No connection to EUMETSAT.")
        return

    collection_id = custom_collection.value.strip() or collection_select.value
    try:
        sh, sm = int(start_hour_input.value), int(start_min_input.value)
        eh, em = int(end_hour_input.value), int(end_min_input.value)
    except:
        log_message("❌ Invalid time input.")
        return

    try:
        sd = datetime.strptime(start_date_input.value.strip(), "%Y-%m-%d").date()
        ed = datetime.strptime(end_date_input.value.strip(), "%Y-%m-%d").date()
    except:
        log_message("❌ Invalid date input.")
        return

    start_dt = datetime.combine(sd, datetime.min.time().replace(hour=sh, minute=sm)).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(ed, datetime.min.time().replace(hour=eh, minute=em)).replace(tzinfo=timezone.utc)

    if start_dt >= end_dt:
        log_message("❌ Start date must be before end date.")
        return

    log_message(f"🔍 Searching {collection_id}")
    results = list(datastore.get_collection(collection_id).search(dtstart=start_dt, dtend=end_dt))
    log_message(f"📊 Found {len(results)} products")

    out_dir = Path(output_dir_input.value)
    out_dir.mkdir(parents=True, exist_ok=True)

    current_downloads.clear()
    count = 0
    for i, product in enumerate(results, 1):
        with product.open() as fsrc:
            fname = Path(fsrc.name).name
            dest = out_dir / fname
            if dest.exists():
                log_message(f"⚠️ Exists, skipping: {fname}")
                current_downloads.append(dest)
                continue
            log_message(f"⬇️ ({i}/{len(results)}) {fname}")
            with open(dest, "wb") as fdst:
                shutil.copyfileobj(fsrc, fdst)
            current_downloads.append(dest)
            log_message(f"✅ Saved: {fname}")
            count += 1

    log_message(f"🎉 Done. {count} new file(s) downloaded. Total: {len(current_downloads)}")
    log_message("✅ DOWNLOAD COMPLETE ✅")


def unzip_files():
    if not current_downloads:
        log_message("❌ No files to unzip.")
        return

    out_dir = Path(output_dir_input.value)
    zip_files = list(out_dir.glob("*.zip"))
    if not zip_files:
        log_message("ℹ️ No .zip files found.")
        return

    unzipped = 0
    for fp in zip_files:
        try:
            with zipfile.ZipFile(fp, "r") as zf:
                for file_name in zf.namelist():
                    if file_name.lower().endswith(".nat"):
                        zf.extract(file_name, out_dir)
                        log_message(f"📦 Extracted: {file_name}")
                unzipped += 1
        except Exception as e:
            log_message(f"❌ Failed {fp.name}: {e}")

    log_message(f"🎉 Extracted from {unzipped} archive(s).")
    log_message("✅ UNZIP COMPLETE ✅")


def clear_log():
    log_display.text = ""


def delete_zips_and_extracted():
    try:
        out_dir = Path(output_dir_input.value)
        if not out_dir.exists():
            log_message("❌ Output directory does not exist.")
            return

        deleted_files = 0

        # Delete zip files
        for zip_fp in out_dir.glob("*.zip"):
            zip_fp.unlink()
            log_message(f"🗑 Deleted zip: {zip_fp.name}")
            deleted_files += 1

        # Delete extracted folders
        for folder in out_dir.iterdir():
            if folder.is_dir():
                shutil.rmtree(folder)
                log_message(f"🗑 Deleted folder: {folder.name}")
                deleted_files += 1

        if deleted_files == 0:
            log_message("ℹ️ No zip files or folders found to delete.")
        else:
            log_message(f"✅ Deleted {deleted_files} item(s).")

    except Exception as e:
        log_message(f"❌ Delete error: {e}")

def on_delete_click():
    t = Thread(target=delete_zips_and_extracted, daemon=True)
    t.start()

delete_button.on_click(on_delete_click)
# ------------------ Event bindings ------------------
download_button.on_click(download_files)
unzip_button.on_click(unzip_files)
clear_log_button.on_click(clear_log)

# ------------------ Layout ------------------
L2 = column(
    title_div,
    status_div,
    row(collection_select, custom_collection),
    row(start_date_input, start_hour_input, start_min_input),
    row(end_date_input, end_hour_input, end_min_input),
    row(output_dir_input),
    row(download_button, unzip_button, clear_log_button,delete_button),
    log_display
)
# curdoc().title = "EUMETSAT Data Downloader"

def make_swiper():
    # Your swiper code here
    from bokeh.io import curdoc
    from bokeh.layouts import column
    from bokeh.plotting import figure
    from bokeh.models import Div, TextInput, Button
    from pathlib import Path
    from PIL import Image
    import numpy as np
    import io
    import base64
    from bokeh.io.export import get_screenshot_as_png
    title = Div(text="<h2>Image Swiper</h2>")

    # ===== Initial empty image URLs =====
    url1 = ""
    url2 = ""
    def clean_path(p: str) -> Path:
        # Remove leading file:// if present, and strip spaces
        if p.startswith("file://"):
            p = p[len("file://"):]
        return Path(p.strip())
    def load_png_as_rgba(path: Path):
        """Load PNG and return RGBA image as uint32 numpy array for Bokeh."""
        img = Image.open(path).convert("RGBA")
        arr = np.array(img, dtype=np.uint8)
        view = arr.view(dtype=np.uint32).reshape((arr.shape[0], arr.shape[1]))
        view = np.fliplr(view)  # Flip vertically for Bokeh
        return view, img.width, img.height

    def fig_to_base64_png(fig):
        """Render a Bokeh figure to PNG and return as base64 string."""
        img = get_screenshot_as_png(fig)  # Needs selenium + driver
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    # --- UI ---
    title = Div(text="<h2>PNG Image Swipe Viewer</h2>", width=800)
    input1 = TextInput(title="PNG Path 1", value="", width=800, stylesheets = [style2])
    input2 = TextInput(title="PNG Path 2", value="", width=800, stylesheets = [style2])
    load_button = Button(label="Load & Compare", button_type="success", width=200, stylesheets = [button_style])

    p1 = figure(width=600, height=400, toolbar_location=None, x_range=(0, 10), y_range=(0, 10))
    p2 = figure(width=600, height=400, toolbar_location=None, x_range=(0, 10), y_range=(0, 10))

    # Remove axis, grids
    for p in (p1, p2):
        p.axis.visible = False
        p.grid.visible = False
        p.outline_line_color = None

    # This Div will host the iframe
    iframe_div = Div(width=980, height=720)

    def update_images():
        global url1, url2
        path1 = clean_path(input1.value)
        path2 = clean_path(input2.value)

        if path1.exists():
            img_rgba, w, h = load_png_as_rgba(path1)
            p1.title.text = path1.name  # Show only filename

            p1.image_rgba(image=[img_rgba], x=0, y=0, dw=w, dh=h)
            p1.x_range.start, p1.x_range.end = 0, w
            p1.y_range.start, p1.y_range.end = 0, h
            url1 = f"data:image/png;base64,{fig_to_base64_png(p1)}"

        if path2.exists():
            img_rgba, w, h = load_png_as_rgba(path2)
            p2.title.text = path2.name  # Show only filename

            p2.image_rgba(image=[img_rgba], x=0, y=0, dw=w, dh=h)
            p2.x_range.start, p2.x_range.end = 0, w
            p2.y_range.start, p2.y_range.end = 0, h
            url2 = f"data:image/png;base64,{fig_to_base64_png(p2)}"

        # Now rebuild the swipe HTML
        html_content = f'''<!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pure JS Image Swipe</title>
    <style>
    :root {{ color-scheme: dark light; }}

    .compare {{
        --pos: 50%;
        position: relative;
        inline-size: min(900px, 95vw);
        aspect-ratio: 3 / 2;
        overflow: hidden;
        border-radius: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,.25);
        background: #111;
        user-select: none;
        touch-action: none;
    }}
    .compare img {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: contain;
        background: white;
    }}
    .compare .top {{
        clip-path: polygon(0 0, var(--pos) 0, var(--pos) 100%, 0 100%);
    }}
    .compare .divider {{
        position: absolute;
        inset: 0;
        pointer-events: none;
    }}
    .compare .divider::before {{
        content: "";
        position: absolute;
        left: var(--pos);
        top: 0;
        bottom: 0;
        width: 2px;
        background: rgba(255,255,255,.85);
        transform: translateX(-1px);
    }}
    .compare input[type="range"] {{
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        opacity: 0;
        pointer-events: auto;
    }}
    body {{
        min-height: 100vh;
        margin: 0;
        display: grid;
        place-content: center;
        gap: 16px;
        font-family: system-ui, sans-serif;
        background: #222;
        color: white;
    }}
    .label {{
        text-align: center; opacity: .8; font-size: 14px;
    }}
    </style>
    </head>
    <body>

    <div class="compare" id="compare">
    <img src="{url1}" alt="After / Background" class="bottom" />
    <img src="{url2}" alt="Before / Foreground" class="top" />
    <div class="divider"></div>
    <input type="range" min="0" max="100" value="50" aria-label="Swipe comparison position" />
    </div>

    <div class="label">Drag to compare Bokeh plots</div>

    <script>
    (function () {{
    const root = document.querySelector('.compare');
    const range = root.querySelector('input[type="range"]');

    function setPos(pct) {{
        pct = Math.max(0, Math.min(100, pct));
        root.style.setProperty('--pos', pct + '%');
        range.value = String(pct);
    }}

    let dragging = false;
    function clientX(evt) {{
        return (evt.touches && evt.touches[0] ? evt.touches[0].clientX : evt.clientX);
    }}
    function onDown(evt) {{
        dragging = true;
        root.setPointerCapture?.(evt.pointerId);
        onMove(evt);
    }}
    function onMove(evt) {{
        if (!dragging && evt.type !== 'pointermove') return;
        const rect = root.getBoundingClientRect();
        const x = clientX(evt) - rect.left;
        setPos((x / rect.width) * 100);
    }}
    function onUp() {{
        dragging = false;
    }}

    range.addEventListener('input', e => setPos(parseFloat(e.target.value)));
    root.addEventListener('mousedown', onDown);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);

    root.addEventListener('touchstart', onDown, {{passive: true}});
    window.addEventListener('touchmove', onMove, {{passive: true}});
    window.addEventListener('touchend', onUp);

    if ('onpointerdown' in window) {{
        root.addEventListener('pointerdown', onDown);
        window.addEventListener('pointermove', onMove);
        window.addEventListener('pointerup', onUp);
    }}
    setPos(parseFloat(range.value));
    }})();
    </script>
    </body>
    </html>'''

        html_b64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        iframe_html = f'<iframe src="data:text/html;base64,{html_b64}" width="960" height="700" frameborder="0"></iframe>'
        iframe_div.text = iframe_html

    load_button.on_click(update_images)

    L3 = column(
            title,
            input1,
            input2,
            load_button,
            iframe_div
        )

    return L3  # Replace with your actual layout

# ===== Create Panels =====
main_plot_panel = TabPanel(child=L1, title="NATEX")
downloader_panel = TabPanel(child=L2, title="Downloader")
swiper_panel = TabPanel(child=make_swiper(), title="Swiper")

# ===== Combine into Tabs =====
tabs = Tabs(tabs=[main_plot_panel, downloader_panel, swiper_panel], stylesheets = [tabs_style])

# ===== Only one curdoc() =====
curdoc().add_root(tabs)
curdoc().title = "NATEX"
