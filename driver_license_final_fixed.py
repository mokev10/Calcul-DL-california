#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version finale : thème (light/dark) robuste + CSS ciblé pour widgets + toggle icône seule
# Remplace entièrement ton ancien fichier par celui-ci.

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

st.set_page_config(page_title="Permis CA", layout="wide")

# ---------- Icons fournis ----------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# ---------- Data minimal ----------
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

# Try to fetch extended ZIP DB (non bloquant)
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
    lines = [ln.strip() for ln in text.splitlines()]
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

# Field offices (unchanged)
field_offices = {
    "Baie de San Francisco": {"Corte Madera": 525, "Daly City": 599, "Oakland": 501, "San Francisco": 503},
    "Grand Los Angeles": {"Los Angeles": 502, "Santa Monica": 548, "Pasadena": 510},
    "Sud Californie": {"San Diego": 707},
}
FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

# Build ZIP <-> City mapping
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

# ---------- THEME CSS (ciblé pour widgets) ----------
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
  --photo-bg: #0f172a;
}
"""

COMMON_CSS = r"""
html, body, [class*="css"] { background: var(--bg) !important; color: var(--text) !important; font-family: Inter, sans-serif; }

/* Card */
.card { width:520px; margin:18px auto; padding:16px; border-radius:12px; background:var(--card-bg); box-shadow:0 8px 24px rgba(2,6,23,0.06); border:1px solid var(--control-border); color:var(--text); }

/* Photo */
.photo { width:96px; height:120px; background:var(--photo-bg); border-radius:10px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; }

/* Labels / values */
.label { opacity:0.75; font-size:11px; color:var(--muted); margin-top:6px; }
.value { font-weight:600; color:var(--text); }

/* Inputs / selects / textareas */
input[type="text"], input[type="number"], textarea, select, .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {
  background: var(--control-bg) !important;
  color: var(--text) !important;
  border: 1px solid var(--control-border) !important;
  border-radius: 10px !important;
  padding: 8px 10px !important;
  box-shadow: none !important;
  font-size: 13px !important;
}

/* Select truncation */
.stSelectbox select, select {
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  max-width: 100% !important;
}

