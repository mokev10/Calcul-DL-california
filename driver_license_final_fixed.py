#!/usr/bin/env python3
# driver_license_final.py
# Générateur de permis CA (Streamlit)
# Version : intègre automatiquement ZIP_DB depuis GitHub et FIELD_OFFICE (PDF) pour remplir la colonne office.
# Remplace entièrement ton ancien fichier par celui-ci.
#
# Requirements recommandés :
# pip install streamlit requests reportlab pdfplumber
# pdf417gen est optionnel (vendorisez si nécessaire)

import streamlit as st
import datetime
import random
import hashlib
import io
import base64
import requests
import re
from typing import Dict, List, Optional, Tuple
import streamlit.components.v1 as components

# ReportLab pour export PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# CONFIG : URLs raw GitHub (modifier si besoin)
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"
GITHUB_RAW_FIELD_OFFICE_PDF = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/FIELD_OFFICE.pdf"

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

def rdigits(r, n):
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
    return str(r.randint(10, 99))

# -------------------------
# Récupération depuis GitHub
def fetch_text_url(url: str, timeout: int = 10) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def fetch_binary_url(url: str, timeout: int = 10) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

# -------------------------
# Parsing ZIP_DB.txt (heuristique)
def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    db: Dict[str, Dict[str, str]] = {}
    if not text:
        return db
    t = text.replace("\r", "\n")
    t = re.sub(r"<\/?t(?:able|r|d|h)[^>]*>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"&nbsp;|\t", " ", t)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.search(r"\b(9[0-6]\d{3})\b", ln)
        if m:
            z = m.group(1)
            city = ""
            state = "CA"
            office = ""
            after = ln[m.end():].strip(" ,:-")
            if after and re.search(r"[A-Za-z]", after):
                city_candidate = re.split(r"[,\-–:]", after)[0].strip()
                if city_candidate:
                    city = city_candidate.title()
            if not city and i + 1 < len(lines):
                next_ln = lines[i + 1]
                if not re.search(r"\b9[0-6]\d{3}\b", next_ln) and re.search(r"[A-Za-z]", next_ln):
                    city = re.split(r"[,\-–:]", next_ln)[0].strip().title()
                    if i + 2 < len(lines):
                        maybe_state = lines[i + 2]
                        if re.fullmatch(r"[A-Z]{2}", maybe_state):
                            state = maybe_state
                        elif "CA" in maybe_state:
                            state = "CA"
            if not city and i - 1 >= 0:
                prev_ln = lines[i - 1]
                if not re.search(r"\b9[0-6]\d{3}\b", prev_ln) and re.search(r"[A-Za-z]", prev_ln):
                    city = re.split(r"[,\-–:]", prev_ln)[0].strip().title()
            db[z] = {"city": city, "state": state, "office": office}
            i += 1
            continue
        i += 1
    # pass supplémentaire : séquences Zip/City/State
    for j in range(len(lines) - 2):
        a, b, c = lines[j], lines[j + 1], lines[j + 2]
        if re.fullmatch(r"\d{5}", a) and re.search(r"[A-Za-z]", b) and re.search(r"\bCA\b|\b[A-Z]{2}\b", c):
            z = a
            city = b.title()
            state = "CA" if "CA" in c else c.strip()
            db[z] = {"city": city, "state": state, "office": db.get(z, {}).get("office", "")}
    # normaliser clés
    normalized: Dict[str, Dict[str, str]] = {}
    for z, info in db.items():
        zc = re.sub(r"\D", "", z)[:5]
        if len(zc) == 5:
            normalized[zc] = {
                "city": (info.get("city") or "").strip(),
                "state": (info.get("state") or "CA").strip(),
                "office": (info.get("office") or "").strip()
            }
    return normalized

# -------------------------
# Parsing FIELD_OFFICE.pdf -> mapping city -> office string (Region — City (ID))
# Utilise pdfplumber si disponible, sinon tente heuristique sur bytes->texte
def parse_field_office_pdf_bytes(pdf_bytes: bytes) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    if not pdf_bytes:
        return mapping
    # essayer pdfplumber si installé
    try:
        import pdfplumber
        text_all = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_all += page_text + "\n"
    except Exception:
        # fallback : décoder bytes en texte (peut être brouillé)
        try:
            text_all = pdf_bytes.decode("utf-8", errors="replace")
        except Exception:
            text_all = ""
    # nettoyer HTML/table tags éventuels
    t = text_all.replace("\r", "\n")
    t = re.sub(r"<\/?t(?:able|r|d|h)[^>]*>", "\n", t, flags=re.IGNORECASE)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    # heuristique : on cherche des blocs "Région" suivi de lignes "Ville / Secteur" + "Code ID"
    region = ""
    i = 0
    while i < len(lines):
        ln = lines[i]
        # détecter un titre de région (ex: "Baie de San Francisco", "Grand Los Angeles", "Orange County / Sud", "Vallée Centrale")
        if re.search(r"Baie de San Francisco|Grand Los Angeles|Orange County|Vallée Centrale|Central Valley|San Francisco Bay|Los Angeles", ln, re.IGNORECASE):
            region = ln.strip()
            i += 1
            continue
        # détecter pattern: City  (maybe)  ID  OR City \n ID
        # cas 1: ligne contient "City   ID"
        m_inline = re.match(r"^([A-Za-z' .\-&()]+)\s+(\d{2,3})$", ln)
        if m_inline:
            city = m_inline.group(1).strip().title()
            code = m_inline.group(2).strip()
            office_label = f"{region} — {city} ({code})" if region else f"{city} ({code})"
            mapping[city.upper()] = office_label
            i += 1
            continue
        # cas 2: ligne = City, ligne suivante = ID
        if i + 1 < len(lines) and re.fullmatch(r"\d{2,3}", lines[i + 1]):
            city = ln.strip().title()
            code = lines[i + 1].strip()
            office_label = f"{region} — {city} ({code})" if region else f"{city} ({code})"
            mapping[city.upper()] = office_label
            i += 2
            continue
        # cas 3: ligne contient "City" and next token contains code in same line separated by tabs/commas
        m_split = re.match(r"^([A-Za-z' .\-&()]+)[,\t]+\s*(\d{2,3})$", ln)
        if m_split:
            city = m_split.group(1).strip().title()
            code = m_split.group(2).strip()
            office_label = f"{region} — {city} ({code})" if region else f"{city} ({code})"
            mapping[city.upper()] = office_label
            i += 1
            continue
        # cas 4: ligne contient "City  /  Code" with slashes
        m_slash = re.match(r"^([A-Za-z' .\-&()]+)\s*/\s*(\d{2,3})$", ln)
        if m_slash:
            city = m_slash.group(1).strip().title()
            code = m_slash.group(2).strip()
            office_label = f"{region} — {city} ({code})" if region else f"{city} ({code})"
            mapping[city.upper()] = office_label
            i += 1
            continue
        i += 1
    return mapping

# -------------------------
# Base minimale fallback (si fetch échoue)
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": "Baie de San Francisco — Corte Madera (525)"},
    "95818": {"city": "Sacramento", "state": "CA", "office": "Sacramento (500)"},
    "94102": {"city": "San Francisco", "state": "CA", "office": "Baie de San Francisco — San Francisco (503)"},
    "94015": {"city": "Daly City", "state": "CA", "office": "Baie de San Francisco — Daly City (599)"},
}

