#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version complète prête à coller
# - Préserve l'UI/UX initiale (menus déroulants city/zip, field offices, photo par défaut selon Sexe)
# - Validation AAMVA optionnelle via aamva_utils.py (si présent)
# - Toggle afficher/masquer codes-barres PDF417
# - Clés uniques pour widgets pour éviter StreamlitDuplicateElementId
# - Corrige le problème où les menus "city" et "zip" ne s'affichaient pas

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

# Fallback GS
GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# Default images
# -------------------------
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"

# -------------------------
# Minimal ZIP_DB fallback (ensures zip/city menus always available)
# -------------------------
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "94920": {"city": "Corte Madera", "state": "CA", "office": ""},
}

# Try to fetch a richer ZIP_DB from GitHub (non-blocking)
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
    t = text.replace("\r", "\n")
    t = re.sub(r"<\/?t(?:able|r|d|h)[^>]*>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"&nbsp;|\t", " ", t)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    for ln in lines:
        m = re.search(r"\b(\d{5})\b", ln)
        if m:
            z = m.group(1)
            # try to extract city after zip
            after = ln[m.end():].strip(" ,:-")
            city = ""
            if after and re.search(r"[A-Za-z]", after):
                city = re.split(r"[,\-–:]", after)[0].strip().title()
            db[z] = {"city": city or "", "state": "CA", "office": ""}
    return db

fetched = fetch_github_zipdb(GITHUB_RAW_ZIPDB)
if fetched:
    parsed = parse_zipdb_text(fetched)
    if parsed:
        ZIP_DB.update(parsed)

# -------------------------
# Field offices (kept)
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

# Build city and zip indices
def build_indices(zip_db: Dict[str, Dict[str, str]]):
    city_to_zips: Dict[str, List[str]] = {}
    for z, info in zip_db.items():
        city = (info.get("city") or "").strip()
        if city:
            city_to_zips.setdefault(city.title(), []).append(z)
    return city_to_zips

CITY_TO_ZIPS = build_indices(ZIP_DB)
ZIP_OPTIONS = sorted(ZIP_DB.keys())
CITY_OPTIONS = sorted({info["city"].title() for info in ZIP_DB.values() if info.get("city")})

# -------------------------
# CSS + UI
# -------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.card { width: 450px; border-radius: 14px; padding: 16px; background: linear-gradient(135deg,#1e3a8a,#2563eb); color: white; box-shadow: 0 10px 30px rgba(0,0,0,0.15); margin: auto; }
.header { display:flex; justify-content:space-between; align-items:center; font-weight:700; font-size:14px; margin-bottom:10px; }
.body { display:flex; gap:12px; }
.photo { width:90px; height:110px; background:#e5e7eb; border-radius:8px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
.info { flex:1; font-size:12px; }
.label { opacity:0.7; font-size:10px; }
.value { font-weight:700; margin-bottom:4px; }
.badge { background:white; color:#1e3a8a; padding:2px 6px; border-radius:6px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar controls (unique keys)
# -------------------------
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6, key="sb_columns")
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0,9)), index=2, key="sb_ecc")
scale_param = st.sidebar.slider("Échelle", 1, 6, 3, key="sb_scale")
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3, key="sb_ratio")
color_param = st.sidebar.color_picker("Couleur du code", "#000000", key="sb_color")

if "show_barcodes" not in st.session_state:
    st.session_state["show_barcodes"] = True
show_barcodes = st.sidebar.checkbox("Afficher les codes-barres (PDF417)", value=st.session_state["show_barcodes"], key="sb_show_barcodes")

enable_validator = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False, key="sb_enable_validator")
if enable_validator and not _AAMVA_UTILS_AVAILABLE:
    st.sidebar.info("aamva_utils.py introuvable — la validation est désactivée automatiquement.")

st.sidebar.markdown("**Rasterisation (aperçu PNG/GIF)**")
raster_scale_ui = st.sidebar.selectbox("Scale raster (entier)", [1,2,3,4,5], index=2, key="sb_raster")
gif_delay_ui = st.sidebar.number_input("GIF delay (ms)", min_value=50, max_value=2000, value=200, step=50, key="sb_gif_delay")

# -------------------------
# Utilities
# -------------------------
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
# FORM (keys preserved)
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

# --- ZIP and City dropdowns (ensure they display)
zip_options = ZIP_OPTIONS if ZIP_OPTIONS else ["94925"]
city_options = CITY_OPTIONS if CITY_OPTIONS else ["Corte Madera"]

col_zip, col_city = st.columns([2,3])
with col_zip:
    zip_select = st.selectbox("Code postal", options=zip_options,
                              index=zip_options.index(zip_options[0]) if zip_options else 0,
                              key="ui_zip")
with col_city:
    city_select = st.selectbox("Ville", options=city_options,
                               index=city_options.index(city_options[0]) if city_options else 0,
                               key="ui_city")

# Field office select (flattened)
office_all = sorted(set(FIELD_OFFICE_MAP.values()))
if not office_all:
    office_all = [""]
office_choice = st.selectbox("Field Office", office_all, index=0, key="ui_office")

generate = st.button("Générer la carte", key="ui_generate")

