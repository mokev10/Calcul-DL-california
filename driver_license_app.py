# driver_license_app.py
# Streamlit — Générateur AAMVA (texte brut) avec DAJ lié à la subdivision
# Correction : en-tête ANSI sans espaces dans la séquence IIN+version+design (ex: "636033080001")
# Usage: streamlit run driver_license_app.py

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — AAMVA Brut", layout="wide")

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
# Abréviations Canada pour DAJ
# ---------------------------
CA_ABBR = {
    "Alberta":"AB","British Columbia":"BC","Manitoba":"MB","New Brunswick":"NB",
    "Newfoundland and Labrador":"NL","Northwest Territories":"NT","Nova Scotia":"NS",
    "Nunavut":"NU","Ontario":"ON","Prince Edward Island":"PE","Quebec":"QC",
    "Saskatchewan":"SK","Yukon":"YT"
}

# ---------------------------
# Données pour selects
# ---------------------------
US_STATES = sorted(list(IIN_US.keys()))
CA_PROVINCES = sorted(list(IIN_CA.keys()))

# ---------------------------
# Champs préfixés (nom, aide)
# ---------------------------
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (ex: CAN pour Canada, US pour United States)"),
    ("DCS", "Nom de famille (ex: NICOLAS)"),
    ("DAC", "Prénom (ex: JEAN)"),
    ("DBB", "Date de naissance (YYYY-MM-DD ou YYYYMMDD)"),
    ("DAG", "Adresse ligne 1 (ex: 1560 SHERBROOKE ST E)"),
    ("DAI", "Ville (ex: MONTREAL)"),
    ("DAJ", "Province/État (ex: QC ou California)"),
    ("DAK", "Code postal / ZIP (ex: H2L4M1 ou 90001)"),
    ("DBD", "Date d'émission (YYYY-MM-DD ou YYYYMMDD)"),
    ("DBA", "Date d'expiration (YYYY-MM-DD ou YYYYMMDD)"),
    ("DBC", "Sexe (1 = Homme, 2 = Femme)"),
    ("DAU", "Taille (ex: 180 cm)"),
    ("DAY", "Couleur des yeux (ex: BRUN)"),
    ("DCF", "Numéro de référence du document (ex: PEJQ04N96)")
]

# ---------------------------
# Exemple modifiable pour Canada (préremplissage)
# ---------------------------
CANADA_EXAMPLE = {
    "DCG": "CAN",
    "DCS": "NICOLAS",
    "DAC": "JEAN",
    "DBB": "19941208",
    "DAG": "1560 SHERBROOKE ST E",
    "DAI": "MONTREAL",
    "DAJ": "Quebec",          # valeur d'exemple (sera convertie en QC si country==Canada)
    "DAK": "H2L4M1",
    "DBD": "20230510",
    "DBA": "20310509",
    "DBC": "1",
    "DAU": "180",
    "DAY": "BRUN",
    "DCF": "PEJQ04N96"
}

# ---------------------------
# Session state initialisation
# ---------------------------
if "show_hint" not in st.session_state:
    st.session_state["show_hint"] = False
if "prev_country" not in st.session_state:
    st.session_state["prev_country"] = ""
if "prev_subdivision" not in st.session_state:
    st.session_state["prev_subdivision"] = ""
if "last_aamva" not in st.session_state:
    st.session_state["last_aamva"] = ""