# -------------------------
# Charger ZIP_DB.txt depuis GitHub
fetched_zip_text = fetch_text_url(GITHUB_RAW_ZIPDB)
if fetched_zip_text:
    parsed_zip = parse_zipdb_text(fetched_zip_text)
    if parsed_zip:
        # merge parsed (parsed prend la priorité)
        ZIP_DB.update(parsed_zip)

# Charger FIELD_OFFICE.pdf depuis GitHub et construire mapping city->office
fetched_field_bytes = fetch_binary_url(GITHUB_RAW_FIELD_OFFICE_PDF)
FIELD_OFFICE_MAP: Dict[str, str] = {}
if fetched_field_bytes:
    try:
        FIELD_OFFICE_MAP = parse_field_office_pdf_bytes(fetched_field_bytes)
    except Exception:
        FIELD_OFFICE_MAP = {}

# Si on a mapping de bureaux, appliquer aux ZIP_DB (si city correspond)
if FIELD_OFFICE_MAP:
    for z, info in list(ZIP_DB.items()):
        city = (info.get("city") or "").strip().upper()
        if city and city in FIELD_OFFICE_MAP:
            ZIP_DB[z]["office"] = FIELD_OFFICE_MAP[city]
        else:
            # tentative de correspondance approximative : comparer sans accents et en enlevant espaces/points
            def normalize(s: str) -> str:
                s2 = s.upper()
                s2 = re.sub(r"[^\w]", "", s2)
                return s2
            norm_city = normalize(info.get("city", ""))
            for fc, office_label in FIELD_OFFICE_MAP.items():
                if normalize(fc) == norm_city:
                    ZIP_DB[z]["office"] = office_label
                    break

