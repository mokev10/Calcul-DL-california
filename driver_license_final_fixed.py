#!/usr/bin/env python3
# driver_license_final_fixed.py
# Générateur de permis CA (Streamlit)
# Version : intégration automatique du texte (Output.txt) pour remplir ZIP_DB
# Remplace entièrement le fichier précédent par celui-ci.

import streamlit as st
import datetime
import random
import hashlib
import io
import base64
import requests
import re
import csv
from typing import Dict, Optional, List, Tuple

# Optional PDF parsing libs are not required here because user provided text.
# PDF417 attempt import (optional)
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

# ReportLab for PDF export
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import streamlit.components.v1 as components

st.set_page_config(page_title="Permis CA - ZIP Auto Import", layout="centered")

# -------------------------
# Utilities
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
# Minimal default ZIP_DB (kept small until import)
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": "Baie de San Francisco — Corte Madera (525)"},
    "95818": {"city": "Sacramento", "state": "CA", "office": "Sacramento / Nord — Sacramento (Broadway) (500)"},
    "94102": {"city": "San Francisco", "state": "CA", "office": "Baie de San Francisco — San Francisco (503)"},
    "94015": {"city": "Daly City", "state": "CA", "office": "Baie de San Francisco — Daly City (599)"},
}

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
# CSS
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
.debug { font-size:12px; background:#f6f6f6; padding:8px; border-radius:6px; margin-top:12px; color:#111; white-space:pre-wrap; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Parsing logic for the provided text (Output.txt style)
def parse_text_to_zip_entries(text: str) -> Dict[str, Dict[str, str]]:
    """
    Robust heuristics to extract zipcode, city, state, (optional office) from a raw text dump.
    Returns a dict mapping zipcode -> {city, state, office}
    """
    entries: Dict[str, Dict[str, str]] = {}

    # Normalize whitespace and replace HTML table tags if present
    t = text.replace("\r", "\n")
    t = re.sub(r"<\/?table>|<\/?tr>|<\/?td>|<\/?th>", "\n", t, flags=re.IGNORECASE)
    t = re.sub(r"&nbsp;|\t", " ", t)
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]

    # Strategy A: lines that contain a 5-digit zip and a city on same or adjacent lines
    i = 0
    while i < len(lines):
        ln = lines[i]
        # find 5-digit zip anywhere in the line
        m = re.search(r"\b(9[0-6]\d{3})\b", ln)
        if m:
            z = m.group(1)
            # attempt to find city on same line after zip
            after = ln[m.end():].strip(" ,:-")
            city = ""
            state = "CA"
            office = ""
            if after:
                # if after contains letters, take first chunk as city
                city_candidate = re.split(r"[,\t\-–:]", after)[0].strip()
                if re.search(r"[A-Za-z]", city_candidate):
                    city = city_candidate.title()
            # else try next line(s) for city/state
            if not city and i + 1 < len(lines):
                next_ln = lines[i+1]
                # if next line looks like a city (letters) and not another zip
                if not re.search(r"\b9[0-6]\d{3}\b", next_ln) and re.search(r"[A-Za-z]", next_ln):
                    city = re.split(r"[,\t\-–:]", next_ln)[0].strip().title()
                    # if next line contains state or office, try to capture
                    # check following line for state or office
                    if i + 2 < len(lines):
                        maybe_state = lines[i+2]
                        if re.search(r"\bCA\b", maybe_state):
                            state = "CA"
                        elif re.search(r"\b[A-Z]{2}\b", maybe_state):
                            state = re.search(r"\b([A-Z]{2})\b", maybe_state).group(1)
            # fallback: if city still empty, try previous line
            if not city and i - 1 >= 0:
                prev_ln = lines[i-1]
                if not re.search(r"\b9[0-6]\d{3}\b", prev_ln) and re.search(r"[A-Za-z]", prev_ln):
                    city = re.split(r"[,\t\-–:]", prev_ln)[0].strip().title()
            entries[z] = {"city": city, "state": state, "office": office}
            i += 1
            continue
        i += 1

    # Strategy B: detect table-like sequences "ZipCode City State" repeated
    # Try to find sequences of three tokens where first is zip, second is city, third is state
    for idx in range(len(lines)-2):
        a, b, c = lines[idx], lines[idx+1], lines[idx+2]
        if re.fullmatch(r"\d{5}", a) and re.fullmatch(r"[A-Za-z][A-Za-z '\-\.&]+", b) and re.fullmatch(r"[A-Z]{2}", c):
            z = a
            city = b.title()
            state = c
            entries[z] = {"city": city, "state": state, "office": entries.get(z, {}).get("office", "")}

    # Strategy C: look for patterns like "City  CA  94925" or "City CA 94925"
    # We'll search for 5-digit zips and look backwards for a city token
    for idx, ln in enumerate(lines):
        for m in re.finditer(r"\b(9[0-6]\d{3})\b", ln):
            z = m.group(1)
            if z in entries and entries[z].get("city"):
                continue
            # try to extract city from same line before zip
            before = ln[:m.start()].strip(" ,:-")
            city = ""
            if before:
                # take last comma-separated chunk
                city_candidate = re.split(r"[,\t\-–:]", before)[-1].strip()
                if re.search(r"[A-Za-z]", city_candidate):
                    city = city_candidate.title()
            # if still empty, try previous line
            if not city and idx > 0:
                prev = lines[idx-1]
                if not re.search(r"\b9[0-6]\d{3}\b", prev) and re.search(r"[A-Za-z]", prev):
                    city = re.split(r"[,\t\-–:]", prev)[0].strip().title()
            if not city:
                city = entries.get(z, {}).get("city", "")
            entries[z] = {"city": city, "state": entries.get(z, {}).get("state", "CA"), "office": entries.get(z, {}).get("office", "")}

    # Strategy D: clean up empty city names by grouping zips by nearby known cities
    # If many zips have empty city but share contiguous blocks, leave empty (user can refine)
    # Final normalization: ensure zip keys are 5-digit strings
    normalized: Dict[str, Dict[str, str]] = {}
    for z, info in entries.items():
        zc = re.sub(r"\D", "", z)[:5]
        if len(zc) == 5:
            normalized[zc] = {
                "city": (info.get("city") or "").strip(),
                "state": (info.get("state") or "CA").strip(),
                "office": (info.get("office") or "").strip()
            }
    return normalized

