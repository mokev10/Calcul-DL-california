#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version finale — interface pédagogique Streamlit
# - Champs ZIP et Ville en texte libre
# - Field Office en menu unique (Région — Ville (Code))
# - Numéro de permis : initiale du nom de famille + chiffres alternés pair/impair
# - Un seul bouton "Générer (pédagogique)" : régénère le numéro et affiche l'aperçu
# - Sélecteur de date personnalisé (calendrier) intégré
# Usage académique uniquement — NE GÉNÈRE PAS de documents officiels

import calendar
import datetime
import random
from typing import Dict, List, Tuple, Optional

import streamlit as st

# ---------------------------
# Configuration page
# ---------------------------
st.set_page_config(page_title="Générateur pédagogique de permis — Version finale", layout="wide")

# ---------------------------
# Données (extraits / à compléter)
# ---------------------------
ZIP_DB: Dict[str, Dict[str, str]] = {
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    # Étendre jusqu'à 96162 si nécessaire
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
# Utilitaires : numéro de permis
# ---------------------------
def _initial_from_family_name(family_name: str) -> str:
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
    Retourne : <InitialeMajuscule><digits alternés pair/impair>
    Ex: Davis -> 'D' + 8 chiffres alternés.
    Usage pédagogique uniquement.
    """
    initial = _initial_from_family_name(family_name)
    parts: List[str] = []
    for i in range(digits):
        parts.append(_random_even_digit() if i % 2 == 0 else _random_odd_digit())
    return initial + "".join(parts)

def format_date(d: datetime.date) -> str:
    return d.strftime("%Y/%m/%d")

# ---------------------------
# Sélecteur de date personnalisé (calendrier)
# ---------------------------
WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

def _month_year_key(prefix: str, dt: datetime.date) -> str:
    return f"{prefix}_{dt.year}_{dt.month}"

def custom_date_picker(label: str, default: Optional[datetime.date] = None) -> Optional[datetime.date]:
    """
    Composant calendrier simple : navigation mois, sélection d'un jour.
    Retourne datetime.date ou None.
    """
    if default is None:
        default = datetime.date.today()

    if "cdp_display_month" not in st.session_state:
        st.session_state["cdp_display_month"] = datetime.date(default.year, default.month, 1)
    if "cdp_selected_date" not in st.session_state:
        st.session_state["cdp_selected_date"] = default

    st.markdown(f"**{label}**")
    display = st.session_state["cdp_display_month"]
    prev_month = (display.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
    next_month = (display.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 6, 1])
    with nav_col1:
        if st.button("◀", key=_month_year_key("prev", display)):
            st.session_state["cdp_display_month"] = prev_month
    with nav_col2:
        st.markdown(f"### {display.strftime('%B %Y')}")
    with nav_col3:
        if st.button("▶", key=_month_year_key("next", display)):
            st.session_state["cdp_display_month"] = next_month

    # Mois rapide via selectbox
    months = [datetime.date(display.year, m, 1) for m in range(1, 13)]
    month_labels = [m.strftime("%b") for m in months]
    sel_month_idx = display.month - 1
    chosen_month = st.selectbox("Mois", options=month_labels, index=sel_month_idx, key=_month_year_key("select_month", display))
    chosen_month_num = month_labels.index(chosen_month) + 1
    if chosen_month_num != display.month:
        st.session_state["cdp_display_month"] = display.replace(month=chosen_month_num, day=1)
        display = st.session_state["cdp_display_month"]

    # Construire la grille du mois
    year = display.year
    month = display.month
    cal = calendar.Calendar(firstweekday=0)  # Monday start
    month_days = list(cal.itermonthdates(year, month))

    # En-têtes
    cols = st.columns(7)
    for i, wd in enumerate(WEEKDAYS):
        cols[i].markdown(f"**{wd}**")

    # Jours (6 semaines)
    for week_idx in range(6):
        week = month_days[week_idx*7:(week_idx+1)*7]
        cols = st.columns(7)
        for i, day in enumerate(week):
            is_current_month = (day.month == month)
            key = f"cdp_day_{year}_{month}_{week_idx}_{i}_{day.isoformat()}"
            label_day = str(day.day)
            if is_current_month:
                # Mettre en évidence le jour sélectionné
                selected = st.session_state.get("cdp_selected_date")
                if selected == day:
                    btn_label = f"**[{label_day}]**"
                else:
                    btn_label = label_day
                if cols[i].button(btn_label, key=key):
                    st.session_state["cdp_selected_date"] = day
            else:
                cols[i].markdown(f"<span style='color:#9aa0a6'>{label_day}</span>", unsafe_allow_html=True)

    # Effacer la sélection
    clear_col, _ = st.columns([1, 6])
    with clear_col:
        if st.button("Effacer la date", key="cdp_clear"):
            st.session_state["cdp_selected_date"] = None

    return st.session_state.get("cdp_selected_date")

# ---------------------------
# Initialisation session_state
# ---------------------------
if "license_number" not in st.session_state:
    st.session_state["license_number"] = generate_license_number_from_name("HARRIS")
if "generated" not in st.session_state:
    st.session_state["generated"] = False
if "last_payload" not in st.session_state:
    st.session_state["last_payload"] = None

# ---------------------------
# Style minimal
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
# UI principale
# ---------------------------
st.title("Générateur pédagogique de permis — Version finale")
st.caption("Usage académique uniquement — interface pédagogique, pas de documents officiels")

left_col, right_col = st.columns([1.1, 0.9])

with left_col:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Saisie utilisateur")

    family_name = st.text_input("Nom de famille", value="HARRIS")
    given_name = st.text_input("Prénom", value="ROSA")
    sex = st.selectbox("Sexe", options=["M", "F", "X"], index=0)
    dob = custom_date_picker("Date de naissance", default=datetime.date(1990, 1, 3))

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
    # Affiche la valeur stockée dans session_state (modifiable)
    st.text_input("Numéro de permis (pseudo)", key="license_number")
    issue_date = custom_date_picker("Date d’émission", default=datetime.date.today())
    if issue_date is None:
        issue_date = datetime.date.today()
    default_exp = (issue_date.replace(year=issue_date.year + 5) - datetime.timedelta(days=15))
    expiration_date = custom_date_picker("Date d'expiration", default=default_exp)
    if expiration_date is None:
        expiration_date = default_exp

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

    # --- UN SEUL BOUTON : régénère le numéro à partir du nom ET génère l'aperçu ---
    if st.button("Générer (pédagogique)"):
        # Régénérer license_number à partir du nom de famille
        st.session_state["license_number"] = generate_license_number_from_name(family_name)
        # Construire payload
        payload = {
            "family_name": family_name,
            "given_name": given_name,
            "sex": sex,
            "dob": format_date(dob) if dob else "",
            "address_line": address_line,
            "city": city_input,
            "zip": zip_input,
            "license_number": st.session_state["license_number"],
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
        st.session_state["generated"] = True
        st.session_state["last_payload"] = payload
        st.success("Numéro régénéré et aperçu généré (usage pédagogique).")

with right_col:
    if st.session_state.get("generated", False) and st.session_state.get("last_payload") is not None:
        payload = st.session_state["last_payload"]
        st.markdown('<div class="preview">', unsafe_allow_html=True)
        st.subheader("Aperçu (prévisualisation pédagogique)")
        st.markdown(f"**NAME:** {payload['given_name']} {payload['family_name']}")
        st.markdown(f"**SEX:** {payload['sex']}    **DOB:** {payload['dob']}")
        st.markdown(f"**DLN (pseudo):** {payload['license_number']}")
        st.markdown(f"**ADDRESS:** {payload['address_line']}")
        st.markdown(f"**CITY / ZIP:** {payload['city']} / {payload['zip']}")
        st.markdown(f"**FIELD OFFICE:** {payload['field_office_label']}")
        st.markdown(f"**ISSUE DATE:** {payload['issue_date']}")
        st.markdown(f"**EXPIRATION DATE:** {payload['expiration_date']}")
        st.markdown(f"**RESTRICTIONS:** {payload['restrictions']}    **ENDORSEMENTS:** {payload['endorsements']}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Payload JSON (pédagogique)")
        st.json(payload)

        st.markdown("---")
        st.markdown("### Carte (HTML preview)")
        card_html = f"""
        <div style="font-family:Arial,Helvetica,sans-serif; width:520px; border-radius:12px; padding:18px;
                    background: linear-gradient(90deg,#0f4c81,#2b7bbf); color:white;">
          <h2 style="margin:0">CALIFORNIA USA DRIVER LICENSE (PREVIEW)</h2>
          <div style="margin-top:12px;">
            <strong>DLN:</strong> {payload['license_number']}<br/>
            <strong>NAME:</strong> {payload['given_name']} {payload['family_name']}<br/>
            <strong>ADDRESS:</strong> {payload['address_line']}<br/>
            <strong>CITY / ZIP:</strong> {payload['city']} / {payload['zip']}<br/>
            <strong>FIELD OFFICE:</strong> {payload['field_office_label']}<br/>
            <strong>ISSUE DATE:</strong> {payload['issue_date']} &nbsp;&nbsp;
            <strong>EXP DATE:</strong> {payload['expiration_date']}
          </div>
        </div>
        """
        st.components.v1.html(card_html, height=300)
    else:
        st.info("Aucun aperçu disponible. Cliquez sur « Générer (pédagogique) » pour régénérer le numéro et afficher l'aperçu.")

# ---------------------------
# Notes développeur (dans le fichier)
# ---------------------------
# - Le calendrier personnalisé (custom_date_picker) est utilisé pour Date de naissance, Date d'émission et Date d'expiration.
# - Un seul bouton "Générer (pédagogique)" : régénère le numéro à partir du nom de famille et affiche l'aperçu.
# - Le numéro est stocké dans st.session_state['license_number'] et mis à jour à chaque génération.
# - Les champs ZIP et Ville sont des champs texte libres.
# - Ce code est strictement pédagogique ; ne pas l'utiliser pour produire des documents officiels.