# Construire indices inverses
def build_indices(zip_db: Dict[str, Dict[str, str]]):
    city_to_zips: Dict[str, List[str]] = {}
    office_to_zips: Dict[str, List[str]] = {}
    for z, info in zip_db.items():
        city = (info.get("city") or "").strip()
        office = (info.get("office") or "").strip()
        if city:
            city_to_zips.setdefault(city.upper(), []).append(z)
        if office:
            office_to_zips.setdefault(office, []).append(z)
    return city_to_zips, office_to_zips

CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)

# -------------------------
# CSS minimal (garder propre)
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.card { width: 480px; border-radius: 12px; padding: 14px; background: linear-gradient(135deg,#1e3a8a,#2563eb); color: white; box-shadow: 0 8px 24px rgba(0,0,0,0.12); margin: auto; }
.header { display:flex; justify-content:space-between; align-items:center; font-weight:700; font-size:14px; margin-bottom:8px; }
.body { display:flex; gap:12px; }
.photo { width:86px; height:106px; background:#e5e7eb; border-radius:8px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
.info { flex:1; font-size:12px; }
.label { opacity:0.75; font-size:10px; }
.value { font-weight:700; margin-bottom:4px; }
.badge { background:white; color:#1e3a8a; padding:2px 6px; border-radius:6px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar : paramètres PDF417 uniquement (pas d'affichage source)
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6)
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0, 9)), index=2)
scale_param = st.sidebar.slider("Échelle", 1, 6, 3)
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3)
color_param = st.sidebar.color_picker("Couleur du code", "#000000")

# -------------------------
# PDF417 import attempt
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    try:
        import pdf417gen
        from pdf417gen import encode, render_svg
        _PDF417_AVAILABLE = True
    except Exception:
        _PDF417_AVAILABLE = False

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
# Formulaire principal
st.title("Générateur officiel de permis CA")

# Defaults session_state
defaults = {
    "ln_input": "HARMS",
    "fn_input": "ROSA",
    "address1_input": "2570 24TH STREET",
    "address2_input": "",
    "zip_select": next(iter(ZIP_DB.keys())) if ZIP_DB else "90001",
    "city_select": ZIP_DB.get(next(iter(ZIP_DB.keys())), {}).get("city", "") if ZIP_DB else "",
    "state_input": ZIP_DB.get(next(iter(ZIP_DB.keys())), {}).get("state", "CA") if ZIP_DB else "CA",
    "office_select": ZIP_DB.get(next(iter(ZIP_DB.keys())), {}).get("office", "") if ZIP_DB else "",
    "sex_input": "M",
    "dob_input": datetime.date(1990, 1, 1),
    "h1_input": 5,
    "h2_input": 10,
    "w_input": 160,
    "eyes_input": "BRN",
    "hair_input": "BRN",
    "cls_input": "C",
    "rstr_input": "NONE",
    "endorse_input": "NONE",
    "iss_input": datetime.date.today(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Synchronisation callbacks
def update_from_zip():
    z = st.session_state.get("zip_select", "").strip()
    z_digits = re.sub(r"\D", "", z)
    if z_digits in ZIP_DB:
        info = ZIP_DB[z_digits]
        st.session_state["city_select"] = info.get("city", "")
        st.session_state["state_input"] = info.get("state", "CA")
        st.session_state["office_select"] = info.get("office", "")
    else:
        try:
            zi = int(z_digits)
            if 90001 <= zi <= 96162:
                st.session_state["city_select"] = ""
                st.session_state["office_select"] = ""
                st.session_state["state_input"] = "CA"
            else:
                st.warning("ZIP hors plage CA (90001–96162) et non présent dans la base.")
        except Exception:
            st.warning("ZIP invalide et non présent dans la base.")

def update_from_city():
    city = st.session_state.get("city_select", "").strip()
    if not city:
        return
    zips = CITY_TO_ZIPS.get(city.upper(), [])
    if zips:
        chosen = zips[0]
        st.session_state["zip_select"] = chosen
        info = ZIP_DB[chosen]
        st.session_state["state_input"] = info.get("state", "CA")
        st.session_state["office_select"] = info.get("office", "")
    else:
        st.warning("Ville non trouvée dans la base locale.")

def update_from_office():
    office = st.session_state.get("office_select", "").strip()
    if not office:
        return
    zips = OFFICE_TO_ZIPS.get(office, [])
    if zips:
        chosen = zips[0]
        st.session_state["zip_select"] = chosen
        info = ZIP_DB[chosen]
        st.session_state["city_select"] = info.get("city", "")
        st.session_state["state_input"] = info.get("state", "CA")
    else:
        st.info("Aucune correspondance ZIP connue pour ce bureau dans la base locale.")

# Widgets
ln = st.text_input("Nom de famille", st.session_state["ln_input"], key="ln_input")
fn = st.text_input("Prénom", st.session_state["fn_input"], key="fn_input")
address1 = st.text_input("Adresse (ligne 1)", st.session_state["address1_input"], key="address1_input")
address2 = st.text_input("Adresse (ligne 2)", st.session_state["address2_input"], key="address2_input")

zip_options = sorted(ZIP_DB.keys())
city_options = sorted({info["city"] for info in ZIP_DB.values() if info.get("city")})
office_options = sorted({info["office"] for info in ZIP_DB.values() if info.get("office")})

col_zip, col_city = st.columns([2,3])
with col_zip:
    zip_select = st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state.get("zip_select")) if st.session_state.get("zip_select") in zip_options else 0,
        key="zip_select",
        on_change=update_from_zip
    )
