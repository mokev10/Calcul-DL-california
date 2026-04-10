#!/usr/bin/env python3
# driver_license_final_fixed.py
# Streamlit app — Générateur de permis CA
# Intègre ZIP_DB depuis GitHub et un dictionnaire field_offices intégré.
# Ajoute trois options de téléchargement du code-barres PDF417 : SVG, PNG, GIF.
#
# Requirements:
# pip install streamlit requests reportlab pdf417gen cairosvg pillow

import streamlit as st
import datetime
import random
import hashlib
import io
import base64
import requests
import re
from typing import Dict, List, Optional
import streamlit.components.v1 as components

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# Configuration: GitHub raw URL for ZIP_DB.txt
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"

# -------------------------
# Field offices dict (extrait simplifié)
field_offices = {
    "Grand Los Angeles": {
        "Los Angeles (Hope St)": 502,
        "Arleta": 628,
        "Bellflower": 610,
        "Culver City": 514,
        "Glendale": 540,
        "Hollywood": 633,
        "Inglewood": 544,
        "Long Beach": 507,
        "Montebello": 531,
        "Pasadena": 510,
        "Santa Monica": 548,
        "Torrance": 592,
        "West Covina": 591
    }
    # ... autres régions comme dans ton dictionnaire complet
}

FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        label = f"{region} — {city} ({code})"
        FIELD_OFFICE_MAP[city.upper()] = label

# -------------------------
# Utilitaires
def seed(*x):
    parts = []
    for item in x:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8], 16)

def rdigits(r, n): return "".join(r.choice("0123456789") for _ in range(n))
def rletter(r, initial): return initial[0].upper() if initial and initial[0].isalpha() else random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
def next_sequence(r): return str(r.randint(10, 99))

# -------------------------
# Fetch ZIP_DB.txt
def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    db: Dict[str, Dict[str, str]] = {}
    if not text: return db
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i in range(len(lines)-2):
        if re.fullmatch(r"\d{5}", lines[i]):
            z = lines[i]
            city = lines[i+1].title()
            state = lines[i+2]
            db[z] = {"city": city, "state": state, "office": ""}
    return db

ZIP_DB = {"94015": {"city": "Daly City", "state": "CA", "office": ""}}
fetched_text = fetch_github_zipdb(GITHUB_RAW_ZIPDB)
if fetched_text:
    ZIP_DB.update(parse_zipdb_text(fetched_text))

# -------------------------
# Appliquer FIELD_OFFICE_MAP
def normalize_key(s: str) -> str: return re.sub(r"[^\w]", "", (s or "").upper())
norm_field_map = {normalize_key(k): v for k,v in FIELD_OFFICE_MAP.items()}
for z, info in ZIP_DB.items():
    city = info.get("city","")
    key = normalize_key(city)
    if key in norm_field_map:
        ZIP_DB[z]["office"] = norm_field_map[key]

CITY_TO_ZIPS = {info["city"].upper(): [z] for z,info in ZIP_DB.items() if info.get("city")}
OFFICE_TO_ZIPS = {info["office"]: [z] for z,info in ZIP_DB.items() if info.get("office")}

# -------------------------
# PDF417
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    pass

def generate_pdf417_svg(data_bytes: bytes, columns:int, security_level:int, scale:int, ratio:int, color:str) -> str:
    codes = encode(data_bytes, columns=columns, security_level=security_level, force_binary=False)
    svg_tree = render_svg(codes, scale=scale, ratio=ratio, color=color)
    import xml.etree.ElementTree as ET
    return ET.tostring(svg_tree.getroot(), encoding="utf-8", method="xml").decode("utf-8")

# -------------------------
# UI
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom", "HARMS")
fn = st.text_input("Prénom", "ROSA")
zip_select = st.selectbox("Code postal", sorted(ZIP_DB.keys()))
city_select = st.selectbox("Ville", sorted({info["city"] for info in ZIP_DB.values() if info.get("city")}))
office_select = st.selectbox("Field Office", sorted(set(FIELD_OFFICE_MAP.values())))

generate = st.button("Générer la carte")

if generate:
    r = random.Random(seed(ln, fn))
    dl = rletter(r, ln) + rdigits(r,7)
    fields = {"DCS": ln, "DAC": fn, "DAQ": dl}
    aamva = "@\n\rANSI 636014080102DL\n" + "\n".join(f"{k}{v}" for k,v in fields.items())
    data_bytes = aamva.encode("utf-8")

    if _PDF417_AVAILABLE:
        svg_str = generate_pdf417_svg(data_bytes, columns=6, security_level=2, scale=3, ratio=3, color="#000000")
        svg_str = svg_str.replace('<svg ', '<svg shape-rendering="crispEdges" ')
        st.markdown(svg_str, unsafe_allow_html=True)

        # Téléchargements
        import cairosvg
        from PIL import Image
        png_bytes = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), scale=4)
        img = Image.open(io.BytesIO(png_bytes))
        buf = io.BytesIO(); img.save(buf, format="GIF"); gif_bytes = buf.getvalue()

        cols = st.columns(3)
        with cols[0]:
            st.download_button("Télécharger SVG", svg_str.encode("utf-8"), "pdf417.svg", "image/svg+xml")
        with cols[1]:
            st.download_button("Télécharger PNG", png_bytes, "pdf417.png", "image/png")
        with cols[2]:
            st.download_button("Télécharger GIF", gif_bytes, "pdf417.gif", "image/gif")
    else:
        st.error("pdf417gen non disponible.")
