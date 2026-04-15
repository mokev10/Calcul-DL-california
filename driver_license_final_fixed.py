#!/usr/bin/env python3
# driver_license_modern.py
# Interface moderne complète — prêt à copier
# - Field office découplé du ZIP/ville
# - Aperçu carte stylée (HTML/CSS)
# - Sidebar pour options PDF417 / AAMVA
# - Chargement paresseux ZIP DB (local JSON ou GitHub)
# - Export PDF minimal si reportlab présent
# - Ne simplifie pas la logique : fichier complet

import base64
import datetime
import hashlib
import io
import json
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

st.set_page_config(page_title="Générateur officiel de permis Californien", layout="wide")

IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"
LOCAL_ZIPDB_JSON = "zip_db.json"

# -------------------------
# Utilitaires et ZIP DB
# -------------------------
def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[|,\t;]+", line)
        if len(parts) >= 2:
            zip_code = parts[0].strip()
            city = parts[1].strip() if len(parts) > 1 else ""
            state = parts[2].strip() if len(parts) > 2 else "CA"
            office = parts[3].strip() if len(parts) > 3 else ""
            if re.fullmatch(r"\d{5}", zip_code):
                out[zip_code] = {"city": city, "state": state, "office": office}
    return out

def load_zip_db() -> Dict[str, Dict[str, str]]:
    # Tentative chargement local JSON
    try:
        with open(LOCAL_ZIPDB_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    # Tentative fetch distant
    try:
        resp = requests.get(GITHUB_RAW_ZIPDB, timeout=6)
        if resp.status_code == 200:
            parsed = parse_zipdb_text(resp.text)
            if parsed:
                return parsed
    except Exception:
        pass
    # Fallback minimal
    return {
        "94102": {"city": "San Francisco", "state": "CA", "office": ""},
        "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
        "92101": {"city": "San Diego", "state": "CA", "office": ""},
    }

_ZIP_DB_CACHE: Optional[Dict[str, Dict[str, str]]] = None
def get_zip_db() -> Dict[str, Dict[str, str]]:
    global _ZIP_DB_CACHE
    if _ZIP_DB_CACHE is None:
        _ZIP_DB_CACHE = load_zip_db()
    return _ZIP_DB_CACHE

def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())

def format_date(dt: datetime.date) -> str:
    return dt.strftime("%Y-%m-%d")

def generate_random_id() -> str:
    return hashlib.sha1(str(random.random()).encode()).hexdigest()[:10]

# Neutralisation de toute inférence automatique de field_office
def infer_field_office(zip_code: str, city: str) -> str:
    return ""

def build_payload(data: Dict[str, str]) -> Dict[str, str]:
    payload: Dict[str, str] = {}
    payload["first_name"] = data.get("first_name", "")
    payload["last_name"] = data.get("last_name", "")
    payload["middle_name"] = data.get("middle_name", "")
    payload["sex"] = data.get("sex", "")
    payload["dob"] = data.get("dob", "")
    payload["address"] = data.get("address", "")
    payload["city"] = data.get("city", "")
    payload["state"] = data.get("state", "")
    payload["zip"] = data.get("zip", "")
    payload["field_office"] = data.get("field_office", "") or ""
    payload["license_number"] = data.get("license_number", generate_random_id())
    payload["issue_date"] = data.get("issue_date", format_date(datetime.date.today()))
    payload["expiry_date"] = data.get("expiry_date", format_date(datetime.date.today() + datetime.timedelta(days=365*5)))
    payload["height"] = data.get("height", "")
    payload["weight"] = data.get("weight", "")
    payload["eye_color"] = data.get("eye_color", "")
    payload["hair_color"] = data.get("hair_color", "")
    payload["restrictions"] = data.get("restrictions", "")
    payload["endorsements"] = data.get("endorsements", "")
    payload["class"] = data.get("class", "")
    return payload

# -------------------------
# PDF / PDF417 helpers
# -------------------------
def generate_pdf_preview(payload: Dict[str, str], photo_bytes: Optional[bytes] = None) -> bytes:
    buffer = io.BytesIO()
    if not _REPORTLAB_AVAILABLE:
        # Fallback PDF minimal
        buffer.write(b"%PDF-1.4\n% fallback\n")
        buffer.write(b"1 0 obj << /Type /Catalog >> endobj\ntrailer << >>\n%%EOF")
        return buffer.getvalue()

    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Permis CALIFORNIA - Aperçu")
    c.setFont("Helvetica", 10)
    y = height - 100
    for k, v in payload.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72
    if photo_bytes:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 160, height - 200, width=100, height=120)
        except Exception:
            pass
    c.showPage()
    c.save()
    return buffer.getvalue()