with col_city:
    city_select = st.selectbox(
        "Ville",
        options=city_options,
        index=city_options.index(st.session_state.get("city_select")) if st.session_state.get("city_select") in city_options else 0,
        key="city_select",
        on_change=update_from_city
    )

office_all = sorted([o for o in office_options if o])
if not office_all:
    office_all = [""]
office_select = st.selectbox(
    "Field Office",
    options=office_all,
    index=office_all.index(st.session_state.get("office_select")) if st.session_state.get("office_select") in office_all else 0,
    key="office_select",
    on_change=update_from_office
)

state = st.text_input("État (abbrev.)", st.session_state["state_input"], key="state_input")
sex = st.selectbox("Sexe", ["M", "F"], index=0 if st.session_state["sex_input"] == "M" else 1, key="sex_input")
dob = st.date_input("Date de naissance", st.session_state["dob_input"], key="dob_input")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds", 0, 8, st.session_state["h1_input"], key="h1_input")
    w = st.number_input("Poids (lb)", 30, 500, st.session_state["w_input"], key="w_input")
with col2:
    h2 = st.number_input("Pouces", 0, 11, st.session_state["h2_input"], key="h2_input")
    eyes = st.text_input("Yeux", st.session_state["eyes_input"], key="eyes_input")
hair = st.text_input("Cheveux", st.session_state["hair_input"], key="hair_input")
cls = st.text_input("Classe", st.session_state["cls_input"], key="cls_input")
rstr = st.text_input("Restrictions", st.session_state["rstr_input"], key="rstr_input")
endorse = st.text_input("Endorsements", st.session_state["endorse_input"], key="endorse_input")
iss = st.date_input("Date d'émission", st.session_state["iss_input"], key="iss_input")

generate = st.button("Générer la carte")

# -------------------------
# Validation & génération
def validate_inputs() -> List[str]:
    errors: List[str] = []
    if not st.session_state.get("ln_input", "").strip():
        errors.append("Nom de famille requis.")
    if not st.session_state.get("fn_input", "").strip():
        errors.append("Prénom requis.")
    if st.session_state.get("dob_input") > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if st.session_state.get("iss_input") > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if st.session_state.get("w_input", 0) < 30 or st.session_state.get("w_input", 0) > 500:
        errors.append("Poids hors plage attendue.")
    if st.session_state.get("h1_input", 0) < 0 or st.session_state.get("h1_input", 0) > 8 or st.session_state.get("h2_input", 0) < 0 or st.session_state.get("h2_input", 0) > 11:
        errors.append("Taille hors plage attendue.")
    if not st.session_state.get("address1_input", "").strip():
        errors.append("Adresse (ligne 1) requise.")
    if not st.session_state.get("city_select", "").strip():
        errors.append("Ville requise.")
    if not st.session_state.get("state_input", "").strip():
        errors.append("État requis.")
    if not st.session_state.get("zip_select", "").strip():
        errors.append("Code postal requis.")
    z = re.sub(r"\D", "", st.session_state.get("zip_select", ""))
    if z and z not in ZIP_DB:
        try:
            zi = int(z)
            if not (90001 <= zi <= 96162):
                errors.append("Code postal hors plage CA (90001–96162).")
        except Exception:
            errors.append("Code postal invalide.")
    return errors

