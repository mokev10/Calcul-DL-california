#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version complète prête à coller
# - Charge ZIP_DB.txt depuis GitHub (raw) et l'utilise pour remplir City / ZIP / Field Office
# - Synchronisation bidirectionnelle ZIP <-> City <-> Field Office
# - Validation AAMVA optionnelle via aamva_utils.py (si présent)
# - Toggle afficher/masquer codes-barres PDF417
# - Clés uniques pour tous les widgets (évite StreamlitDuplicateElementId)
# Requirements (recommandé): streamlit requests reportlab pdf417gen pillow

import streamlit as st
import datetime, random, hashlib, io, base64, requests, re
import streamlit.components.v1 as components
from typing import Dict, List, Optional, Tuple, Any

# ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

# Pillow (optionnel)
try:
    from PIL import Image, ImageDraw, ImageOps
    _PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageDraw = None
    _PIL_AVAILABLE = False

# pdf417gen (optionnel)
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# Optional aamva_utils (validation + autocorrection)
try:
    from aamva_utils import validate_aamva_payload, auto_correct_payload, example_payload, GS as AAMVA_GS
    _AAMVA_UTILS_AVAILABLE = True
except Exception:
    _AAMVA_UTILS_AVAILABLE = False
    AAMVA_GS = None

GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

st.set_page_config(page_title="Permis CA", layout="wide")

# -------------------------
# Defaults and assets
# -------------------------
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"

# -------------------------
# Load ZIP_DB from GitHub raw (non-blocking fallback to minimal built-in)
# -------------------------
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"

# Minimal fallback DB (ensures dropdowns always have values)
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "94920": {"city": "Corte Madera", "state": "CA", "office": ""},
}

def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    """
    Parse a raw text ZIP_DB file (various formats tolerated).
    Returns mapping zip -> {city, state, office}
    Heuristics: lines containing 5-digit zip and city names.
    """
    db: Dict[str, Dict[str, str]] = {}
    if not text:
        return db
    t = text.replace("\r", "\n")
    t = re.sub(r"<\/?t(?:able|r|d|h)[^>]*>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"&nbsp;|\t", " ", t)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    for ln in lines:
        # try patterns: "City  CA  94102" or "94102 City CA" or "94102 City"
        m_zip = re.search(r"\b(\d{5})\b", ln)
        if m_zip:
            z = m_zip.group(1)
            # attempt to extract city: text before or after zip
            before = ln[:m_zip.start()].strip(" ,;-")
            after = ln[m_zip.end():].strip(" ,;-")
            city = ""
            state = "CA"
            # prefer before if it contains letters
            if before and re.search(r"[A-Za-z]", before):
                city = re.split(r"[,\-–:]", before)[-1].strip().title()
            elif after and re.search(r"[A-Za-z]", after):
                city = re.split(r"[,\-–:]", after)[0].strip().title()
            # fallback: try to split by multiple columns
            if not city:
                parts = re.split(r"\s{2,}", ln)
                for p in parts:
                    if re.search(r"[A-Za-z]", p) and not re.search(r"\b\d{5}\b", p):
                        city = p.strip().title()
                        break
            db[z] = {"city": city or "", "state": state, "office": ""}
    # Normalize keys
    normalized: Dict[str, Dict[str, str]] = {}
    for z, info in db.items():
        zc = re.sub(r"\D", "", z)[:5]
        if len(zc) == 5:
            normalized[zc] = {"city": (info.get("city") or "").strip(), "state": (info.get("state") or "CA").strip(), "office": (info.get("office") or "").strip()}
    return normalized

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
        "Hayward": 521, "Los Gatos": 641, "Novato": 647, "Oakland (Claremont)": 501,
        "Oakland (Coliseum)": 604, "Pittsburg": 651, "Pleasanton": 639, "Redwood City": 542,
        "San Francisco": 503, "San Jose (Alma)": 516, "San Jose (Driver License Center)": 607,
        "San Mateo": 594, "Santa Clara": 632, "Vallejo": 538
    },
    "Grand Los Angeles": {
        "Arleta": 628, "Bellflower": 610, "Culver City": 514, "Glendale": 540,
        "Hollywood": 633, "Inglewood": 544, "Long Beach": 507, "Los Angeles (Hope St)": 502,
        "Montebello": 531, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592, "West Covina": 591
    },
    "Orange County / Sud": {
        "Costa Mesa": 627, "Fullerton": 547, "Laguna Hills": 642, "Santa Ana": 529,
        "San Clemente": 652, "Westminster": 623
    },
    "Vallée Centrale": {
        "Bakersfield": 511, "Fresno": 505, "Lodi": 595, "Modesto": 536, "Stockton": 517, "Visalia": 519
    }
}
FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

