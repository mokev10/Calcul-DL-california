#!/usr/bin/env python3
# permis_california_optimized.py
# Script complet, optimisé pour réduire le temps de chargement initial.
# Colle ce fichier en remplacement complet.

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

# Page config (doit être la première commande exécutable)
st.set_page_config(page_title="PERMIS CALIFORNIA", layout="wide")

# --- Optional heavy libs guarded ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# --- Assets ---
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"

# --- Small embedded ZIP_DB sample (keeps startup light) ---
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "90650": {"city": "Norwalk", "state": "CA", "office": ""},  # exemple Norwalk
}

# --- Field offices mapping (restored / compact) ---
field_offices = {
    "Baie de San Francisco": {"San Francisco": 503, "Oakland": 501, "Daly City": 599, "Corte Madera": 525},
    "Grand Los Angeles": {"Los Angeles": 502, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592},
    "Orange County / Sud": {"Anaheim": 547, "Garden Grove": 547, "Santa Ana": 529},
    "Vallée Centrale": {"Sacramento": 505, "Fresno": 505, "Bakersfield": 511},
    "Sud Californie": {"San Diego": 707},
}
FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

# --- County fallback (embarquée pour éviter appels réseau) ---
ZIP_TO_COUNTY: Dict[str, str] = {
    "90650": "Los Angeles",  # Norwalk
    "94015": "San Mateo",
    "94102": "San Francisco",
    "94601": "Alameda",
    "90001": "Los Angeles",
}
COUNTY_TO_FIELD_OFFICE: Dict[str, str] = {
    "Los Angeles": "Grand Los Angeles — Los Angeles (502)",
    "San Francisco": "Baie de San Francisco — San Francisco (503)",
    "San Mateo": "Baie de San Francisco — San Mateo (594)",
    "Alameda": "Baie de San Francisco — Oakland (501)",
}

# --- Utilities ---
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

# --- Caching network fetch and parsing to avoid repeated cost ---
@st.cache_data(ttl=60 * 60)  # cache 1h
def fetch_github_zipdb_cached(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

@st.cache_data(ttl=60 * 60)
def parse_zipdb_text_cached(text: str) -> Dict[str, Dict[str, str]]:
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
    # heuristic fallback
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

# --- Infer field office with county fallback (no blocking at startup) ---
def get_county_for_zip_or_city(zip_code: str = "", city: str = "") -> Optional[str]:
    z = normalize_zip(zip_code)
    if z and z in ZIP_TO_COUNTY:
        return ZIP_TO_COUNTY[z]
    # network fallback intentionally not called at startup; will be called only on user demand
    return None

def infer_field_office(city: str, zip_code: str = "") -> str:
    key = (city or "").strip().upper()
    if key:
        if key in FIELD_OFFICE_MAP:
            return FIELD_OFFICE_MAP[key]
        for label in FIELD_OFFICE_MAP.values():
            if key in label.upper():
                return label
    county = get_county_for_zip_or_city(zip_code=zip_code, city=city)
    if county:
        mapped = COUNTY_TO_FIELD_OFFICE.get(county)
        if mapped:
            return mapped
        return f"{county} County — (Field Office non répertorié)"
    return "Unknown Field Office"

# --- Build ZIP_CITY_FIELD_OFFICE lazily but quickly ---
def build_zip_city_field_office(zip_db: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, List[str]]]:
    mapping: Dict[str, Dict[str, List[str]]] = {}
    for zip_code, info in zip_db.items():
        z = normalize_zip(zip_code)
        if len(z) != 5:
            continue
        city = (info.get("city") or "").strip().title()
        office = (info.get("office") or "").strip()
        if not city:
            continue
        if not office:
            office = infer_field_office(city, zip_code=z)
        entry = mapping.setdefault(z, {"cities": [], "field_offices": []})
        if city not in entry["cities"]:
            entry["cities"].append(city)
        if office and office not in entry["field_offices"]:
            entry["field_offices"].append(office)
    if not mapping:
        mapping["94015"] = {"cities": ["Daly City"], "field_offices": ["Baie de San Francisco — Daly City (599)"]}
    for z, entry in mapping.items():
        if not entry["cities"]:
            entry["cities"] = ["Unknown City"]
        if not entry["field_offices"]:
            entry["field_offices"] = ["Unknown Field Office"]
    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))

ZIP_CITY_FIELD_OFFICE = build_zip_city_field_office(ZIP_DB)

