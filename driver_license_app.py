# driver_license_app.py
# Streamlit — Générateur AAMVA avec infobulles modernes (hover-only, animation fluide, auto-hide)
# - Aucun préremplissage automatique ni boutons d'exemple
# - DAQ modifiable et utilisé en priorité
# - DAJ lié automatiquement à la subdivision (abréviations CA/US) sans écraser saisies manuelles
# - En-tête numérique IIN+VER+DES concaténé sans espaces
# - Sortie commence par "@\n" et utilise les séquences littérales "\n"
# - Infobulles : apparaissent uniquement au survol, animation fluide, disparaissent au mouseleave
# - Sur mobile : tap affiche brièvement l'infobulle (auto-hide), accessible au clavier

import streamlit as st
import datetime
from typing import Dict, List, Tuple

st.set_page_config(page_title="Driver License App — AAMVA (Tooltips)", layout="wide")

# ---------------------------
# CSS + JS injectés pour tooltips modernes
# - Tooltips visibles uniquement au hover (desktop)
# - Transition fluide d'apparition/disparition
# - Auto-hide au mouseleave
# - Tap on mobile shows tooltip briefly (3s)
# - Accessible via keyboard (focus/blur)
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
      --tooltip-color: #eaf0ff;
      --radius:12px;
      --ease: cubic-bezier(.2,.9,.3,1);
    }
    .app-wrap {
      max-width:1100px;
      margin:28px auto;
      padding:22px;
      border-radius:var(--radius);
      background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      box-shadow: 0 12px 40px rgba(2,6,23,0.6);
      border: 1px solid rgba(255,255,255,0.03);
      color: #eaf0ff;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }
    .app-header { display:flex; gap:14px; align-items:center; margin-bottom:12px; }
    .app-logo { width:48px; height:48px; border-radius:10px; background: linear-gradient(135deg,var(--accent),#2bb0ff); display:flex; align-items:center; justify-content:center; font-weight:700; color:white; font-size:18px; box-shadow: 0 8px 24px rgba(79,140,255,0.14); }
    .app-title { margin:0; font-size:18px; }
    .app-sub { margin:2px 0 0 0; color:var(--muted); font-size:13px; }

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

    /* Help bubble */
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
    .help-bubble .tooltip::after {
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

    /* Show tooltip on hover (desktop) */
    .help-bubble:hover .tooltip,
    .help-bubble.show .tooltip {
      opacity:1;
      transform: translateY(-50%) translateX(0) scale(1);
      pointer-events:auto;
    }

    /* On small screens, place tooltip below */
    @media (max-width:720px){
      .help-bubble .tooltip { right:auto; left:50%; top:calc(100% + 10px); transform: translateX(-50%) translateY(6px) scale(0.98); }
      .help-bubble .tooltip::after { left:50%; top:-6px; transform:translateX(-50%) rotate(180deg); clip-path: polygon(50% 0, 0 100%, 100% 100%); }
    }

    .actions { display:flex; gap:12px; margin-top:18px; align-items:center; }
    .btn { padding:10px 14px; border-radius:10px; border:none; background: linear-gradient(90deg,var(--accent),#2bb0ff); color:white; font-weight:600; cursor:pointer; box-shadow: 0 8px 24px rgba(79,140,255,0.14); }
    .btn.ghost { background:transparent; border:1px solid rgba(255,255,255,0.06); color:var(--muted); box-shadow:none; }

    .output-card { margin-top:16px; padding:12px; border-radius:10px; background: rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.02); font-family: monospace; white-space: pre-wrap; color:#dfe9ff; }
    </style>

    <script>
    // JS to support mobile/touch: show tooltip briefly on tap and auto-hide on mouseleave
    document.addEventListener('DOMContentLoaded', function(){
      // delegate: find all help-bubble elements injected by Streamlit
      function setupHelpBubbles(){
        const bubbles = document.querySelectorAll('.help-bubble');
        bubbles.forEach(b => {
          // ensure we don't attach multiple listeners
          if (b.dataset.tooltipInit === '1') return;
          b.dataset.tooltipInit = '1';

          // show on focus (keyboard)
          b.addEventListener('focus', () => { b.classList.add('show'); });
          b.addEventListener('blur', () => { b.classList.remove('show'); });

          // on touch/click: toggle show briefly (mobile)
          b.addEventListener('click', (ev) => {
            // prevent immediate blur/focus issues
            ev.stopPropagation();
            b.classList.add('show');
            // auto-hide after 3000ms
            clearTimeout(b._hideTimeout);
            b._hideTimeout = setTimeout(() => { b.classList.remove('show'); }, 3000);
          });

          // ensure tooltip hides on mouseleave immediately
          b.addEventListener('mouseleave', () => {
            b.classList.remove('show');
            clearTimeout(b._hideTimeout);
          });

          // also hide when clicking elsewhere
          document.addEventListener('click', function docClick(){ b.classList.remove('show'); clearTimeout(b._hideTimeout); document.removeEventListener('click', docClick); }, { once: true });
        });
      }

      // initial setup and also observe DOM changes (Streamlit re-renders)
      setupHelpBubbles();
      const observer = new MutationObserver(() => { setupHelpBubbles(); });
      observer.observe(document.body, { childList: true, subtree: true });
    });
    </script>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Data / mappings
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
CA_ABBR = {"Alberta":"AB","British Columbia":"BC","Manitoba":"MB","New Brunswick":"NB","Newfoundland and Labrador":"NL","Northwest Territories":"NT","Nova Scotia":"NS","Nunavut":"NU","Ontario":"ON","Prince Edward Island":"PE","Quebec":"QC","Saskatchewan":"SK","Yukon":"YT"}
US_ABBR = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY","District of Columbia":"DC","Puerto Rico":"PR","Guam":"GU","U.S. Virgin Islands":"VI","American Samoa":"AS","Northern Mariana Islands":"MP"}

US_STATES = sorted(list(IIN_US.keys()))
CA_PROVINCES = sorted(list(IIN_CA.keys()))

# ---------------------------
# Fields definition and session init
# ---------------------------
FIELDS: List[Tuple[str, str]] = [
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

for code, _ in FIELDS:
    key = f"field_{code}"
    if key not in st.session_state:
        st.session_state[key] = ""

if "prev_subdivision" not in st.session_state:
    st.session_state["prev_subdivision"] = ""
if "last_aamva" not in st.session_state:
    st.session_state["last_aamva"] = ""

# ---------------------------
# Page layout
# ---------------------------
st.markdown("<div class='app-wrap'>", unsafe_allow_html=True)
st.markdown("<div class='app-header'><div class='app-logo'>A</div><div><h2 class='app-title'>Générateur AAMVA</h2><div class='app-sub'>Infobulles modernes au survol — apparence fluide</div></div></div>", unsafe_allow_html=True)

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

# Grid of fields with help bubbles (right column contains the bubble)
st.markdown("<div class='grid'>", unsafe_allow_html=True)

# Left card (first half of fields)
st.markdown("<div class='card'><h3 style='margin-top:0'>Informations personnelles</h3>", unsafe_allow_html=True)
for code, help_text in FIELDS[:8]:
    col_input, col_help = st.columns([8,1])
    with col_input:
        label = f"{code}"
        if code == "DBC":
            st.selectbox(label, ["", "1 - Homme", "2 - Femme"], key=f"field_{code}")
        else:
            st.text_input(label, value=st.session_state.get(f"field_{code}", ""), key=f"field_{code}")
    safe_help = help_text.replace("'", "&#39;").replace('"', "&quot;")
    help_html = f"""
      <div class="help-bubble" tabindex="0" role="button" aria-label="{safe_help}">
        ?
        <div class="tooltip" role="tooltip">{safe_help}</div>
      </div>
    """
    with col_help:
        st.markdown(help_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Right card (remaining fields)
st.markdown("<div class='card'><h3 style='margin-top:0'>Adresse & Détails</h3>", unsafe_allow_html=True)
for code, help_text in FIELDS[8:]:
    col_input, col_help = st.columns([8,1])
    with col_input:
        label = f"{code}"
        if code == "DBC":
            st.selectbox(label, ["", "1 - Homme", "2 - Femme"], key=f"field_{code}")
        else:
            st.text_input(label, value=st.session_state.get(f"field_{code}", ""), key=f"field_{code}")
    safe_help = help_text.replace("'", "&#39;").replace('"', "&quot;")
    help_html = f"""
      <div class="help-bubble" tabindex="0" role="button" aria-label="{safe_help}">
        ?
        <div class="tooltip" role="tooltip">{safe_help}</div>
      </div>
    """
    with col_help:
        st.markdown(help_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close grid

# Actions
col_a, col_b = st.columns([1,1])
with col_a:
    if st.button("Générer le bloc AAMVA (séquences '\\n' littérales)"):
        fields_values = {code: st.session_state.get(f"field_{code}", "").strip() for code, _ in FIELDS}
        def get_iin(country_name: str, subdivision_name: str) -> str:
            if country_name == "United States":
                return IIN_US.get(subdivision_name, "000000")
            if country_name == "Canada":
                return IIN_CA.get(subdivision_name, "000000")
            return "000000"
        def normalize_date(v: str) -> str:
            return v.replace("-", "").strip()
        iin = get_iin(country, subdivision)
        version = "08"
        design = "0001"
        iin_sequence = f"{iin}{version}{design}"
        data_lines = []
        daq = fields_values.get("DAQ","") or fields_values.get("DCF","")
        if daq:
            data_lines.append(f"DAQ{daq}")
        order = ["DCS","DAC","DBB","DAG","DAI","DAJ","DAK","DBD","DBA","DBC","DAU","DAY","DCE","DCG","DCF"]
        for code in order:
            val = fields_values.get(code,"")
            if val:
                if code in ("DBB","DBD","DBA"):
                    val = normalize_date(val)
                val = str(val).replace("\n"," ").strip()
                data_lines.append(f"{code}{val}")
        real_data_block = "\n".join(data_lines) + ("\n" if data_lines else "")
        length = f"{len(real_data_block):04d}"
        offset = "0041"
        header = f"ANSI {iin_sequence}DL{offset}{length}DL"
        data_block_literal = "\\n".join(data_lines) + "\\n" if data_lines else ""
        final = "@\\n" + header + "\\n" + data_block_literal
        st.session_state["last_aamva"] = final
with col_b:
    if st.button("Réinitialiser"):
        for code, _ in FIELDS:
            st.session_state[f"field_{code}"] = ""
        st.session_state["last_aamva"] = ""
        st.experimental_rerun()

# Output
if st.session_state.get("last_aamva"):
    st.markdown("<div class='output-card'>", unsafe_allow_html=True)
    st.code(st.session_state["last_aamva"], language=None)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:14px;color:var(--muted);font-size:13px'>Les infobulles s'affichent uniquement au survol (desktop). Sur mobile, appuie brièvement sur l'icône pour afficher l'aide (auto-hide).</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # close app-wrap