/* Buttons */
button, .stDownloadButton button {
  background: linear-gradient(135deg,var(--accent),#1e40af) !important;
  color: #fff !important;
  border-radius: 10px !important;
  padding: 8px 12px !important;
  border: none !important;
  font-weight: 600 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#071033,#0f172a) !important; color: var(--text) !important; }

/* Expander */
.stExpander { background: var(--card-bg) !important; border-radius:8px !important; }

/* Progress bar */
div[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,var(--accent),#1e40af) !important; border-radius:8px !important; }

/* PDF417 svg preview */
[data-testid="stMarkdownContainer"] > div > div > svg { max-width:100% !important; height:auto !important; display:block; margin:8px auto; }

/* Header toggle area */
.header-toggle { display:flex; justify-content:flex-end; align-items:center; gap:8px; }
.header-toggle img { width:22px; height:22px; border-radius:6px; }

/* Small screens */
@media (max-width:800px) {
  .card { width:92% !important; padding:12px !important; }
  .photo { width:84px; height:104px; }
}
"""

def inject_css_for_theme(theme: str):
    vars_css = LIGHT_VARS if theme == "light" else DARK_VARS
    full = f"<style>{vars_css}\n{COMMON_CSS}</style>"
    # inject invisibly (height=0) to avoid showing raw CSS
    components.html(full, height=0)

# Initialize theme in session_state
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"
inject_css_for_theme(st.session_state["theme"])

# ---------- Sidebar controls ----------
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6, key="sb_columns")
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0, 9)), index=2, key="sb_ecc")
scale_param = st.sidebar.slider("Échelle (SVG)", 1, 6, 3, key="sb_scale")
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3, key="sb_ratio")
color_param = st.sidebar.color_picker("Couleur du code", "#000000", key="sb_color")
st.sidebar.markdown("---")
if "show_barcodes" not in st.session_state:
    st.session_state["show_barcodes"] = True
show_barcodes = st.sidebar.checkbox("Afficher les codes-barres (PDF417)", value=st.session_state["show_barcodes"], key="sb_show_barcodes")
st.sidebar.markdown("---")
enable_validator = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False, key="sb_enable_validator")
if enable_validator and not _AAMVA_UTILS_AVAILABLE:
    st.sidebar.info("aamva_utils.py introuvable — validation désactivée.")

# ---------- Header with icon-only toggle ----------
header_col1, header_col2 = st.columns([8, 2])
with header_col1:
    st.markdown("<h2 style='margin:0;padding:0'>Générateur officiel de permis CA</h2>", unsafe_allow_html=True)
with header_col2:
    current = st.session_state.get("theme", "light")
    target = "dark" if current == "light" else "light"
    icon_to_show = ICON_DARK if target == "dark" else ICON_LIGHT
    # Render icon and a tiny invisible button to toggle theme server-side
    st.markdown(f'<div class="header-toggle"><img src="{icon_to_show}" alt="toggle" /></div>', unsafe_allow_html=True)
    # invisible button (label is a single space to avoid visible text)
    if st.button(" ", key="ui_toggle_theme_icon"):
        st.session_state["theme"] = target
        inject_css_for_theme(st.session_state["theme"])
        st.success(f"Thème changé en {st.session_state['theme']}. Rechargez la page si nécessaire (Ctrl+R).")

# ---------- Callbacks ZIP <-> City ----------
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

# ---------- Main form ----------
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

placeholder = "Choisir une option"
zip_options = [placeholder] + sorted(ZIP_TO_CITIES.keys())
city_options_all = sorted(CITY_TO_ZIPS.keys())
office_options_from_db = sorted({info.get("office") for info in ZIP_DB.values() if info.get("office")})
field_office_labels = sorted(set(FIELD_OFFICE_MAP.values()))
office_options = [placeholder] + sorted(set(office_options_from_db) | set(field_office_labels)) if (office_options_from_db or field_office_labels) else [placeholder]

if "ui_zip" not in st.session_state:
    st.session_state["ui_zip"] = placeholder
if "ui_city" not in st.session_state:
    st.session_state["ui_city"] = placeholder
if "ui_office" not in st.session_state:
    st.session_state["ui_office"] = office_options[0] if office_options else placeholder

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

selected_zip = st.session_state.get("ui_zip", placeholder)
if selected_zip != placeholder and selected_zip in ZIP_TO_CITIES:
    cities_for_zip = [placeholder] + ZIP_TO_CITIES[selected_zip]
else:
    cities_for_zip = [placeholder] + city_options_all

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

# ---------- Validation & helpers (inchangés) ----------
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

# ---------- Generation flow ----------
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

    IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
    IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
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
            <div style="background:var(--control-bg);color:var(--text);padding:4px 8px;border-radius:6px;font-weight:700">{dl}</div>
        </div>
        <div style="display:flex;gap:12px">
            {photo_html}
            <div style="font-size:12px">
                <div class="label">Nom</div><div class="value">{ln}</div>
                <div class="label">Prénom</div><div class="value">{fn}</div>
                <div class="label">Address</div><div class="value">{address_sel}</div>
                <div class="label">Ville / ZIP</div><div class="value">{city_sel} / {zip_sel}</div>
                <div class="label">Field Office</div><div class="value">{office_sel}</div>
                <div class="label">ISS / EXP</div><div class="value">{iss.strftime('%m/%d/%Y')} / {exp.strftime('%m/%d/%Y')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

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
                svg_html = f"<div style='background:var(--control-bg);padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
                with st.expander("Aperçu PDF417 (SVG)", expanded=True):
                    components.html(svg_html, height=260, scrolling=True)
                    st.download_button("Télécharger PDF417 (SVG)", data=svg_str.encode("utf-8"), file_name="pdf417.svg", mime="image/svg+xml", key="dl_pdf417_svg_main")
            except Exception as exc:
                st.error("Erreur génération PDF417 : " + str(exc))
        else:
            st.warning("pdf417gen non disponible.")

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
