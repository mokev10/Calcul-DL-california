#!/usr/bin/env python3
# driver_license_final_fixed.py

import base64
import datetime
import hashlib
import io
import random
import re
from typing import Dict, List, Optional

import requests
import streamlit as st
import streamlit.components.v1 as components

# ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

# pdf417gen (optionnel)
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# AAMVA utils (optionnel)
try:
    from aamva_utils import (
        validate_aamva_payload,
        auto_correct_payload,
        example_payload,
        GS as AAMVA_GS,
        build_aamva_payload_continuous,
    )
    _AAMVA_UTILS_AVAILABLE = True
except Exception:
    _AAMVA_UTILS_AVAILABLE = False
    AAMVA_GS = None

GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

# Page config
st.set_page_config(page_title="Permis CA", layout="wide")

# ---------- GESTION DU THÈME ----------
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# ---------- Icons fournis ----------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# ---------- Minimal ZIP DB ----------
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "92101": {"city": "San Diego", "state": "CA", "office": ""},
    "90272": {"city": "Pacific Palisades", "state": "CA", "office": ""},
    "90265": {"city": "Malibu", "state": "CA", "office": ""},
    "90266": {"city": "Malibu", "state": "CA", "office": ""},
    "90270": {"city": "Maywood", "state": "CA", "office": ""},
    "90274": {"city": "Palos Verdes Peninsula", "state": "CA", "office": ""},
    "90275": {"city": "Rancho Palos Verdes", "state": "CA", "office": ""},
    "90277": {"city": "Redondo Beach", "state": "CA", "office": ""},
}

GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"
def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    db: Dict[str, Dict[str, str]] = {}
    if not text:
        return db
    lines =
    i = 0
    while i + 2 < len(lines):
        zip_code = lines[i]
        city = lines[i+1]
        state = lines[i+2].upper()
        if re.fullmatch(r"\d{5}", zip_code) and city and state == "CA":
            db[zip_code] = {"city": city.title(), "state": "CA", "office": ""}
            i += 3
            while i < len(lines) and not lines[i]:
                i += 1
            continue
        i += 1
    return db

fetched = fetch_github_zipdb(GITHUB_RAW_ZIPDB)
if fetched:
    parsed = parse_zipdb_text(fetched)
    if parsed:
        ZIP_DB.update(parsed)

field_offices = {
    "Baie de San Francisco": {"Corte Madera": 525, "Daly City": 599, "Oakland": 501, "San Francisco": 503},
    "Grand Los Angeles": {"Los Angeles": 502, "Santa Monica": 548, "Pasadena": 510},
    "Sud Californie": {"San Diego": 707},
}
FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

ZIP_TO_CITIES: Dict[str, List[str]] = {}
CITY_TO_ZIPS: Dict[str, List[str]] = {}
for z, info in ZIP_DB.items():
    city = (info.get("city") or "").strip().title()
    if city:
        ZIP_TO_CITIES.setdefault(z, []).append(city)
        CITY_TO_ZIPS.setdefault(city, []).append(z)
if not ZIP_TO_CITIES:
    ZIP_TO_CITIES["94015"] = ["Daly City"]
    CITY_TO_ZIPS["Daly City"] = ["94015"]

# ---------- Utilities ----------
def normalize_city(value: str) -> str:
    return (value or "").strip().title()

def normalize_zip(value: str) -> str:
    return re.sub(r"\D", "", (value or ""))[:5]

def seed(*values):
    parts = []
    for item in values:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8], 16)

def rdigits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))

def rletter(rng: random.Random, initial: str) -> str:
    if isinstance(initial, str) and initial and initial[0].isalpha():
        return initial[0].upper()
    return rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(rng: random.Random) -> str:
    return str(rng.randint(10, 99))

# ---------- THEME CSS (variables + common) ----------
LIGHT_VARS = """
:root{
  --bg: #f5f7fa;
  --card-bg: #ffffff;
  --text: #0f172a;
  --muted: #6b7280;
  --accent: #2563eb;
  --control-bg: #ffffff;
  --control-border: #e6eef8;
  --photo-bg: #eef2ff;
}
"""
DARK_VARS = """
:root{
  --bg: #0b1220;
  --card-bg: #0f172a;
  --text: #e6eef8;
  --muted: #9aa6bf;
  --accent: #60a5fa;
  --control-bg: #0f172a;
  --control-border: rgba(255,255,255,0.06);
  --photo-bg: #1e293b;
}
"""

COMMON_CSS = r"""
<style>
/* Global */
html, body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: var(--text) !important; font-family: Inter, sans-serif; }

/* Card */
.card { width:520px; margin:18px auto; padding:16px; border-radius:12px; background:var(--card-bg); box-shadow:0 8px 24px rgba(2,6,23,0.06); border:1px solid var(--control-border); color:var(--text); }

/* Photo */
.photo { width:96px; height:120px; background:var(--photo-bg); border-radius:10px; overflow:hidden; border: 1px dashed var(--muted); }

/* Labels / values */
.label { opacity:0.75; font-size:11px; color:var(--muted); margin-top:6px; }
.value { font-weight:600; color:var(--text); }

/* Inputs / selects / textareas */
input, select, textarea, .stTextInput div div, .stSelectbox div div {
  background: var(--control-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--control-border) !important;
  border-radius: 10px !important;
}

/* Buttons */
.stButton button {
  background: linear-gradient(135deg,var(--accent),#1e40af) !important;
  color: #fff !important;
  border-radius: 10px !important;
  border: none !important;
}

[data-testid="stSidebar"] { background: linear-gradient(180deg,#071033,#0f172a) !important; color: white !important; }
</style>
"""

# Injection du thème
theme_choice = DARK_VARS if st.session_state.theme == 'dark' else LIGHT_VARS
st.markdown(f"<style>{theme_choice}</style>", unsafe_allow_html=True)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ---------- INTERFACE ----------
col_head, col_opt = st.columns([0.8, 0.2])
with col_head:
    st.title("Générateur officiel de permis CA")
with col_opt:
    icon_url = ICON_LIGHT if st.session_state.theme == 'dark' else ICON_DARK
    st.image(icon_url, width=24)
    st.button("Changer Mode", on_click=toggle_theme)

# Formulaire exemple pour vérifier les champs
st.subheader("Informations")
c1, c2 = st.columns(2)
with c1:
    nom = st.text_input("Nom de famille", "HAMMS")
    prenom = st.text_input("Prénom", "AVIVA")
with c2:
    zip_code = st.text_input("Code postal", "95818")
    dob = st.text_input("Date de naissance", "1980/01/01")

st.markdown(f"""
<div class="card">
    <div style="display: flex;">
        <div class="photo"></div>
        <div style="margin-left: 20px;">
            <h2 style="margin:0; color:var(--accent);">CALIFORNIA</h2>
            <p class="label">LN</p><p class="value">{nom}</p>
            <p class="label">FN</p><p class="value">{prenom}</p>
            <p class="label">DOB</p><p class="value">{dob}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
