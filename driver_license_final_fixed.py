import streamlit as st
from typing import Dict, List, Tuple
import datetime

st.set_page_config(page_title="Pays / Subdivision — Images centrées", layout="wide")

# --- Données minimales (extrait) ---
US_STATES = {"California":"CA","New York":"NY","Texas":"TX"}  # remplacer par la liste complète
CAN_PROVINCES = {"Quebec":"QC","Ontario":"ON","British Columbia":"BC"}  # remplacer par la liste complète

PREFIX_FIELDS: List[Tuple[str,str]] = [
    ("DCG","Code du pays (ex: CAN)"),
    ("DCS","Nom de famille"),
    ("DAC","Prénom"),
    # ... autres champs ...
]

# --- Upload ou chargement des images ---
st.title("Formulaire préfixes — Pays / Subdivision")

st.markdown("**Téléversez deux images** (ou laisse vide pour ne pas afficher). La première sera l'en‑tête, la seconde s'affichera juste en dessous, toutes deux centrées.")

img1 = st.file_uploader("Image 1 — En‑tête (centrée)", type=["png","jpg","jpeg"], key="img1")
img2 = st.file_uploader("Image 2 — Sous‑en‑tête (centrée)", type=["png","jpg","jpeg"], key="img2")

# --- Affichage centré de la première image (en‑tête) ---
if img1:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.image(img1, use_column_width=True)

# --- Affichage centré de la deuxième image (juste en dessous) ---
if img2:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.image(img2, use_column_width=True)

st.markdown("---")

# --- Sélecteurs centrés (Pays et Subdivision côte à côte, centrés) ---
# On crée une zone centrée en utilisant une colonne centrale
outer_l, center, outer_r = st.columns([1, 2, 1])
with center:
    sel_a, sel_b = st.columns([1, 1])
    with sel_a:
        country = st.selectbox("Pays", ["United States (US)", "Canada (CAN)"], key="country")
    # construire options selon pays
    if country.startswith("United"):
        subdivision_label = "État"
        options = [f"{k} ({v})" for k,v in sorted(US_STATES.items())]
    else:
        subdivision_label = "Province / Territoire"
        options = [f"{k} ({v})" for k,v in sorted(CAN_PROVINCES.items())]
    with sel_b:
        subdivision = st.selectbox(subdivision_label, [""] + options, key="subdivision")

    # texte d'aide centré sous les selects
    st.markdown(
        "<div style='margin-top:8px;padding:10px;border-radius:6px;background:#eef6ff;color:#0f4c81;text-align:center;'>"
        "Sélectionnez un pays et une subdivision pour afficher le formulaire."
        "</div>",
        unsafe_allow_html=True
    )

# --- Formulaire (à droite ou en dessous selon ton layout) ---
if subdivision:
    default_country_code = "US" if country.startswith("United") else "CAN"
    st.markdown("---")
    st.subheader("Champs préfixés (texte libre)")
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1,1])
        key_left = f"field_{left[0]}"
        cols[0].text_input(left[0], value=(default_country_code if left[0]=="DCG" else ""), help=left[1], key=key_left)
        if right:
            key_right = f"field_{right[0]}"
            cols[1].text_input(right[0], value=(default_country_code if right[0]=="DCG" else ""), help=right[1], key=key_right)

    action_l, action_r = st.columns([1,1])
    with action_l:
        if st.button("Enregistrer (session)"):
            payload = {p[0]: st.session_state.get(f"field_{p[0]}", "") for p in PREFIX_FIELDS}
            payload["COUNTRY"] = country
            payload["SUBDIVISION"] = subdivision
            payload["TIMESTAMP"] = datetime.datetime.now().isoformat()
            st.session_state["last_prefix_payload"] = payload
            st.success("Données enregistrées en session.")
    with action_r:
        if st.button("Réinitialiser"):
            for p in PREFIX_FIELDS:
                st.session_state[f"field_{p[0]}"] = ""
            st.info("Champs réinitialisés.")
