#!/usr/bin/env python3
# app_final.py
# Streamlit — Pas d'upload d'images. En-tête centré, deux selects côte-à-côte centrés,
# texte d'aide sous les selects, puis tous les champs (avec selectboxes quand pertinent).
# Usage : streamlit run app_final.py

import datetime
from typing import Dict, List, Tuple
import streamlit as st

st.set_page_config(page_title="Pays / Subdivision — Formulaire complet", layout="wide")

# --- Données complètes ---
US_STATES: Dict[str, str] = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO",
    "Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
    "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH",
    "Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"
}

CAN_PROVINCES_TERRITORIES: Dict[str, str] = {
    "Alberta":"AB","British Columbia":"BC","Prince Edward Island":"PE","Manitoba":"MB",
    "New Brunswick":"NB","Nova Scotia":"NS","Ontario":"ON","Quebec":"QC","Saskatchewan":"SK",
    "Newfoundland and Labrador":"NL","Yukon":"YT","Northwest Territories":"NT","Nunavut":"NU"
}

# --- Champs préfixés (nom, aide) ---
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (ex: CAN pour Canada, US pour United States)"),
    ("DCS", "Nom de famille (ex: NICOLAS)"),
    ("DAC", "Prénom (ex: JEAN)"),
    ("DBB", "Date de naissance (YYYY-MM-DD ou 8 décembre 1994)"),
    ("DAG", "Adresse ligne 1 (ex: 1560 SHERBROOKE ST E)"),
    ("DAI", "Ville (ex: MONTREAL)"),
    ("DAJ", "Province/État (ex: QC ou California)"),
    ("DAK", "Code postal / ZIP (ex: H2L4M1 ou 90001)"),
    ("DBD", "Date d'émission (YYYY-MM-DD)"),
    ("DBA", "Date d'expiration (YYYY-MM-DD)"),
    ("DBC", "Sexe (1 = Homme, 2 = Femme)"),
    ("DAU", "Taille (ex: 180 cm)"),
    ("DAY", "Couleur des yeux (ex: BRUN)"),
    ("DCF", "Numéro de référence du document (ex: PEJQ04N96)")
]

# --- En-tête centré ---
st.markdown("<div style='text-align:center; margin-top:6px;'>"
            "<h1 style='margin:0;'>Formulaire préfixes — Pays / Subdivision</h1>"
            "<p style='color:gray; margin:4px 0 12px 0;'>Usage pédagogique — remplissez les champs après sélection</p>"
            "</div>", unsafe_allow_html=True)

# --- Zone centrale pour selects (centrés) ---
outer_l, center_col, outer_r = st.columns([1, 2, 1])
with center_col:
    sel_left, sel_right = st.columns([1, 1])
    with sel_left:
        country = st.selectbox("Pays", ["United States (US)", "Canada (CAN)"], key="country_main")
    # construire options selon pays
    if country.startswith("United"):
        subdivision_label = "État"
        options = [f"{name} ({abbr})" for name, abbr in sorted(US_STATES.items(), key=lambda x: x[0])]
    else:
        subdivision_label = "Province / Territoire"
        options = [f"{name} ({abbr})" for name, abbr in sorted(CAN_PROVINCES_TERRITORIES.items(), key=lambda x: x[0])]
    with sel_right:
        subdivision = st.selectbox(subdivision_label, [""] + options, key="subdivision_main")

    # texte d'aide centré sous les deux selects
    st.markdown(
        "<div style='margin-top:10px;padding:10px;border-radius:6px;background:#eef6ff;color:#0f4c81;text-align:center;'>"
        "Sélectionnez un pays et une subdivision pour afficher le formulaire."
        "</div>",
        unsafe_allow_html=True
    )

# --- Formulaire complet (affiché si subdivision choisie) ---
if subdivision:
    default_country_code = "US" if country.startswith("United") else "CAN"

    st.markdown("---")
    st.subheader("Champs préfixés (saisie)")

    # Présentation en grille 2 colonnes ; utiliser selectboxes pour les champs qui s'y prêtent
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1, 1])

        # Champ gauche
        key_left = f"field_{left[0]}"
        if left[0] == "DCG":
            cols[0].text_input(left[0], value=default_country_code, help=left[1], key=key_left)
        elif left[0] == "DAJ":
            # DAJ : proposer la subdivision sélectionnée en priorité
            cols[0].selectbox(left[0],
                              options=[subdivision] + [opt for opt in (options if options else []) if opt != subdivision],
                              index=0,
                              help=left[1],
                              key=key_left)
        elif left[0] == "DBC":
            cols[0].selectbox(left[0], options=["", "1 - Homme", "2 - Femme"], help=left[1], key=key_left)
        elif left[0] in ("DAU", "DAY"):
            cols[0].text_input(left[0], value="", help=left[1], placeholder=left[1], key=key_left)
        else:
            cols[0].text_input(left[0], value="", help=left[1], placeholder=left[1], key=key_left)

        # Champ droit
        if right:
            key_right = f"field_{right[0]}"
            if right[0] == "DCG":
                cols[1].text_input(right[0], value=default_country_code, help=right[1], key=key_right)
            elif right[0] == "DAJ":
                cols[1].selectbox(right[0],
                                  options=[subdivision] + [opt for opt in (options if options else []) if opt != subdivision],
                                  index=0,
                                  help=right[1],
                                  key=key_right)
            elif right[0] == "DBC":
                cols[1].selectbox(right[0], options=["", "1 - Homme", "2 - Femme"], help=right[1], key=key_right)
            elif right[0] in ("DAU", "DAY"):
                cols[1].text_input(right[0], value="", help=right[1], placeholder=right[1], key=key_right)
            else:
                cols[1].text_input(right[0], value="", help=right[1], placeholder=right[1], key=key_right)

    st.markdown("---")
    action_l, action_r = st.columns([1, 1])
    with action_l:
        if st.button("Enregistrer (session)"):
            payload = {}
            for prefix, _ in PREFIX_FIELDS:
                payload[prefix] = st.session_state.get(f"field_{prefix}", "")
            payload["COUNTRY_LABEL"] = country
            payload["SUBDIVISION_LABEL"] = subdivision
            payload["TIMESTAMP"] = datetime.datetime.now().isoformat()
            st.session_state["last_prefix_payload"] = payload
            st.success("Données enregistrées en session (usage pédagogique).")
    with action_r:
        if st.button("Réinitialiser les champs"):
            for prefix, _ in PREFIX_FIELDS:
                st.session_state[f"field_{prefix}"] = ""
            st.session_state["field_DCG"] = default_country_code
            st.info("Champs réinitialisés.")

    # Aperçu compact
    if st.session_state.get("last_prefix_payload"):
        st.markdown("---")
        st.subheader("Aperçu des données enregistrées")
        st.json(st.session_state["last_prefix_payload"])
