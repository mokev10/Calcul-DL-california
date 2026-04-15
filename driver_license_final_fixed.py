#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version complète prête à coller
# - Liaison bidirectionnelle ZIP <-> Ville
# - Field Office indépendant
# - Placeholder "Choisir une option"
# - CSS injecté via components.html pour éviter qu'il s'affiche comme texte
# - Aucune modification de la logique métier

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

# AAMVA utils (validation + builder continu)
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

st.set_page_config(page_title="Permis CA", layout="wide")

# -------------------------
# Assets & constants
# -------------------------
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"

# Minimal fallback ZIP_DB (ensures dropdowns always have values)
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

# -------------------------
# Helpers to load/parse ZIP_DB (attempt GitHub fetch)
# -------------------------
def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    db: Dict[str, Dict[str, str]] = {}
    if not text:
        return db

    lines = [ln.strip() for ln in text.splitlines()]
    i = 0
    while i + 2 < len(lines):
        zip_code = lines[i]
        city = lines[i + 1]
        state = lines[i + 2].upper()
        if re.fullmatch(r"\d{5}", zip_code) and city and state == "CA":
            db[zip_code] = {"city": city.title(), "state": "CA", "office": ""}
            i += 3
            while i < len(lines) and not lines[i]:
                i += 1
            continue
        i += 1

    # fallback heuristique seulement si parsing strict vide
    if not db:
        for ln in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            m = re.search(r"\b(\d{5})\b", ln)
            if not m:
                continue
            zip_code = m.group(1)
            before = ln[:m.start()].strip(" ,;-")
            after = ln[m.end():].strip(" ,;-")
            city = ""
            if before and re.search(r"[A-Za-z]", before):
                city = re.split(r"[,\-–:]", before)[-1].strip().title()
            elif after and re.search(r"[A-Za-z]", after):
                city = re.split(r"[,\-–:]", after)[0].strip().title()
            if city:
                db[zip_code] = {"city": city, "state": "CA", "office": ""}

    return db


fetched = fetch_github_zipdb(GITHUB_RAW_ZIPDB)
if fetched:
    parsed = parse_zipdb_text(fetched)
    if parsed:
        ZIP_DB.update(parsed)

# -------------------------
# Field offices mapping (flattened)
# -------------------------
field_offices = {
    "Baie de San Francisco": {
        "Corte Madera": 525, "Daly City": 599, "El Cerrito": 585, "Fremont": 643,
        "Hayward": 521, "Los Gatos": 641, "Novato": 647, "Oakland": 501,
        "Pittsburg": 651, "Pleasanton": 639, "Redwood City": 542,
        "San Francisco": 503, "San Jose": 516, "San Mateo": 594, "Santa Clara": 632,
        "Vallejo": 538,
    },
    "Grand Los Angeles": {
        "Arleta": 628, "Bellflower": 610, "Culver City": 514, "Glendale": 540,
        "Hollywood": 633, "Inglewood": 544, "Long Beach": 507, "Los Angeles": 502,
        "Montebello": 531, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592,
        "West Covina": 591,
    },
    "Orange County / Sud": {
        "Costa Mesa": 627, "Fullerton": 547, "Laguna Hills": 642, "Santa Ana": 529,
        "San Clemente": 652, "Westminster": 623, "Garden Grove": 547, "Anaheim": 547,
    },
    "Vallée Centrale": {
        "Bakersfield": 511, "Fresno": 505, "Lodi": 595, "Modesto": 536, "Stockton": 517,
        "Visalia": 519, "Sacramento": 505,
    },
    "Sud Californie": {
        "San Diego": 707,
    },
}

FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

# -------------------------
# Build mapping for ZIP <-> City linkage
# -------------------------
ZIP_TO_CITIES: Dict[str, List[str]] = {}
CITY_TO_ZIPS: Dict[str, List[str]] = {}

for z, info in ZIP_DB.items():
    city = (info.get("city") or "").strip().title()
    if city:
        ZIP_TO_CITIES.setdefault(z, []).append(city)
        CITY_TO_ZIPS.setdefault(city, []).append(z)

