# driver_license_app.py
# Streamlit — Générateur AAMVA strict (header sans espaces, DAQ modifiable, IIN selon juridiction)
# Sortie EXACTE attendue, commençant par "@\nANSI{IIN}{VER}{DES}DL{OFFSET}{LENGTH}DL..." sans espaces dans la séquence numérique.
# Usage: streamlit run driver_license_app.py

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — AAMVA Strict", layout="wide")

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
# Abréviations pour DAJ
# ---------------------------
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

# ---------------------------
# Données pour selects
# ---------------------------
US_STATES = sorted(list(IIN_US.keys()))
CA_PROVINCES = sorted(list(IIN_CA.keys()))

# ---------------------------
# Champs préfixés (nom, aide) — DAQ inclus et modifiable
# ---------------------------
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (CAN / US)"),
    ("DAQ", "Numéro de permis (modifiable)"),
    ("DCS", "Nom de famille"),
    ("DAC", "Prénom"),
    ("DBB", "Date de naissance (YYYYMMDD)"),
    ("DAG", "Adresse ligne 1"),
    ("DAI", "Ville"),
    ("DAJ", "Province/État (abréviation ou nom)"),
    ("DAK", "Code postal / ZIP"),
    ("DBD", "Date d'émission (YYYYMMDD)"),
    ("DBA", "Date d'expiration (YYYYMMDD)"),
    ("DBC", "Sexe (1=Homme,2=Femme)"),
    ("DAU", "Taille (cm)"),
    ("DAY", "Couleur des yeux"),
    ("DCE", "Classe(s)"),
    ("DCF", "Numéro de référence du document")
]

# ---------------------------
# Exemples modifiables
# ---------------------------
CANADA_EXAMPLE = {
    "DCG": "CAN",
    "DAQ": "N242094120896",
    "DCS": "NICOLAS",
    "DAC": "JEAN",
    "DBB": "19941208",
    "DAG": "1560 SHERBROOKE ST E",
    "DAI": "MONTREAL",
    "DAJ": "Quebec",
    "DAK": "H2L4M1",
    "DBD": "20230510",
    "DBA": "20310509",
    "DBC": "1",
    "DAU": "180",
    "DAY": "BRUN",
    "DCE": "5",
    "DCF": "PEJQ04N96"
}

USA_EXAMPLE = {
    "DCG": "US",
    "DAQ": "A123456789012",
    "DCS": "DOE",
    "DAC": "JOHN",
    "DBB": "19800115",
    "DAG": "123 MAIN ST",
    "DAI": "ANYTOWN",
    "DAJ": "California",
    "DAK": "90001",
    "DBD": "20220101",
    "DBA": "20260101",
    "DBC": "1",
    "DAU": "175",
    "DAY": "BRO",
    "DCE": "D",
    "DCF": "ABC1234567"
}

# ---------------------------
# Session state init
# ---------------------------
if "last_aamva" not in st.session_state:
    st.session_state["last_aamva"] = ""
if "prev_subdivision" not in st.session_state:
    st.session_state["prev_subdivision"] = ""

# Ensure all field keys exist
for prefix, _ in PREFIX_FIELDS:
    key = f"field_{prefix}"
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------------------------
# UI header
# ---------------------------
st.markdown("<div style='text-align:center'><h1 style='margin:0;'>Driver License App — AAMVA Strict</h1></div>", unsafe_allow_html=True)
st.write("Choisis le pays et la subdivision ; les exemples sont insérés automatiquement (modifiable). Le champ DAQ est éditable.")

# ---------------------------
# Country / Subdivision selects
# ---------------------------
cols = st.columns([1, 2, 1])
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

# ---------------------------
# Hint
# ---------------------------
if country and not subdivision:
    st.info("Sélectionne une subdivision pour préremplir DAJ automatiquement (modifiable).")

# ---------------------------
# Auto-fill examples (only fill empty fields)
# ---------------------------
if country == "Canada":
    for k, v in CANADA_EXAMPLE.items():
        key = f"field_{k}"
        if st.session_state.get(key, "") == "":
            st.session_state[key] = v
elif country == "United States":
    for k, v in USA_EXAMPLE.items():
        key = f"field_{k}"
        if st.session_state.get(key, "") == "":
            st.session_state[key] = v

# ---------------------------
# DAJ auto-update when subdivision chosen (use abbreviations for CA/US)
# ---------------------------
current_daj = st.session_state.get("field_DAJ", "").strip()
prev_sub = st.session_state.get("prev_subdivision", "")

if subdivision and subdivision != prev_sub:
    if country == "Canada":
        daj_val = CA_ABBR.get(subdivision, subdivision)
    elif country == "United States":
        daj_val = US_ABBR.get(subdivision, subdivision)
    else:
        daj_val = subdivision

    example_daj_can = CANADA_EXAMPLE.get("DAJ", "")
    example_daj_us = USA_EXAMPLE.get("DAJ", "")
    if current_daj == "" or current_daj == prev_sub or current_daj == example_daj_can or current_daj == example_daj_us:
        st.session_state["field_DAJ"] = daj_val

    st.session_state["prev_subdivision"] = subdivision
elif not subdivision:
    st.session_state["prev_subdivision"] = ""