def generate_pdf417_svg(payload_text: str) -> Optional[str]:
    if not _PDF417_AVAILABLE:
        return None
    try:
        codes = encode(payload_text, columns=6, security_level=2)
        svg = render_svg(codes, scale=3)
        return svg
    except Exception:
        return None

# -------------------------
# Validation
# -------------------------
def validate_inputs(first_name: str, last_name: str, dob: str, zip_code: str) -> List[str]:
    errors: List[str] = []
    if not first_name.strip():
        errors.append("Le prénom est requis.")
    if not last_name.strip():
        errors.append("Le nom est requis.")
    try:
        datetime.datetime.strptime(dob, "%Y-%m-%d")
    except Exception:
        errors.append("Date de naissance invalide. Format attendu YYYY-MM-DD.")
    if zip_code and not re.fullmatch(r"\d{5}", zip_code.strip()):
        errors.append("ZIP invalide. Utilisez 5 chiffres.")
    return errors

# -------------------------
# UI : CSS moderne + composants
# -------------------------
MODERN_CSS = """
<style>
:root{
  --bg:#0f1724;
  --card:#0b1220;
  --accent:#0ea5a4;
  --muted:#94a3b8;
  --glass: rgba(255,255,255,0.03);
  --card-radius:14px;
}
body { background: linear-gradient(180deg,#071029 0%, #0b1220 100%); color: #e6eef8; }
.stApp { background: transparent; }
.header {
  display:flex; align-items:center; gap:16px; margin-bottom:18px;
}
.logo {
  width:56px; height:56px; border-radius:12px; background:linear-gradient(135deg,#06b6d4,#7c3aed); display:flex; align-items:center; justify-content:center; font-weight:700; color:white;
  box-shadow: 0 6px 18px rgba(12, 74, 110, 0.35);
}
.title { font-size:20px; font-weight:700; margin:0; }
.subtitle { color:var(--muted); font-size:13px; margin-top:2px; }

.card {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius: var(--card-radius);
  padding:18px;
  box-shadow: 0 8px 30px rgba(2,6,23,0.6);
  border: 1px solid rgba(255,255,255,0.03);
}

.form-grid { display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
.field { margin-bottom:10px; }
.small-muted { color:var(--muted); font-size:12px; }

.preview-card {
  width:100%; max-width:420px; border-radius:12px; padding:16px; background: linear-gradient(180deg,#0b2a4a,#042033);
  color:#fff; box-shadow: 0 10px 30px rgba(2,6,23,0.6);
  border: 1px solid rgba(255,255,255,0.04);
}
.license-title { font-weight:800; font-size:14px; color:#cfefff; letter-spacing:1px; }
.license-number { font-weight:700; font-size:18px; color:var(--accent); margin-top:8px; }
.license-row { display:flex; justify-content:space-between; margin-top:8px; font-size:13px; color:#dbeafe; }
.badge { background: rgba(255,255,255,0.04); padding:6px 8px; border-radius:8px; font-size:12px; color:var(--muted); }
.btn-primary {
  background: linear-gradient(90deg,#06b6d4,#7c3aed); color:white; padding:10px 14px; border-radius:10px; border:none; font-weight:700;
}
.small-btn { background: rgba(255,255,255,0.03); color:#dbeafe; padding:8px 10px; border-radius:8px; border:none; }
.footer-note { color:var(--muted); font-size:12px; margin-top:10px; }
</style>
"""