# Ensure at least one mapping exists
if not ZIP_TO_CITIES:
    ZIP_TO_CITIES["94015"] = ["Daly City"]
    CITY_TO_ZIPS["Daly City"] = ["94015"]

# -------------------------
# Utility functions
# -------------------------
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


def build_aamva_tags(fields: Dict[str, str]) -> str:
    enriched = dict(fields)
    enriched.setdefault("DAG", "2570 24TH STREET")
    enriched.setdefault("DAI", "OAKLAND")
    enriched.setdefault("DAJ", "CA")
    enriched.setdefault("DAK", "94601")
    if _AAMVA_UTILS_AVAILABLE:
        return build_aamva_payload_continuous(enriched)
    ordered = ["DAQ", "DCS", "DAC", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"]
    return "@ANSI 636014080102DL" + "".join(f"{tag}{enriched.get(tag,'')}" for tag in ordered if enriched.get(tag))

# -------------------------
# CSS string (kept in a Python variable)
# -------------------------
CSS = """
/* Global */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #f5f7fa; color: #0f172a; }

/* Container card */
.card {
  width: 520px;
  border-radius: 14px;
  padding: 18px;
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(250,250,252,0.96));
  border: 1px solid rgba(30,58,138,0.06);
  box-shadow: 0 10px 30px rgba(16,24,40,0.06);
  margin: 18px auto;
  transition: transform .18s ease, box-shadow .18s ease;
}
.card:hover { transform: translateY(-4px); box-shadow: 0 18px 40px rgba(16,24,40,0.08); }

/* Header / badge */
.card .header { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; color:#0f172a; font-weight:700; }
.card .badge { background:#ffffff; color:#0f172a; padding:6px 10px; border-radius:8px; font-weight:700; box-shadow:0 4px 12px rgba(2,6,23,0.06); }

/* Photo */
.photo { width:96px; height:120px; background:#eef2ff; border-radius:10px; overflow:hidden; border:1px solid rgba(15,23,42,0.04); }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }

/* Info column */
.info { flex:1; font-size:13px; line-height:1.35; color:#0b1220; }
.label { opacity:0.7; font-size:11px; margin-top:6px; }
.value { font-weight:600; margin-bottom:6px; color:#071033; }

/* Form controls styling */
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select, textarea {
  border-radius:10px !important;
  border:1px solid #e6eef8 !important;
  padding:8px 10px !important;
  background:#ffffff !important;
  box-shadow:none !important;
  font-size:13px !important;
}

/* Force selectbox container sizing and prevent overflow */
.stSelectbox, .stSelectbox>div, .stSelectbox>div>div {
  max-width: 100% !important;
  box-sizing: border-box !important;
  overflow: hidden !important;
}

/* Visible select control: truncate long text with ellipsis */
.stSelectbox select, .stSelectbox select {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  display: inline-block !important;
  max-width: 100% !important;
}

/* Also target common Streamlit internal classes for different versions */
.css-1v3fvcr .stSelectbox select, .css-1v3fvcr select {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

/* Make placeholder visually distinct */
.stSelectbox select option:first-child {
  color: #6b7280;
  font-style: italic;
}

/* Focus style */
.stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, textarea:focus {
  outline: none !important;
  box-shadow: 0 6px 18px rgba(37,99,235,0.12) !important;
  border-color: #2563eb !important;
}

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0f172a,#1e293b); color: #e6eef8; }
section[data-testid="stSidebar"] .css-1d391kg { color: #e6eef8; }
section[data-testid="stSidebar"] .stMarkdown { color: #e6eef8; }

/* Buttons and download buttons */
button, .stDownloadButton button {
  background: linear-gradient(135deg,#2563eb,#1e40af) !important;
  color: #fff !important;
  border-radius: 10px !important;
  padding: 8px 14px !important;
  border: none !important;
  font-weight: 600 !important;
  box-shadow: 0 6px 18px rgba(37,99,235,0.12) !important;
}
button:hover, .stDownloadButton button:hover { transform: translateY(-2px); }

/* Expander and panels */
.stExpander { border-radius:10px !important; border:1px solid rgba(15,23,42,0.04) !important; background: #fff !important; }
.stExpanderSummary { font-weight:600 !important; }

/* PDF417 preview container */
[data-testid="stMarkdownContainer"] > div > div > svg {
  max-width: 100% !important;
  height: auto !important;
  display: block;
  margin: 8px auto;
}

/* Progress bar */
div[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg,#2563eb,#1e40af) !important;
  border-radius: 8px !important;
}

/* Small screens adjustments */
@media (max-width: 800px) {
  .card { width: 92% !important; padding: 14px; }
  .photo { width:84px; height:104px; }
  .stSelectbox select { font-size: 14px !important; }
}

/* Minor utility tweaks */
.kv { color:#64748b; font-size:12px; }
"""

# Inject CSS via components.html with height=0 to avoid visible text rendering
components.html(f"<style>{CSS}</style>", height=0)

# -------------------------
# Sidebar controls
# -------------------------
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6, key="sb_columns")
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0, 9)), index=2, key="sb_ecc")
scale_param = st.sidebar.slider("Échelle (SVG)", 1, 6, 3, key="sb_scale")
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3, key="sb_ratio")
color_param = st.sidebar.color_picker("Couleur du code", "#000000", key="sb_color")

