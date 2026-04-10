#!/usr/bin/env python3
# driver_license_final_fixed.py
# Générateur de permis CA (Streamlit)
# Version finale : import PDF/CSV pour ZIP_DB, selectboxes recherchables synchronisés,
# parsing AAMVA, génération PDF417 (si pdf417gen présent).
#
# Remplace entièrement ton ancien fichier par celui-ci.
# Requirements recommandés (ajoute dans requirements.txt si besoin):
# streamlit, requests, reportlab, pdf417gen (optionnel), pdfplumber (optionnel)

import streamlit as st
import datetime
import random
import hashlib
import io
import base64
import requests
import re
import csv
import json
from typing import Dict, Optional, List

# Optional PDF parsing library
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except Exception:
    _PDFPLUMBER_AVAILABLE = False

# PDF417 library attempt
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

st.set_page_config(page_title="Permis CA - Import ZIP", layout="centered")

# -------------------------
# Helper functions
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

# -------------------------
# Minimal default sample (kept small) - will be replaced by import
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": "Baie de San Francisco — Corte Madera (525)"},
    "95818": {"city": "Sacramento", "state": "CA", "office": "Sacramento / Nord — Sacramento (Broadway) (500)"},
    "94102": {"city": "San Francisco", "state": "CA", "office": "Baie de San Francisco — San Francisco (503)"},
    "94015": {"city": "Daly City", "state": "CA", "office": "Baie de San Francisco — Daly City (599)"},
}

CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)

# -------------------------
# UI: upload PDF or CSV to populate ZIP_DB
st.title("Importer la base ZIP (ZIP → City → State → Field Office)")

st.markdown(
    "Tu peux téléverser **un PDF** (liste ZIP/City) ou **un CSV** (colonnes: zipcode,city,state,office). "
    "Le script tentera d'extraire automatiquement les paires ZIP/City/State/Office depuis le PDF."
)

col1, col2 = st.columns(2)
with col1:
    uploaded_pdf = st.file_uploader("Téléverser le PDF contenant la base ZIP (optionnel)", type=["pdf"])
with col2:
    uploaded_csv = st.file_uploader("Ou téléverser un CSV (zipcode,city,state,office)", type=["csv"])

# Button to trigger import
if st.button("Importer et reconstruire la base ZIP"):
    imported = 0
    errors = []
    new_db: Dict[str, Dict[str, str]] = {}

    # 1) Try CSV first if provided
    if uploaded_csv is not None:
        try:
            text = uploaded_csv.read().decode("utf-8", errors="replace")
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                z = re.sub(r"\D", "", (row.get("zipcode") or "").strip())
                if not z:
                    continue
                new_db[z] = {
                    "city": (row.get("city") or "").strip(),
                    "state": (row.get("state") or "").strip() or "CA",
                    "office": (row.get("office") or "").strip(),
                }
            imported += len(new_db)
            st.success(f"Import CSV : {len(new_db)} entrées ajoutées.")
        except Exception as e:
            errors.append(f"Erreur import CSV: {e}")

    # 2) If PDF provided, try to extract
    if uploaded_pdf is not None:
        try:
            pdf_bytes = uploaded_pdf.read()
            text_all = ""
            if _PDFPLUMBER_AVAILABLE:
                try:
                    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                        for page in pdf.pages:
                            text_all += page.extract_text() or ""
                except Exception as e:
                    # fallback to raw bytes->text
                    text_all = pdf_bytes.decode("utf-8", errors="replace")
            else:
                # fallback: decode bytes to text (may be messy)
                text_all = pdf_bytes.decode("utf-8", errors="replace")

            # Heuristics: find patterns like "90001 CITYNAME" or "90001, CITYNAME" or "90001 CITY, ST"
            # We'll search for 5-digit zips in CA range and capture following words as city.
            pattern = re.compile(r"\b(9[0-6]\d{3})\b[,\s\-–:]*([A-Z][A-Za-z' .\-&]+(?:\s[A-Z][A-Za-z' .\-&]+){0,3})", re.MULTILINE)
            found = pattern.findall(text_all)
            # If not many matches, try a looser pattern: zip then anything up to newline
            if len(found) < 10:
                loose = re.compile(r"\b(9[0-6]\d{3})\b[^\n\r]{0,80}", re.MULTILINE)
                loose_found = loose.findall(text_all)
                # attempt to extract city from the same line by splitting
                lines = text_all.splitlines()
                for ln in lines:
                    m = re.search(r"\b(9[0-6]\d{3})\b", ln)
                    if m:
                        z = m.group(1)
                        # try to get city after zip
                        after = ln[m.end():].strip(" ,:-")
                        city_guess = after.split(",")[0].strip()
                        if city_guess:
                            new_db[z] = {"city": city_guess, "state": "CA", "office": ""}
                # also add loose_found zips if not present
                for z in loose_found:
                    if z not in new_db:
                        new_db[z] = {"city": "", "state": "CA", "office": ""}
            else:
                # process found tuples
                for z, city in found:
                    city_clean = city.strip().title()
                    new_db[z] = {"city": city_clean, "state": "CA", "office": ""}

            imported += len(new_db)
            st.success(f"Extraction PDF : {len(new_db)} entrées détectées (heuristique).")
        except Exception as e:
            errors.append(f"Erreur extraction PDF: {e}")

    # 3) Merge into ZIP_DB if any new entries
    if new_db:
        # Merge: prefer existing ZIP_DB values if present, else new
        for z, info in new_db.items():
            if z in ZIP_DB:
                # update missing fields only
                for k in ("city", "state", "office"):
                    if not ZIP_DB[z].get(k) and info.get(k):
                        ZIP_DB[z][k] = info.get(k)
            else:
                ZIP_DB[z] = info
        # rebuild indices
        CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_DB)
        st.success(f"Base ZIP_DB mise à jour : total entrées = {len(ZIP_DB)}")
    else:
        st.info("Aucune nouvelle entrée détectée dans les fichiers fournis.")

    if errors:
        for e in errors:
            st.error(e)