# -------------------------
# UI: allow user to paste text or upload the text file (Output.txt)
st.title("Importer automatiquement la base ZIP depuis ton texte (Output.txt)")

st.markdown(
    "Colle le contenu du fichier texte (Output.txt) ou téléverse le fichier texte. "
    "Le script va parser automatiquement les Zip / City / State et remplir la base."
)

col1, col2 = st.columns(2)
with col1:
    uploaded_txt = st.file_uploader("Téléverser Output.txt (texte)", type=["txt"])
with col2:
    pasted = st.text_area("Ou coller le texte ici", height=200)

if st.button("Parser et intégrer le texte"):
    raw = ""
    if uploaded_txt is not None:
        try:
            raw = uploaded_txt.read().decode("utf-8", errors="replace")
        except Exception:
            raw = uploaded_txt.read().decode("latin-1", errors="replace")
    elif pasted and pasted.strip():
        raw = pasted
    else:
        st.error("Aucun texte fourni. Colle le contenu ou téléverse le fichier Output.txt.")
        st.stop()

    parsed = parse_text_to_zip_entries(raw)
    if not parsed:
        st.warning("Aucune entrée ZIP détectée par l'heuristique. Le texte peut avoir un format particulier.")
    else:
        # Merge parsed into ZIP_DB (prefer existing non-empty values)
        added = 0
        updated = 0
        for z, info in parsed.items():
            if z in ZIP_DB:
                # update missing fields only
                changed = False
                for k in ("city", "state", "office"):
                    if info.get(k) and not ZIP_DB[z].get(k):
                        ZIP_DB[z][k] = info[k]
                        changed = True
                if changed:
                    updated += 1
            else:
                ZIP_DB[z] = {"city": info.get("city",""), "state": info.get("state","CA"), "office": info.get("office","")}
                added += 1
        # rebuild indices
        CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)
        st.success(f"Import terminé — ajoutés: {added}, mis à jour: {updated}, total base: {len(ZIP_DB)}")

# -------------------------
# Allow quick automatic mapping: if user enters a zip, auto-select city/office
st.markdown("---")
st.title("Générateur officiel de permis CA (avec ZIP auto)")

# Ensure session_state defaults
if "ln_input" not in st.session_state:
    st.session_state.update({
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
    })

# Synchronization callbacks
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

# Form fields
ln = st.text_input("Nom de famille", st.session_state["ln_input"], key="ln_input")
fn = st.text_input("Prénom", st.session_state["fn_input"], key="fn_input")
address1 = st.text_input("Adresse (ligne 1)", st.session_state["address1_input"], key="address1_input")
address2 = st.text_input("Adresse (ligne 2)", st.session_state["address2_input"], key="address2_input")

# Build options from ZIP_DB (refresh each render)
zip_options = sorted(ZIP_DB.keys())
city_options = sorted({info.get("city") for info in ZIP_DB.values() if info.get("city")})
office_options = sorted({info.get("office") for info in ZIP_DB.values() if info.get("office")})

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

office_all = sorted(set(office_options))
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

# Debug panel
st.markdown("### Debug (aperçu de la base et session_state)")
st.write(f"Entrées ZIP_DB : {len(ZIP_DB)}")
if st.checkbox("Afficher quelques entrées ZIP_DB"):
    sample = dict(list(ZIP_DB.items())[:200])
    st.json(sample)
st.code({k: st.session_state.get(k) for k in sorted(st.session_state.keys())}, language="json")

# -------------------------
# Validation and generation (AAMVA + PDF)
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
    # Validate zip numeric range if not in DB
    z = re.sub(r"\D", "", st.session_state.get("zip_select", ""))
    if z and z not in ZIP_DB:
        try:
            zi = int(z)
            if not (90001 <= zi <= 96162):
                errors.append("Code postal hors plage CA (90001–96162).")
        except Exception:
            errors.append("Code postal invalide.")
    return errors

def build_aamva_tags(fields: Dict[str, str]) -> str:
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
    m = re.search(r"\((\d{3})\)", office_choice or "")
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

    # photo default
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
        # minimal parser for debug
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

    # PDF417 display if available
    if _PDF417_AVAILABLE:
        try:
            svg_str = encode(data_bytes, columns=6, security_level=2, force_binary=False)
            # render_svg returns an ElementTree; use helper if available
            svg_html = "<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>PDF417</div>"
            components.html(svg_html, height=220, scrolling=True)
        except Exception as e:
            st.error("Erreur génération PDF417 : " + str(e))
    else:
        st.info("pdf417gen non disponible. Le PDF417 ne sera pas affiché.")

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