st.sidebar.markdown("---")
if "show_barcodes" not in st.session_state:
    st.session_state["show_barcodes"] = True
show_barcodes = st.sidebar.checkbox(
    "Afficher les codes-barres (PDF417)",
    value=st.session_state["show_barcodes"],
    key="sb_show_barcodes",
)

st.sidebar.markdown("---")
enable_validator = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False, key="sb_enable_validator")
if enable_validator and not _AAMVA_UTILS_AVAILABLE:
    st.sidebar.info("aamva_utils.py introuvable — la validation est désactivée automatiquement.")

# -------------------------
# Callbacks to keep ZIP <-> City linked (bidirectional)
# -------------------------
def on_zip_change():
    z = normalize_zip(st.session_state.get("ui_zip", ""))
    if not z:
        return
    cities = ZIP_TO_CITIES.get(z, [])
    if cities:
        st.session_state["ui_city"] = cities[0]


def on_city_change():
    city = normalize_city(st.session_state.get("ui_city", ""))
    if not city:
        return
    zips = CITY_TO_ZIPS.get(city, [])
    if zips:
        st.session_state["ui_zip"] = zips[0]

# -------------------------
# Main UI form (ZIP and City linked; Field Office independent)
# -------------------------
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom de famille", "HARMS", key="ui_ln")
fn = st.text_input("Prénom", "ROSA", key="ui_fn")
sex = st.selectbox("Sexe", ["M", "F"], key="ui_sex")
dob = st.date_input("Date de naissance", datetime.date(1990, 1, 1), key="ui_dob")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds", 0, 8, 5, key="ui_h1")
    w = st.number_input("Poids (lb)", 30, 500, 160, key="ui_w")
with col2:
    h2 = st.number_input("Pouces", 0, 11, 10, key="ui_h2")
    eyes = st.text_input("Yeux", "BRN", key="ui_eyes")
hair = st.text_input("Cheveux", "BRN", key="ui_hair")
cls = st.text_input("Classe", "C", key="ui_cls")
rstr = st.text_input("Restrictions", "NONE", key="ui_rstr")
endorse = st.text_input("Endorsements", "NONE", key="ui_endorse")
iss = st.date_input("Date d'émission", datetime.date.today(), key="ui_iss")
address_line = st.text_input("Address Line", "2570 24TH STREET", key="ui_address_line")

# Build options lists with placeholder first
placeholder = "Choisir une option"

