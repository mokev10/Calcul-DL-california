#!/usr/bin/env python3
# driver_license_final_fixed.py
# Générateur de permis CA (Streamlit)
# Version avec boutons "Appliquer" pour lookup ZIP <-> city <-> field office et debug visible.

import streamlit as st
import datetime, random, hashlib, io, base64, requests, re
import streamlit.components.v1 as components
from typing import Dict, Optional

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# Petite "base de données" ZIP -> city/state/office
ZIP_DB = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": "Baie de San Francisco — Corte Madera (525)"},
    "95818": {"city": "Sacramento", "state": "CA", "office": "Sacramento / Nord — Sacramento (Broadway) (500)"},
    "94102": {"city": "San Francisco", "state": "CA", "office": "Baie de San Francisco — San Francisco (503)"},
    "94015": {"city": "Daly City", "state": "CA", "office": "Baie de San Francisco — Daly City (599)"},
}

# Reverse indices
CITY_TO_ZIPS: Dict[str, list] = {}
OFFICE_TO_ZIPS: Dict[str, list] = {}
for z, info in ZIP_DB.items():
    city_u = info["city"].upper()
    CITY_TO_ZIPS.setdefault(city_u, []).append(z)
    office = info.get("office")
    if office:
        OFFICE_TO_ZIPS.setdefault(office, []).append(z)

# -------------------------
# Images par défaut (M / F)
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"

# -------------------------
# CSS (inchangé)
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
.debug { font-size:12px; background:#f6f6f6; padding:8px; border-radius:6px; margin-top:12px; color:#111; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar PDF417 params
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6)
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0,9)), index=2)
scale_param = st.sidebar.slider("Échelle", 1, 6, 3)
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3)
color_param = st.sidebar.color_picker("Couleur du code", "#000000")
st.sidebar.markdown("Si pdf417gen n'est pas complet, l'app affichera un message d'avertissement.")

# -------------------------
# Offices (liste complète)
offices = {
    "Baie de San Francisco — Corte Madera (525)": 525,
    "Baie de San Francisco — Daly City (599)": 599,
    "Baie de San Francisco — El Cerrito (585)": 585,
    "Baie de San Francisco — Fremont (643)": 643,
    "Baie de San Francisco — Hayward (521)": 521,
    "Baie de San Francisco — Los Gatos (641)": 641,
    "Baie de San Francisco — Novato (647)": 647,
    "Baie de San Francisco — Oakland (Claremont) (501)": 501,
    "Baie de San Francisco — Oakland (Coliseum) (604)": 604,
    "Baie de San Francisco — Pittsburg (651)": 651,
    "Baie de San Francisco — Pleasanton (639)": 639,
    "Baie de San Francisco — Redwood City (542)": 542,
    "Baie de San Francisco — San Francisco (503)": 503,
    "Baie de San Francisco — San Jose (Alma) (516)": 516,
    "Baie de San Francisco — San Jose (Driver License Center) (607)": 607,
    "Baie de San Francisco — San Mateo (594)": 594,
    "Baie de San Francisco — Santa Clara (632)": 632,
    "Baie de San Francisco — Vallejo (538)": 538,
    "Grand Los Angeles — Arleta (628)": 628,
    "Grand Los Angeles — Bellflower (610)": 610,
    "Grand Los Angeles — Culver City (514)": 514,
    "Grand Los Angeles — Glendale (540)": 540,
    "Grand Los Angeles — Hollywood (633)": 633,
    "Grand Los Angeles — Inglewood (544)": 544,
    "Grand Los Angeles — Long Beach (507)": 507,
    "Grand Los Angeles — Los Angeles (Hope St) (502)": 502,
    "Grand Los Angeles — Montebello (531)": 531,
    "Grand Los Angeles — Pasadena (510)": 510,
    "Grand Los Angeles — Santa Monica (548)": 548,
    "Grand Los Angeles — Torrance (592)": 592,
    "Grand Los Angeles — West Covina (591)": 591,
    "Orange County / Sud — Costa Mesa (627)": 627,
    "Orange County / Sud — Fullerton (547)": 547,
    "Orange County / Sud — Laguna Hills (642)": 642,
    "Orange County / Sud — Santa Ana (529)": 529,
    "Orange County / Sud — San Clemente (652)": 652,
    "Orange County / Sud — Westminster (623)": 623,
    "San Diego & Environs — Chula Vista (609)": 609,
    "San Diego & Environs — El Cajon (549)": 549,
    "San Diego & Environs — Oceanside (593)": 593,
    "San Diego & Environs — San Diego (Clairemont) (618)": 618,
    "San Diego & Environs — San Diego (Normal St) (504)": 504,
    "San Diego & Environs — San Marcos (637)": 637,
    "San Diego & Environs — San Ysidro (649)": 649,
    "Sacramento / Nord — Auburn (533)": 533,
    "Sacramento / Nord — Chico (534)": 534,
    "Sacramento / Nord — Eureka (522)": 522,
    "Sacramento / Nord — Redding (550)": 550,
    "Sacramento / Nord — Roseville (635)": 635,
    "Sacramento / Nord — Sacramento (Broadway) (500)": 500,
    "Sacramento / Nord — Sacramento (South) (603)": 603,
    "Sacramento / Nord — Woodland (535)": 535,
    "Vallée Centrale — Bakersfield (511)": 511,
    "Vallée Centrale — Fresno (505)": 505,
    "Vallée Centrale — Lodi (595)": 595,
    "Vallée Centrale — Modesto (536)": 536,
    "Vallée Centrale — Stockton (517)": 517,
    "Vallée Centrale — Visalia (519)": 519
}

