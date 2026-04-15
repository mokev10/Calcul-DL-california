#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version modifiée : Field Office en un seul menu déroulant indépendant du ZIP/ville
# Copiez-collez ce fichier en remplacement complet.

import base64
import datetime
import hashlib
import io
import random
import re
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components

# ReportLab (PDF) - optional
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

# AAMVA utils (validation + builder continu) - optional
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

# ---------------------------
# ZIP database (extrait)
# ---------------------------
# Note: 'office' field intentionally laissé vide pour éviter tout rattachement automatique.
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "92101": {"city": "San Diego", "state": "CA", "office": ""},
    # ... (conserver le reste de vos entrées ZIP_DB ici)
}

# ---------------------------
# Field offices (structure indépendante)
# ---------------------------
FIELD_OFFICES: Dict[str, Dict[str, int]] = {
    "Baie de San Francisco": {
        "Corte Madera": 525,
        "Daly City": 599,
        "El Cerrito": 585,
        "Fremont": 643,
        "Hayward": 521,
        "Los Gatos": 641,
        "Novato": 647,
        "Oakland (Claremont)": 501,
        "Oakland (Coliseum)": 604,
        "Pittsburg": 651,
        "Pleasanton": 639,
        "Redwood City": 542,
        "San Francisco": 503,
        "San Jose (Alma)": 516,
        "San Jose (Driver License Center)": 607,
        "San Mateo": 594,
        "Santa Clara": 632,
        "Vallejo": 538,
    },
    "Grand Los Angeles": {
        "Arleta": 628,
        "Bellflower": 610,
        "Culver City": 514,
        "Glendale": 540,
        "Hollywood": 633,
        "Inglewood": 544,
        "Long Beach": 507,
        "Los Angeles (Hope St)": 502,
        "Montebello": 531,
        "Pasadena": 510,
        "Santa Monica": 548,
        "Torrance": 592,
        "West Covina": 591,
    },
    "Orange County / Sud": {
        "Costa Mesa": 627,
        "Fullerton": 547,
        "Laguna Hills": 642,
        "Santa Ana": 529,
        "San Clemente": 652,
        "Westminster": 623,
        "Chula Vista": 609,
        "El Cajon": 549,
        "Oceanside": 593,
        "San Diego (Clairemont)": 618,
        "San Diego (Normal St)": 504,
        "San Marcos": 637,
        "San Ysidro": 649,
        "Auburn": 533,
        "Chico": 534,
        "Eureka": 522,
        "Redding": 550,
        "Roseville": 635,
        "Sacramento (Broadway)": 500,
        "Sacramento (South)": 603,
        "Woodland": 535,
    },
    "Vallée Centrale": {
        "Bakersfield": 511,
        "Fresno": 505,
        "Lodi": 595,
        "Modesto": 536,
        "Stockton": 517,
        "Visalia": 519,
    },
}

# Flatten field offices into une seule liste pour le menu déroulant
def build_field_office_options(field_offices: Dict[str, Dict[str, int]]) -> List[Tuple[str, int]]:
    """
    Retourne une liste de tuples (label, id) où label = "Région — Ville (ID)".
    """
    options: List[Tuple[str, int]] = []
    for region, cities in field_offices.items():
        for city, fid in cities.items():
            label = f"{region} — {city} ({fid})"
            options.append((label, fid))
    # Tri alphabétique par label pour une UX cohérente
    options.sort(key=lambda x: x[0].lower())
    return options

FIELD_OFFICE_OPTIONS = build_field_office_options(FIELD_OFFICES)

# ---------------------------
# Helpers
# ---------------------------
def generate_license_number() -> str:
    """Génère un numéro de permis aléatoire (format simple)."""
    return "H" + "".join(str(random.randint(0, 9)) for _ in range(8))

def format_date(d: datetime.date) -> str:
    return d.strftime("%Y/%m/%d")

