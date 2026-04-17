# driver_license_app.py
# Streamlit — Formulaire + génération d'un bloc AAMVA copiable (texte "brut")
# Usage: streamlit run driver_license_app.py

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — Générateur AAMVA", layout="wide")

# ---------------------------
# IIN mapping (US states + Canadian provinces)
# ---------------------------
IIN_US = {
    "Alabama":"636033","Alaska":"636059","Arizona":"636026","Arkansas":"636021","California":"636014",
    "Colorado":"636020","Connecticut":"636006","Delaware":"636011","Florida":"636010","Georgia":"636055",
    "Hawaii":"636047","Idaho":"636050","Illinois":"636035","Indiana":"636037","Iowa":"636018",
    "Kansas":"636022","Kentucky":"636046","Louisiana":"636007","Maine":"636041","Maryland":"636003",
    "Massachusetts":"636002","Michigan":"636032","Minnesota":"636038","Mississippi":"636051","Missouri":"636030",
    "Montana":"636008","Nebraska":"636054","Nevada":"636049","New Hampshire":"636039","New Jersey":"636036",
    "New Mexico":"636009","New York":"636001","North Carolina":"636004","North Dakota":"636034","Ohio":"636023",
    "Oklahoma":"636058","Oregon":"636029","Pennsylvania":"636025","Rhode Island":"636052","South Carolina":"636005",
    "South Dakota":"636042","Tennessee":"636053","Texas":"636015","Utah":"636040","Vermont":"636024",
    "Virginia":"636000","Washington":"636045","West Virginia":"636061","Wisconsin":"636031","Wyoming":"636060",
    "District of Columbia":"636043","Puerto Rico":"636017","Guam":"636019","U.S. Virgin Islands":"636016",
    "American Samoa":"636044","Northern Mariana Islands":"636056"
}

IIN_CA = {
    "Alberta":"636031","British Columbia":"636028","Manitoba":"636030","New Brunswick":"636027",
    "Newfoundland and Labrador":"636029","Northwest Territories":"636062","Nova Scotia":"636025",
    "Nunavut":"636063","Ontario":"636032","Prince Edward Island":"636026","Quebec":"636033",
    "Saskatchewan":"636034","Yukon":"636064"
}

# ---------------------------
# Données pour selects (extraits ; tu peux remplacer par listes complètes)
# ---------------------------
US_STATES = sorted(list(IIN_US.keys()))
CA_PROVINCES = sorted(list(IIN_CA.keys()))

# ---------------------------
# Champs préfixés (nom, aide)
# ---------------------------
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (ex: CAN, US)"),
    ("DCS", "Nom de famille"),
    ("DAC", "Prénom"),
    ("DBB", "Date de naissance (YYYYMMDD ou YYYY-MM-DD)"),
    ("DAG", "Adresse ligne 1"),
    ("DAI", "Ville"),
    ("DAJ", "Province/État (abréviation ou nom)"),
    ("DAK", "Code postal / ZIP"),
    ("DBD", "Date d'émission (YYYYMMDD)"),
    ("DBA", "Date d'expiration (YYYYMMDD)"),
    ("DBC", "Sexe (1 = Homme, 2 = Femme)"),
    ("DAU", "Taille (cm)"),
    ("DAY", "Couleur des yeux"),
    ("DCF", "Numéro de référence du document")
]

# ---------------------------
# UI : en-tête
# ---------------------------
st.markdown("<div style='text-align:center'><h1 style='margin:0;'>Driver License App — Générateur AAMVA</h1></div>", unsafe_allow_html=True)
st.write("Remplis les champs puis clique sur **Générer le bloc** pour obtenir le texte brut copiable.")

# ---------------------------
# Sélecteurs pays / subdivision (centrés côte à côte)
# ---------------------------
outer_l, center_col, outer_r = st.columns([1, 2, 1])
with center_col:
    c1, c2 = st.columns([1,1])
    with c1:
        country = st.selectbox("Pays", ["", "Canada", "United States"], key="country")
    with c2:
        if country == "United States":
            subdivision = st.selectbox("État", [""] + US_STATES, key="subdivision")
        elif country == "Canada":
            subdivision = st.selectbox("Province / Territoire", [""] + CA_PROVINCES, key="subdivision")
        else:
            subdivision = st.selectbox("Subdivision", [""], key="subdivision")

# ---------------------------
# Texte d'aide : s'affiche après sélection du pays et disparaît quand subdivision choisie
# ---------------------------
if country and not subdivision:
    st.info("Sélectionnez un pays et une subdivision pour afficher le formulaire.")