# -------------------------
# Initialisation session_state sûre
defaults = {
    "ln_input": "HARMS", "fn_input": "ROSA",
    "address1_input": "2570 24TH STREET", "address2_input": "",
    "postal_code_input": "94925", "city_input": "Corte Madera", "state_input": "CA",
    "sex_input": "M", "dob_input": datetime.date(1990,1,1),
    "h1_input": 5, "h2_input": 10, "w_input": 160,
    "eyes_input": "BRN", "hair_input": "BRN",
    "cls_input": "C", "rstr_input": "NONE", "endorse_input": "NONE",
    "iss_input": datetime.date.today(), "office_choice": list(offices.keys())[0]
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------
# Fonctions utilitaires
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
    return r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(r):
    return str(r.randint(10,99))

# -------------------------
# Lookup functions (utilisées par les boutons)
def apply_postal_code_lookup():
    pc = st.session_state.get("postal_code_input", "").strip()
    pc_digits = re.sub(r"\D", "", pc)[:10]
    if pc_digits in ZIP_DB:
        info = ZIP_DB[pc_digits]
        st.session_state["city_input"] = info.get("city", st.session_state.get("city_input"))
        st.session_state["state_input"] = info.get("state", st.session_state.get("state_input"))
        office_name = info.get("office")
        if office_name and office_name in offices:
            st.session_state["office_choice"] = office_name
        st.success(f"Lookup ZIP {pc_digits} → {info['city']}, {info['state']}")
    else:
        st.warning(f"Code postal {pc_digits} non trouvé dans la base locale.")

def apply_city_lookup():
    city_val = st.session_state.get("city_input", "").strip().upper()
    if not city_val:
        st.warning("Ville vide.")
        return
    zips = CITY_TO_ZIPS.get(city_val)
    if zips:
        chosen = zips[0]
        info = ZIP_DB[chosen]
        st.session_state["postal_code_input"] = chosen
        st.session_state["state_input"] = info.get("state", st.session_state.get("state_input"))
        if info.get("office") in offices:
            st.session_state["office_choice"] = info.get("office")
        st.success(f"Lookup Ville {city_val} → ZIP {chosen}")
    else:
        st.warning(f"Ville '{city_val}' non trouvée dans la base locale.")

def apply_office_lookup():
    office_val = st.session_state.get("office_choice", "")
    if not office_val:
        st.warning("Field Office vide.")
        return
    zips = OFFICE_TO_ZIPS.get(office_val)
    if zips:
        chosen = zips[0]
        info = ZIP_DB[chosen]
        st.session_state["postal_code_input"] = chosen
        st.session_state["city_input"] = info.get("city", st.session_state.get("city_input"))
        st.session_state["state_input"] = info.get("state", st.session_state.get("state_input"))
        st.success(f"Lookup Office → ZIP {chosen}, Ville {info.get('city')}")
    else:
        st.info("Aucune correspondance ZIP connue pour ce bureau dans la base locale.")

# -------------------------
# Parser AAMVA minimal (pour debug)
AAMVA_MAP = {
    "DCS":"last_name","DAC":"first_name","DCT":"full_name_trunc",
    "DBB":"date_of_birth","DBA":"expiration_date","DBD":"issue_date",
    "DAQ":"id_number","DAG":"address1","DAH":"address2","DAI":"city",
    "DAJ":"state","DAK":"postal_code","DCF":"document_discriminator",
    "DAU":"height","DAY":"eye_color","DAZ":"hair_color"
}
def mmddyyyy_to_iso(s: str) -> Optional[str]:
    s = s.strip()
    if not re.fullmatch(r"\d{6,8}", s):
        return None
    try:
        return datetime.datetime.strptime(s, "%m%d%Y").date().isoformat()
    except Exception:
        return None

def normalize_name(name: str) -> str:
    name = name.strip().replace("<", " ").replace("/", " ")
    return " ".join(part.capitalize() for part in name.split())

def parse_payload(payload: str) -> Dict[str, Optional[str]]:
    s = payload.replace("\r\n", "\n").replace("\r", "\n")
    s = s.lstrip("\n\r @\u001e")
    lines = [ln for ln in s.split("\n") if ln.strip() != ""]
    result = {"raw_lines": lines}
    token_re = re.compile(r"^([A-Z]{3})(.*)$")
    for ln in lines:
        m = token_re.match(ln)
        if m:
            code = m.group(1); value = m.group(2).strip()
            key = AAMVA_MAP.get(code)
            if key:
                if key in ("date_of_birth","expiration_date","issue_date"):
                    iso = mmddyyyy_to_iso(value); result[key] = iso or value
                elif key in ("first_name","last_name"):
                    result[key] = normalize_name(value)
                else:
                    result[key] = value
            else:
                result[f"raw_{code}"] = value
        else:
            if ln.startswith("ANSI") or ln.startswith("AAMVA"):
                result["header"] = ln.strip()
            else:
                result.setdefault("other_lines", []).append(ln.strip())
    if result.get("first_name") or result.get("last_name"):
        result["full_name"] = " ".join(p for p in [result.get("first_name"), result.get("last_name")] if p)
    if "postal_code" in result and result["postal_code"]:
        result["postal_code"] = re.sub(r"\D", "", result["postal_code"])
    return result

# -------------------------
# PDF417 helper (attempt import)
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
# Image fetch
def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5); resp.raise_for_status(); return resp.content
    except Exception:
        return None

