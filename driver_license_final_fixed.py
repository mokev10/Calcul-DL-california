#!/usr/bin/env python3
# theme_module_fixed.py
# Collez intégralement ce bloc en tout début de votre script (avant tout widget Streamlit).
# - st.set_page_config doit être la première commande exécutable
# - st.session_state['theme'] initialisé sur 'dark'
# - Callback mutatif (pas de st.rerun() dans le callback)
# - Injection CSS via st.markdown(unsafe_allow_html=True) avec :root variables
# - Ciblage précis .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"]
# - Toggle sans texte : icône seule appliquée au bouton via background-image ciblé par title="theme-toggle"

import streamlit as st

# -------------------------
# Page config (doit être la première commande exécutable)
# -------------------------
st.set_page_config(page_title="Permis CA", layout="wide")

# -------------------------
# Assets (constantes strictes demandées)
# -------------------------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# -------------------------
# State initialization (persistant)
# -------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # valeur par défaut demandée

# -------------------------
# Toggle callback (mutates state only; no st.rerun() here)
# -------------------------
def toggle_theme_callback():
    """
    Inverse st.session_state['theme'] uniquement.
    Ne pas appeler st.rerun() ici (évite le 'no-op').
    Streamlit relancera naturellement le script après l'interaction.
    """
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"

# -------------------------
# Dynamic CSS injection (safe f-strings, double braces for literal CSS braces)
# -------------------------
def inject_theme_css():
    """
    Injecte le CSS dynamique via st.markdown(unsafe_allow_html=True).
    Définit :root variables (--bg-color, --card-bg, --text-color, --border-color).
    Cible précisément .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"].
    Le bouton toggle est ciblé via button[title="theme-toggle"] (le help du bouton).
    """
    theme = st.session_state.get("theme", "dark")
    if theme == "dark":
        bg = "#0b1220"
        card = "#0f172a"
        text = "#e6eef8"
        border = "rgba(255,255,255,0.06)"
        accent = "#60a5fa"
        toggle_icon = ICON_LIGHT  # montrer l'icône du mode cible (light)
    else:
        bg = "#f5f7fa"
        card = "#ffffff"
        text = "#0f172a"
        border = "#e6eef8"
        accent = "#2563eb"
        toggle_icon = ICON_DARK  # montrer l'icône du mode cible (dark)

    # f-string with double braces for literal CSS blocks
    css = f"""
    <style>
    :root {{
      --bg-color: {bg};
      --card-bg: {card};
      --text-color: {text};
      --border-color: {border};
      --accent-color: {accent};
    }}

    /* Apply background and text color to Streamlit app container only */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }}

    /* Ensure markdown and text inherit readable color */
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"], .css-1d391kg {{
      color: var(--text-color) !important;
    }}

    /* Card utility */
    .card {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 10px !important;
      padding: 12px !important;
    }}

    /* Buttons: target Streamlit button elements explicitly */
    .stButton>button, .stDownloadButton>button {{
      background: linear-gradient(135deg, var(--accent-color), #1e40af) !important;
      color: #ffffff !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      font-weight: 600 !important;
      box-shadow: none !important;
    }}

    /* Text inputs: ensure background, text and border override */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    textarea {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
    }}

    /* Selectbox: visible select control */
    .stSelectbox>div>div>select, select {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 6px 8px !important;
      text-overflow: ellipsis !important;
    }}

    /* Sidebar explicit targeting */
    section[data-testid="stSidebar"] {{
      background: linear-gradient(180deg,#071033,#0f172a) !important;
      color: var(--text-color) !important;
      border-right: 1px solid var(--border-color) !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .css-1d391kg {{
      color: var(--text-color) !important;
    }}

    /* Prevent vertical text rendering issues: force horizontal flow */
    .stApp, .stApp * {{
      writing-mode: horizontal-tb !important;
      -webkit-writing-mode: horizontal-tb !important;
      transform: none !important;
    }}

    /* Header toggle container (flex alignment) */
    .header-toggle-container {{
      display: flex !important;
      justify-content: flex-end !important;
      align-items: center !important;
      gap: 8px !important;
    }}

    /* Style the specific toggle button by title attribute (help text) so other buttons are unaffected.
       The button will have title="theme-toggle". We set the icon as background-image so the button shows only the icon. */
    button[title="theme-toggle"] {{
      width: 36px !important;
      height: 36px !important;
      padding: 0 !important;
      border-radius: 8px !important;
      border: 1px solid var(--border-color) !important;
      background-color: transparent !important;
      background-image: url('{toggle_icon}') !important;
      background-repeat: no-repeat !important;
      background-position: center !important;
      background-size: 20px 20px !important;
      color: transparent !important;
      box-shadow: none !important;
      cursor: pointer !important;
    }}

    /* Focus outline for accessibility */
    button[title="theme-toggle"]:focus {{
      outline: 2px solid var(--accent-color) !important;
      outline-offset: 2px !important;
    }}

    @media (max-width: 800px) {{
      .header-toggle-container {{ gap: 6px !important; }}
      button[title="theme-toggle"] {{ width: 32px !important; height: 32px !important; background-size: 18px 18px !important; }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Inject initial CSS BEFORE rendering widgets
inject_theme_css()

# -------------------------
# Layout & Toggle placement (st.columns([0.9, 0.1]))
# -------------------------
left_col, right_col = st.columns([0.9, 0.1])
with left_col:
    st.markdown(
        '<div style="margin:0;padding:0"><strong style="font-size:18px;color:var(--text-color)">Générateur officiel de permis CA</strong></div>',
        unsafe_allow_html=True,
    )

with right_col:
    # Render a small flex container (CSS handles alignment)
    st.markdown('<div class="header-toggle-container"></div>', unsafe_allow_html=True)
    # Button label intentionally empty; help sets title="theme-toggle" so CSS can target it
    st.button("", key="__theme_toggle_button__", help="theme-toggle", on_click=toggle_theme_callback)

# End of theme module. Continue with the rest of your application below.