# -------------------------
# Validation helpers
# -------------------------
def validate_inputs() -> List[str]:
    errors: List[str] = []
    if not ln or not ln.strip():
        errors.append("Nom de famille requis.")
    if not fn or not fn.strip():
        errors.append("Prénom requis.")
    if dob > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if iss > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if w < 30 or w > 500:
        errors.append("Poids hors plage attendue.")
    if h1 < 0 or h1 > 8 or h2 < 0 or h2 > 11:
        errors.append("Taille hors plage attendue.")
    if not zip_select:
        errors.append("Code postal requis.")
    if not city_select:
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
# Main generation flow
# -------------------------
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
        st.stop()

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

    # office code extraction if present in label
    m = re.search(r"\((\d{2,3})\)", office_choice or "")
    office_code = int(m.group(1)) if m else 0

    seq = next_sequence(r).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}/{seq}FD/{iss.year%100}"

    eyes_disp = (eyes or "").upper()
    hair_disp = (hair or "").upper()
    cls_disp = (cls or "").upper()
    rstr_disp = (rstr or "").upper()
    endorse_disp = (endorse or "").upper()
    height_str = f"{int(h1)}'{int(h2)}\""

    # AAMVA fields
    fields = {
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAQ": dl,
        "DAG": "2570 24TH STREET",
        "DAI": city_select.upper(),
        "DAJ": "CA",
        "DAK": zip_select,
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
    }

    aamva = build_aamva_tags(fields)
    data_bytes = aamva.encode("utf-8")

    # Photo handling
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
        <div class="header">
            <div>CALIFORNIA USA DRIVER LICENSE</div>
            <div class="badge">{dl}</div>
        </div>
        <div class="body">
            {photo_html}
            <div class="info">
                <div class="label">Nom</div><div class="value">{ln}</div>
                <div class="label">Prénom</div><div class="value">{fn}</div>
                <div class="label">Sexe</div><div class="value">{sex}</div>
                <div class="label">DOB</div><div class="value">{dob.strftime('%m/%d/%Y')}</div>
                <div class="label">Ville / ZIP</div><div class="value">{city_select} / {zip_select}</div>
                <div class="label">Field Office</div><div class="value">{office_choice}</div>
                <div class="label">DD</div><div class="value">{dd}</div>
                <div class="label">ISS</div><div class="value">{iss.strftime('%m/%d/%Y')}</div>
                <div class="label">EXP</div><div class="value">{exp.strftime('%m/%d/%Y')}</div>
                <div class="label">Classe</div><div class="value">{cls_disp}</div>
                <div class="label">Restrictions</div><div class="value">{rstr_disp}</div>
                <div class="label">Endorsements</div><div class="value">{endorse_disp}</div>
                <div class="label">Yeux / Cheveux / Taille / Poids</div>
                <div class="value">{eyes_disp} / {hair_disp} / {height_str} / {w} lb</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Optional validation
    payload_to_use = aamva
    if enable_validator:
        st.subheader("Validation AAMVA (optionnelle)")
        if _AAMVA_UTILS_AVAILABLE:
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
                else:
                    st.write("Aucune correction automatique proposée.")
        else:
            st.info("Validation non disponible : aamva_utils.py introuvable. Place aamva_utils.py pour activer la validation.")

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
                st.info("Vérifiez le module pdf417gen.")
        else:
            st.warning("pdf417gen non disponible. Vendorisez le module ou installez pdf417gen pour génération automatique.")
    else:
        with st.expander("Codes-barres masqués (cliquer pour afficher)"):
            st.write("Les codes-barres PDF417 sont actuellement masqués. Active la case 'Afficher les codes-barres (PDF417)' dans la barre latérale pour les voir.")
            if st.button("Afficher maintenant", key="ui_show_now"):
                st.session_state["show_barcodes"] = True
                st.experimental_rerun()

    # Download buttons (unique keys)
    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            st.download_button("Télécharger PDF417 (SVG) (panel)", data=svg_str.encode("utf-8"),
                               file_name="pdf417_panel.svg", mime="image/svg+xml", key="dl_pdf417_svg_panel")
    with cols[1]:
        try:
            pdf_bytes = create_pdf_bytes({
                "Nom": ln,
                "Prénom": fn,
                "Sexe": sex,
                "DOB": dob.strftime("%m/%d/%Y"),
                "Ville": city_select,
                "ZIP": zip_select,
                "Field Office": office_choice,
                "DD": dd,
                "ISS": iss.strftime("%m/%d/%Y"),
                "EXP": exp.strftime("%m/%d/%Y"),
                "Classe": cls_disp,
                "Restrictions": rstr_disp,
                "Endorsements": endorse_disp,
                "Yeux/Cheveux/Taille/Poids": f"{eyes_disp}/{hair_disp}/{height_str}/{w} lb"
            }, photo_bytes=photo_bytes)
            st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf",
                               mime="application/pdf", key="dl_permis_pdf")
        except Exception as e:
            st.error("Erreur génération PDF : " + str(e))
            if not _REPORTLAB_AVAILABLE:
                st.info("reportlab non installé : export PDF non disponible.")