# -------------------------
# PDF creation
def create_pdf_bytes(fields: Dict[str,str], photo_bytes: bytes = None) -> bytes:
    buffer = io.BytesIO(); c = canvas.Canvas(buffer, pagesize=letter); width, height = letter
    x = 72; y = height - 72
    c.setFont("Helvetica-Bold", 14); c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE"); y -= 24
    c.setFont("Helvetica", 11)
    for k, v in fields.items():
        c.drawString(x, y, f"{k}: {v}"); y -= 16
        if y < 72: c.showPage(); y = height - 72
    if photo_bytes:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 72 - 90, height - 72 - 110, width=90, height=110)
        except Exception:
            pass
    c.showPage(); c.save(); buffer.seek(0); return buffer.read()

# -------------------------
# FORMULAIRE (widgets)
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom de famille", st.session_state["ln_input"], key="ln_input")
fn = st.text_input("Prénom", st.session_state["fn_input"], key="fn_input")
address1 = st.text_input("Adresse (ligne 1)", st.session_state["address1_input"], key="address1_input")
address2 = st.text_input("Adresse (ligne 2)", st.session_state["address2_input"], key="address2_input")

postal_col, city_col = st.columns([2,3])
with postal_col:
    postal_code = st.text_input("Code postal", st.session_state["postal_code_input"], key="postal_code_input")
with city_col:
    city = st.text_input("Ville", st.session_state["city_input"], key="city_input")

state = st.text_input("État (abbrev.)", st.session_state["state_input"], key="state_input")
sex = st.selectbox("Sexe", ["M","F"], index=0 if st.session_state["sex_input"]=="M" else 1, key="sex_input")
dob = st.date_input("Date de naissance", st.session_state["dob_input"], key="dob_input")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds",0,8,st.session_state["h1_input"], key="h1_input")
    w = st.number_input("Poids (lb)",30,500,st.session_state["w_input"], key="w_input")
with col2:
    h2 = st.number_input("Pouces",0,11,st.session_state["h2_input"], key="h2_input")
    eyes = st.text_input("Yeux", st.session_state["eyes_input"], key="eyes_input")
