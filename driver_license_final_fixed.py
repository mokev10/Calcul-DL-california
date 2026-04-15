#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version mise à jour — champs Code postal et Ville en texte libre
# Interface pédagogique Streamlit — NE GÉNÈRE PAS de permis officiels ni de PDF417

import datetime
import random
from typing import Dict, List, Tuple, Optional

import streamlit as st

# Optional imports (ReportLab/pdf417gen/AAMVA utils) preserved if disponibles
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="Générateur pédagogique de permis (interface)", layout="wide")

# ---------------------------
# ZIP database (extrait)
# ---------------------------
# NOTE: kept for reference/validation if needed; fields "office" intentionally empty.
ZIP_DB: Dict[str, Dict[str, str]] = {
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "90011": {"city": "Los Angeles", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    # ... étendre jusqu'à 96162 si nécessaire
}

# ---------------------------
# Field offices (single dropdown)
# ---------------------------
FIELD_OFFICES_BY_REGION: Dict[str, Dict[str, int]] = {
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

def build_field_office_choices(regions: Dict[str, Dict[str, int]]) -> List[Tuple[str, int]]:
    choices: List[Tuple[str, int]] = []
    for region, cities in regions.items():
        for city, code in cities.items():
            label = f"{region} — {city} ({code})"
            choices.append((label, code))
    return choices

FIELD_OFFICE_CHOICES = build_field_office_choices(FIELD_OFFICES_BY_REGION)

# ---------------------------
# Helpers
# ---------------------------
def generate_license_number() -> str:
    return "H" + "".join(str(random.randint(0, 9)) for _ in range(8))

def format_date(d: datetime.date) -> str:
    return d.strftime("%Y/%m/%d")

# ---------------------------
# Minimal CSS for a modern look
# ---------------------------
st.markdown(
    """
    <style>
      .card { background: linear-gradient(180deg,#fff,#f7fbff); padding:16px; border-radius:10px; box-shadow:0 6px 18px rgba(20,30,60,0.06); }
      .preview { background: linear-gradient(90deg,#0f4c81,#2b7bbf); color:#fff; padding:16px; border-radius:10px; }
      .muted { color:#6b7280; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# UI
# ---------------------------
st.title("Générateur pédagogique de permis — Interface")
st.caption("Usage académique uniquement — ne génère pas de documents officiels")

left, right = st.columns([1.1, 0.9])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Saisie utilisateur")

    family_name = st.text_input("Nom de famille", value="HARRIS")
    given_name = st.text_input("Prénom", value="ROSA")
    sex = st.selectbox("Sexe", options=["M", "F", "X"], index=0)
    dob = st.date_input("Date de naissance", value=datetime.date(1990, 1, 3))

    st.markdown("---")
    st.subheader("Caractéristiques physiques (optionnel)")
    height_ft = st.number_input("Pieds", min_value=0, max_value=8, value=5)
    height_in = st.number_input("Pouces", min_value=0, max_value=11, value=10)
    weight_lb = st.number_input("Poids (lb)", min_value=0, max_value=1000, value=160)
    hair = st.text_input("Cheveux", value="BRN")
    eyes = st.text_input("Yeux", value="BRN")

    st.markdown("---")
    st.subheader("Adresse et codes (champs libres)")
    # **CHANGEMENT** : Code postal et Ville sont des champs texte libres
    zip_input = st.text_input("Code postal (ZIP) — champ libre", value="90001")
    city_input = st.text_input("Ville — champ libre", value="Los Angeles")
    address_line = st.text_input("Address Line", value="2570 24TH STREET")

    st.markdown("---")
    st.subheader("Permis et dates")
    license_number = st.text_input("Numéro de permis (pseudo)", value=generate_license_number())
    issue_date = st.date_input("Date d’émission", value=datetime.date.today())
    default_exp = issue_date.replace(year=issue_date.year + 5) - datetime.timedelta(days=15)
    expiration_date = st.date_input("Date d'expiration", value=default_exp)

    st.markdown("---")
    st.subheader("Restrictions / Endorsements")
    restrictions = st.text_input("Restrictions", value="NONE")
    endorsements = st.text_input("Endorsements", value="NONE")

    st.markdown("---")
    st.subheader("Field Office (menu unique, indépendant)")
    field_office_labels = [label for label, code in FIELD_OFFICE_CHOICES]
    # default to first or try to find Los Angeles (502)
    default_idx = 0
    for i, label in enumerate(field_office_labels):
        if "Los Angeles (502)" in label:
            default_idx = i
            break
    field_office_choice = st.selectbox("Field Office (sélection unique)", options=field_office_labels, index=default_idx)
    selected_field_office_code = next((code for label, code in FIELD_OFFICE_CHOICES if label == field_office_choice), None)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    generate = st.button("Générer (pédagogique)")

with right:
    st.markdown('<div class="preview">', unsafe_allow_html=True)
    st.subheader("Aperçu carte (prévisualisation pédagogique)")
    st.markdown(f"**NAME:** {given_name} {family_name}")
    st.markdown(f"**SEX:** {sex}    **DOB:** {format_date(dob)}")
    st.markdown(f"**DLN (pseudo):** {license_number}")
    st.markdown(f"**ADDRESS:** {address_line}")
    st.markdown(f"**CITY / ZIP:** {city_input} / {zip_input}")
    st.markdown(f"**FIELD OFFICE:** {field_office_choice}")
    st.markdown(f"**ISSUE DATE:** {format_date(issue_date)}")
    st.markdown(f"**EXPIRATION DATE:** {format_date(expiration_date)}")
    st.markdown(f"**RESTRICTIONS:** {restrictions}    **ENDORSEMENTS:** {endorsements}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Action
# ---------------------------
if generate:
    payload = {
        "family_name": family_name,
        "given_name": given_name,
        "sex": sex,
        "dob": format_date(dob),
        "address_line": address_line,
        "city": city_input,
        "zip": zip_input,
        "license_number": license_number,
        "issue_date": format_date(issue_date),
        "expiration_date": format_date(expiration_date),
        "restrictions": restrictions,
        "endorsements": endorsements,
        "field_office_label": field_office_choice,
        "field_office_code": selected_field_office_code,
        "height_ft": height_ft,
        "height_in": height_in,
        "weight_lb": weight_lb,
        "hair": hair,
        "eyes": eyes,
    }

    st.success("Données collectées (usage pédagogique).")
    st.json(payload)

    # Simple HTML preview for copy/paste (no official generation)
    card_html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif; width:520px; border-radius:12px; padding:18px;
                background: linear-gradient(90deg,#0f4c81,#2b7bbf); color:white;">
      <h2 style="margin:0">CALIFORNIA USA DRIVER LICENSE (PREVIEW)</h2>
      <div style="margin-top:12px;">
        <strong>DLN:</strong> {license_number}<br/>
        <strong>NAME:</strong> {given_name} {family_name}<br/>
        <strong>ADDRESS:</strong> {address_line}<br/>
        <strong>CITY / ZIP:</strong> {city_input} / {zip_input}<br/>
        <strong>FIELD OFFICE:</strong> {field_office_choice}<br/>
        <strong>ISSUE DATE:</strong> {format_date(issue_date)} &nbsp;&nbsp;
        <strong>EXP DATE:</strong> {format_date(expiration_date)}
      </div>
    </div>
    """
    st.markdown("### Carte (HTML preview)")
    st.components.v1.html(card_html, height=220)

# ---------------------------
# Developer notes
# ---------------------------
# - Les champs "Code postal" et "Ville" sont désormais des champs texte libres (st.text_input).
# - Le dictionnaire ZIP_DB est conservé pour référence/validation si tu veux ajouter une vérification optionnelle.
# - Le menu Field Office reste un seul menu déroulant indépendant (Région — Ville (Code)).
# - Ce fichier est pédagogique : il n'essaie pas de créer de documents officiels, ni de codes-barres AAMVA/PDF417.
# - Pour intégrer la liste complète des ZIP (90001..96162), étends ZIP_DB; garder "office" vide évite tout rattachement automatique.