# -------------------------
# Build indices for linkage
# -------------------------
def build_indices(zip_db: Dict[str, Dict[str, str]]):
    city_to_zips: Dict[str, List[str]] = {}
    office_to_zips: Dict[str, List[str]] = {}
    for z, info in zip_db.items():
        city = (info.get("city") or "").strip().title()
        office = (info.get("office") or "").strip()
        if city:
            city_to_zips.setdefault(city, []).append(z)
        if office:
            office_to_zips.setdefault(office, []).append(z)
    # Map FIELD_OFFICE_MAP labels to zips if city matches
    for z, info in zip_db.items():
        city = (info.get("city") or "").strip().upper()
        if city and city in FIELD_OFFICE_MAP:
            label = FIELD_OFFICE_MAP[city]
            office_to_zips.setdefault(label, []).append(z)
    return city_to_zips, office_to_zips

CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)

# -------------------------
# Helpers
# -------------------------
def normalize_city(s: str) -> str:
    return (s or "").strip().title()

def normalize_zip(z: str) -> str:
    return re.sub(r"\D", "", (z or ""))[:5]

def seed(*x):
    parts = []
    for item in x:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8],16)

def rdigits(r,n):
    return "".join(r.choice("0123456789") for _ in range(n))

def rletter(r, initial):
    try:
        if isinstance(initial, str) and initial and initial[0].isalpha():
            return initial[0].upper()
    except Exception:
        pass
    import random as _rand
    return _rand.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(r):
    return str(r.randint(10,99))

# -------------------------
# UI: styles and sidebar
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.card { width: 480px; border-radius: 12px; padding: 14px; background: linear-gradient(135deg,#1e3a8a,#2563eb); color: white; box-shadow: 0 8px 24px rgba(0,0,0,0.12); margin: auto; }
.photo { width:86px; height:106px; background:#e5e7eb; border-radius:8px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6, key="sb_columns")
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0,9)), index=2, key="sb_ecc")
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
    st.sidebar.info("aamva_utils.py introuvable — la validation est désactivée automatiquement.")

st.sidebar.markdown("**Rasterisation (aperçu PNG/GIF)**")
raster_scale_ui = st.sidebar.selectbox("Scale raster (entier)", [1,2,3,4,5], index=2, key="sb_raster")
gif_delay_ui = st.sidebar.number_input("GIF delay (ms)", min_value=50, max_value=2000, value=200, step=50, key="sb_gif_delay")

# -------------------------
# Synchronization callbacks (ZIP <-> City <-> Field Office)
# -------------------------
def update_from_zip():
    z = normalize_zip(st.session_state.get("ui_zip", ""))
    if not z:
        return
    info = ZIP_DB.get(z)
    if info:
        city = info.get("city", "")
        st.session_state["ui_city"] = city.title() if city else st.session_state.get("ui_city", "")
        # map to field office label if possible
        key = city.upper() if city else ""
        office_label = FIELD_OFFICE_MAP.get(key, info.get("office", ""))
        if not office_label:
            # try to find any office label that contains city
            for lbl in FIELD_OFFICE_MAP.values():
                if city.upper() in lbl.upper():
                    office_label = lbl
                    break
        st.session_state["ui_office"] = office_label or st.session_state.get("ui_office", "")
    else:
        # unknown zip: keep city unchanged
        pass

