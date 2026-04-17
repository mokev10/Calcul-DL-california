# driver_license_app.py
# Streamlit — Générateur AAMVA strict avec styles CSS pour indications (effet survol)
# - Aucun préremplissage automatique ni boutons d'exemple
# - DAQ modifiable et utilisé en priorité
# - DAJ lié automatiquement à la subdivision (abréviations CA/US) sans écraser saisies manuelles
# - En-tête numérique IIN+VER+DES concaténé sans espaces
# - Sortie commence par "@\n" et utilise les séquences littérales "\n"
# - Petites indications affichées à droite de chaque case avec effet CSS au survol (curseur, ombre, transition)

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — AAMVA Strict", layout="wide")

# ---------------------------
# CSS personnalisé pour les indications (help-bubble)
# ---------------------------
st.markdown(
    """
    <style>
    /* Conteneur global pour les petites indications */
    .help-bubble {
        display: inline-block;
        font-size: 12px;
        color: #0b3d91;
        background: rgba(11,61,145,0.06);
        padding: 6px 8px;
        border-radius: 6px;
        border: 1px solid rgba(11,61,145,0.12);
        transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 220px;
        vertical-align: middle;
        cursor: default;
    }

    /* Effet au survol : curseur pointeur, légère élévation et changement de fond */
    .help-bubble:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 6px 18px rgba(11,61,145,0.12);
        background: rgba(11,61,145,0.12);
        cursor: pointer;
    }

    /* Variante compacte pour écrans étroits */
    @media (max-width: 640px) {
        .help-bubble {
            font-size: 11px;
            max-width: 140px;
            padding: 5px 6px;
        }
    }

    /* Style pour le label des champs (pour cohérence visuelle) */
    .field-label {
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

# Abréviations
CA_ABBR = {
    "Alberta":"AB","British Columbia":"BC","Manitoba":"MB","New Brunswick":"NB",
    "Newfoundland and Labrador":"NL","Northwest Territories":"NT","Nova Scotia":"NS",
    "Nunavut":"NU","Ontario":"ON","Prince Edward Island":"PE","Quebec":"QC",
    "Saskatchewan":"SK","Yukon":"YT"
}
US_ABBR = {
    "Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA",
    "Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA",
    "Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA",
    "Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD",
    "Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO",
    "Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ",
    "New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH",
    "Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC",
    "South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT",
    "Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY",
    "District of Columbia":"DC","Puerto Rico":"PR","Guam":"GU","U.S. Virgin Islands":"VI",
    "American Samoa":"AS","Northern Mariana Islands":"MP"
}

US_STATES = sorted(list(IIN_US.keys()))
CA_PROVINCES = sorted(list(IIN_CA.keys()))

# Champs (DAQ inclus) avec aides textuelles
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG","Code du pays (CAN/US) — ex: CAN ou US"),
    ("DAQ","Numéro de permis (modifiable) — ex: N242094120896"),
    ("DCS","Nom de famille — majuscules recommandées"),
    ("DAC","Prénom — majuscules recommandées"),
    ("DBB","Date de naissance — format YYYYMMDD"),
    ("DAG","Adresse ligne 1 — sans accents si possible"),
    ("DAI","Ville — majuscules recommandées"),
    ("DAJ","Province/État — s'auto-remplit selon la subdivision"),
    ("DAK","Code postal / ZIP — ex: H2L4M1 ou 90001"),
    ("DBD","Date d'émission — format YYYYMMDD"),
    ("DBA","Date d'expiration — format YYYYMMDD"),
    ("DBC","Sexe — 1 = Homme, 2 = Femme"),
    ("DAU","Taille (cm) — ex: 180"),
    ("DAY","Couleur des yeux — ex: BRUN"),
    ("DCE","Classe(s) — ex: 5"),
    ("DCF","Numéro de référence du document — ex: PEJQ04N96")
]

# Session init
if "prev_subdivision" not in st.session_state:
    st.session_state["prev_subdivision"] = ""
if "last_aamva" not in st.session_state:
    st.session_state["last_aamva"] = ""

# Ensure fields exist
for prefix, _ in PREFIX_FIELDS:
    key = f"field_{prefix}"
    if key not in st.session_state:
        st.session_state[key] = ""

# UI header
st.markdown("<div style='text-align:center'><h1 style='margin:0;'>Driver License App — AAMVA Strict</h1></div>", unsafe_allow_html=True)
st.write("Remplis les champs manuellement. Les petites indications ont un effet visuel au survol du curseur.")

# Country / subdivision
cols = st.columns([1,2,1])
with cols[1]:
    c1, c2 = st.columns([1,1])
    with c1:
        country = st.selectbox("Pays", ["", "Canada", "United States"], key="country")
    with c2:
        if country == "Canada":
            subdivision = st.selectbox("Province / Territoire", [""] + CA_PROVINCES, key="subdivision")
        elif country == "United States":
            subdivision = st.selectbox("État", [""] + US_STATES, key="subdivision")
        else:
            subdivision = st.selectbox("Subdivision", [""], key="subdivision")

# Hint
if country and not subdivision:
    st.info("Choisis une subdivision pour préremplir DAJ automatiquement (modifiable).")

# DAJ auto-update (abréviations) — ne pas écraser saisies manuelles
current_daj = st.session_state.get("field_DAJ","").strip()
prev_sub = st.session_state.get("prev_subdivision","")
if subdivision and subdivision != prev_sub:
    if country == "Canada":
        daj_val = CA_ABBR.get(subdivision, subdivision)
    elif country == "United States":
        daj_val = US_ABBR.get(subdivision, subdivision)
    else:
        daj_val = subdivision
    if current_daj == "" or current_daj == prev_sub:
        st.session_state["field_DAJ"] = daj_val
    st.session_state["prev_subdivision"] = subdivision
elif not subdivision:
    st.session_state["prev_subdivision"] = ""

# Form fields (grid) — affichage label / input / aide (avec style)
if country:
    st.markdown("---")
    st.subheader("Champs préfixés (saisis manuellement)")

    default_dcg = "CAN" if country=="Canada" else "US" if country=="United States" else ""

    # Pour chaque champ : label (col 0), input (col 1), aide stylée (col 2)
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None

        # Six colonnes : label/input/help pour gauche ; label/input/help pour droite
        row_cols = st.columns([1, 3, 2, 1, 3, 2])

        # LEFT field
        label_l = left[0]
        help_l = left[1]
        key_l = f"field_{label_l}"
        row_cols[0].markdown(f"<div class='field-label'>{label_l}</div>", unsafe_allow_html=True)
        if label_l == "DCG":
            row_cols[1].text_input(label_l, value=st.session_state.get(key_l, default_dcg), key=key_l)
        elif label_l == "DAJ":
            current = st.session_state.get(key_l,"")
            options_display = [""] + ([current] if current else []) + [opt for opt in (CA_PROVINCES if country=="Canada" else US_STATES) if opt != current]
            try:
                idx = options_display.index(current)
            except ValueError:
                idx = 0
            row_cols[1].selectbox(label_l, options=options_display, index=idx, key=key_l)
        elif label_l == "DBC":
            row_cols[1].selectbox(label_l, options=["", "1 - Homme", "2 - Femme"], key=key_l)
        else:
            row_cols[1].text_input(label_l, value=st.session_state.get(key_l,""), key=key_l)
        # help bubble (HTML span with class)
        safe_help_l = help_l.replace("'", "&#39;").replace('"', "&quot;")
        row_cols[2].markdown(f"<span class='help-bubble' title='{safe_help_l}'>{safe_help_l}</span>", unsafe_allow_html=True)

        # RIGHT field (si présent)
        if right:
            label_r = right[0]
            help_r = right[1]
            key_r = f"field_{label_r}"
            row_cols[3].markdown(f"<div class='field-label'>{label_r}</div>", unsafe_allow_html=True)
            if label_r == "DCG":
                row_cols[4].text_input(label_r, value=st.session_state.get(key_r, default_dcg), key=key_r)
            elif label_r == "DAJ":
                current_r = st.session_state.get(key_r,"")
                options_display_r = [""] + ([current_r] if current_r else []) + [opt for opt in (CA_PROVINCES if country=="Canada" else US_STATES) if opt != current_r]
                try:
                    idx_r = options_display_r.index(current_r)
                except ValueError:
                    idx_r = 0
                row_cols[4].selectbox(label_r, options=options_display_r, index=idx_r, key=key_r)
            elif label_r == "DBC":
                row_cols[4].selectbox(label_r, options=["", "1 - Homme", "2 - Femme"], key=key_r)
            else:
                row_cols[4].text_input(label_r, value=st.session_state.get(key_r,""), key=key_r)
            safe_help_r = help_r.replace("'", "&#39;").replace('"', "&quot;")
            row_cols[5].markdown(f"<span class='help-bubble' title='{safe_help_r}'>{safe_help_r}</span>", unsafe_allow_html=True)

    st.markdown("---")

    # Build strict AAMVA block (uses only values currently in the form)
    def get_iin(country_name: str, subdivision_name: str) -> str:
        if country_name == "United States":
            return IIN_US.get(subdivision_name, "000000")
        if country_name == "Canada":
            return IIN_CA.get(subdivision_name, "000000")
        return "000000"

    def normalize_date(v: str) -> str:
        return v.replace("-","").strip()

    def build_strict_aamva(fields: Dict[str,str], country_name: str, subdivision_name: str) -> str:
        # IIN sequence (no spaces) + version + design
        iin = get_iin(country_name, subdivision_name)
        version = "08"
        design = "0001"
        iin_sequence = f"{iin}{version}{design}"  # e.g. 636038080001

        # Build data lines from current fields (DAQ used in priority)
        data_lines = []
        daq = fields.get("DAQ","") or fields.get("DCF","")
        if daq:
            data_lines.append(f"DAQ{daq}")

        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        for code in order:
            val = fields.get(code,"")
            if val:
                if code in ("DBB","DBD","DBA"):
                    val = normalize_date(val)
                val = str(val).replace("\n"," ").strip()
                data_lines.append(f"{code}{val}")

        # Real data block for length calculation (with real newlines)
        real_data_block = "\n".join(data_lines) + ("\n" if data_lines else "")
        length = f"{len(real_data_block):04d}"  # 4 digits

        offset = "0041"  # default; adjust if you implement exact offset calculation

        header = f"ANSI {iin_sequence}DL{offset}{length}DL"  # note: no spaces inside numeric sequence

        # Data block for output uses literal '\n' sequences
        data_block_literal = "\\n".join(data_lines) + "\\n" if data_lines else ""

        final = "@\\n" + header + "\\n" + data_block_literal
        return final

    # Actions
    if st.button("Générer le bloc AAMVA strict (séquences '\\n' littérales)"):
        fields_values = {p[0]: st.session_state.get(f"field_{p[0]}", "").strip() for p in PREFIX_FIELDS}
        aamva = build_strict_aamva(fields_values, country, subdivision)
        st.session_state["last_aamva"] = aamva
        st.success("Bloc généré — copie ci‑dessous (séquences '\\n' littérales).")

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("Enregistrer (session)"):
            payload = {p[0]: st.session_state.get(f"field_{p[0]}", "") for p in PREFIX_FIELDS}
            payload["COUNTRY"] = country
            payload["SUBDIVISION"] = subdivision
            payload["TIMESTAMP"] = datetime.datetime.now().isoformat()
            st.session_state["last_prefix_payload"] = payload
            st.success("Données enregistrées en session.")
    with c2:
        if st.button("Réinitialiser"):
            for p in PREFIX_FIELDS:
                st.session_state[f"field_{p[0]}"] = ""
            st.info("Champs réinitialisés.")

    # Display result (exactly what was generated)
    if st.session_state.get("last_aamva"):
        st.markdown("### Bloc AAMVA (texte brut) — format strict")
        st.code(st.session_state["last_aamva"], language=None)
        st.info("Copie le texte ci‑dessous (Ctrl+C / Cmd+C).")

# Footer
st.markdown("---")
st.caption("Remarque : ce générateur produit le bloc à partir des valeurs saisies. OFFSET par défaut = 0041; VERSION/DESIGN = 08/0001. Si tu veux que j'implémente le calcul exact de l'OFFSET selon la norme AAMVA, je peux l'ajouter.")