# ---------------------------
# Formulaire des champs préfixés (affiché si pays choisi)
# ---------------------------
if country:
    st.markdown("---")
    st.subheader("Champs préfixés (saisie)")
    # Préremplir DCG selon pays
    default_dcg = "US" if country == "United States" else "CAN" if country == "Canada" else ""
    # Afficher les champs en grille 2 colonnes
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1,1])
        # gauche
        key_left = f"field_{left[0]}"
        if left[0] == "DCG":
            cols[0].text_input(left[0], value=default_dcg, help=left[1], key=key_left)
        elif left[0] == "DAJ" and subdivision:
            cols[0].text_input(left[0], value=subdivision, help=left[1], key=key_left)
        else:
            cols[0].text_input(left[0], value="", help=left[1], placeholder=left[1], key=key_left)
        # droite
        if right:
            key_right = f"field_{right[0]}"
            if right[0] == "DCG":
                cols[1].text_input(right[0], value=default_dcg, help=right[1], key=key_right)
            elif right[0] == "DAJ" and subdivision:
                cols[1].text_input(right[0], value=subdivision, help=right[1], key=key_right)
            else:
                cols[1].text_input(right[0], value="", help=right[1], placeholder=right[1], key=key_right)

    st.markdown("---")

    # ---------------------------
    # Génération du bloc AAMVA (texte brut)
    # ---------------------------
    def get_iin_for_selection(country_name: str, subdivision_name: str) -> str:
        if country_name == "United States":
            # subdivision_name attendu comme "State" exact
            return IIN_US.get(subdivision_name, "000000")
        if country_name == "Canada":
            return IIN_CA.get(subdivision_name, "000000")
        return "000000"

    def normalize_date(value: str) -> str:
        # Simpliste : retire les tirets si présent (YYYY-MM-DD -> YYYYMMDD)
        return value.replace("-", "").strip()

    def build_aamva_block(fields: Dict[str, str], country_name: str, subdivision_name: str) -> str:
        # IIN
        iin = get_iin_for_selection(country_name, subdivision_name)
        # Fixed header parts (version etc.) — tu peux ajuster 08/00/01/ etc.
        # On construit un en-tête minimal similaire à ton exemple
        # Format: ANSI <IIN><version><design><subfilecount>DL<offset><length>DL
        # Pour simplifier on met des valeurs plausibles et on calcule la longueur approximative
        data_lines = []
        # DAQ (numéro de permis) si fourni
        if fields.get("DCF"):
            data_lines.append(f"DAQ{fields.get('DCF')}")
        # Ajouter tous les autres champs dans l'ordre demandé (utiliser les préfixes)
        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        # Mais on veut chaque ligne préfixée par le code (ex: DCSNICOLAS)
        for code in order:
            val = fields.get(code)
            if val:
                data_lines.append(f"{code}{val}")
        # Concaténation des données
        data_block = "".join(data_lines)
        # Calculs simples pour offset/length (approx) — ici on met des valeurs statiques raisonnables
        # offset: position où commence la section DL (on met 0041 comme dans ton exemple)
        offset = "0041"
        length = f"{len(data_block):04d}"  # longueur sur 4 chiffres
        header = f"ANSI {iin}08 00 01 DL{offset}{length}DL"
        # Retourner header + DL + data_block (avec un saut de ligne entre chaque code pour lisibilité)
        # L'utilisateur a demandé le "brut" comme dans l'exemple (chaque code sur une ligne)
        lines = [header]
        # Convert data_block into lines per code (we already have data_lines)
        lines.extend(data_lines)
        return "\n".join(lines)

    # Bouton de génération
    if st.button("Générer le bloc AAMVA copiable"):
        # Récupérer les valeurs des champs depuis session_state
        fields_values = {}
        for prefix, _ in PREFIX_FIELDS:
            fields_values[prefix] = st.session_state.get(f"field_{prefix}", "").strip()
        # Si DCF vide, essayer de prendre un champ alternatif (ex: DAQ) — ici on laisse tel quel
        aamva_text = build_aamva_block(fields_values, country, subdivision)
        st.session_state["last_aamva"] = aamva_text
        st.success("Bloc généré — copie ci‑dessous.")

    # Afficher le bloc copiable si présent
    if st.session_state.get("last_aamva"):
        st.markdown("### Bloc AAMVA (texte brut) — copiable")
        st.code(st.session_state["last_aamva"], language=None)
        # Bouton pour copier (Streamlit n'a pas un copy-to-clipboard natif, mais l'utilisateur peut copier depuis la zone)
        st.info("Sélectionne le texte ci‑dessous et copie‑le (Ctrl+C / Cmd+C).")

# ---------------------------
# Footer / notes
# ---------------------------
st.markdown("---")
st.caption("Note : Ce générateur produit un bloc texte pédagogique inspiré du format AAMVA. " 
           "Les en‑têtes (offset/length) sont simplifiés pour l'exemple. Utilise ce texte à des fins de test et d'apprentissage uniquement.")