def update_from_city():
    city = normalize_city(st.session_state.get("ui_city", ""))
    if not city:
        return
    zips = CITY_TO_ZIPS.get(city.title(), [])
    if zips:
        # choose first zip if not already selected
        chosen = zips[0]
        st.session_state["ui_zip"] = chosen
    # set office if mapping exists
    office_label = FIELD_OFFICE_MAP.get(city.upper())
    if office_label:
        st.session_state["ui_office"] = office_label
    else:
        # try to find office by zip
        z = normalize_zip(st.session_state.get("ui_zip", ""))
        info = ZIP_DB.get(z)
        if info and info.get("office"):
            st.session_state["ui_office"] = info.get("office")

def update_from_office():
    office = st.session_state.get("ui_office", "")
    if not office:
        return
    zips = OFFICE_TO_ZIPS.get(office, [])
    if zips:
        st.session_state["ui_zip"] = zips[0]
        info = ZIP_DB.get(zips[0], {})
        city = info.get("city", "")
        if city:
            st.session_state["ui_city"] = city.title()
            return
    # fallback: extract city from label
    m = re.search(r"—\s*(.*?)\s*\(", office)
    if m:
        city_guess = m.group(1).strip()
        st.session_state["ui_city"] = city_guess.title()

# Ensure ZIP_DB entries have office labels where possible
for z, info in ZIP_DB.items():
    city = (info.get("city") or "").strip().upper()
    if city and city in FIELD_OFFICE_MAP:
        ZIP_DB[z]["office"] = FIELD_OFFICE_MAP[city]
    else:
        ZIP_DB[z]["office"] = info.get("office", "")

CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)

# -------------------------
# FORM (with on_change callbacks)
# -------------------------
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom de famille", "HARMS", key="ui_ln")
fn = st.text_input("Prénom", "ROSA", key="ui_fn")
sex = st.selectbox("Sexe", ["M","F"], key="ui_sex")
dob = st.date_input("Date de naissance", datetime.date(1990,1,1), key="ui_dob")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds",0,8,5, key="ui_h1")
    w = st.number_input("Poids (lb)",30,500,160, key="ui_w")
with col2:
    h2 = st.number_input("Pouces",0,11,10, key="ui_h2")
    eyes = st.text_input("Yeux","BRN", key="ui_eyes")
hair = st.text_input("Cheveux","BRN", key="ui_hair")
cls = st.text_input("Classe","C", key="ui_cls")
rstr = st.text_input("Restrictions","NONE", key="ui_rstr")
endorse = st.text_input("Endorsements","NONE", key="ui_endorse")
iss = st.date_input("Date d'émission", datetime.date.today(), key="ui_iss")

# ZIP and City options built from ZIP_DB
zip_options = sorted(ZIP_DB.keys())
city_options = sorted({(info.get("city") or "").title() for info in ZIP_DB.values() if info.get("city")})

# Ensure session defaults exist
if "ui_zip" not in st.session_state:
    st.session_state["ui_zip"] = zip_options[0] if zip_options else "94925"
if "ui_city" not in st.session_state:
    st.session_state["ui_city"] = ZIP_DB.get(st.session_state["ui_zip"], {}).get("city", "").title()
if "ui_office" not in st.session_state:
    st.session_state["ui_office"] = ZIP_DB.get(st.session_state["ui_zip"], {}).get("office", "")

col_zip, col_city = st.columns([2,3])
with col_zip:
    zip_select = st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state["ui_zip"]) if st.session_state["ui_zip"] in zip_options else 0,
        key="ui_zip",
        on_change=update_from_zip
    )
with col_city:
    city_select = st.selectbox(
        "Ville",
        options=city_options,
        index=city_options.index(st.session_state["ui_city"]) if st.session_state["ui_city"] in city_options else 0,
        key="ui_city",
        on_change=update_from_city
    )

# Field office options: union of ZIP_DB offices and FIELD_OFFICE_MAP values
office_options_from_db = sorted({info["office"] for info in ZIP_DB.values() if info.get("office")})
field_office_labels = sorted(set(FIELD_OFFICE_MAP.values()))
office_all = sorted(set(office_options_from_db) | set(field_office_labels))
if not office_all:
    office_all = [""]