# -------------------------
# After import: show counts and allow manual CSV export of current ZIP_DB
st.markdown("### État de la base ZIP")
st.write(f"Nombre d'entrées dans ZIP_DB : **{len(ZIP_DB)}**")
if st.button("Télécharger ZIP_DB actuel (CSV)"):
    # prepare CSV bytes
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["zipcode", "city", "state", "office"])
    for z, info in sorted(ZIP_DB.items()):
        writer.writerow([z, info.get("city", ""), info.get("state", ""), info.get("office", "")])
    st.download_button("Télécharger CSV", data=out.getvalue().encode("utf-8"), file_name="zip_db_export.csv", mime="text/csv")

# -------------------------
# Build selectbox options from ZIP_DB
zip_options = sorted(ZIP_DB.keys())
city_options = sorted({info.get("city") for info in ZIP_DB.values() if info.get("city")})
office_options = sorted({info.get("office") for info in ZIP_DB.values() if info.get("office")})

# Ensure session_state keys exist
if "zip_select" not in st.session_state:
    st.session_state["zip_select"] = zip_options[0] if zip_options else "90001"
if "city_select" not in st.session_state:
    st.session_state["city_select"] = (ZIP_DB.get(st.session_state["zip_select"], {}).get("city") or "")
if "office_select" not in st.session_state:
    st.session_state["office_select"] = (ZIP_DB.get(st.session_state["zip_select"], {}).get("office") or "")

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
        # accept numeric zip in CA range but clear city/office
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

# -------------------------
# FORMULAIRE principal (utilisateur)
st.markdown("---")
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom de famille", "HARMS", key="ln_input")
fn = st.text_input("Prénom", "ROSA", key="fn_input")
address1 = st.text_input("Adresse (ligne 1)", "2570 24TH STREET", key="address1_input")
address2 = st.text_input("Adresse (ligne 2)", "", key="address2_input")

# Selectboxes synchronisés (searchable)
col_zip, col_city = st.columns([2,3])
with col_zip:
    zip_select = st.selectbox("Code postal", options=zip_options, index=zip_options.index(st.session_state.get("zip_select")) if st.session_state.get("zip_select") in zip_options else 0, key="zip_select", on_change=update_from_zip)
with col_city:
    city_select = st.selectbox("Ville", options=city_options, index=city_options.index(st.session_state.get("city_select")) if st.session_state.get("city_select") in city_options else 0, key="city_select", on_change=update_from_city)