zip_options = [placeholder] + sorted(ZIP_TO_CITIES.keys())
city_options_all = sorted(CITY_TO_ZIPS.keys())
office_options_from_db = sorted({info.get("office") for info in ZIP_DB.values() if info.get("office")})
field_office_labels = sorted(set(FIELD_OFFICE_MAP.values()))
office_options = [placeholder] + sorted(set(office_options_from_db) | set(field_office_labels)) if (office_options_from_db or field_office_labels) else [placeholder]

# Ensure session defaults exist (use placeholder as default)
if "ui_zip" not in st.session_state:
    st.session_state["ui_zip"] = placeholder
if "ui_city" not in st.session_state:
    st.session_state["ui_city"] = placeholder
if "ui_office" not in st.session_state:
    st.session_state["ui_office"] = office_options[0] if office_options else placeholder

# Layout: limit column widths to avoid overflow
col_zip, col_city = st.columns([1.2, 1.8])
with col_zip:
    st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state["ui_zip"]) if st.session_state["ui_zip"] in zip_options else 0,
        key="ui_zip",
        on_change=on_zip_change,
        help="Sélectionnez un code postal — la ville associée sera mise à jour automatiquement."
    )

# Determine cities to show based on selected zip (if placeholder selected, show all cities)
selected_zip = st.session_state.get("ui_zip", placeholder)
if selected_zip != placeholder and selected_zip in ZIP_TO_CITIES:
    cities_for_zip = [placeholder] + ZIP_TO_CITIES[selected_zip]
else:
    cities_for_zip = [placeholder] + city_options_all

# Ensure ui_city is valid for the current cities_for_zip
if st.session_state.get("ui_city") not in cities_for_zip:
    st.session_state["ui_city"] = cities_for_zip[0]

with col_city:
    st.selectbox(
        "Ville",
        options=cities_for_zip,
        index=cities_for_zip.index(st.session_state["ui_city"]) if st.session_state["ui_city"] in cities_for_zip else 0,
        key="ui_city",
        on_change=on_city_change,
        help="Sélectionnez une ville — le code postal associé sera mis à jour automatiquement."
    )

st.selectbox(
    "Field Office",
    options=office_options,
    index=office_options.index(st.session_state["ui_office"]) if st.session_state["ui_office"] in office_options else 0,
    key="ui_office",
    help="Sélectionnez un Field Office (indépendant des autres menus).",
)

generate = st.button("Générer la carte", key="ui_generate")

# -------------------------
# Validation & generation helpers
# -------------------------
def validate_inputs() -> List[str]:
    errors: List[str] = []
    if not st.session_state.get("ui_ln", "").strip():
        errors.append("Nom de famille requis.")
    if not st.session_state.get("ui_fn", "").strip():
        errors.append("Prénom requis.")
    if st.session_state.get("ui_dob") > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if st.session_state.get("ui_iss") > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if st.session_state.get("ui_w", 0) < 30 or st.session_state.get("ui_w", 0) > 500:
        errors.append("Poids hors plage attendue.")
    if st.session_state.get("ui_h1", 0) > 8 or st.session_state.get("ui_h2", 0) > 11:
        errors.append("Taille hors plage attendue.")

    zip_code_raw = st.session_state.get("ui_zip", "")
    city_raw = st.session_state.get("ui_city", "")
    address = st.session_state.get("ui_address_line", "").strip()

    if not zip_code_raw or zip_code_raw == placeholder:
        errors.append("Code postal requis.")
    if not city_raw or city_raw == placeholder:
        errors.append("Ville requise pour générer le code PDF417")
    if not address:
        errors.append("Adresse requise.")

    return errors


