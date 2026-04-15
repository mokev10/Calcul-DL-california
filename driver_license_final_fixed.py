#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version mise à jour — license_number commence par l'initiale du nom de famille
# Usage pédagogique uniquement — NE GÉNÈRE PAS de documents officiels

import datetime
import random
from typing import Dict, List, Tuple, Optional

import streamlit as st

# Optional imports (ReportLab/pdf417gen/AAMVA utils) preserved if available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="Générateur pédagogique de permis (mise à jour)", layout="wide")

# ---------------------------
# Données (extraits)
# ---------------------------
ZIP_DB: Dict[str, Dict[str, str]] = {
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    # ... étendre si nécessaire
}

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
    choices.sort(key=lambda x: x[0].lower())
    return choices

FIELD_OFFICE_CHOICES = build_field_office_choices(FIELD_OFFICES_BY_REGION)

# ---------------------------
# Nouvelle logique de génération du numéro de permis
# ---------------------------
def _initial_from_family_name(family_name: str) -> str:
    """
    Retourne la première lettre majuscule du nom de famille si c'est une lettre A-Z,
    sinon retourne 'H' par défaut.
    """
    if not family_name:
        return "H"
    first = family_name.strip()[0].upper()
    if "A" <= first <= "Z":
        return first
    return "H"

def _random_even_digit() -> str:
    return str(random.choice([0,2,4,6,8]))

def _random_odd_digit() -> str:
    return str(random.choice([1,3,5,7,9]))

def generate_license_number_from_name(family_name: str, digits: int = 8) -> str:
    """
    Génère un numéro pseudo-aléatoire commençant par l'initiale du nom de famille.
    Les chiffres suivants alternent pair/impair : position 0 -> pair, position 1 -> impair, etc.
    Ex: Davis -> 'D' + 8 chiffres alternés -> 'D21291706' (exemple)
    Usage pédagogique uniquement.
    """
    initial = _initial_from_family_name(family_name)
    parts: List[str] = []
    for i in range(digits):
        if i % 2 == 0:
            parts.append(_random_even_digit())
        else:
            parts.append(_random_odd_digit())
    return initial + "".join(parts)

# ---------------------------
# Helpers UI
# ---------------------------
def format_date(d: datetime.date) -> str:
    return d.strftime("%Y/%m/%d")

# ---------------------------
# UI Streamlit
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

st.title("Générateur pédagogique de permis — Numéro basé sur le nom de famille")
st.caption("Usage académique uniquement — le numéro est pseudo‑aléatoire et non officiel")

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
    zip_input = st.text_input("Code postal (ZIP) — champ libre", value="90001")
    city_input = st.text_input("Ville — champ libre", value="Los Angeles")
    address_line = st.text_input("Address Line", value="2570 24TH STREET")

    st.markdown("---")
    st.subheader("Permis et dates")
    # Utilise la nouvelle fonction pour générer le numéro par défaut
    default_license = generate_license_number_from_name(family_name)
    license_number = st.text_input("Numéro de permis (pseudo)", value=default_license)
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
    default_idx = 0
    for i, label in enumerate(field_office_labels):
        if "Los Angeles (502)" in label:
            default_idx = i
            break
    field_office_choice = st.selectbox("Field Office (sélection unique)", options=field_office_labels, index=default_idx)
    selected_field_office_code = next((code for label, code in FIELD_OFFICE_CHOICES if label == field_office_choice), None)

    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    # Bouton pour régénérer le numéro en fonction du nom saisi
    if st.button("Régénérer le numéro à partir du nom de famille"):
        license_number = generate_license_number_from_name(family_name)
        st.success(f"Numéro mis à jour : {license_number}")

    generate = st.button("Collecter les données (pédagogique)")

with right:
    st.markdown('<div class="preview">', unsafe_allow_html=True)
    st.subheader("Aperçu (prévisualisation pédagogique)")
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

    # Aperçu HTML simple (copie/coller)
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
# Notes développeur
# ---------------------------
# - La fonction generate_license_number_from_name(family_name) applique la règle demandée :
#   initiale = première lettre du nom de famille (A-Z) ou 'H' par défaut,
#   puis 8 chiffres alternant pair/impair.
# - Ce numéro est purement pédagogique et pseudo‑aléatoire.
# - Si tu veux un autre schéma d'alternance (impair/pair début, longueur différente), je peux l'adapter.
# - Ne pas utiliser ce code pour produire des documents officiels.