hair = st.text_input("Cheveux", st.session_state["hair_input"], key="hair_input")
cls = st.text_input("Classe", st.session_state["cls_input"], key="cls_input")
rstr = st.text_input("Restrictions", st.session_state["rstr_input"], key="rstr_input")
endorse = st.text_input("Endorsements", st.session_state["endorse_input"], key="endorse_input")
iss = st.date_input("Date d'émission", st.session_state["iss_input"], key="iss_input")

office_list = list(offices.keys())
if st.session_state.get("office_choice") not in office_list:
    st.session_state["office_choice"] = office_list[0]
office_choice = st.selectbox("Field Office", office_list, index=office_list.index(st.session_state["office_choice"]), key="office_choice")

# Buttons to apply lookups (explicit, reliable)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Appliquer code postal"):
        apply_postal_code_lookup()
with c2:
    if st.button("Appliquer ville"):
        apply_city_lookup()
with c3:
    if st.button("Appliquer bureau"):
        apply_office_lookup()

generate = st.button("Générer la carte")

# Debug panel (visible)
st.markdown("### Debug session_state")
st.code({k: st.session_state[k] for k in sorted(st.session_state.keys())}, language="json")

# -------------------------
# VALIDATIONS et génération (inchangées)
def validate_inputs():
    errors = []
    if not st.session_state.get("ln_input", "").strip(): errors.append("Nom de famille requis.")
    if not st.session_state.get("fn_input", "").strip(): errors.append("Prénom requis.")
    if st.session_state.get("dob_input") > datetime.date.today(): errors.append("Date de naissance ne peut pas être dans le futur.")
    if st.session_state.get("iss_input") > datetime.date.today(): errors.append("Date d'émission ne peut pas être dans le futur.")
    if st.session_state.get("w_input", 0) < 30 or st.session_state.get("w_input", 0) > 500: errors.append("Poids hors plage attendue.")
    if st.session_state.get("h1_input", 0) < 0 or st.session_state.get("h1_input", 0) > 8 or st.session_state.get("h2_input", 0) < 0 or st.session_state.get("h2_input", 0) > 11: errors.append("Taille hors plage attendue.")
    if not st.session_state.get("address1_input", "").strip(): errors.append("Adresse (ligne 1) requise.")
    if not st.session_state.get("city_input", "").strip(): errors.append("Ville requise.")
    if not st.session_state.get("state_input", "").strip(): errors.append("État requis.")
    if not st.session_state.get("postal_code_input", "").strip(): errors.append("Code postal requis.")
    return errors

def build_aamva_tags(fields: Dict[str,str]) -> str:
    header = "@\n\rANSI 636014080102DL"
    parts = [header]
    for tag in ("DCS","DAC","DBB","DBA","DBD","DAQ","DAG","DAH","DAI","DAJ","DAK","DCF","DAU","DAY","DAZ"):
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return "\u001e\r".join(parts) + "\r"

# Attempt to import pdf417gen
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

