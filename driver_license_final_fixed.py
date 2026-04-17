#!/usr/bin/env python3
# country_subdivision_form_equal_boxes.py
# Streamlit — En-tête fixe, deux menus déroulants côte à côte de même taille,
# et formulaire préfixes affiché dans la colonne de droite.
# Usage : streamlit run country_subdivision_form_equal_boxes.py

import datetime
from typing import Dict, List, Tuple, Optional

import streamlit as st

st.set_page_config(page_title="Formulaire préfixes — boîtes égales", layout="wide")

# --- Données : US states (50) et Canada provinces/territories (13) ---
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

# --- Préfixes et descriptions (titre, sous-titre/exemple) ---
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (ex: CAN pour Canada, US pour United States) [8]"),
    ("DCS", "Nom de famille (ex: NICOLAS) [5, 8]"),
    ("DAC", "Prénom (ex: JEAN) [5, 8]"),
    ("DBB", "Date de naissance (ex: 1994-12-08) [5, 8]"),
    ("DAG", "Adresse ligne 1 (ex: 1560 SHERBROOKE ST E) [5, 8]"),
    ("DAI", "Ville (ex: MONTREAL) [5, 8]"),
    ("DAJ", "Province/État (ex: QC ou California) [5, 8]"),
    ("DAK", "Code postal / ZIP (ex: H2L4M1 ou 90001) [5, 8]"),
    ("DBD", "Date d'émission (ex: 2023-05-10) [8]"),
    ("DBA", "Date d'expiration (ex: 2031-05-09) [5, 8]"),
    ("DBC", "Sexe (1 = Homme, 2 = Femme) [8]"),
    ("DAU", "Taille (ex: 180 cm) [8]"),
    ("DAY", "Couleur des yeux (ex: BRUN) [8]"),
    ("DCF", "Numéro de référence du document (ex: PEJQ04N96) [5]")
]

# --- En-tête (toujours présent) ---
st.title("Formulaire préfixes — Pays / Subdivision")
st.caption("Usage pédagogique — remplissez les champs texte libre après sélection du pays et de la subdivision")

# --- Layout principal ---
# Trois colonnes : les deux premières pour les menus (mêmes largeurs), la troisième pour le formulaire
col_menu_1, col_menu_2, col_form = st.columns([0.33, 0.33, 0.34])

# --- Menus côte à côte, mêmes tailles ---
with col_menu_1:
    country = st.selectbox("Pays", ["United States (US)", "Canada (CAN)"], key="select_country_equal")

with col_menu_2:
    # Construire la liste liée en fonction du pays
    if country.startswith("United"):
        options = [f"{name} ({abbr})" for name, abbr in sorted(US_STATES.items(), key=lambda x: x[0])]
        subdivision_label = "État"
    else:
        options = [f"{name} ({abbr})" for name, abbr in sorted(CAN_PROVINCES_TERRITORIES.items(), key=lambda x: x[0])]
        subdivision_label = "Province / Territoire"
    subdivision = st.selectbox(subdivision_label, [""] + options, key="select_subdivision_equal")

# --- Formulaire (colonne de droite) ---
with col_form:
    if subdivision:
        default_country_code = "US" if country.startswith("United") else "CAN"

        # Card visuel pour meilleure lisibilité
        st.markdown("<div style='padding:12px;border-radius:8px;background:#ffffff;box-shadow:0 1px 6px rgba(0,0,0,0.06)'>", unsafe_allow_html=True)
        st.subheader("Champs préfixés (texte libre)")
        st.markdown("Remplissez les champs ci‑dessous. Chaque champ est un champ texte libre avec un petit aide‑texte.")

        # Grille 2 colonnes équilibrées pour les champs
        for i in range(0, len(PREFIX_FIELDS), 2):
            left = PREFIX_FIELDS[i]
            right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
            cols = st.columns([1, 1])
            # Champ gauche
            key_left = f"field_{left[0]}"
            if left[0] == "DCG":
                cols[0].text_input(left[0], value=default_country_code, help=left[1], key=key_left)
            else:
                cols[0].text_input(left[0], value="", help=left[1], placeholder=left[1], key=key_left)

            # Champ droit
            if right:
                key_right = f"field_{right[0]}"
                if right[0] == "DCG":
                    cols[1].text_input(right[0], value=default_country_code, help=right[1], key=key_right)
                else:
                    cols[1].text_input(right[0], value="", help=right[1], placeholder=right[1], key=key_right)

        st.markdown("</div>", unsafe_allow_html=True)

        # Actions
        st.markdown("")  # spacing
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

        # Aperçu si présent
        if st.session_state.get("last_prefix_payload"):
            st.markdown("---")
            st.subheader("Aperçu des données enregistrées (session)")
            st.json(st.session_state["last_prefix_payload"])
    else:
        st.info("Sélectionnez un pays et une subdivision pour afficher le formulaire.")

# --- Ajustements UI/UX supplémentaires (optionnels) ---
# - Les deux menus sont strictement de la même largeur (colonnes [0.33, 0.33, 0.34]).
# - L'en-tête reste toujours visible en haut comme demandé.
# - Si tu veux que les labels des menus soient plus compacts (ex: 'Pays' et 'État'), je peux les raccourcir.
# - Si tu veux que la colonne formulaire soit plus large, indique la proportion souhaitée (ex: [0.28,0.28,0.44]).