# --- Derived maps ---
CITY_TO_ZIPS: Dict[str, List[str]] = {}
OFFICE_TO_ZIPS: Dict[str, List[str]] = {}
for zip_code, row in ZIP_CITY_FIELD_OFFICE.items():
    for city in row["cities"]:
        CITY_TO_ZIPS.setdefault(city, []).append(zip_code)
    for office in row["field_offices"]:
        OFFICE_TO_ZIPS.setdefault(office, []).append(zip_code)

# --- Minimal CSS and fonts ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.card { width:480px; border-radius:12px; padding:14px; background:linear-gradient(135deg,#1e3a8a,#2563eb); color:white; box-shadow:0 8px 24px rgba(0,0,0,0.12); margin:auto; }
.photo { width:86px; height:106px; background:#e5e7eb; border-radius:8px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar controls (lightweight) ---
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

# --- Diagnostics expander to help debug slow loads ---
with st.expander("Diagnostic (si chargement lent)", expanded=False):
    st.write("Taille ZIP_DB embarquée :", len(ZIP_DB))
    st.write("Taille ZIP_CITY_FIELD_OFFICE :", len(ZIP_CITY_FIELD_OFFICE))
    st.write("Exemples CITY_TO_ZIPS (3) :", dict(list(CITY_TO_ZIPS.items())[:3]))
    st.write("Exemples OFFICE_TO_ZIPS (3) :", dict(list(OFFICE_TO_ZIPS.items())[:3]))
    st.info("Si la page met trop de temps, clique sur 'Charger DB complète' pour lancer le fetch en arrière-plan.")

# --- Button to load extended ZIP DB on demand (non-blocking for initial render) ---
col_load_left, col_load_right = st.columns([3, 1])
with col_load_left:
    st.markdown("Charger la base ZIP complète depuis GitHub (optionnel, peut prendre du temps).")
with col_load_right:
    if st.button("Charger DB complète", key="load_full_db"):
        st.info("Téléchargement et parsing en cours (opération mise en cache). Patientez...")
        fetched = fetch_github_zipdb_cached(GITHUB_RAW_ZIPDB)
        if fetched:
            parsed = parse_zipdb_text_cached(fetched)
            if parsed:
                ZIP_DB.update(parsed)
                # rebuild mapping
                ZIP_CITY_FIELD_OFFICE.clear()
                ZIP_CITY_FIELD_OFFICE.update(build_zip_city_field_office(ZIP_DB))
                CITY_TO_ZIPS.clear()
                OFFICE_TO_ZIPS.clear()
                for zip_code, row in ZIP_CITY_FIELD_OFFICE.items():
                    for city in row["cities"]:
                        CITY_TO_ZIPS.setdefault(city, []).append(zip_code)
                    for office in row["field_offices"]:
                        OFFICE_TO_ZIPS.setdefault(office, []).append(zip_code)
                st.success("DB complète chargée et mise en cache.")
            else:
                st.warning("Parsing GitHub DB n'a retourné aucune entrée valide.")
        else:
            st.error("Impossible de télécharger la DB depuis GitHub (timeout ou réseau).")

# --- Main UI form ---
st.title("PERMIS CALIFORNIA")

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

# --- ZIP / City / Field Office selects (fast) ---
zip_options = list(ZIP_CITY_FIELD_OFFICE.keys()) or ["94015"]
if "ui_zip" not in st.session_state or st.session_state["ui_zip"] not in ZIP_CITY_FIELD_OFFICE:
    st.session_state["ui_zip"] = zip_options[0]

selected_zip = st.session_state["ui_zip"]
selected_row = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {"cities": ["Unknown City"], "field_offices": ["Unknown Field Office"]})
city_options = selected_row.get("cities") or ["Unknown City"]
office_options = selected_row.get("field_offices") or ["Unknown Field Office"]

if "ui_city" not in st.session_state or st.session_state["ui_city"] not in city_options:
    st.session_state["ui_city"] = city_options[0]
if "ui_office" not in st.session_state or st.session_state["ui_office"] not in office_options:
    st.session_state["ui_office"] = office_options[0]

col_zip, col_city = st.columns([2, 3])
with col_zip:
    st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state["ui_zip"]),
        key="ui_zip",
        on_change=lambda: None,
    )

# re-evaluate after potential zip change
selected_zip = st.session_state["ui_zip"]
selected_row = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {"cities": ["Unknown City"], "field_offices": ["Unknown Field Office"]})
city_options = selected_row.get("cities") or ["Unknown City"]
office_options = selected_row.get("field_offices") or ["Unknown Field Office"]
if st.session_state.get("ui_city") not in city_options:
    st.session_state["ui_city"] = city_options[0]