# Generation flow
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs: st.error(e)
        st.stop()

    ln_val = st.session_state["ln_input"]; fn_val = st.session_state["fn_input"]
    address1_val = st.session_state["address1_input"]; address2_val = st.session_state["address2_input"]
    city_val = st.session_state["city_input"]; state_val = st.session_state["state_input"]
    postal_val = re.sub(r"\D", "", st.session_state["postal_code_input"])[:10]

    r = random.Random(seed(ln_val,fn_val,st.session_state["dob_input"]))
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

    office_code = offices[st.session_state["office_choice"]]
    seq = next_sequence(r).zfill(2)
    dd = f"{st.session_state['iss_input'].strftime('%m/%d/%Y')}{office_code}/{seq}FD/{st.session_state['iss_input'].year%100}"

    eyes_disp = (st.session_state.get("eyes_input") or "").upper()
    hair_disp = (st.session_state.get("hair_input") or "").upper()
    cls_disp = (st.session_state.get("cls_input") or "").upper()
    rstr_disp = (st.session_state.get("rstr_input") or "").upper()
    endorse_disp = (st.session_state.get("endorse_input") or "").upper()
    height_str = f"{int(st.session_state.get('h1_input',0))}'{int(st.session_state.get('h2_input',0))}\""

    fields = {
        "DCS": ln_val.upper(), "DAC": fn_val.upper(),
        "DBB": st.session_state["dob_input"].strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"), "DBD": st.session_state["iss_input"].strftime("%m%d%Y"),
        "DAQ": dl, "DAG": address1_val.upper(),
        "DAH": address2_val.upper() if address2_val else None,
        "DAI": city_val.upper(), "DAJ": state_val.upper(), "DAK": postal_val,
        "DCF": dd, "DAU": f"{int(st.session_state.get('h1_input',0))}{int(st.session_state.get('h2_input',0))}",
        "DAY": eyes_disp, "DAZ": hair_disp
    }
    fields = {k: v for k, v in fields.items() if v is not None}
    aamva = build_aamva_tags(fields)
    data_bytes = aamva.encode("utf-8")

    photo_bytes = None
    photo_src = IMAGE_M_URL if st.session_state.get("sex_input") == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/png"
        if photo_bytes[:3] == b'\xff\xd8\xff': mime = "image/jpeg"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    html = f\"\"\"
    <div class="card">
        <div class="header"><div>CALIFORNIA USA DRIVER LICENSE</div><div class="badge">{dl}</div></div>
        <div class="body">{photo_html}
            <div class="info">
                <div class="label">Nom</div><div class="value">{ln_val}</div>
                <div class="label">Prénom</div><div class="value">{fn_val}</div>
                <div class="label">Sexe</div><div class="value">{st.session_state.get('sex_input')}</div>
                <div class="label">DOB</div><div class="value">{st.session_state['dob_input'].strftime('%m/%d/%Y')}</div>
                <div class="label">Adresse</div><div class="value">{address1_val} {address2_val}</div>
                <div class="label">Ville / État / Code postal</div><div class="value">{city_val} / {state_val} / {postal_val}</div>
                <div class="label">Field Office</div><div class="value">{st.session_state['office_choice']}</div>
                <div class="label">DD</div><div class="value">{dd}</div>
                <div class="label">ISS</div><div class="value">{st.session_state['iss_input'].strftime('%m/%d/%Y')}</div>
                <div class="label">EXP</div><div class="value">{exp.strftime('%m/%d/%Y')}</div>
                <div class="label">Classe</div><div class="value">{cls_disp}</div>
                <div class="label">Restrictions</div><div class="value">{rstr_disp}</div>
                <div class="label">Endorsements</div><div class="value">{endorse_disp}</div>
                <div class="label">Yeux / Cheveux / Taille / Poids</div><div class="value">{eyes_disp} / {hair_disp} / {height_str} / {w} lb</div>
            </div>
        </div>
    </div>
    \"\"\"
    st.markdown(html, unsafe_allow_html=True)

    st.subheader("Payload AAMVA (brut)")
    st.code(aamva, language="text")

    if st.button("Afficher AAMVA JSON parsé"):
        parsed = parse_payload(aamva)
        st.json(parsed)

    svg_str = None
    if _PDF417_AVAILABLE:
        try:
            svg_str = generate_pdf417_svg(data_bytes, columns=columns_param, security_level=security_level_param, scale=scale_param, ratio=ratio_param, color=color_param)
            svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
            components.html(svg_html, height=220, scrolling=True)
        except Exception as e:
            st.error("Erreur génération PDF417 : " + str(e)); st.info("Vérifiez le module pdf417gen dans le dossier vendorisé.")
    else:
        st.warning("pdf417gen non disponible. Vendorisez le module ou complétez pdf417gen/__init__.py pour exposer encode et render_svg.")

    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            svg_bytes = svg_str.encode("utf-8")
            st.download_button("Télécharger PDF417 (SVG)", data=svg_bytes, file_name="pdf417.svg", mime="image/svg+xml")
    with cols[1]:
        pdf_bytes = create_pdf_bytes({
            "Nom": ln_val, "Prénom": fn_val, "Sexe": st.session_state.get("sex_input"),
            "DOB": st.session_state["dob_input"].strftime("%m/%d/%Y"),
            "Adresse": f"{address1_val} {address2_val}".strip(), "Ville": city_val, "État": state_val, "Code postal": postal_val,
            "Field Office": st.session_state["office_choice"], "DD": dd,
            "ISS": st.session_state["iss_input"].strftime("%m/%d/%Y"), "EXP": exp.strftime("%m/%d/%Y"),
            "Classe": cls_disp, "Restrictions": rstr_disp, "Endorsements": endorse_disp,
            "Yeux/Cheveux/Taille/Poids": f"{eyes_disp}/{hair_disp}/{height_str}/{w} lb"
        }, photo_bytes=photo_bytes)
        st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf", mime="application/pdf")
