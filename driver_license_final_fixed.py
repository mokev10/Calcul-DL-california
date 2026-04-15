# THEME MODULE — State-Aware Dark/Light toggle for Streamlit (Atomic CSS)
# Coller intégralement en haut de votre script (avant tout widget Streamlit)
# - ICON_DARK / ICON_LIGHT déclarés strictement comme demandé
# - Persistance via st.session_state (initialisé sur 'dark')
# - Injection CSS via st.markdown(unsafe_allow_html=True) avec :root variables (--bg-color, --text-color, --border-color)
# - Ciblage explicite des sélecteurs .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"]
# - Le bouton toggle n'affiche pas de texte ; l'icône Icons8 est appliquée au bouton via CSS ciblé (title="theme-toggle")
# - Callback utilise st.rerun() pour forcer le rafraîchissement (avec fallback)
# - Bloc complet, prêt à copier-coller, sans coupure

import streamlit as st

# -------------------------
# Asset Management (constants)
# -------------------------
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# -------------------------
# State Management
# -------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # default as requested

def _attempt_rerun():
    """
    Try to rerun the app using the most compatible API available.
    Prefer st.rerun if present, otherwise fallback to experimental_rerun.
    """
    try:
        rerun_fn = getattr(st, "rerun", None)
        if callable(rerun_fn):
            rerun_fn()
            return
    except Exception:
        pass
    try:
        st.experimental_rerun()
    except Exception:
        return

def toggle_theme_callback():
    """Flip theme state and trigger a rerun for immediate DOM refresh."""
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
    inject_theme_css()  # re-inject CSS immediately
    _attempt_rerun()

# -------------------------
# Dynamic Style Injection (Atomic CSS)
# -------------------------
def inject_theme_css():
    """
    Inject CSS using st.markdown(unsafe_allow_html=True).
    Uses f-strings and double braces to avoid .format() KeyError with CSS braces.
    Defines :root variables --bg-color, --text-color, --border-color.
    Targets .stApp, .stButton, .stTextInput, .stSelectbox, and section[data-testid="stSidebar"].
    Also styles the toggle button by targeting button[title="theme-toggle"].
    """
    theme = st.session_state.get("theme", "dark")
    if theme == "dark":
        bg = "#0b1220"
        card_bg = "#0f172a"
        text = "#e6eef8"
        border = "rgba(255,255,255,0.06)"
        accent = "#60a5fa"
        toggle_icon = ICON_LIGHT  # show icon of target mode (light) on the button
    else:
        bg = "#f5f7fa"
        card_bg = "#ffffff"
        text = "#0f172a"
        border = "#e6eef8"
        accent = "#2563eb"
        toggle_icon = ICON_DARK  # show icon of target mode (dark) on the button

    # Build CSS with f-string and literal braces for CSS blocks
    css = f"""
    <style>
    :root {{
      --bg-color: {bg};
      --card-bg: {card_bg};
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

    /* Style the specific toggle button by title attribute to avoid affecting other buttons.
       The button has title="theme-toggle" (set via st.button(help="theme-toggle")).
       We set the icon as background-image so the button shows only the icon and no text. */
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
    }}

    /* Ensure empty-label buttons remain accessible (focus outline) */
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

# Inject initial CSS before rendering widgets
inject_theme_css()

# -------------------------
# Header & Toggle (UI/UX)
# -------------------------
# Use st.columns([0.9, 0.1]) to isolate the toggle on the right as requested
left_col, right_col = st.columns([0.9, 0.1])
with left_col:
    # Minimal title to verify UI rendering; color uses CSS variable
    st.markdown('<div style="margin:0;padding:0"><strong style="font-size:18px;color:var(--text-color)">Générateur officiel de permis CA</strong></div>', unsafe_allow_html=True)

with right_col:
    # The button must not display text; we set help="theme-toggle" so CSS can target button[title="theme-toggle"]
    # The icon is applied via CSS background-image on that button (see inject_theme_css)
    # Use an empty label as requested
    if st.button("", key="__theme_toggle_button__", help="theme-toggle", on_click=toggle_theme_callback):
        # on_click will call toggle_theme_callback; this branch executes after click in some Streamlit versions
        pass

# -------------------------
# End of theme module
# -------------------------
# From here, continue with the rest of your application code (forms, generation logic, etc.).
# The theme module above is self-contained and safe to place at the very top of your script.