# ---------------------------
# Streamlit UI
# ---------------------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg,#f7fbff 0%, #eef6ff 100%); }
    .card { background: white; padding: 18px; border-radius: 12px; box-shadow: 0 6px 18px rgba(15,23,42,0.08); }
    .small { font-size: 0.9rem; color: #6b7280; }
    .title { font-weight:700; font-size:1.6rem; color:#0f172a; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Générateur officiel de permis Californien")
st.write("Interface académique — champs indépendants : ZIP, Ville et Field Office (menu unique).")

# Layout en colonnes
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Saisie utilisateur</div>', unsafe_allow_html=True)

    last_name = st.text_input("Nom de famille", value="HARRIS")
    first_name = st.text_input("Prénom", value="ROSA")
    sex = st.selectbox("Sexe", options=["M", "F", "X"], index=0)
    dob = st.date_input("Date de naissance", value=datetime.date(1990, 1, 3))

    st.markdown("---")
    st.subheader("Caractéristiques physiques")
    height_ft = st.number_input("Pieds", min_value=0, max_value=8, value=5)
    height_in = st.number_input("Pouces", min_value=0, max_value=11, value=10)
    weight_lb = st.number_input("Poids (lb)", min_value=0, max_value=1000, value=160)
    hair = st.text_input("Cheveux", value="BRN")
    eyes = st.text_input("Yeux", value="BRN")

    st.markdown("---")
    st.subheader("Adresse (menus déroulants)")
    # ZIP menu déroulant
    zip_options = sorted(ZIP_DB.keys())
    selected_zip = st.selectbox("Code postal", options=[""] + zip_options, index=zip_options.index("90001") + 1 if "90001" in zip_options else 0)

    # Ville menu déroulant (basé sur la liste ZIP_DB unique cities)
    # Construire liste unique de villes à partir de ZIP_DB
    unique_cities = sorted({v["city"] for v in ZIP_DB.values()})
    selected_city = st.selectbox("Ville", options=[""] + unique_cities, index=unique_cities.index("Los Angeles") + 1 if "Los Angeles" in unique_cities else 0)

    address_line = st.text_input("Address Line", value="2570 24TH STREET")

    st.markdown("---")
    st.subheader("Permis et dates")
    license_number = st.text_input("Numéro de permis", value=generate_license_number())
    issue_date = st.date_input("Date d’émission", value=datetime.date.today())
    # expiration par défaut 5 ans après issue
    expiration_date = st.date_input("Date d'expiration", value=issue_date + datetime.timedelta(days=5*365))

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Paramètres Field Office</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Sélectionnez le Field Office (menu unique, indépendant du ZIP/ville)</div>', unsafe_allow_html=True)

    # Menu déroulant unique pour Field Office (label, id)
    fo_labels = [label for label, _ in FIELD_OFFICE_OPTIONS]
    fo_ids = [fid for _, fid in FIELD_OFFICE_OPTIONS]

    # Pré-sélection : si vous voulez une valeur par défaut, vous pouvez la définir ici
    default_index = 0
    selected_fo_label = st.selectbox("Field Office (Région — Ville (ID))", options=[""] + fo_labels, index=default_index + 1)

    # Récupérer l'ID correspondant si sélection faite
    selected_fo_id: Optional[int] = None
    if selected_fo_label:
        # trouver id
        for label, fid in FIELD_OFFICE_OPTIONS:
            if label == selected_fo_label:
                selected_fo_id = fid
                break

    st.markdown("---")
    st.subheader("Options PDF417 / AAMVA")
    pdf417_enable = st.checkbox("Affiche les codes-barres (PDF417)", value=False)
    aamva_validate = st.checkbox("Activer la validation AAMVA (optionnel)", value=False)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Génération / Preview
# ---------------------------
st.markdown("---")
preview_col, action_col = st.columns([3, 1])

with preview_col:
    st.subheader("Aperçu de la carte")
    card_html = f"""
    <div style="background:linear-gradient(90deg,#0ea5e9,#0369a1);color:white;padding:18px;border-radius:12px;width:520px;">
      <div style="font-weight:700;font-size:18px;">CALIFORNIA USA DRIVER LICENSE</div>
      <div style="margin-top:12px;">
        <div><strong>Numéro:</strong> {license_number}</div>
        <div><strong>Nom:</strong> {last_name} {first_name}</div>
        <div><strong>Sexe:</strong> {sex} &nbsp; <strong>Naissance:</strong> {format_date(dob)}</div>
        <div style="margin-top:8px;"><strong>Adresse:</strong> {address_line}</div>
        <div><strong>Ville / ZIP:</strong> {selected_city or '—'} / {selected_zip or '—'}</div>
        <div><strong>Field Office:</strong> {selected_fo_label or '—'}</div>
        <div style="margin-top:8px;"><strong>Émis:</strong> {format_date(issue_date)} &nbsp; <strong>Expire:</strong> {format_date(expiration_date)}</div>
      </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

with action_col:
    st.write("")
    st.write("")
    if st.button("Générer la carte"):
        st.success("Carte générée (aperçu ci‑dessus).")
        # Ici vous pouvez ajouter la logique de génération PDF / PDF417 si nécessaire.
        # Exemple : construire payload AAMVA, générer PDF, etc.
        if pdf417_enable and _PDF417_AVAILABLE:
            st.info("PDF417 activé — génération du code-barres (si la librairie est installée).")
        elif pdf417_enable:
            st.warning("pdf417gen non installé — impossible de générer le code-barres localement.")

# ---------------------------
# Notes et export (optionnel)
# ---------------------------
st.markdown("---")
st.info("Remarques :\n- Le menu Field Office est totalement indépendant du ZIP et de la ville.\n- ZIP et Ville sont fournis comme menus déroulants distincts et ne modifient pas le Field Office.")

# Fin du fichier