if st.session_state.get("ui_office") not in office_options:
    st.session_state["ui_office"] = office_options[0]

with col_city:
    st.selectbox(
        "Ville",
        options=city_options,
        index=city_options.index(st.session_state["ui_city"]),
        key="ui_city",
        on_change=lambda: None,
    )

st.selectbox(
    "Field Office",
    options=office_options,
    index=office_options.index(st.session_state["ui_office"]),
    key="ui_office",
    on_change=lambda: None,
)

# --- Button to resolve field office via county (lazy, user-triggered) ---
col_resolve_left, col_resolve_right = st.columns([3, 1])
with col_resolve_left:
    st.markdown("Si le Field Office est 'Unknown Field Office', clique sur **Résoudre Field Office** pour tenter une résolution via comté embarqué ou Nominatim (fallback).")
with col_resolve_right:
    if st.button("Résoudre Field Office", key="resolve_field_office"):
        zip_sel = normalize_zip(st.session_state.get("ui_zip", ""))
        city_sel = normalize_city(st.session_state.get("ui_city", ""))
        st.info(f"Tentative de résolution pour ZIP {zip_sel} / Ville {city_sel}.")
        county = get_county_for_zip_or_city(zip_sel, city_sel)
        if not county:
            # optional network fallback (short timeout)
            try:
                url = "https://nominatim.openstreetmap.org/search"
                params = {"q": f"{city_sel} {zip_sel} CA", "format": "json", "addressdetails": 1, "limit": 1}
                headers = {"User-Agent": "PermisCA-App/1.0 (+https://example.com)"}
                resp = requests.get(url, params=params, headers=headers, timeout=4)
                resp.raise_for_status()
                data = resp.json()
                if data:
                    addr = data[0].get("address", {})
                    county = addr.get("county") or addr.get("state_district") or addr.get("region")
                    if county:
                        county = re.sub(r"\s*County\s*$", "", county).strip()
                        ZIP_TO_COUNTY[zip_sel] = county
            except Exception:
                county = None
        if county:
            st.success(f"Comté résolu : {county}")
            mapped = COUNTY_TO_FIELD_OFFICE.get(county)
            new_office = mapped if mapped else f"{county} County — (Field Office non répertorié)"
        else:
            st.warning("Impossible de résoudre le comté pour cette entrée.")
            new_office = "Unknown Field Office"
        # update local mapping for this zip
        if zip_sel in ZIP_CITY_FIELD_OFFICE:
            row = ZIP_CITY_FIELD_OFFICE[zip_sel]
            if "Unknown Field Office" in row["field_offices"]:
                row["field_offices"].remove("Unknown Field Office")
            if new_office not in row["field_offices"]:
                row["field_offices"].append(new_office)
            st.session_state["ui_office"] = new_office
            st.success(f"Field Office mis à jour : {new_office}")

# --- Generate button and flow (keeps original logic) ---
generate = st.button("Générer la carte", key="ui_generate")

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
    zip_code = normalize_zip(st.session_state.get("ui_zip", ""))
    city = normalize_city(st.session_state.get("ui_city", ""))
    address = st.session_state.get("ui_address_line", "").strip()
    if not zip_code:
        errors.append("Code postal requis.")
    if not city:
        errors.append("Ville requise pour générer le code PDF417")
    if not address:
        errors.append("Adresse requise.")
    row = ZIP_CITY_FIELD_OFFICE.get(zip_code)
    if row:
        allowed = [normalize_city(c) for c in (row.get("cities") or [])]
        if city not in allowed:
            errors.append(f"Incohérence ZIP → Ville: {zip_code} n'est pas lié à {city}.")
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

    row = ZIP_CITY_FIELD_OFFICE.get(zip_sel, {})
    if not city_sel and row.get("cities"):
        city_sel = normalize_city(row["cities"][0])
        st.session_state["ui_city"] = city_sel

    if not city_sel:
        st.error("Ville requise pour générer le code PDF417")
        st.stop()

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
        payload_to_use = "@ANSI 636014080102DL00410288ZA03290015DL" + "".join(
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

    html = f\"\"\"
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
    \"\"\"
    st.markdown(html, unsafe_allow_html=True)

    # PDF417 / export (optionnel) - identique à ton flux
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
            st.warning("pdf417gen non disponible. Installez le module si nécessaire.")

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