# ---------------------------
# Form fields (grid) — DAQ is editable
# ---------------------------
if country:
    st.markdown("---")
    st.subheader("Champs préfixés (modifiable)")

    default_dcg = "CAN" if country == "Canada" else "US" if country == "United States" else ""

    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1,1])

        # left
        key_l = f"field_{left[0]}"
        if left[0] == "DCG":
            cols[0].text_input(left[0], value=st.session_state.get(key_l, default_dcg), key=key_l)
        elif left[0] == "DAJ":
            # show selectbox with current value
            current = st.session_state.get(key_l, "")
            options_display = [""] + ([st.session_state.get(key_l)] if st.session_state.get(key_l) else []) + [opt for opt in (CA_PROVINCES if country=="Canada" else US_STATES) if opt != st.session_state.get(key_l)]
            try:
                idx = options_display.index(current)
            except ValueError:
                idx = 0
            cols[0].selectbox(left[0], options=options_display, index=idx, key=key_l)
        else:
            cols[0].text_input(left[0], value=st.session_state.get(key_l, ""), key=key_l)

        # right
        if right:
            key_r = f"field_{right[0]}"
            if right[0] == "DCG":
                cols[1].text_input(right[0], value=st.session_state.get(key_r, default_dcg), key=key_r)
            elif right[0] == "DAJ":
                current_r = st.session_state.get(key_r, "")
                options_display_r = [""] + ([st.session_state.get(key_r)] if st.session_state.get(key_r) else []) + [opt for opt in (CA_PROVINCES if country=="Canada" else US_STATES) if opt != st.session_state.get(key_r)]
                try:
                    idx_r = options_display_r.index(current_r)
                except ValueError:
                    idx_r = 0
                cols[1].selectbox(right[0], options=options_display_r, index=idx_r, key=key_r)
            else:
                cols[1].text_input(right[0], value=st.session_state.get(key_r, ""), key=key_r)

    st.markdown("---")

    # ---------------------------
    # Build AAMVA block EXACT format
    # ---------------------------
    def get_iin(country_name: str, subdivision_name: str) -> str:
        if country_name == "United States":
            return IIN_US.get(subdivision_name, "000000")
        if country_name == "Canada":
            return IIN_CA.get(subdivision_name, "000000")
        return "000000"

    def normalize_date(v: str) -> str:
        return v.replace("-", "").strip()

    def build_strict_aamva(fields: Dict[str, str], country_name: str, subdivision_name: str) -> str:
        """
        Returns a single string starting with the literal sequence:
        @\nANSI{IIN}{VER}{DES}DL{OFFSET}{LENGTH}DL... followed by data lines separated by literal '\n'
        - No spaces inside the numeric sequence IIN+VER+DES (e.g. 636038080001)
        - OFFSET and LENGTH are zero-padded as in examples
        - LENGTH is computed on the real data block (with real newlines), then formatted as 4 digits
        """
        iin = get_iin(country_name, subdivision_name)
        version = "08"    # default; can be exposed to UI if needed
        design = "0001"   # default
        iin_sequence = f"{iin}{version}{design}"  # concatenated without spaces

        # Build data lines in the requested order
        data_lines = []

        # DAQ: use field_DAQ if present, else fallback to DCF
        daq = fields.get("DAQ", "") or fields.get("DCF", "")
        if daq:
            data_lines.append(f"DAQ{daq}")

        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        for code in order:
            val = fields.get(code, "")
            if val:
                if code in ("DBB","DBD","DBA"):
                    val = normalize_date(val)
                # remove internal newlines and trim
                val = str(val).replace("\n", " ").strip()
                data_lines.append(f"{code}{val}")

        # Real data block with real newlines (for length calculation)
        real_data_block = "\n".join(data_lines) + ("\n" if data_lines else "")
        length = f"{len(real_data_block):04d}"

        # OFFSET: default 0041 (kept as example); you can compute or expose if needed
        offset = "0041"

        # Header: "ANSI " + iin_sequence + "DL" + offset + length + "DL"
        header = f"ANSI {iin_sequence}DL{offset}{length}DL"

        # Data block for output must use literal '\n' sequences between lines and end with '\n'
        # i.e. "DCSNICOLAS\nDACJEAN\n..."
        data_block_literal = "\\n".join(data_lines) + "\\n" if data_lines else ""

        # Final string: start with literal "@\n"
        final = "@\\n" + header + "\\n" + data_block_literal
        return final

    # ---------------------------
    # Actions
    # ---------------------------
    if st.button("Générer le bloc AAMVA strict (séquences '\\n' littérales)"):
        fields_values = {}
        for prefix, _ in PREFIX_FIELDS:
            fields_values[prefix] = st.session_state.get(f"field_{prefix}", "").strip()
        aamva = build_strict_aamva(fields_values, country, subdivision)
        st.session_state["last_aamva"] = aamva
        st.success("Bloc généré — copie ci‑dessous (séquences '\\n' littérales).")

    # Save / reset
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

    # Display result
    if st.session_state.get("last_aamva"):
        st.markdown("### Bloc AAMVA (texte brut) — format strict")
        st.code(st.session_state["last_aamva"], language=None)
        st.info("Copie le texte ci‑dessous (Ctrl+C / Cmd+C).")

# Footer
st.markdown("---")
st.caption("Sortie strictement formatée. L'IIN est choisi selon la juridiction; OFFSET par défaut = 0041; VERSION/DESIGN = 08/0001 (modifiable dans le code si nécessaire).")
