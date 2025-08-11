# NATEX — a simple `.nat` explorer (Satpy + Bokeh)

**NATEX** is a fast, minimal viewer for EUMETSAT **SEVIRI** `.nat` files built with **Satpy** and **Bokeh**.  
It loads time-sorted frames, applies Satpy composites, overlays coastlines/borders, and lets you animate, probe pixel colors, and compare PNGs with a swipe tool. It also includes a small **EUMETSAT downloader** tab.

## ✨ Features
- Load `.nat` files via glob pattern and auto-group by timestamp
- Choose from many Satpy composites (e.g., `day_microphysics`, `airmass`, `natural_color`, …)
- Plate Carrée **or** native geostationary view
- Coastlines & country borders (Natural Earth)
- Frame slider + play/pause animation
- Pixel color timeline on click (alpha-aware)
- Simple downloader for EUMETSAT collections (optional)
- A “Swiper” tab to visually compare two PNGs

---

## 🧰 Requirements

### Python
- Python **3.10+** (3.11 recommended)

### System packages (for Cartopy/Proj/GEOS)
On Debian/Ubuntu:
```bash
sudo apt-get update && sudo apt-get install -y \
  python3-dev build-essential \
  libproj-dev proj-data proj-bin \
  libgeos-dev \
  libgdal-dev gdal-bin
```

# 1) create & activate a virtual env
python -m venv .venv
source .venv/bin/activate

# 2) upgrade pip
pip install --upgrade pip

# 3) install deps (conda users can skip to "Run")
pip install \
  bokeh==3.* \
  satpy \
  pyresample \
  cartopy \
  pillow \
  shapely \
  pyproj \
  numpy \
  eumdac


# from the repo root:
bokeh serve app.py --port 5006 --show
bokeh serve app.py --port 5006 --allow-websocket-origin="*"