def render_preview_card(payload: Dict[str, str], photo_b64: Optional[str] = None) -> str:
    # Génère HTML de la carte d'aperçu (responsive)
    name = f"{payload.get('last_name','').upper()} {payload.get('first_name','').upper()}"
    lic = payload.get("license_number", "")
    addr = payload.get("address", "")
    city = payload.get("city", "")
    zipc = payload.get("zip", "")
    field_office = payload.get("field_office", "")
    issue = payload.get("issue_date", "")
    expiry = payload.get("expiry_date", "")
    class_ = payload.get("class", "")
    restrictions = payload.get("restrictions", "")
    endorsements = payload.get("endorsements", "")

    photo_html = ""
    if photo_b64:
        photo_html = f'<img src="data:image/png;base64,{photo_b64}" style="width:96px;height:96px;border-radius:8px;object-fit:cover;border:2px solid rgba(255,255,255,0.06)"/>'
    else:
        photo_html = '<div style="width:96px;height:96px;border-radius:8px;background:linear-gradient(135deg,#0ea5a4,#7c3aed);display:flex;align-items:center;justify-content:center;font-weight:700;color:white">IMG</div>'

    html = f"""
    <div class="preview-card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div class="license-title">CALIFORNIA USA DRIVER LICENSE</div>
          <div class="license-number">{lic}</div>
        </div>
        <div style="text-align:right">{photo_html}</div>
      </div>
      <div style="margin-top:12px;font-weight:700;font-size:14px">{name}</div>
      <div style="margin-top:8px;color:#cfefff">{addr}</div>
      <div class="license-row">
        <div>{city} / {zipc}</div>
        <div class="badge">{class_ or 'Class C'}</div>
      </div>
      <div class="license-row">
        <div>FIELD OFFICE</div>
        <div style="max-width:180px;text-align:right;color:#dbeafe">{field_office or '—'}</div>
      </div>
      <div class="license-row" style="margin-top:10px">
        <div>ISSUE: {issue}</div>
        <div>EXP: {expiry}</div>
      </div>
      <div class="footer-note">Restrictions: {restrictions or 'NONE'} · Endorsements: {endorsements or 'NONE'}</div>
    </div>
    """
    return html

