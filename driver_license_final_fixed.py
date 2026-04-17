# app_country_region.py
# Streamlit : menu pays + menu lié (États US ou Provinces/Territoires CAN)
# Usage : streamlit run app_country_region.py

import streamlit as st

st.set_page_config(page_title="Pays → États/Provinces liés", layout="centered")
st.title("Sélecteur Pays et États / Provinces liés")

# --- Données ---
US_STATES = {
    "Alabama": "AL","Alaska": "AK","Arizona": "AZ","Arkansas": "AR","Californie": "CA",
    "Colorado": "CO","Connecticut": "CT","Delaware": "DE","Floride": "FL","Géorgie": "GA",
    "Hawaï": "HI","Idaho": "ID","Illinois": "IL","Indiana": "IN","Iowa": "IA",
    "Kansas": "KS","Kentucky": "KY","Louisiane": "LA","Maine": "ME","Maryland": "MD",
    "Massachusetts": "MA","Michigan": "MI","Minnesota": "MN","Mississippi": "MS","Missouri": "MO",
    "Montana": "MT","Nebraska": "NE","Nevada": "NV","New Hampshire": "NH","New Jersey": "NJ",
    "Nouveau‑Mexique": "NM","New York": "NY","Caroline du Nord": "NC","Dakota du Nord": "ND",
    "Ohio": "OH","Oklahoma": "OK","Oregon": "OR","Pennsylvanie": "PA","Rhode Island": "RI",
    "Caroline du Sud": "SC","Dakota du Sud": "SD","Tennessee": "TN","Texas": "TX","Utah": "UT",
    "Vermont": "VT","Virginie": "VA","Washington": "WA","Virginie‑Occidentale": "WV",
    "Wisconsin": "WI","Wyoming": "WY"
}

CAN_PROVINCES_TERRITORIES = {
    "Alberta": "AB","Colombie‑Britannique": "BC","Île‑du‑Prince‑Édouard": "PE",
    "Manitoba": "MB","Nouveau‑Brunswick": "NB","Nouvelle‑Écosse": "NS",
    "Ontario": "ON","Québec": "QC","Saskatchewan": "SK","Terre‑Neuve‑et‑Labrador": "NL",
    "Yukon": "YT","Territoires du Nord‑Ouest": "NT","Nunavut": "NU"
}

# --- Menu pays ---
country_options = ["United States (US)", "Canada (CAN)"]
country = st.selectbox("Choisissez un pays :", country_options)

# --- Menu lié (dynamique) ---
if country.startswith("United"):
    title = "Sélectionnez un État (United States)"
    # Construire liste affichage "Nom (AB)"
    state_labels = [f"{name} ({abbr})" for name, abbr in sorted(US_STATES.items(), key=lambda x: x[0])]
    selected_state = st.selectbox(title, [""] + state_labels)
    if selected_state:
        # extraire abréviation
        abbr = selected_state.split("(")[-1].strip(")")
        st.markdown(f"**Sélection :** {selected_state}")
        st.markdown(f"**Abréviation USPS :** {abbr}")

elif country.startswith("Canada"):
    title = "Sélectionnez une Province / Territoire (Canada)"
    prov_labels = [f"{name} ({abbr})" for name, abbr in sorted(CAN_PROVINCES_TERRITORIES.items(), key=lambda x: x[0])]
    selected_prov = st.selectbox(title, [""] + prov_labels)
    if selected_prov:
        abbr = selected_prov.split("(")[-1].strip(")")
        st.markdown(f"**Sélection :** {selected_prov}")
        st.markdown(f"**Abréviation Canada Post :** {abbr}")

# --- Optionnel : comportement additionnel ---
st.caption("Règle d'or : les deux menus sont liés — le second affiche uniquement les subdivisions du pays sélectionné.")