def build_aamva_tags(fields: Dict[str,str]) -> str:
    header = "@\n\rANSI 636014080102DL"
    parts = [header]
    for tag in ("DCS","DAC","DBB","DBA","DBD","DAQ","DAG","DAH","DAI","DAJ","DAK","DCF","DAU","DAY","DAZ"):
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return "\u001e\r".join(parts) + "\r"

def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def create_pdf_bytes(fields: Dict[str,str], photo_bytes: bytes = None) -> bytes:
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
    if photo_bytes:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 72 - 90, height - 72 - 110, width=90, height=110)
        except Exception:
            pass
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
        st.stop()

    ln_val = st.session_state["ln_input"]
    fn_val = st.session_state["fn_input"]
    address1_val = st.session_state["address1_input"]
    address2_val = st.session_state["address2_input"]
    city_val = st.session_state["city_select"]
    state_val = st.session_state["state_input"]
    postal_val = st.session_state["zip_select"]

    r = random.Random(seed(ln_val, fn_val, st.session_state["dob_input"]))
    dl = rletter(r, ln_val[0] if ln_val else "") + rdigits(r,7)

    exp_year = st.session_state["iss_input"].year + 5
    try:
        exp = datetime.date(exp_year, st.session_state["dob_input"].month, st.session_state["dob_input"].day)
    except ValueError:
        if st.session_state["dob_input"].month == 2 and st.session_state["dob_input"].day == 29:
            exp = datetime.date(exp_year, 2, 28)
        else:
            last_day = (datetime.date(exp_year, st.session_state["dob_input"].month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            exp = datetime.date(exp_year, st.session_state["dob_input"].month, min(st.session_state["dob_input"].day, last_day))

    office_choice = st.session_state.get("office_select", "")
    m = re.search(r"\((\d{2,3})\)", office_choice or "")
    office_code = int(m.group(1)) if m else 0

    seq = next_sequence(r).zfill(2)
    dd = f"{st.session_state['iss_input'].strftime('%m/%d/%Y')}{office_code}/{seq}FD/{st.session_state['iss_input'].year%100}"

    eyes_disp = (st.session_state.get("eyes_input") or "").upper()
    hair_disp = (st.session_state.get("hair_input") or "").upper()
    cls_disp = (st.session_state.get("cls_input") or "").upper()
    rstr_disp = (st.session_state.get("rstr_input") or "").upper()
    endorse_disp = (st.session_state.get("endorse_input") or "").upper()
    height_str = f"{int(st.session_state.get('h1_input',0))}'{int(st.session_state.get('h2_input',0))}\""

    fields = {
        "DCS": ln_val.upper(),
        "DAC": fn_val.upper(),
        "DBB": st.session_state["dob_input"].strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": st.session_state["iss_input"].strftime("%m%d%Y"),
        "DAQ": dl,
        "DAG": address1_val.upper(),
        "DAH": address2_val.upper() if address2_val else None,
        "DAI": city_val.upper(),
        "DAJ": state_val.upper(),
        "DAK": re.sub(r"\D","",postal_val)[:10],
        "DCF": dd,
        "DAU": f"{int(st.session_state.get('h1_input',0))}{int(st.session_state.get('h2_input',0))}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
    }
    fields = {k:v for k,v in fields.items() if v is not None}
    aamva = build_aamva_tags(fields)
    data_bytes = aamva.encode("utf-8")

    # photo par défaut
    IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
    IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
    photo_src = IMAGE_M_URL if st.session_state.get("sex_input") == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/png"
        if photo_bytes[:3] == b'\xff\xd8\xff':
            mime = "image/jpeg"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    html = (
        "<div class='card'>"
        "<div class='header'><div>CALIFORNIA USA DRIVER LICENSE</div>"
        f"<div class='badge'>{dl}</div></div>"
        "<div class='body'>"
        f"{photo_html}"
        "<div class='info'>"
        "<div class='label'>Nom</div><div class='value'>" + ln_val + "</div>"
        "<div class='label'>Prénom</div><div class='value'>" + fn_val + "</div>"
        "<div class='label'>Sexe</div><div class='value'>" + st.session_state.get("sex_input") + "</div>"
        "<div class='label'>DOB</div><div class='value'>" + st.session_state["dob_input"].strftime("%m/%d/%Y") + "</div>"
        "<div class='label'>Adresse</div><div class='value'>" + f"{address1_val} {address2_val}" + "</div>"
        "<div class='label'>Ville / État / Code postal</div><div class='value'>" + f"{city_val} / {state_val} / {postal_val}" + "</div>"
        "<div class='label'>Field Office</div><div class='value'>" + (office_choice or "") + "</div>"
        "<div class='label'>DD</div><div class='value'>" + dd + "</div>"
        "<div class='label'>ISS</div><div class='value'>" + st.session_state['iss_input'].strftime('%m/%d/%Y') + "</div>"
        "<div class='label'>EXP</div><div class='value'>" + exp.strftime('%m/%d/%Y') + "</div>"
        "<div class='label'>Classe</div><div class='value'>" + cls_disp + "</div>"
        "<div class='label'>Restrictions</div><div class='value'>" + rstr_disp + "</div>"
        "<div class='label'>Endorsements</div><div class='value'>" + endorse_disp + "</div>"
        "<div class='label'>Yeux / Cheveux / Taille / Poids</div><div class='value'>" + f"{eyes_disp} / {hair_disp} / {height_str} / {w} lb" + "</div>"
        "</div></div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)

    st.subheader("Payload AAMVA (brut)")
    st.code(aamva, language="text")

    if st.button("Afficher AAMVA JSON parsé"):
        def parse_payload(payload: str) -> Dict[str,str]:
            s = payload.replace("\r\n","\n").replace("\r","\n")
            s = s.lstrip("\n\r @\u001e")
            lines = [ln for ln in s.split("\n") if ln.strip()]
            result = {}
            for ln in lines:
                m = re.match(r"^([A-Z]{3})(.*)$", ln)
                if m:
                    result[m.group(1)] = m.group(2).strip()
            return result
        st.json(parse_payload(aamva))

    # PDF417
    if _PDF417_AVAILABLE:
        try:
            svg_str = generate_pdf417_svg(data_bytes, columns=columns_param, security_level=security_level_param, scale=scale_param, ratio=ratio_param, color=color_param)
            svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
            components.html(svg_html, height=220, scrolling=True)
        except Exception as e:
            st.error("Erreur génération PDF417 : " + str(e))
            st.info("Vérifiez le module pdf417gen dans le dossier vendorisé.")
    else:
        st.warning("pdf417gen non disponible. Vendorisez le module si vous voulez afficher PDF417.")

    cols = st.columns(2)
    with cols[0]:
        if _PDF417_AVAILABLE:
            try:
                svg_bytes = svg_str.encode("utf-8")
                st.download_button("Télécharger PDF417 (SVG)", data=svg_bytes, file_name="pdf417.svg", mime="image/svg+xml")
            except Exception:
                pass
    with cols[1]:
        pdf_bytes = create_pdf_bytes({
            "Nom": ln_val,
            "Prénom": fn_val,
            "Sexe": st.session_state.get("sex_input"),
            "DOB": st.session_state["dob_input"].strftime("%m/%d/%Y"),
            "Adresse": f"{address1_val} {address2_val}".strip(),
            "Ville": city_val,
            "État": state_val,
            "Code postal": postal_val,
            "Field Office": office_choice,
            "DD": dd,
            "ISS": st.session_state["iss_input"].strftime("%m/%d/%Y"),
            "EXP": exp.strftime("%m/%d/%Y"),
            "Classe": cls_disp,
            "Restrictions": rstr_disp,
            "Endorsements": endorse_disp,
            "Yeux/Cheveux/Taille/Poids": f"{eyes_disp}/{hair_disp}/{height_str}/{w} lb"
        }, photo_bytes=photo_bytes)
        st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf", mime="application/pdf")