def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def create_pdf_bytes(fields: Dict[str, str], photo_bytes: bytes = None) -> bytes:
    if not _REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab non disponible.")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x, y = 72, height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE")
    y -= 24
    c.setFont("Helvetica", 11)
    for key, val in fields.items():
        c.drawString(x, y, f"{key}: {val}")
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    if photo_bytes and ImageReader is not None:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 162, height - 182, width=90, height=110)
        except Exception:
            pass
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_pdf417_svg(data_bytes: bytes, columns: int, security_level: int, scale: int, ratio: int, color: str) -> str:
    if not _PDF417_AVAILABLE:
        raise RuntimeError("Module pdf417gen non disponible.")
    codes = encode(data_bytes, columns=columns, security_level=security_level, force_binary=False)
    svg_tree = render_svg(codes, scale=scale, ratio=ratio, color=color)
    try:
        import xml.etree.ElementTree as ET
        svg_bytes = ET.tostring(svg_tree.getroot(), encoding="utf-8", method="xml")
        return svg_bytes.decode("utf-8")
    except Exception:
        return str(svg_tree)

# -------------------------
# Generation flow
# -------------------------
if generate:
    errors = validate_inputs()
    if errors:
        for err in errors:
            st.error(err)
        st.stop()

    ln = st.session_state["ui_ln"]
    fn = st.session_state["ui_fn"]
    sex = st.session_state["ui_sex"]
    dob = st.session_state["ui_dob"]
    h1 = st.session_state["ui_h1"]
    h2 = st.session_state["ui_h2"]
    w = st.session_state["ui_w"]
    eyes = st.session_state["ui_eyes"]
    hair = st.session_state["ui_hair"]
    cls = st.session_state["ui_cls"]
    rstr = st.session_state["ui_rstr"]
    endorse = st.session_state["ui_endorse"]
    iss = st.session_state["ui_iss"]
    zip_sel = normalize_zip(st.session_state["ui_zip"])
    city_sel = normalize_city(st.session_state["ui_city"])
    office_sel = st.session_state["ui_office"]
    address_sel = st.session_state["ui_address_line"].strip()

    rng = random.Random(seed(ln, fn, dob))
    dl = rletter(rng, ln[0] if ln else "") + rdigits(rng, 7)

    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        exp = datetime.date(exp_year, dob.month, min(dob.day, 28))

    m = re.search(r"\((\d{2,3})\)", office_sel or "")
    office_code = int(m.group(1)) if m else 0
    seq = next_sequence(rng).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}/{seq}FD/{iss.year % 100}"

    fields = {
        "DAQ": dl,
        "DCS": ln.upper().strip(),
        "DAC": fn.upper().strip(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAG": address_sel.upper(),
        "DAI": city_sel.upper(),
        "DAJ": "CA",
        "DAK": zip_sel,
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": (eyes or "").upper(),
        "DAZ": (hair or "").upper(),
    }

    for required in ("DAG", "DAI", "DAJ", "DAK"):
        if not str(fields.get(required, "")).strip():
            st.error(f"Champ AAMVA obligatoire manquant: {required}")
            st.stop()

    if _AAMVA_UTILS_AVAILABLE:
        payload_to_use = build_aamva_payload_continuous(fields)
    else:
        ordered = ["DAQ", "DCS", "DAC", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"]
        payload_to_use = "@ANSI 636014080102DL" + "".join(
            f"{tag}{str(fields.get(tag, '')).strip()}" for tag in ordered if str(fields.get(tag, "")).strip()
        )

    if any(x in payload_to_use for x in ("\n", "\r", "\x1E")):
        st.error("Payload invalide: des séparateurs interdits ont été détectés.")
        st.stop()

    photo_src = IMAGE_M_URL if sex == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/jpeg" if photo_bytes[:3] == b"\xff\xd8\xff" else "image/png"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    html = f"""
    <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">CALIFORNIA USA DRIVER LICENSE</div>
            <div style="background:white;color:#1e3a8a;padding:4px 8px;border-radius:6px;font-weight:700">{dl}</div>
        </div>
        <div style="display:flex;gap:12px">
            {photo_html}
            <div style="font-size:12px">
                <div style="opacity:0.8;font-size:10px">Nom</div><div style="font-weight:700">{ln}</div>
                <div style="opacity:0.8;font-size:10px">Prénom</div><div style="font-weight:700">{fn}</div>
                <div style="opacity:0.8;font-size:10px">Address</div><div style="font-weight:700">{address_sel}</div>
                <div style="opacity:0.8;font-size:10px">Ville / ZIP</div><div style="font-weight:700">{city_sel} / {zip_sel}</div>
                <div style="opacity:0.8;font-size:10px">Field Office</div><div style="font-weight:700">{office_sel}</div>
                <div style="opacity:0.8;font-size:10px">ISS / EXP</div><div style="font-weight:700">{iss.strftime('%m/%d/%Y')} / {exp.strftime('%m/%d/%Y')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Optional validation UI
    if enable_validator and _AAMVA_UTILS_AVAILABLE:
        st.subheader("Validation AAMVA (optionnelle)")
        results = validate_aamva_payload(payload_to_use)
        with st.expander("Résultats de validation", expanded=True):
            if results.get("errors"):
                st.error(f"Erreurs détectées ({len(results['errors'])}) :")
                for e in results["errors"]:
                    st.write("- " + e)
            else:
                st.success("Aucune erreur bloquante détectée.")
            for wmsg in results.get("warnings", []):
                st.warning(wmsg)
            for info in results.get("infos", []):
                st.info(info)

            corrected, applied = auto_correct_payload(payload_to_use)
            if corrected and corrected != payload_to_use:
                st.markdown("### Version corrigée proposée")
                for a in applied:
                    st.write("- " + a)
                st.text_area("Payload corrigé (modifiable)", value=corrected, height=200, key="ui_aamva_corrected_preview")
                if st.button("Appliquer la correction et utiliser pour génération", key="ui_apply_correction"):
                    payload_to_use = st.session_state.get("ui_aamva_corrected_preview", corrected)
                    st.success("Correction appliquée.")

    # PDF417 generation & preview
    svg_str = None
    if show_barcodes:
        st.subheader("PDF417")
        if _PDF417_AVAILABLE:
            try:
                svg_str = generate_pdf417_svg(
                    payload_to_use.encode("utf-8"),
                    columns=columns_param,
                    security_level=security_level_param,
                    scale=scale_param,
                    ratio=ratio_param,
                    color=color_param,
                )
                svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
                with st.expander("Aperçu PDF417 (SVG)", expanded=True):
                    components.html(svg_html, height=260, scrolling=True)
                    st.download_button("Télécharger PDF417 (SVG)", data=svg_str.encode("utf-8"), file_name="pdf417.svg", mime="image/svg+xml", key="dl_pdf417_svg_main")
            except Exception as exc:
                st.error("Erreur génération PDF417 : " + str(exc))
        else:
            st.warning("pdf417gen non disponible. Vendorisez le module ou installez pdf417gen.")

    # Downloads
    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            st.download_button("Télécharger PDF417 (SVG) (panel)", data=svg_str.encode("utf-8"), file_name="pdf417_panel.svg", mime="image/svg+xml", key="dl_pdf417_svg_panel")
    with cols[1]:
        try:
            pdf_bytes = create_pdf_bytes({
                "Nom": ln,
                "Prénom": fn,
                "Address": address_sel,
                "Sexe": sex,
                "DOB": dob.strftime("%m/%d/%Y"),
                "Ville": city_sel,
                "ZIP": zip_sel,
                "Field Office": office_sel,
                "ISS": iss.strftime("%m/%d/%Y"),
                "EXP": exp.strftime("%m/%d/%Y"),
                "Classe": cls.upper(),
                "Restrictions": rstr.upper(),
                "Endorsements": endorse.upper(),
                "Yeux/Cheveux/Taille/Poids": f"{eyes.upper()}/{hair.upper()}/{int(h1)}'{int(h2)}\"/{w} lb",
            }, photo_bytes=photo_bytes)
            st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf", mime="application/pdf", key="dl_permis_pdf")
        except Exception as exc:
            st.error("Erreur génération PDF : " + str(exc))
            if not _REPORTLAB_AVAILABLE:
                st.info("reportlab non installé : export PDF non disponible.")
