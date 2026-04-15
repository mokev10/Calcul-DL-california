#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version modifiée : découplage complet field_office <-> ZIP/ville
# Fichier complet prêt à copier

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

st.set_page_config(page_title="Permis CALIFORNIA", layout="wide")

IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"
LOCAL_ZIPDB_JSON = "zip_db.json"

# --- Chargement paresseux de la base ZIP
def load_zip_db() -> Dict[str, Dict[str, str]]:
    """
    Charge la base ZIP depuis un fichier local JSON si présent,
    sinon tente de récupérer depuis GITHUB_RAW_ZIPDB (texte).
    Le format attendu local est un JSON mapping ZIP -> {"city": "...", "state": "...", "office": "..."}
    NOTE: field 'office' est conservée dans la DB pour compatibilité, mais
    elle NE SERA PAS utilisée pour préremplir le champ field_office dans l'UI.
    """
    # Tentative chargement local JSON
    try:
        with open(LOCAL_ZIPDB_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except FileNotFoundError:
        pass
    except Exception:
        # si erreur de parsing, on ignore et on tente le fetch distant
        pass

    # Tentative fetch distant (texte) et parsing simple
    try:
        resp = requests.get(GITHUB_RAW_ZIPDB, timeout=6)
        if resp.status_code == 200:
            text = resp.text
            parsed = parse_zipdb_text(text)
            if parsed:
                return parsed
    except Exception:
        pass

    # Fallback minimal si tout échoue : petite table d'exemple
    return {
        "94102": {"city": "San Francisco", "state": "CA", "office": ""},
        "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
        "92101": {"city": "San Diego", "state": "CA", "office": ""},
    }

def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    """
    Parse un texte brut de type ZIP_DB.txt en mapping ZIP -> {city, state, office}
    Format attendu par ligne : ZIP|City|State|Office  (ou similaire)
    Cette fonction est robuste aux lignes vides et commentaires.
    """
    out: Dict[str, Dict[str, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # On supporte plusieurs séparateurs possibles
        parts = re.split(r"[|,\t;]+", line)
        if len(parts) >= 2:
            zip_code = parts[0].strip()
            city = parts[1].strip() if len(parts) > 1 else ""
            state = parts[2].strip() if len(parts) > 2 else "CA"
            office = parts[3].strip() if len(parts) > 3 else ""
            if re.fullmatch(r"\d{5}", zip_code):
                out[zip_code] = {"city": city, "state": state, "office": office}
    return out

# Charge la DB une seule fois
_ZIP_DB_CACHE: Optional[Dict[str, Dict[str, str]]] = None
def get_zip_db() -> Dict[str, Dict[str, str]]:
    global _ZIP_DB_CACHE
    if _ZIP_DB_CACHE is None:
        _ZIP_DB_CACHE = load_zip_db()
    return _ZIP_DB_CACHE

# --- Fonctions utilitaires
def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())

def format_date(dt: datetime.date) -> str:
    return dt.strftime("%Y-%m-%d")

def generate_random_id() -> str:
    return hashlib.sha1(str(random.random()).encode()).hexdigest()[:10]

# --- NE PLUS INFÉRER field_office depuis ZIP/ville
# Toute logique d'inférence a été neutralisée : field_office doit être saisi par l'utilisateur.
def infer_field_office(zip_code: str, city: str) -> str:
    """
    Fonction neutralisée volontairement : ne plus inférer automatiquement le field office.
    Retourne une chaîne vide pour indiquer qu'aucune inférence automatique n'est effectuée.
    """
    return ""

# --- Construction du payload AAMVA (simplifiée mais complète)
def build_payload(data: Dict[str, str]) -> Dict[str, str]:
    """
    Construit le payload AAMVA (ou un dictionnaire équivalent) à partir des données utilisateur.
    IMPORTANT : on utilise la valeur 'field_office' fournie par l'utilisateur (même si vide).
    """
    payload: Dict[str, str] = {}
    # Champs de base
    payload["first_name"] = data.get("first_name", "")
    payload["last_name"] = data.get("last_name", "")
    payload["middle_name"] = data.get("middle_name", "")
    payload["sex"] = data.get("sex", "")
    payload["dob"] = data.get("dob", "")
    payload["address"] = data.get("address", "")
    payload["city"] = data.get("city", "")
    payload["state"] = data.get("state", "")
    payload["zip"] = data.get("zip", "")
    # Field office : valeur fournie par l'utilisateur, pas d'inférence
    payload["field_office"] = data.get("field_office", "") or ""
    # Autres champs simulés
    payload["license_number"] = data.get("license_number", generate_random_id())
    payload["issue_date"] = data.get("issue_date", format_date(datetime.date.today()))
    payload["expiry_date"] = data.get("expiry_date", format_date(datetime.date.today() + datetime.timedelta(days=365*5)))
    payload["height"] = data.get("height", "")
    payload["weight"] = data.get("weight", "")
    payload["eye_color"] = data.get("eye_color", "")
    payload["hair_color"] = data.get("hair_color", "")
    return payload

# --- Génération PDF simple (si reportlab disponible)
def generate_pdf_preview(payload: Dict[str, str], photo_bytes: Optional[bytes] = None) -> bytes:
    """
    Génère un PDF minimaliste contenant les informations du payload et la photo si fournie.
    Retourne les octets du PDF.
    """
    buffer = io.BytesIO()
    if not _REPORTLAB_AVAILABLE:
        # Retourner un PDF texte basique sans reportlab
        buffer.write(b"%PDF-1.4\n% Simple fallback PDF\n")
        buffer.write(f"1 0 obj << /Type /Catalog >> endobj\n".encode("utf-8"))
        buffer.write(b"trailer << >>\n%%EOF")
        return buffer.getvalue()

    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    # Titre
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Permis CALIFORNIA - Aperçu")
    # Texte payload
    c.setFont("Helvetica", 10)
    y = height - 100
    for k, v in payload.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72
    # Photo si fournie
    if photo_bytes:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 160, height - 200, width=100, height=120)
        except Exception:
            # ignore image errors
            pass
    c.showPage()
    c.save()
    return buffer.getvalue()

# --- Génération PDF417 (optionnel)
def generate_pdf417_svg(payload_text: str) -> Optional[str]:
    if not _PDF417_AVAILABLE:
        return None
    try:
        codes = encode(payload_text, columns=6, security_level=2)
        svg = render_svg(codes, scale=3)
        return svg
    except Exception:
        return None

# --- Validation d'entrée
def validate_inputs(first_name: str, last_name: str, dob: str, zip_code: str) -> List[str]:
    errors: List[str] = []
    if not first_name.strip():
        errors.append("Le prénom est requis.")
    if not last_name.strip():
        errors.append("Le nom est requis.")
    # DOB format YYYY-MM-DD
    try:
        datetime.datetime.strptime(dob, "%Y-%m-%d")
    except Exception:
        errors.append("Date de naissance invalide. Format attendu YYYY-MM-DD.")
    if zip_code and not re.fullmatch(r"\d{5}", zip_code.strip()):
        errors.append("ZIP invalide. Utilisez 5 chiffres.")
    return errors

# --- UI Streamlit complète
def main():
    st.title("Générateur officiel de permis Californien")
    st.markdown("**Note** : le champ Field office n'est plus inféré depuis le ZIP/ville. Saisissez-le manuellement si nécessaire.")

    # Chargement DB ZIP (paresseux)
    zip_db = get_zip_db()

    # Formulaire utilisateur
    with st.form("dl_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Prénom", value="")
            middle_name = st.text_input("Deuxième prénom", value="")
            last_name = st.text_input("Nom de famille", value="")
            sex = st.selectbox("Sexe", options=["", "M", "F", "X"])
            dob = st.text_input("Date de naissance (YYYY-MM-DD)", value="")
            license_number = st.text_input("Numéro de permis (laisser vide pour générer)", value="")
        with col2:
            address = st.text_input("Adresse", value="")
            zip_code = st.text_input("Code postal (ZIP)", value="", max_chars=10)
            # Affichage de la ville détectée si présente dans la DB
            detected_city = ""
            detected_state = ""
            if zip_code and zip_code.strip() in zip_db:
                detected_city = zip_db[zip_code.strip()].get("city", "")
                detected_state = zip_db[zip_code.strip()].get("state", "")
                st.write(f"**Ville détectée**: {detected_city}  **État**: {detected_state}")
            # Permettre saisie manuelle de la ville si besoin
            city = st.text_input("Ville (si ZIP inconnu ou pour correction)", value=detected_city)
            state = st.text_input("État", value=detected_state or "CA")
            # Field office totalement indépendant
            field_office = st.text_input("Field office (saisissez manuellement) — ne sera pas inféré", value="")
            height = st.text_input("Taille (ex: 180 cm)", value="")
            weight = st.text_input("Poids (ex: 75 kg)", value="")
            eye_color = st.text_input("Couleur des yeux", value="")
            hair_color = st.text_input("Couleur des cheveux", value="")

        # Photo par URL ou upload
        photo_source = st.radio("Photo source", options=["URL", "Upload", "Aucune"], index=0)
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

        submitted = st.form_submit_button("Générer le permis")

    if submitted:
        # Validation
        errors = validate_inputs(first_name, last_name, dob, zip_code)
        if errors:
            for e in errors:
                st.error(e)
            return

        # Préparer données
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
            # Field office : valeur fournie par l'utilisateur, pas d'inférence
            "field_office": normalize_name(field_office),
            "height": height,
            "weight": weight,
            "eye_color": eye_color,
            "hair_color": hair_color,
            "license_number": license_number.strip() or generate_random_id(),
        }

        payload = build_payload(data)

        # Optionnel : validation AAMVA si disponible
        if _AAMVA_UTILS_AVAILABLE:
            try:
                # auto_correct_payload peut corriger certains formats
                corrected = auto_correct_payload(payload)
                payload = corrected
                valid, issues = validate_aamva_payload(payload)
                if not valid:
                    st.warning("Le payload AAMVA contient des avertissements/erreurs :")
                    for it in issues:
                        st.write(f"- {it}")
            except Exception:
                # ne pas bloquer si aamva_utils échoue
                pass

        # Affichage aperçu
        st.subheader("Aperçu des données")
        st.json(payload)

        # Génération PDF
        pdf_bytes = generate_pdf_preview(payload, photo_bytes)
        if pdf_bytes:
            st.download_button("Télécharger le PDF", data=pdf_bytes, file_name="permis_preview.pdf", mime="application/pdf")

        # Génération PDF417 (texte du payload)
        payload_text = GS.join([f"{k}={v}" for k, v in payload.items()])
        svg = generate_pdf417_svg(payload_text)
        if svg:
            components.html(svg, height=200)
            st.download_button("Télécharger le PDF417 SVG", data=svg, file_name="barcode.svg", mime="image/svg+xml")
        else:
            st.info("Génération PDF417 non disponible (bibliothèque manquante).")

        st.success("Génération terminée. Le champ Field office utilisé est celui saisi manuellement.")

if __name__ == "__main__":
    main()
