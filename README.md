# NATEX — a simple `.nat` files explorer

**NATEX** is a quick viewer for EUMETSAT `.nat` files built in **Python** with **Satpy** and **Bokeh**.  
It loads time-sorted frames, applies Satpy composites, overlays coastlines/borders, and lets you animate, probe pixel colors, and compare PNGs with a swipe tool. It also includes a simple **EUMETSAT downloader** tab.

## ✨ Features
- 🗺 Interactive Map Viewer. View satellite composites in Plate Carrée or Geostationary projection.
- Load `.nat` files via glob pattern
- 🌈 Multiple Composites Support for dozens of predefined composites (e.g., airmass, natural_color, dust, day_microphysics, and more).
- Plate Carrée **or** native geostationary view
- Coastlines & country borders with custom color.
- Smooth zoom & pan with WebGL rendering.
- Frame slider + play/pause animation
- 📊 Pixel Color Time Series Click any pixel in the image to see how its color changes across the loaded frames.
- 🖌 Freehand Drawing & Annotations Draw directly on the map, add custom text labels, and color your annotations. Includes Undo support with a custom toolbar icon.
- 📡 EUMETSAT Downloader Connect to the EUMETSAT Data Store, search datasets by date/time range, and download .nat files directly.
- 📦 File Management Built-in unzipper and zip cleaner.
- 🔄 Image Swipe Viewer Compare two different PNG images interactively with a draggable swipe handle.

---

1) Load your path either with a single .nat file or multiple by adding *.nat at the end (e.g. /home/michael/nats/*nat))
2) Select your Composite (and/or Reader if necessary), your area (lat, lon) and the projection (Plate Carree or Geostationary).
3) Click *Apply*. The files will be loading. It takes some time...
   
![NATEX1](assets/natex1.gif)

4) You can zoom in/out, pan and animate either with play button or the slider.
![NATEX2](assets/natex2.gif)

5) Users can change the color of the coastlines and the custom draws.
![NATEX3](assets/natex3.gif)

6) Users can draw on the plot. Click on the pen which is in the toolbar on the right of the plot. Then on the left, under the slider, type the text you want to display on the draw, and go to the map drawing for example a circle around a dust plume. You can erase the draws with the 'erase' button on the toolbar (the last one). To deactivate the pen, click again on the pen (to not be with blue mark). You can choose pan and wheel zoom to continue the exploration.
![NATEX4](assets/natex4.gif)

7) Add your credentials to download the files for the date of interest. Download, Unzip (keeps inly the .nat files) and/or remove the zip files at the end. The folder will be defined by the user in the home dir.
![NATEX5](assets/natex5.gif)

8) Finally, there is a swiper module to load the local .png and compare them. Please note, that in the folder where you downloaded the .nat files, after their loading in NATEX, the corresponding .png images will be saved in the same dir.
![NATEX6](assets/natex6.gif)



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



Docker
# 1. Build the image
docker build -t natex .

# 2. Run the container
docker run -it --rm -p 5006:5006 natex




NATEX – Satellite .nat File Explorer & Visualizer
NATEX (NATural Earth Explorer) is an interactive Python + Bokeh web application for exploring, visualizing, and analyzing EUMETSAT .nat satellite data.
It provides a modern, responsive UI with real-time map rendering, image swiping, and integrated EUMETSAT data downloads.

🚀 Features
📡 EUMETSAT Downloader
Connect to the EUMETSAT Data Store, search datasets by date/time range, and download .nat files directly.

🗺 Interactive Map Viewer

View satellite composites in Plate Carrée or Geostationary projection.

Toggle between coastlines, borders, and custom color styling.

Smooth zoom & pan with WebGL rendering.

🌈 Multiple Composites
Support for dozens of predefined composites (e.g., airmass, natural_color, dust, day_microphysics, and more).

🖌 Freehand Drawing & Annotations
Draw directly on the map, add custom text labels, and color your annotations.
Includes Undo support with a custom toolbar icon.

📊 Pixel Color Time Series
Click any pixel in the image to see how its color changes across the loaded frames.

🔄 Image Swipe Viewer
Compare two different PNG images interactively with a draggable swipe handle.

📦 File Management
Built-in unzipper, zip cleaner, and dataset organizer.

📂 App Structure
The application is organized into three main tabs:

Map – Main satellite composite viewer.

Downloader – EUMETSAT data access and file management.

Swiper – Side-by-side PNG image comparison tool.

🛠 Tech Stack
Python 3.11

Bokeh for the interactive web UI

Satpy & Pyresample for satellite data handling

Cartopy & Shapely for geospatial features

EUMDAC for EUMETSAT API access

Pillow for image manipulation

Selenium for rendering screenshots

📦 Installation
You can run NATEX either locally or inside Docker.

Local Install
bash
Αντιγραφή
Επεξεργασία
git clone https://github.com/yourusername/NATEX.git
cd NATEX

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

bokeh serve --show --port 5006 .
Docker
bash
Αντιγραφή
Επεξεργασία
docker build -t natex .
docker run -it --rm -p 5006:5006 natex
Visit: http://localhost:5006/NATEX

📷 Screenshots
(Add your UI screenshots here for visual appeal.)

📜 License
MIT License — feel free to use, modify, and share.
