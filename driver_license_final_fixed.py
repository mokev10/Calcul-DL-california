# theme_module_final.py
# Module complet à coller en tout début de votre script Streamlit (avant tout widget)
# - State-aware (st.session_state), initialisé sur 'dark'
# - Injection CSS via st.markdown(unsafe_allow_html=True) avec :root (--bg-color, --text-color, --border-color)
# - Ciblage explicite .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"]
# - Toggle sans texte : icône seule (Icons8) appliquée au bouton via CSS background-image
# - Robust toggle flow : pas d'appel direct à st.rerun() dans le callback (évite le "no-op"); rerun déclenché en dehors du callback si nécessaire

import streamlit as st

# -------------------------
# Assets (constantes strictes)
# -------------------------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# -------------------------
# State initialization
# -------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # valeur par défaut demandée

# Flag utilisé pour demander un rerun en dehors du callback (évite st.rerun() dans callback)
if "theme_pending_rerun" not in st.session_state:
    st.session_state["theme_pending_rerun"] = False

# -------------------------
# Toggle callback (ne fait que muter l'état)
# -------------------------
def toggle_theme_callback():
    """
    Callback minimal : inverse le thème et marque qu'un rerun est souhaité.
    Ne fait PAS appel à st.rerun() directement (évite le no-op dans certains environnements).
    """
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
    st.session_state["theme_pending_rerun"] = True

# -------------------------
# CSS injection (Atomic :root + targeted selectors)
# -------------------------
def inject_theme_css():
    """
    Injecte le CSS dynamique via st.markdown(unsafe_allow_html=True).
    Utilise f-strings et double-accolades pour inclure des blocs CSS littéraux.
    Définit :root variables (--bg-color, --text-color, --border-color).
    Cible explicitement les sélecteurs Streamlit demandés.
    Le bouton toggle est ciblé via button[title="theme-toggle"] (le help du bouton).
    """
    theme = st.session_state.get("theme", "dark")
    if theme == "dark":
        bg = "#0b1220"
        card = "#0f172a"
        text = "#e6eef8"
        border = "rgba(255,255,255,0.06)"
        accent = "#60a5fa"
        # icon shown on the button is the target mode (light) so user understands action
        toggle_icon = ICON_LIGHT
    else:
        bg = "#f5f7fa"
        card = "#ffffff"
        text = "#0f172a"
        border = "#e6eef8"
        accent = "#2563eb"
        toggle_icon = ICON_DARK

    # Build CSS with f-string; use double braces {{ }} to include literal braces in CSS blocks
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
    # Inject CSS into the DOM
    st.markdown(css, unsafe_allow_html=True)

# Inject CSS now (before widgets)
inject_theme_css()

# -------------------------
# If a toggle was requested in a previous run, trigger a rerun now (outside callback)
# This avoids calling st.rerun() inside the callback (which can be a no-op).
# -------------------------
if st.session_state.get("theme_pending_rerun", False):
    # Clear the flag and attempt a rerun using the most compatible API
    st.session_state["theme_pending_rerun"] = False
    try:
        rerun_fn = getattr(st, "rerun", None)
        if callable(rerun_fn):
            rerun_fn()
        else:
            st.experimental_rerun()
    except Exception:
        # If rerun is not permitted in this environment, rely on the injected CSS and subsequent interactions.
        pass

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
    # Place the toggle inside a flex container (CSS ensures alignment)
    st.markdown('<div class="header-toggle-container"></div>', unsafe_allow_html=True)
    # The button label is intentionally empty; help parameter sets title="theme-toggle" for CSS targeting
    # Use on_click to mutate state only (no direct rerun inside callback)
    if st.button("", key="__theme_toggle_button__", help="theme-toggle", on_click=toggle_theme_callback):
        # Some Streamlit versions call on_click synchronously and then continue; we do not call rerun here.
        pass

# -------------------------
# From here, continue with the rest of your application code.
# The theme module above is self-contained and safe to place at the very top of your script.
# -------------------------
