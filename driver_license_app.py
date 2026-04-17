# driver_license_app.py
# Streamlit — Générateur AAMVA final (zone flottante centrée supprimée)
# - Aucun préremplissage automatique
# - DAQ modifiable et utilisé en priorité
# - DAJ s'auto-remplit selon la subdivision (abréviations CA/US) sans écraser saisies manuelles
# - Infobulles (tooltips) STRICTEMENT au hover (desktop) et au focus (accessibilité)
# - En-tête ANSI construit sans espaces dans la séquence IIN+VERSION+DESIGN
# - Sortie littérale commence par "@\n" puis header puis lignes séparées par la séquence littérale "\n"
# Usage: streamlit run driver_license_app.py

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — AAMVA Final", layout="wide")

# ---------------------------
# CSS (tooltips hover-only, design moderne)
# ---------------------------
st.markdown(
    """
    <style>
    :root{
      --bg:#071025;
      --card:#0b1220;
      --muted:#9aa7c7;
      --accent:#4f8cff;
      --tooltip-bg: rgba(18,24,40,0.98);
      --tooltip-color:#eaf0ff;
      --radius:12px;
      --ease:cubic-bezier(.2,.9,.3,1);
    }
    body { background: linear-gradient(180deg,#071025 0%, #071a2b 60%); color: #eaf0ff; font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial; }
    .app-wrap { max-width:1100px; margin:28px auto; padding:22px; border-radius:var(--radius); background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); box-shadow: 0 12px 40px rgba(2,6,23,0.6); border: 1px solid rgba(255,255,255,0.03); }
    .header { display:flex; gap:14px; align-items:center; margin-bottom:12px; }
    .logo { width:48px; height:48px; border-radius:10px; background: linear-gradient(135deg,var(--accent),#2bb0ff); display:flex; align-items:center; justify-content:center; font-weight:700; color:white; font-size:18px; box-shadow: 0 8px 24px rgba(79,140,255,0.14); }
    .title { margin:0; font-size:18px; }
    .sub { margin:2px 0 0 0; color:var(--muted); font-size:13px; }

    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:18px; margin-top:18px; }
    .card { background: var(--card); border-radius:12px; padding:14px; border:1px solid rgba(255,255,255,0.02); }

    .field-row { display:flex; gap:12px; align-items:center; margin-bottom:12px; }
    .field-main { flex:1; }
    label.field-label { display:block; font-size:12px; color:var(--muted); margin-bottom:6px; font-weight:600; }

    input[type="text"], select {
      width:100%;
      padding:10px 12px;
      border-radius:10px;
      border:1px solid rgba(255,255,255,0.04);
      background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00));
      color: #eaf0ff;
      outline:none;
      transition: box-shadow .18s var(--ease), transform .12s var(--ease), border-color .12s var(--ease);
      font-size:14px;
    }
    input[type="text"]:focus, select:focus{
      box-shadow: 0 8px 26px rgba(79,140,255,0.12);
      border-color: rgba(79,140,255,0.6);
      transform: translateY(-1px);
    }

    /* Help bubble (hover-only) */
    .help-bubble {
      display:inline-flex;
      align-items:center;
      justify-content:center;
      width:36px;
      height:36px;
      border-radius:10px;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border:1px solid rgba(255,255,255,0.03);
      color:var(--muted);
      font-weight:700;
      cursor:default;
      position:relative;
      transition: transform .12s var(--ease), box-shadow .12s var(--ease), background .12s var(--ease);
      user-select:none;
    }
    .help-bubble:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 12px 36px rgba(2,6,23,0.6); color:#fff; background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015)); cursor:help; }

    .help-bubble .tooltip {
      position:absolute;
      right:calc(100% + 12px);
      top:50%;
      transform: translateY(-50%) translateX(6px) scale(0.98);
      background: var(--tooltip-bg);
      color: var(--tooltip-color);
      padding:10px 12px;
      border-radius:10px;
      font-size:13px;
      white-space:nowrap;
      opacity:0;
      pointer-events:none;
      box-shadow: 0 10px 30px rgba(2,6,23,0.6);
      transition: opacity .22s var(--ease), transform .22s var(--ease);
      z-index:40;
      border: 1px solid rgba(255,255,255,0.04);
      transform-origin: right center;
    }
    .help-bubble .tooltip::after{
      content:"";
      position:absolute;
      left:100%;
      top:50%;
      transform:translateY(-50%);
      width:10px;height:10px;
      background:var(--tooltip-bg);
      border-left:1px solid rgba(255,255,255,0.04);
      clip-path: polygon(0 50%, 100% 0, 100% 100%);
    }

    /* Show tooltip on hover (desktop) and on focus (keyboard) only */
    .help-bubble:hover .tooltip,
    .help-bubble:focus .tooltip {
      opacity:1;
      transform: translateY(-50%) translateX(0) scale(1);
      pointer-events:auto;
    }

    @media (max-width:720px){
      .help-bubble .tooltip{
        right:auto;
        left:50%;
        top:calc(100% + 10px);
        transform: translateX(-50%) translateY(6px) scale(0.98);
      }
      .help-bubble .tooltip::after{
        left:50%;
        top:-6px;
        transform:translateX(-50%) rotate(180deg);
        clip-path: polygon(50% 0, 0 100%, 100% 100%);
      }
    }

    .actions{
      display:flex;
      gap:12px;
      margin-top:18px;
      align-items:center;
    }
    .btn{
      padding:10px 14px;
      border-radius:10px;
      border: none;
      background: linear-gradient(90deg,var(--accent),#2bb0ff);
      color:white;
      font-weight:600;
      cursor:pointer;
      box-shadow: 0 8px 24px rgba(79,140,255,0.14);
      transition: transform .12s var(--ease), box-shadow .12s var(--ease);
    }
    .btn.ghost{
      background:transparent;
      border:1px solid rgba(255,255,255,0.06);
      color:var(--muted);
      box-shadow:none;
    }

    .output {
      margin-top:16px;
      padding:12px;
      border-radius:10px;
      background: rgba(255,255,255,0.02);
      border:1px solid rgba(255,255,255,0.02);
      font-family: monospace;
      white-space: pre-wrap;
      color:#dfe9ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Jurisdiction mappings (IIN + abbreviations)
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

# ---------------------------
# Fields definition (no auto-fill)
# ---------------------------
PREFIX_FIELDS: List[Tuple[str, str]] = [
    ("DCG", "Code du pays (ex: CAN pour Canada, US pour United States)"),
    ("DAQ", "Numéro de permis (ex: N242094120896)"),
    ("DCS", "Nom de famille (ex: NICOLAS)"),
    ("DAC", "Prénom (ex: JEAN)"),
    ("DBB", "Date de naissance (YYYY-MM-DD ou YYYYMMDD)"),
    ("DAG", "Adresse ligne 1 (ex: 1560 SHERBROOKE ST E)"),
    ("DAI", "Ville (ex: MONTREAL)"),
    ("DAJ", "Province/État (ex: QC ou CA)"),
    ("DAK", "Code postal / ZIP (ex: H2L4M1 ou 90001)"),
    ("DBD", "Date d'émission (YYYY-MM-DD ou YYYYMMDD)"),
    ("DBA", "Date d'expiration (YYYY-MM-DD ou YYYYMMDD)"),
    ("DBC", "Sexe (1 = Homme, 2 = Femme)"),
    ("DAU", "Taille (ex: 180 cm)"),
    ("DAY", "Couleur des yeux (ex: BRUN)"),
    ("DCE", "Classe(s)"),
    ("DCF", "Numéro de référence du document (ex: PEJQ04N96)")
]

# Initialize session state for fields
for prefix, _ in PREFIX_FIELDS:
    key = f"field_{prefix}"
    if key not in st.session_state:
        st.session_state[key] = ""

if "prev_subdivision" not in st.session_state:
    st.session_state["prev_subdivision"] = ""
if "last_aamva" not in st.session_state:
    st.session_state["last_aamva"] = ""

# ---------------------------
# Header / selectors (non-flottant)
# ---------------------------
st.markdown("<div class='app-wrap'>", unsafe_allow_html=True)
st.markdown("<div class='header'><div class='logo'>A</div><div><h2 class='title'>Générateur AAMVA</h2><div class='sub'>Champs vides par défaut — infobulles au survol uniquement</div></div></div>", unsafe_allow_html=True)

# Place selectors inline (no floating centered container)
country_col, subdivision_col = st.columns([1,1])
with country_col:
    country = st.selectbox("Pays", ["", "Canada", "United States"], key="country_main")
with subdivision_col:
    if country == "United States":
        subdivision = st.selectbox("État", [""] + US_STATES, key="subdivision_main")
    elif country == "Canada":
        subdivision = st.selectbox("Province / Territoire", [""] + CA_PROVINCES, key="subdivision_main")
    else:
        subdivision = st.selectbox("Subdivision", [""], key="subdivision_main")

# ---------------------------
# DAJ auto-update (abbr) without overwriting manual edits
# ---------------------------
current_daj = st.session_state.get("field_DAJ", "").strip()
prev_sub = st.session_state.get("prev_subdivision", "")

if subdivision and subdivision != prev_sub:
    if country == "Canada":
        daj_value = CA_ABBR.get(subdivision, subdivision)
    elif country == "United States":
        daj_value = US_ABBR.get(subdivision, subdivision)
    else:
        daj_value = subdivision

    # Only set DAJ if empty or equal to previous auto value
    if current_daj == "" or current_daj == prev_sub:
        st.session_state["field_DAJ"] = daj_value

    st.session_state["prev_subdivision"] = subdivision
elif not subdivision:
    st.session_state["prev_subdivision"] = ""

# ---------------------------
# Form (displayed if country chosen)
# ---------------------------
if country:
    st.markdown("---")
    st.subheader("Champs préfixés (saisie)")

    default_dcg = "US" if country == "United States" else "CAN" if country == "Canada" else ""

    # Prepare DAJ options (prioritize selected subdivision)
    daj_options = []
    if subdivision:
        if country == "Canada":
            abbr = CA_ABBR.get(subdivision, "")
            first = abbr if abbr else subdivision
        else:
            first = subdivision
        daj_options = [first] + [opt for opt in (US_STATES if country == "United States" else CA_PROVINCES) if opt != subdivision]
    else:
        daj_options = (US_STATES if country == "United States" else CA_PROVINCES) if country else []

    # Display fields in two-column grid
    for i in range(0, len(PREFIX_FIELDS), 2):
        left = PREFIX_FIELDS[i]
        right = PREFIX_FIELDS[i+1] if i+1 < len(PREFIX_FIELDS) else None
        cols = st.columns([1, 1])

        # Left field
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

        # Right field
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
    # Utility functions for AAMVA generation
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
        L'en-tête numérique IIN+version+design est concaténé sans espaces, par ex: "636038080001"
        """
        iin = get_iin_for_selection(country_name, subdivision_name)
        version = "08"
        design = "0001"
        iin_sequence = f"{iin}{version}{design}"  # ex: "636038080001"

        data_lines = []

        # DAQ priority: use DAQ field if present, else DCF
        daq_val = fields.get("DAQ") or fields.get("DCF") or ""
        if daq_val:
            data_lines.append(f"DAQ{daq_val}")

        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        for code in order:
            val = fields.get(code)
            if val:
                if code in ("DBB","DBD","DBA"):
                    val = normalize_date(val)
                val = str(val).replace("\n", " ").strip()
                data_lines.append(f"{code}{val}")

        # Real data block for length calculation (with real newlines)
        real_data_block = "\n".join(data_lines) + ("\n" if data_lines else "")
        length = f"{len(real_data_block):04d}"

        offset = "0041"  # default offset; adjust if you implement exact calculation

        # Header: "ANSI " + iin_sequence + "DL" + offset + length + "DL" (no spaces inside numeric sequence)
        header = f"ANSI {iin_sequence}DL{offset}{length}DL"

        # Data block for output uses literal '\n' sequences
        data_block_literal = "\\n".join(data_lines) + "\\n" if data_lines else ""

        final = "@\\n" + header + "\\n" + data_block_literal
        return final

    # ---------------------------
    # Actions
    # ---------------------------
    if st.button("Générer"):
        fields_values = {prefix: st.session_state.get(f"field_{prefix}", "").strip() for prefix, _ in PREFIX_FIELDS}
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

    # Display generated block if present
    if st.session_state.get("last_aamva"):
        st.markdown("### Bloc AAMVA (texte brut) — copiable (séquences '\\n' littérales)")
        st.code(st.session_state["last_aamva"], language=None)
        st.info("Sélectionne le texte ci‑dessous et copie‑le (Ctrl+C / Cmd+C).")

# Footer / notes
st.markdown("---")
st.caption(
    "Note : La sortie contient des séquences littérales '\\n' pour représenter les retours à la ligne. "
    "L'en-tête ANSI utilise une séquence IIN+version+design concaténée sans espaces (ex: 636038080001DL00410214DL). "
    "Utilise ce texte à des fins de test et d'apprentissage uniquement."
)
