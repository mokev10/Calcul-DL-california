#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version mise à jour — interface moderne Streamlit
# Colle ce fichier en remplacement complet de celui qui a été modifié.
#
# The interface collects nom, prénom, sexe, date de naissance, adresse, ZIP, ville, field office (saisi manuellement),
# caractéristiques physiques, numéro de permis, dates d’émission/expiration, etc.
# Colle ce fichier en remplacement complet de celui qui a été modifié.

import datetime
import io
import random
import hashlib
from typing import Dict, List, Tuple, Optional

import streamlit as st

# Optional imports (ReportLab/pdf417gen/AAMVA utils) left as in original file if available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

# ---------------------------
# ZIP database (partial)
# ---------------------------
# NOTE: keep "office" empty here — field office selection is independent (single dropdown).
ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "92101": {"city": "San Diego", "state": "CA", "office": ""},
    "90272": {"city": "Pacific Palisades", "state": "CA", "office": ""},
    "90265": {"city": "Malibu", "state": "CA", "office": ""},
    "90266": {"city": "Malibu", "state": "CA", "office": ""},
    "90270": {"city": "Maywood", "state": "CA", "office": ""},
    "90274": {"city": "Palos Verdes Peninsula", "state": "CA", "office": ""},
    "90275": {"city": "Rancho Palos Verdes", "state": "CA", "office": ""},
    "90277": {"city": "Redondo Beach", "state": "CA", "office": ""},
    "90278": {"city": "Redondo Beach", "state": "CA", "office": ""},
    "90291": {"city": "Venice", "state": "CA", "office": ""},
    "90292": {"city": "Venice", "state": "CA", "office": ""},
    "90301": {"city": "Inglewood", "state": "CA", "office": ""},
    "90401": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90501": {"city": "Torrance", "state": "CA", "office": ""},
    "90601": {"city": "Whittier", "state": "CA", "office": ""},
    "90701": {"city": "Long Beach", "state": "CA", "office": ""},
    "90802": {"city": "Long Beach", "state": "CA", "office": ""},
    "91101": {"city": "Pasadena", "state": "CA", "office": ""},
    "91201": {"city": "Glendale", "state": "CA", "office": ""},
    "91301": {"city": "Agoura Hills", "state": "CA", "office": ""},
    "91401": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91501": {"city": "Burbank", "state": "CA", "office": ""},
    "91601": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91701": {"city": "Azusa", "state": "CA", "office": ""},
    "91710": {"city": "Chino", "state": "CA", "office": ""},
    "91730": {"city": "Duarte", "state": "CA", "office": ""},
    "91901": {"city": "Chula Vista", "state": "CA", "office": ""},
    "92003": {"city": "Carlsbad", "state": "CA", "office": ""},
    # ... (extend as needed; keep office empty)
}

# ---------------------------
# Field offices (single dropdown)
# ---------------------------
# Provided mapping: region -> {city: code}
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

# Build a single flat list for the single dropdown (region — city (code))
def build_field_office_choices(regions: Dict[str, Dict[str, int]]) -> List[Tuple[str, int]]:
    choices: List[Tuple[str, int]] = []
    for region, cities in regions.items():
        for city, code in cities.items():
            label = f"{region} — {city} ({code})"
            choices.append((label, code))
    return choices


FIELD_OFFICE_CHOICES = build_field_office_choices(FIELD_OFFICES_BY_REGION)


# ---------------------------
# Helper utilities
# ---------------------------
def generate_license_number() -> str:
    """Generate a pseudo license number (not real)."""
    return "H" + "".join(str(random.randint(0, 9)) for _ in range(8))


def format_date(d: datetime.date) -> str:
    return d.strftime("%Y/%m/%d")


def get_city_from_zip(zip_code: str) -> Optional[str]:
    entry = ZIP_DB.get(zip_code)
    return entry["city"] if entry else None


# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Générateur officiel de permis Californien", layout="wide")

