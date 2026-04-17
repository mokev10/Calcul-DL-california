# driver_license_app.py
# Streamlit — Version finale demandée
# - En-tête centré
# - Deux selects côte à côte, centrés et de même taille (Pays / Subdivision)
# - Texte d'aide affiché **après** la sélection du pays et **masqué** dès que la subdivision ou le formulaire suivant apparaît
# - Formulaire complet des préfixes (DCG, DCS, DAC, ...) affiché après sélection de la subdivision
# - Comportement réactif : si l'utilisateur change de pays, le texte d'aide réapparaît

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App", layout="wide")

# ---------------------------
# Données : États US et Provinces CAN
# ---------------------------
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

# ---------------------------
# Champs préfixés (nom, aide)
# ---------------------------
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

# ---------------------------
# Session state initialisation
# ---------------------------
if "show_hint" not in st.session_state:
    st.session_state["show_hint"] = False

if "prev_country" not in st.session_state:
    st.session_state["prev_country"] = ""

# ---------------------------
# En-tête centré
# ---------------------------
st.markdown(
    "<div style='text-align:center; margin-top:6px;'>"
    "<h1 style='margin:0;'>Formulaire préfixes — Pays / Subdivision</h1>"
    "<p style='color:gray; margin:4px 0 12px 0;'>Usage pédagogique — remplissez les champs après sélection</p>"
    "</div>",
    unsafe_allow_html=True
)

# ---------------------------
# Zone centrale : selects centrés côte à côte (mêmes tailles)
# ---------------------------
outer_l, center_col, outer_r = st.columns([1, 2, 1])
with center_col:
    sel_left, sel_right = st.columns([1, 1])
    with sel_left:
        country = st.selectbox("Pays", ["", "United States (US)", "Canada (CAN)"], key="country_main")
    # Si le pays change par rapport à la session, réactiver le hint
    if country != st.session_state.get("prev_country", ""):
        # si l'utilisateur a choisi un pays non vide, on affiche le hint
        st.session_state["show_hint"] = bool(country)
        st.session_state["prev_country"] = country

    # Construire options selon pays
    if country.startswith("United"):
        subdivision_label = "État"
        options = [f"{name} ({abbr})" for name, abbr in sorted(US_STATES.items(), key=lambda x: x[0])]
    elif country.startswith("Canada") or country == "Canada (CAN)":
        subdivision_label = "Province / Territoire"
        options = [f"{name} ({abbr})" for name, abbr in sorted(CAN_PROVINCES_TERRITORIES.items(), key=lambda x: x[0])]
    else:
        subdivision_label = "Subdivision"
        options = []

    with sel_right:
        subdivision = st.selectbox(subdivision_label, [""] + options, key="subdivision_main")

    # Afficher le hint uniquement si show_hint True ET qu'aucune subdivision n'est encore choisie
    if st.session_state["show_hint"] and not subdivision:
        st.markdown(
            "<div style='margin-top:10px;padding:10px;border-radius:6px;background:#eef6ff;color:#0f4c81;text-align:center;'>"
            "Sélectionnez un pays et une subdivision pour afficher le formulaire."
            "</div>",
            unsafe_allow_html=True
        )

# ---------------------------
# Logique : masquer le hint dès que la subdivision est choisie (ou quand le formulaire s'affiche)
# ---------------------------
if subdivision:
    st.session_state["show_hint"] = False

# ---------------------------
# Formulaire complet (affiché si subdivision choisie)
# ---------------------------
if subdivision:
    default_country_code = "US" if country.startswith("United") else "CAN"

    st.markdown("---")
    st.subheader("Champs préfixés (saisie)")

    # Présentation en grille 2 colonnes ; utiliser selectboxes pour les champs qui s'y prêtent
    # Préparer la liste d'options pour DAJ (Province/État) afin de proposer la subdivision sélectionnée en priorité
    daj_options = [subdivision] + [opt for opt in options if opt != subdivision]

    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1, 1])

        # Champ gauche
        key_left = f"field_{left[0]}"
        if left[0] == "DCG":
            cols[0].text_input(left[0], value=default_country_code, help=left[1], key=key_left)
        elif left[0] == "DAJ":
            cols[0].selectbox(left[0], options=daj_options, index=0, help=left[1], key=key_left)
        elif left[0] == "DBC":
            cols[0].selectbox(left[0], options=["", "1 - Homme", "2 - Femme"], help=left[1], key=key_left)
        else:
            cols[0].text_input(left[0], value="", help=left[1], placeholder=left[1], key=key_left)

        # Champ droit
        if right:
            key_right = f"field_{right[0]}"
            if right[0] == "DCG":
                cols[1].text_input(right[0], value=default_country_code, help=right[1], key=key_right)
            elif right[0] == "DAJ":
                cols[1].selectbox(right[0], options=daj_options, index=0, help=right[1], key=key_right)
            elif right[0] == "DBC":
                cols[1].selectbox(right[0], options=["", "1 - Homme", "2 - Femme"], help=right[1], key=key_right)
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