office_select = st.selectbox(
    "Field Office",
    options=office_all,
    index=office_all.index(st.session_state.get("ui_office")) if st.session_state.get("ui_office") in office_all else 0,
    key="ui_office",
    on_change=update_from_office
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
    if st.session_state.get("ui_h1", 0) < 0 or st.session_state.get("ui_h2", 0) < 0 or st.session_state.get("ui_h1", 0) > 8 or st.session_state.get("ui_h2", 0) > 11:
        errors.append("Taille hors plage attendue.")
    if not st.session_state.get("ui_zip"):
        errors.append("Code postal requis.")
    if not st.session_state.get("ui_city"):
        errors.append("Ville requise.")
    return errors

def build_aamva_tags(fields: Dict[str,str]) -> str:
    header = "@\r\nANSI 636014080102DL"
    parts = [header]
    order = ["DAQ","DCS","DAC","DBB","DBA","DBD","DAG","DAI","DAJ","DAK","DCF","DAU","DAY","DAZ"]
    for tag in order:
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return GS.join(parts) + "\r"

def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def create_pdf_bytes(fields: Dict[str,str], photo_bytes: bytes = None) -> bytes:
    if not _REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab non disponible.")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 72
    y = height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE")
    y -= 24
    c.setFont("Helvetica", 11)
    for k, v in fields.items():
        c.drawString(x, y, f"{k}: {v}")
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    if photo_bytes and ImageReader is not None:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 72 - 90, height - 72 - 110, width=90, height=110)
        except Exception:
            pass
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_pdf417_svg(data_bytes: bytes, columns:int, security_level:int, scale:int, ratio:int, color:str) -> str:
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
# Generate card and outputs
# -------------------------
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
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
    zip_sel = st.session_state["ui_zip"]
    city_sel = st.session_state["ui_city"]
    office_sel = st.session_state["ui_office"]

    r = random.Random(seed(ln,fn,dob))
    dl = rletter(r, ln[0] if ln else "") + rdigits(r,7)

    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        if dob.month == 2 and dob.day == 29:
            exp = datetime.date(exp_year, 2, 28)
        else:
            last_day = (datetime.date(exp_year, dob.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            exp = datetime.date(exp_year, dob.month, min(dob.day, last_day))

    m = re.search(r"\((\d{2,3})\)", office_sel or "")
    office_code = int(m.group(1)) if m else 0

    seq = next_sequence(r).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}/{seq}FD/{iss.year%100}"

    eyes_disp = (eyes or "").upper()
    hair_disp = (hair or "").upper()
    cls_disp = (cls or "").upper()
    rstr_disp = (rstr or "").upper()
    endorse_disp = (endorse or "").upper()
    height_str = f"{int(h1)}'{int(h2)}\""

    fields = {
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAQ": dl,
        "DAG": "2570 24TH STREET",
        "DAI": city_sel.upper(),
        "DAJ": "CA",
        "DAK": normalize_zip(zip_sel),
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
    }

    aamva = build_aamva_tags(fields)
    payload_to_use = aamva

    # Photo
    photo_src = IMAGE_M_URL if sex == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/png"
        if photo_bytes[:3] == b'\xff\xd8\xff':
            mime = "image/jpeg"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    # Card HTML
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
                <div style="opacity:0.8;font-size:10px">DOB</div><div style="font-weight:700">{dob.strftime('%m/%d/%Y')}</div>
                <div style="opacity:0.8;font-size:10px">Ville / ZIP</div><div style="font-weight:700">{city_sel} / {zip_sel}</div>
                <div style="opacity:0.8;font-size:10px">Field Office</div><div style="font-weight:700">{office_sel}</div>
                <div style="opacity:0.8;font-size:10px">ISS / EXP</div><div style="font-weight:700">{iss.strftime('%m/%d/%Y')} / {exp.strftime('%m/%d/%Y')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Optional validation
    if enable_validator and _AAMVA_UTILS_AVAILABLE:
        st.subheader("Validation AAMVA (optionnelle)")
        results = validate_aamva_payload(payload_to_use)
        errors = results.get("errors", [])
        warnings = results.get("warnings", [])
        infos = results.get("infos", [])
        with st.expander("Résultats de validation", expanded=True):
            if errors:
                st.error(f"Erreurs détectées ({len(errors)}) :")
                for e in errors:
                    st.write("- " + e)
            else:
                st.success("Aucune erreur bloquante détectée.")
            if warnings:
                st.warning(f"Avertissements ({len(warnings)}) :")
                for w in warnings:
                    st.write("- " + w)
            if infos:
                st.info("Informations :")
                for i in infos:
                    st.write("- " + i)
            corrected, applied = auto_correct_payload(payload_to_use)
            if corrected and corrected != payload_to_use:
                st.markdown("### Version corrigée proposée")
                if applied:
                    st.write("Corrections proposées :")
                    for a in applied:
                        st.write("- " + a)
                st.text_area("Payload corrigé (modifiable)", value=corrected, height=200, key="ui_aamva_corrected_preview")
                if st.button("Appliquer la correction et utiliser pour génération", key="ui_apply_correction"):
                    st.session_state["aamva_payload"] = st.session_state.get("ui_aamva_corrected_preview", corrected)
                    st.success("Correction appliquée. Le payload corrigé sera utilisé pour la génération.")
                    payload_to_use = st.session_state["aamva_payload"]

    # PDF417 generation (show/hide)
    svg_str = None
    if st.session_state.get("show_barcodes", True):
        st.subheader("PDF417")
        if _PDF417_AVAILABLE:
            try:
                svg_str = generate_pdf417_svg(payload_to_use.encode("utf-8"),
                                             columns=columns_param,
                                             security_level=security_level_param,
                                             scale=scale_param,
                                             ratio=ratio_param,
                                             color=color_param)
                svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
                with st.expander("Aperçu PDF417 (SVG)", expanded=True):
                    components.html(svg_html, height=260, scrolling=True)
                    st.download_button("Télécharger PDF417 (SVG)", data=svg_str.encode("utf-8"),
                                       file_name="pdf417.svg", mime="image/svg+xml", key="dl_pdf417_svg_main")
            except Exception as e:
                st.error("Erreur génération PDF417 : " + str(e))
        else:
            st.warning("pdf417gen non disponible. Vendorisez le module ou installez pdf417gen pour génération automatique.")
    else:
        with st.expander("Codes-barres masqués (cliquer pour afficher)"):
            st.write("Les codes-barres PDF417 sont actuellement masqués. Active la case 'Afficher les codes-barres (PDF417)' dans la barre latérale pour les voir.")
            if st.button("Afficher maintenant", key="ui_show_now"):
                st.session_state["show_barcodes"] = True
                st.experimental_rerun()

    # Downloads (unique keys)
    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            st.download_button("Télécharger PDF417 (SVG) (panel)", data=svg_str.encode("utf-8"),
                               file_name="pdf417_panel.svg", mime="image/svg+xml", key="dl_pdf417_svg_panel")
    with cols[1]:
        try:
            pdf_bytes = create_pdf_bytes({
                "Nom": ln, "Prénom": fn, "Sexe": sex, "DOB": dob.strftime("%m/%d/%Y"),
                "Ville": city_sel, "ZIP": zip_sel, "Field Office": office_sel,
                "DD": dd, "ISS": iss.strftime("%m/%d/%Y"), "EXP": exp.strftime("%m/%d/%Y"),
                "Classe": cls_disp, "Restrictions": rstr_disp, "Endorsements": endorse_disp,
                "Yeux/Cheveux/Taille/Poids": f"{eyes_disp}/{hair_disp}/{height_str}/{w} lb"
            }, photo_bytes=photo_bytes)
            st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf",
                               mime="application/pdf", key="dl_permis_pdf")
        except Exception as e:
            st.error("Erreur génération PDF : " + str(e))
            if not _REPORTLAB_AVAILABLE:
                st.info("reportlab non installé : export PDF non disponible.")