# Minimal modern CSS
st.markdown(
    """
    <style>
    .app-header {
        display:flex;
        align-items:center;
        gap:16px;
    }
    .card {
        background: linear-gradient(180deg, #ffffff 0%, #f3f6fb 100%);
        border-radius:12px;
        padding:18px;
        box-shadow: 0 6px 18px rgba(20,30,60,0.08);
    }
    .left-col { max-width: 520px; }
    .field-label { font-weight:600; color:#233; margin-bottom:6px; }
    .muted { color:#6b7280; font-size:13px; }
    .preview-card {
        background: linear-gradient(90deg,#0f4c81,#2b7bbf);
        color: white;
        border-radius:12px;
        padding:18px;
        min-height:220px;
    }
    .small { font-size:12px; color:#e6eefc; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="app-header"><h1 style="margin:0">Générateur officiel de permis Californien</h1></div>', unsafe_allow_html=True)
        st.markdown('<div class="muted">Interface moderne — remplissez les champs et générez la carte</div>', unsafe_allow_html=True)
    with col2:
        st.image("https://img.icons8.com/fluency/48/000000/id-card.png", width=48)

st.write("")

# Main layout
left_col, right_col = st.columns([1.1, 0.9])

with left_col:
    st.markdown('<div class="card left-col">', unsafe_allow_html=True)

    st.subheader("Saisie utilisateur")
    # Personal info
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
    st.subheader("Adresse et codes")
    # ZIP dropdown (from ZIP_DB keys)
    zip_options = sorted(ZIP_DB.keys())
    zip_selected = st.selectbox("Code postal (ZIP)", options=zip_options, index=zip_options.index("90001") if "90001" in zip_options else 0)
    # City dropdown: show the city corresponding to selected ZIP, but allow manual override by selecting from all unique cities
    # Build unique city list
    unique_cities = sorted({v["city"] for v in ZIP_DB.values()})
    # Preselect city based on zip
    city_default = get_city_from_zip(zip_selected) or unique_cities[0]
    city_selected = st.selectbox("Ville", options=unique_cities, index=unique_cities.index(city_default) if city_default in unique_cities else 0)

    address_line = st.text_input("Address Line", value="2570 24TH STREET")

    st.markdown("---")
    st.subheader("Permis et dates")
    license_number = st.text_input("Numéro de permis", value=generate_license_number())
    issue_date = st.date_input("Date d’émission", value=datetime.date.today())
    # default expiration 5 years minus a few days
    default_exp = issue_date.replace(year=issue_date.year + 5) - datetime.timedelta(days=15)
    expiration_date = st.date_input("Date d'expiration", value=default_exp)

    st.markdown("---")
    st.subheader("Restrictions / Endorsements")
    restrictions = st.text_input("Restrictions", value="NONE")
    endorsements = st.text_input("Endorsements", value="NONE")

    st.markdown("---")
    st.subheader("Field Office (sélectionnez dans le menu unique)")
    # Single dropdown for field office (region — city (code))
    field_office_labels = [label for label, code in FIELD_OFFICE_CHOICES]
    # Try to default to "Grand Los Angeles — Los Angeles (502)" if present
    default_idx = 0
    for i, label in enumerate(field_office_labels):
        if "Los Angeles (502)" in label:
            default_idx = i
            break
    field_office_choice = st.selectbox("Field Office (sélection unique)", options=field_office_labels, index=default_idx)
    # Extract code from selection
    selected_field_office_code = None
    for label, code in FIELD_OFFICE_CHOICES:
        if label == field_office_choice:
            selected_field_office_code = code
            break

    st.markdown("</div>", unsafe_allow_html=True)

    # Generate button
    st.write("")
    generate = st.button("Générer la carte", type="primary")

with right_col:
    st.markdown('<div class="card preview-card">', unsafe_allow_html=True)
    st.subheader("Aperçu carte")
    # Live preview
    st.markdown(f"**NAME:** {given_name} {family_name}")
    st.markdown(f"**SEX:** {sex}    **DOB:** {format_date(dob)}")
    st.markdown(f"**DLN:** {license_number}")
    st.markdown(f"**ADDRESS:** {address_line}")
    st.markdown(f"**CITY / ZIP:** {city_selected} / {zip_selected}")
    st.markdown(f"**FIELD OFFICE:** {field_office_choice}")
    st.markdown(f"**ISSUE DATE:** {format_date(issue_date)}")
    st.markdown(f"**EXPIRATION DATE:** {format_date(expiration_date)}")
    st.markdown(f"**RESTRICTIONS:** {restrictions}    **ENDORSEMENTS:** {endorsements}")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Generation logic
# ---------------------------
if generate:
    # Build a payload (example) — independent field office selection
    payload = {
        "family_name": family_name,
        "given_name": given_name,
        "sex": sex,
        "dob": format_date(dob),
        "address_line": address_line,
        "city": city_selected,
        "zip": zip_selected,
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

    # Show confirmation and payload
    st.success("Carte générée (aperçu ci-dessous).")
    st.json(payload)

    # Optionally: create a simple printable card as HTML for copy/paste or PDF generation
    card_html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif; width:520px; border-radius:12px; padding:18px;
                background: linear-gradient(90deg,#0f4c81,#2b7bbf); color:white;">
      <h2 style="margin:0">CALIFORNIA USA DRIVER LICENSE</h2>
      <div style="margin-top:12px;">
        <strong>DLN:</strong> {license_number}<br/>
        <strong>NAME:</strong> {given_name} {family_name}<br/>
        <strong>ADDRESS:</strong> {address_line}<br/>
        <strong>CITY / ZIP:</strong> {city_selected} / {zip_selected}<br/>
        <strong>FIELD OFFICE:</strong> {field_office_choice}<br/>
        <strong>ISSUE DATE:</strong> {format_date(issue_date)} &nbsp;&nbsp;
        <strong>EXP DATE:</strong> {format_date(expiration_date)}
      </div>
    </div>
    """
    st.markdown("### Carte (HTML preview)")
    st.components.v1.html(card_html, height=220)

# ---------------------------
# Notes for developers (kept in-file)
# ---------------------------
# - Field office selection is intentionally independent from ZIP_DB and city selection.
# - ZIP_DB entries keep "office" empty to avoid automatic linking.
# - FIELD_OFFICES_BY_REGION contains the region -> (city -> code) mapping; a single dropdown is built from it.
# - To extend ZIP_DB to cover 90001..96162, append entries to ZIP_DB; keep "office" empty.
# - To change the default field office, modify the default_idx logic above.
#
# End of file.