office_all = sorted(set(office_options))
office_select = st.selectbox("Field Office", options=office_all, index=office_all.index(st.session_state.get("office_select")) if st.session_state.get("office_select") in office_all else 0, key="office_select", on_change=update_from_office)

state = st.text_input("État (abbrev.)", st.session_state.get("state_input", "CA"), key="state_input")
sex = st.selectbox("Sexe", ["M", "F"], index=0, key="sex_input")
dob = st.date_input("Date de naissance", datetime.date(1990, 1, 1), key="dob_input")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds", 0, 8, 5, key="h1_input")
    w = st.number_input("Poids (lb)", 30, 500, 160, key="w_input")
with col2:
    h2 = st.number_input("Pouces", 0, 11, 10, key="h2_input")
    eyes = st.text_input("Yeux", "BRN", key="eyes_input")
hair = st.text_input("Cheveux", "BRN", key="hair_input")
cls = st.text_input("Classe", "C", key="cls_input")
rstr = st.text_input("Restrictions", "NONE", key="rstr_input")
endorse = st.text_input("Endorsements", "NONE", key="endorse_input")
iss = st.date_input("Date d'émission", datetime.date.today(), key="iss_input")

generate = st.button("Générer la carte")

# Debug panel
st.markdown("### Debug (aperçu de la base et session_state)")
st.write(f"Entrées ZIP_DB : {len(ZIP_DB)}")
if st.checkbox("Afficher ZIP_DB (quelques entrées)"):
    sample = dict(list(ZIP_DB.items())[:50])
    st.json(sample)
st.code({k: st.session_state.get(k) for k in sorted(st.session_state.keys())}, language="json")

# -------------------------
# VALIDATIONS et génération (identique à précédentes versions)
def validate_inputs() -> List[str]:
    errors: List[str] = []
    if not ln.strip():
        errors.append("Nom de famille requis.")
    if not fn.strip():
        errors.append("Prénom requis.")
    if dob > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if iss > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if w < 30 or w > 500:
        errors.append("Poids hors plage attendue.")
    if h1 < 0 or h1 > 8 or h2 < 0 or h2 > 11:
        errors.append("Taille hors plage attendue.")
    if not address1.strip():
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
    for tag in ("DCS", "DAC", "DBB", "DBA", "DBD", "DAQ", "DAG", "DAH", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"):
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return "\u001e\r".join(parts) + "\r"

# PDF417 generation helper (if available)
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

def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def create_pdf_bytes(fields: Dict[str, str], photo_bytes: bytes = None) -> bytes:
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

# -------------------------
# Final generation
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
        st.stop()

    ln_val = ln
    fn_val = fn
    address1_val = address1
    address2_val = address2
    city_val = st.session_state["city_select"]
    state_val = st.session_state["state_input"]
    postal_val = st.session_state["zip_select"]

    r = random.Random(seed(ln_val, fn_val, st.session_state["dob_input"]))
    dl = rletter(r, ln_val[0] if ln_val else "") + rdigits(r, 7)

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
    height_str = f"{int(st.session_state.get('h1_input', 0))}'{int(st.session_state.get('h2_input', 0))}\""

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
        "DAK": re.sub(r"\D", "", postal_val)[:10],
        "DCF": dd,
        "DAU": f"{int(st.session_state.get('h1_input', 0))}{int(st.session_state.get('h2_input', 0))}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
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
        if photo_bytes[:3] == b'\xff\xd8\xff':
            mime = "image/jpeg"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    # Card HTML
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
        "<div class='label'>ISS</div><div class='value'>" + st.session_state['iss_input'].strftime("%m/%d/%Y") + "</div>"
        "<div class='label'>EXP</div><div class='value'>" + exp.strftime("%m/%d/%Y") + "</div>"
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
        parsed = parse_payload(aamva)
        st.json(parsed)

    # PDF417 display if available
    if _PDF417_AVAILABLE:
        try:
            svg_str = generate_pdf417_svg(data_bytes, columns=6, security_level=2, scale=3, ratio=3, color="#000000")
            svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
            components.html(svg_html, height=220, scrolling=True)
        except Exception as e:
            st.error("Erreur génération PDF417 : " + str(e))
    else:
        st.info("pdf417gen non disponible. Le PDF417 ne sera pas affiché.")

    # Download PDF
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