# -------------------------
# Main UI
# -------------------------
def main():
    st.markdown(MODERN_CSS, unsafe_allow_html=True)
    # Header
    st.markdown("""
    <div class="header">
      <div class="logo">DL</div>
      <div>
        <div class="title">Générateur officiel de permis Californien</div>
        <div class="subtitle">Interface moderne — Field office non inféré, saisie manuelle requise</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar options
    st.sidebar.markdown("## Options")
    show_pdf417 = st.sidebar.checkbox("Afficher les options PDF417 (optionnel)", value=True)
    pdf417_ecc = st.sidebar.selectbox("Niveau ECC", options=[0,1,2,3,4], index=2)
    pdf417_scale = st.sidebar.slider("Échelle PDF417", min_value=1, max_value=6, value=3)
    enable_aamva = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Aide**")
    st.sidebar.markdown("Le champ Field office n'est pas inféré depuis le ZIP/ville. Saisissez-le manuellement.")

    zip_db = get_zip_db()

    # Form layout
    with st.form("dl_form", clear_on_submit=False):
        left, right = st.columns([2,1])
        with left:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0'>Informations personnelles</h4>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                last_name = st.text_input("Nom de famille", value="")
                first_name = st.text_input("Prénom", value="")
                middle_name = st.text_input("Deuxième prénom", value="")
                sex = st.selectbox("Sexe", options=["", "M", "F", "X"])
                dob = st.text_input("Date de naissance (YYYY-MM-DD)", value="")
            with col2:
                class_ = st.text_input("Classe", value="C")
                restrictions = st.text_input("Restrictions", value="NONE")
                endorsements = st.text_input("Endorsements", value="NONE")
                issue_date = st.text_input("Date d'émission (YYYY-MM-DD)", value=format_date(datetime.date.today()))
                expiry_date = st.text_input("Date d'expiration (YYYY-MM-DD)", value=format_date(datetime.date.today() + datetime.timedelta(days=365*5)))
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="card" style="margin-top:12px">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0'>Adresse</h4>", unsafe_allow_html=True)
            address = st.text_input("Address Line", value="")
            zip_code = st.text_input("Code postal", value="", max_chars=10)
            detected_city = ""
            detected_state = ""
            if zip_code and zip_code.strip() in zip_db:
                detected_city = zip_db[zip_code.strip()].get("city", "")
                detected_state = zip_db[zip_code.strip()].get("state", "")
                st.markdown(f"<div class='small-muted'>Ville détectée: <strong>{detected_city}</strong> · État: <strong>{detected_state}</strong></div>", unsafe_allow_html=True)
            city = st.text_input("Ville (si ZIP inconnu ou correction)", value=detected_city)
            state = st.text_input("État", value=detected_state or "CA")
            # Field office indépendant
            field_office = st.text_input("Field Office (saisissez manuellement)", value="")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="card" style="margin-top:12px">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0'>Physique / Identifiants</h4>", unsafe_allow_html=True)
            height = st.text_input("Taille (ex: 180 cm)", value="")
            weight = st.text_input("Poids (ex: 75 kg)", value="")
            eye_color = st.text_input("Couleur des yeux", value="")
            hair_color = st.text_input("Couleur des cheveux", value="")
            license_number = st.text_input("Numéro de permis (laisser vide pour générer)", value="")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="card" style="margin-top:12px">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0'>Photo</h4>", unsafe_allow_html=True)
            photo_source = st.radio("Source photo", options=["URL", "Upload", "Aucune"], index=0)
            photo_bytes: Optional[bytes] = None
            if photo_source == "URL":
                photo_url = st.text_input("URL de la photo", value=IMAGE_M_URL)
                if photo_url:
                    try:
                        r = requests.get(photo_url, timeout=6)
                        if r.status_code == 200:
                            photo_bytes = r.content
                    except Exception:
                        photo_bytes = None
            elif photo_source == "Upload":
                uploaded = st.file_uploader("Téléversez une photo", type=["png", "jpg", "jpeg"])
                if uploaded:
                    try:
                        photo_bytes = uploaded.read()
                    except Exception:
                        photo_bytes = None
            st.markdown("</div>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Générer la carte", help="Génère l'aperçu et les fichiers téléchargeables")
        with right:
            # Aperçu carte
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0'>Aperçu</h4>", unsafe_allow_html=True)
            # Préparer payload minimal pour l'aperçu en temps réel
            preview_data = {
                "first_name": first_name or "",
                "last_name": last_name or "",
                "middle_name": middle_name or "",
                "sex": sex or "",
                "dob": dob or "",
                "address": address or "",
                "city": city or "",
                "state": state or "",
                "zip": zip_code or "",
                "field_office": field_office or "",
                "license_number": license_number.strip() or generate_random_id(),
                "issue_date": issue_date or format_date(datetime.date.today()),
                "expiry_date": expiry_date or format_date(datetime.date.today() + datetime.timedelta(days=365*5)),
                "height": height or "",
                "weight": weight or "",
                "eye_color": eye_color or "",
                "hair_color": hair_color or "",
                "restrictions": restrictions or "",
                "endorsements": endorsements or "",
                "class": class_ or "C",
            }
            photo_b64 = None
            if photo_bytes:
                try:
                    photo_b64 = base64.b64encode(photo_bytes).decode("utf-8")
                except Exception:
                    photo_b64 = None

            preview_html = render_preview_card(preview_data, photo_b64)
            st.markdown(preview_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Actions rapides
            st.markdown('<div style="margin-top:12px">', unsafe_allow_html=True)
            if st.button("Réinitialiser", key="reset_btn"):
                # Simple refresh: reload page
                st.experimental_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # Après soumission : validation et génération
    if submitted:
        errors = validate_inputs(first_name, last_name, dob, zip_code)
        if errors:
            for e in errors:
                st.error(e)
            st.stop()

        data = {
            "first_name": normalize_name(first_name),
            "middle_name": normalize_name(middle_name),
            "last_name": normalize_name(last_name),
            "sex": sex,
            "dob": dob,
            "address": normalize_name(address),
            "city": normalize_name(city),
            "state": normalize_name(state),
            "zip": zip_code.strip(),
            "field_office": normalize_name(field_office),
            "height": height,
            "weight": weight,
            "eye_color": eye_color,
            "hair_color": hair_color,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "class": class_,
            "license_number": license_number.strip() or generate_random_id(),
            "issue_date": issue_date or format_date(datetime.date.today()),
            "expiry_date": expiry_date or format_date(datetime.date.today() + datetime.timedelta(days=365*5)),
        }

        payload = build_payload(data)

        # Optionnel : validation AAMVA
        if enable_aamva and _AAMVA_UTILS_AVAILABLE:
            try:
                corrected = auto_correct_payload(payload)
                payload = corrected
                valid, issues = validate_aamva_payload(payload)
                if not valid:
                    st.warning("Le payload AAMVA contient des avertissements/erreurs :")
                    for it in issues:
                        st.write(f"- {it}")
            except Exception:
                pass

        st.success("Génération terminée — le champ Field office utilisé est celui saisi manuellement.")
        st.subheader("Payload AAMVA / Données")
        st.json(payload)

        # PDF
        pdf_bytes = generate_pdf_preview(payload, photo_bytes)
        if pdf_bytes:
            st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_preview.pdf", mime="application/pdf")

        # PDF417
        payload_text = GS.join([f"{k}={v}" for k, v in payload.items()])
        svg = generate_pdf417_svg(payload_text) if show_pdf417 else None
        if svg:
            components.html(svg, height=220)
            st.download_button("Télécharger PDF417 (SVG)", data=svg, file_name="barcode.svg", mime="image/svg+xml")
        else:
            if show_pdf417:
                st.info("Génération PDF417 non disponible (bibliothèque manquante).")

if __name__ == "__main__":
    main()
