# theme_module_final_stable.py
# Module complet et autonome à coller en tout début de votre script Streamlit (avant tout widget).
# - State-aware (st.session_state), initialisé sur 'dark'
# - Injection CSS sûre via st.markdown(unsafe_allow_html=True) avec :root (--bg-color, --text-color, --border-color)
# - Ciblage explicite des sélecteurs .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"]
# - Toggle sans texte : icône seule (Icons8) appliquée au bouton via CSS background-image
# - Pas d'appel à st.rerun() dans le callback (Streamlit rerun automatique après interaction)
# - Utilise f-strings avec doubles accolades pour éviter les KeyError / erreurs de formatage

import streamlit as st

# -------------------------
# Assets (constantes strictes demandées)
# -------------------------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# -------------------------
# State initialization
# -------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # valeur par défaut demandée

# -------------------------
# Toggle callback (mutates state only)
# -------------------------
def toggle_theme_callback():
    """
    Callback minimal : inverse le thème.
    Ne fait PAS appel à st.rerun() ni à st.experimental_rerun() — Streamlit relancera le script automatiquement.
    """
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"

# -------------------------
# CSS injection (Atomic :root + targeted selectors)
# -------------------------
def inject_theme_css():
    """
    Injecte le CSS dynamique via st.markdown(unsafe_allow_html=True).
    Utilise f-strings et double-accolades {{ }} pour inclure des blocs CSS littéraux.
    Définit :root variables (--bg-color, --text-color, --border-color).
    Cible explicitement .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"].
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

    # Note: dans un f-string, pour inclure une accolade littérale on écrit '{{' ou '}}'.
    css = f"""
    <style>
    :root {{
      --bg-color: {bg};
      --card-bg: {card};
      --text-color: {text};
      --border-color: {border};
      --accent-color: {accent};
    }}

    /* Appliquer le fond et la couleur du texte à la zone principale Streamlit uniquement */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }}

    /* Markdown / textes */
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"], .css-1d391kg {{
      color: var(--text-color) !important;
    }}

    /* Cartes utilitaires */
    .card {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 10px !important;
      padding: 12px !important;
    }}

    /* Boutons Streamlit (général) */
    .stButton>button, .stDownloadButton>button {{
      background: linear-gradient(135deg, var(--accent-color), #1e40af) !important;
      color: #ffffff !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      font-weight: 600 !important;
      box-shadow: none !important;
    }}

    /* Inputs textuels */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    textarea {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
    }}

    /* Selectbox */
    .stSelectbox>div>div>select, select {{
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 6px 8px !important;
      text-overflow: ellipsis !important;
    }}

    /* Sidebar ciblée */
    section[data-testid="stSidebar"] {{
      background: linear-gradient(180deg,#071033,#0f172a) !important;
      color: var(--text-color) !important;
      border-right: 1px solid var(--border-color) !important;
    }}
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .css-1d391kg {{
      color: var(--text-color) !important;
    }}

    /* Forcer flux horizontal (évite texte vertical) */
    .stApp, .stApp * {{
      writing-mode: horizontal-tb !important;
      -webkit-writing-mode: horizontal-tb !important;
      transform: none !important;
    }}

    /* Conteneur flex pour le toggle (alignement à droite) */
    .header-toggle-container {{
      display: flex !important;
      justify-content: flex-end !important;
      align-items: center !important;
      gap: 8px !important;
    }}

    /* Cibler uniquement le bouton toggle via son title (help) pour éviter d'impacter d'autres boutons.
       Le bouton aura title="theme-toggle". On applique l'icône en background-image. */
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

    /* Focus visible pour accessibilité */
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
    # Injection sûre
    st.markdown(css, unsafe_allow_html=True)

# Inject initial CSS BEFORE rendering widgets
inject_theme_css()

# -------------------------
# Header & Toggle UI (st.columns([0.9, 0.1]) as requested)
# -------------------------
left_col, right_col = st.columns([0.9, 0.1])
with left_col:
    st.markdown(
        '<div style="margin:0;padding:0"><strong style="font-size:18px;color:var(--text-color)">Générateur officiel de permis CA</strong></div>',
        unsafe_allow_html=True,
    )

with right_col:
    # Conteneur flex (CSS gère l'alignement)
    st.markdown('<div class="header-toggle-container"></div>', unsafe_allow_html=True)
    # Bouton sans texte ; help="theme-toggle" permet de cibler le bouton en CSS (title attribute)
    # on_click ne fait que muter le state ; Streamlit relancera le script automatiquement après l'interaction.
    st.button("", key="__theme_toggle_button__", help="theme-toggle", on_click=toggle_theme_callback)

# -------------------------
# NOTE SUR LE FLUX
# -------------------------
# - Le callback toggle_theme_callback inverse st.session_state["theme"] uniquement.
# - Streamlit redémarre le script automatiquement après l'interaction, donc inject_theme_css()
#   sera ré-exécuté en début de script avec la nouvelle valeur de st.session_state["theme"].
# - Aucun appel à st.rerun() n'est nécessaire ni effectué dans le callback (évite le "no-op").
#
# -------------------------
# À partir d'ici, collez le reste de votre application (formulaires, génération PDF, etc.).
# Le module de thème est autonome et doit rester en tête du fichier.
# -------------------------
