#!/usr/bin/env python3
# country_subdivision_form.py
# Streamlit — formulaire pédagogique lié Pays -> État/Province -> champs préfixés (DCG, DCS, DAC, ...)
# Usage : streamlit run country_subdivision_form.py
#
# Comportement :
# - Menu pays (United States (US) / Canada (CAN))
# - Menu lié : si US => liste des 50 États (nom + abbr), si CAN => provinces/territoires (nom + abbr)
# - Après sélection pays + subdivision, affichage d'un formulaire contenant un champ texte libre
#   pour chaque préfixe demandé (DCG, DCS, DAC, DBB, DAG, DAI, DAJ, DAK, DBD, DBA, DBC, DAU, DAY, DCF)
# - Chaque champ affiche un petit sous-titre explicatif et un exemple (placeholder)
# - Usage pédagogique uniquement

import datetime
from typing import Dict, List, Tuple, Optional

import streamlit as st

st.set_page_config(page_title="Formulaire préfixes (DCG / DCS / ...)", layout="wide")

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
    ("DBB", "Date de naissance (ex: 1994-12-08 ou 8 décembre 1994) [5, 8]"),
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

# --- UI : sélection pays et subdivision liée ---
st.title("Sélecteur Pays → Subdivision → Formulaire préfixes")
st.markdown("Choisissez d'abord le pays, puis la subdivision (État / Province). Le formulaire s'affichera ensuite.")

col1, col2 = st.columns([0.6, 1.4])

with col1:
    country = st.selectbox("Pays", ["United States (US)", "Canada (CAN)"])

    # Construire la liste liée en fonction du pays
    if country.startswith("United"):
        subtitle = "Sélectionnez un État (United States)"
        # afficher en format "Nom (AB)"
        options = [f"{name} ({abbr})" for name, abbr in sorted(US_STATES.items(), key=lambda x: x[0])]
    else:
        subtitle = "Sélectionnez une Province / Territoire (Canada)"
        options = [f"{name} ({abbr})" for name, abbr in sorted(CAN_PROVINCES_TERRITORIES.items(), key=lambda x: x[0])]

    subdivision = st.selectbox(subtitle, [""] + options)

# --- Affichage du formulaire seulement si une subdivision est choisie ---
with col2:
    if subdivision:
        st.success(f"Pays sélectionné : **{country}** — Subdivision : **{subdivision}**")
        st.markdown("Remplissez les champs ci‑dessous. Chaque champ est un texte libre (usage pédagogique).")

        # Préremplir DCG selon le pays
        default_country_code = "US" if country.startswith("United") else "CAN"

        # Utiliser une colonne en deux pour une meilleure mise en page
        for i in range(0, len(PREFIX_FIELDS), 2):
            left = PREFIX_FIELDS[i]
            right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
            cols = st.columns([1,1])
            # Champ gauche
            key_left = f"field_{left[0]}"
            placeholder_left = left[1]
            # Si DCG, mettre valeur par défaut
            if left[0] == "DCG":
                val = st.text_input(left[0], value=default_country_code, help=left[1], key=key_left)
            else:
                val = st.text_input(left[0], value="", help=left[1], placeholder=placeholder_left, key=key_left)

            # Champ droit
            if right:
                key_right = f"field_{right[0]}"
                placeholder_right = right[1]
                if right[0] == "DCG":
                    val2 = cols[1].text_input(right[0], value=default_country_code, help=right[1], key=key_right)
                else:
                    val2 = cols[1].text_input(right[0], value="", help=right[1], placeholder=placeholder_right, key=key_right)

        st.markdown("---")
        st.markdown("### Actions")
        action_col1, action_col2 = st.columns([1,1])
        with action_col1:
            if st.button("Enregistrer (session)"):
                # Collecter les valeurs et stocker en session_state sous last_prefix_payload
                payload = {}
                for prefix, _desc in PREFIX_FIELDS:
                    payload[prefix] = st.session_state.get(f"field_{prefix}", "")
                # Ajouter pays et subdivision choisis
                payload["COUNTRY_LABEL"] = country
                payload["SUBDIVISION_LABEL"] = subdivision
                payload["TIMESTAMP"] = datetime.datetime.now().isoformat()
                st.session_state["last_prefix_payload"] = payload
                st.success("Données enregistrées en session (usage pédagogique).")
        with action_col2:
            if st.button("Réinitialiser les champs"):
                for prefix, _ in PREFIX_FIELDS:
                    st.session_state[f"field_{prefix}"] = ""
                # remettre DCG par défaut
                st.session_state["field_DCG"] = default_country_code
                st.info("Champs réinitialisés.")

        # Afficher l'aperçu si des données ont été enregistrées
        if st.session_state.get("last_prefix_payload"):
            st.markdown("---")
            st.subheader("Aperçu des données enregistrées (session)")
            st.json(st.session_state["last_prefix_payload"])

    else:
        st.info("Sélectionnez un pays et une subdivision pour afficher le formulaire de champs préfixés.")