# Ensure all field keys exist in session_state
for prefix, _ in PREFIX_FIELDS:
    key = f"field_{prefix}"
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------------------------
# En-tête centré
# ---------------------------
st.markdown(
    "<div style='text-align:center; margin-top:6px;'>"
    "<h1 style='margin:0;'>Formulaire préfixes — Pays / Subdivision</h1>"
    "<p style='color:gray; margin:4px 0 12px 0;'>Usage pédagogique — exemple automatique pour Canada (modifiable)</p>"
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
        country = st.selectbox("Pays", ["", "Canada", "United States"], key="country_main")
    # Si le pays change, activer le hint (si pays non vide) et réinitialiser prev_subdivision
    if country != st.session_state.get("prev_country", ""):
        st.session_state["show_hint"] = bool(country)
        st.session_state["prev_country"] = country
        st.session_state["prev_subdivision"] = ""

    # Construire options selon pays
    if country == "United States":
        subdivision_label = "État"
        options = [f"{name}" for name in US_STATES]
    elif country == "Canada":
        subdivision_label = "Province / Territoire"
        options = [f"{name}" for name in CA_PROVINCES]
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
# Masquer le hint dès que la subdivision est choisie
# ---------------------------
if subdivision:
    st.session_state["show_hint"] = False

# ---------------------------
# Préremplissage automatique d'exemple pour Canada
# - Ne remplit que les champs vides pour ne pas écraser les saisies de l'utilisateur.
# ---------------------------
if country == "Canada":
    for code, example_val in CANADA_EXAMPLE.items():
        key = f"field_{code}"
        if st.session_state.get(key, "") == "":
            st.session_state[key] = example_val

# ---------------------------
# Liaison DAJ <-> subdivision (DAJ mis automatiquement selon la sélection)
# - DAJ prend l'abréviation pour le Canada (QC, ON, ...), sinon le nom de l'état pour US.
# - On n'écrase pas DAJ si l'utilisateur a saisi manuellement une valeur différente.
# ---------------------------
current_daj = st.session_state.get("field_DAJ", "").strip()
prev_sub = st.session_state.get("prev_subdivision", "")

if subdivision and subdivision != prev_sub:
    if country == "Canada":
        daj_value = CA_ABBR.get(subdivision, subdivision)
    else:
        daj_value = subdivision
    example_daj = CANADA_EXAMPLE.get("DAJ", "")
    if current_daj == "" or current_daj == prev_sub or current_daj == example_daj:
        st.session_state["field_DAJ"] = daj_value
    st.session_state["prev_subdivision"] = subdivision
elif not subdivision:
    st.session_state["prev_subdivision"] = ""

# ---------------------------
# Formulaire complet (affiché si pays choisi)
# ---------------------------
if country:
    st.markdown("---")
    st.subheader("Champs préfixés (saisie)")

    default_dcg = "US" if country == "United States" else "CAN" if country == "Canada" else ""

    # Préparer DAJ options (priorité à la subdivision sélectionnée)
    daj_options = []
    if subdivision:
        if country == "Canada":
            abbr = CA_ABBR.get(subdivision, "")
            first = abbr if abbr else subdivision
        else:
            first = subdivision
        daj_options = [first] + [opt for opt in options if opt != subdivision]
    else:
        daj_options = options

    # Afficher champs en grille 2 colonnes
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1, 1])

        # Champ gauche
        key_left = f"field_{left[0]}"
        if left[0] == "DCG":
            cols[0].text_input(left[0], value=st.session_state.get(key_left, default_dcg), help=left[1], key=key_left)
        elif left[0] == "DAJ":
            current_val = st.session_state.get(key_left, "")
            display_options = [""] + daj_options
            try:
                idx = display_options.index(current_val)
            except ValueError:
                idx = 0
            cols[0].selectbox(left[0], options=display_options, index=idx, help=left[1], key=key_left)
        elif left[0] == "DBC":
            cols[0].selectbox(left[0], options=["", "1 - Homme", "2 - Femme"], help=left[1], key=key_left)
        else:
            cols[0].text_input(left[0], value=st.session_state.get(key_left, ""), help=left[1], placeholder=left[1], key=key_left)

        # Champ droit
        if right:
            key_right = f"field_{right[0]}"
            if right[0] == "DCG":
                cols[1].text_input(right[0], value=st.session_state.get(key_right, default_dcg), help=right[1], key=key_right)
            elif right[0] == "DAJ":
                current_val_r = st.session_state.get(key_right, "")
                display_options_r = [""] + daj_options
                try:
                    idx_r = display_options_r.index(current_val_r)
                except ValueError:
                    idx_r = 0
                cols[1].selectbox(right[0], options=display_options_r, index=idx_r, help=right[1], key=key_right)
            elif right[0] == "DBC":
                cols[1].selectbox(right[0], options=["", "1 - Homme", "2 - Femme"], help=right[1], key=key_right)
            else:
                cols[1].text_input(right[0], value=st.session_state.get(key_right, ""), help=right[1], placeholder=right[1], key=key_right)

    st.markdown("---")

    # ---------------------------
    # Fonctions utilitaires pour la génération AAMVA (format avec "\n" littéraux)
    # Correction : en-tête construit sans espaces dans la séquence IIN+version+design.
    # ---------------------------
    def get_iin_for_selection(country_name: str, subdivision_name: str) -> str:
        if country_name == "United States":
            return IIN_US.get(subdivision_name, "000000")
        if country_name == "Canada":
            return IIN_CA.get(subdivision_name, "000000")
        return "000000"

    def normalize_date(value: str) -> str:
        return value.replace("-", "").strip()

    def build_aamva_block_with_escapes(fields: Dict[str, str], country_name: str, subdivision_name: str) -> str:
        """
        Retourne une chaîne où chaque saut de ligne est représenté par la séquence littérale '\n'.
        La chaîne commence par "@\n" (séquence littérale) puis l'en-tête ANSI et les lignes de données.
        IMPORTANT: la séquence numérique IIN+version+design est concaténée sans espaces,
        par exemple: "636033080001" (IIN=636033, version=08, design=0001).
        """
        iin = get_iin_for_selection(country_name, subdivision_name)
        data_lines = []

        # Si DCF (numéro de référence) présent, l'utiliser comme DAQ (numéro de permis)
        if fields.get("DCF"):
            data_lines.append(f"DAQ{fields.get('DCF')}")

        # Ordre des champs pour sortie
        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        for code in order:
            val = fields.get(code)
            if val:
                if code in ("DBB","DBD","DBA"):
                    val = normalize_date(val)
                # Supprimer retours à la ligne internes et trim
                val = str(val).replace("\n", " ").strip()
                data_lines.append(f"{code}{val}")

        # Construire data_block avec séquences littérales '\n' entre lignes et terminer par '\n'
        data_block_literal = "\\n".join(data_lines) + "\\n" if data_lines else ""

        # Calcul simple d'offset/length (valeurs plausibles pour l'exemple)
        offset = "0041"
        # length = nombre de caractères du bloc de données réel (avec retours réels)
        real_data_block = "\n".join(data_lines) + "\n" if data_lines else ""
        length = f"{len(real_data_block):04d}"

        # En-tête : **un espace** après "ANSI", puis la séquence IIN+version+design **sans espaces**
        # version = "08", design = "0001" (exemple), concaténés directement après l'IIN
        version = "08"
        design = "0001"
        iin_sequence = f"{iin}{version}{design}"  # ex: "636033080001" (aucun espace)
        header = f"ANSI {iin_sequence}DL{offset}{length}DL"

        # Construire la sortie finale avec séquences littérales '\n'
        final = "@\\n" + header + "\\n" + data_block_literal
        return final

    # ---------------------------
    # Actions : Générer / Enregistrer / Réinitialiser
    # ---------------------------
    if st.button("Générer le bloc AAMVA copiable (avec '\\n' littéraux)"):
        fields_values = {}
        for prefix, _ in PREFIX_FIELDS:
            fields_values[prefix] = st.session_state.get(f"field_{prefix}", "").strip()
        aamva_text = build_aamva_block_with_escapes(fields_values, country, subdivision)
        st.session_state["last_aamva"] = aamva_text
        st.success("Bloc généré — copie ci‑dessous (les séquences '\\n' représentent des retours à la ligne).")

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
            st.session_state["field_DCG"] = default_dcg
            st.info("Champs réinitialisés.")

    # Afficher le bloc copiable si présent (sans interpréter les '\n')
    if st.session_state.get("last_aamva"):
        st.markdown("### Bloc AAMVA (texte brut) — copiable (séquences '\\n' littérales)")
        st.code(st.session_state["last_aamva"], language=None)
        st.info("Sélectionne le texte ci‑dessous et copie‑le (Ctrl+C / Cmd+C).")

# ---------------------------
# Footer / notes
# ---------------------------
st.markdown("---")
st.caption(
    "Note : La sortie contient des séquences littérales '\\n' pour représenter les retours à la ligne. "
    "L'en-tête ANSI utilise une séquence IIN+version+design concaténée sans espaces (ex: 636033080001). "
    "Utilise ce texte à des fins de test et d'apprentissage uniquement."
)
