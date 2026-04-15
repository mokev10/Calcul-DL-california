# THEME MODULE — Atomic UI, State-Aware Dark/Light toggle for Streamlit
# Coller intégralement en haut de votre script (avant tout widget Streamlit)
# - ICON_DARK and ICON_LIGHT declared as requested
# - Injection CSS via st.markdown(unsafe_allow_html=True) with :root variables (--bg-color, --text-color, --card-bg, --border-color)
# - Targets: .stApp, .stButton, .stTextInput, .stSelectbox, section[data-testid="stSidebar"]
# - Layout: st.columns([0.9, 0.1]) with flex container for toggle
# - State persisted in st.session_state initialized to 'dark'
# - Callback toggles state and attempts st.rerun() (with safe fallback)
# - Fournit un bloc complet, prêt à coller sans coupure

import streamlit as st

# Configuration des Assets (constantes strictes demandées)
ICON_DARK = "https://icons8.com"
ICON_LIGHT = "https://icons8.com"

# --- State initialization (persist theme in session_state) ---
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"  # initialize on 'dark' as requested

# --- CSS injection function (uses :root variables exactly as specified) ---
def inject_theme_css(theme: str) -> None:
    """
    Inject dynamic :root variables and targeted CSS rules.
    Must be called BEFORE rendering widgets to maximize effect.
    """
    if theme == "dark":
        root_vars = """
        :root{
          --bg-color: #0b1220;
          --text-color: #e6eef8;
          --card-bg: #0f172a;
          --border-color: rgba(255,255,255,0.06);
        }
        """
    else:
        root_vars = """
        :root{
          --bg-color: #f5f7fa;
          --text-color: #0f172a;
          --card-bg: #ffffff;
          --border-color: #e6eef8;
        }
        """

    css = r"""
    /* Root variables injected dynamically */
    {root_vars}

    /* Apply background and text color to Streamlit app container only */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background-color: var(--bg-color) !important;
      color: var(--text-color) !important;
    }

    /* Ensure markdown and text inherit readable color */
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"], .css-1d391kg {
      color: var(--text-color) !important;
    }

    /* Card utility */
    .card {
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 10px !important;
      padding: 12px !important;
    }

    /* Buttons: target Streamlit button elements explicitly */
    .stButton>button, .stDownloadButton>button, .stButton button {
      background: linear-gradient(135deg, var(--text-color), #1e40af) !important;
      color: var(--bg-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      font-weight: 600 !important;
      box-shadow: none !important;
    }

    /* Text inputs: ensure background, text and border override */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    textarea {
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
    }

    /* Selectbox: visible select control */
    .stSelectbox>div>div>select, select {
      background-color: var(--card-bg) !important;
      color: var(--text-color) !important;
      border: 1px solid var(--border-color) !important;
      border-radius: 8px !important;
      padding: 6px 8px !important;
      text-overflow: ellipsis !important;
    }

    /* Sidebar explicit targeting */
    section[data-testid="stSidebar"] {
      background: linear-gradient(180deg,#071033,#0f172a) !important;
      color: var(--text-color) !important;
      border-right: 1px solid var(--border-color) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .css-1d391kg {
      color: var(--text-color) !important;
    }

    /* Prevent vertical text rendering issues: force horizontal flow */
    .stApp, .stApp * {
      writing-mode: horizontal-tb !important;
      -webkit-writing-mode: horizontal-tb !important;
      transform: none !important;
    }

    /* Flex container for header toggle (keeps icon aligned right) */
    .header-toggle-container {
      display: flex !important;
      justify-content: flex-end !important;
      align-items: center !important;
      gap: 8px !important;
    }

    /* Icon styling */
    .theme-icon {
      width: 22px !important;
      height: 22px !important;
      border-radius: 6px !important;
      object-fit: contain !important;
      display: inline-block !important;
    }

    /* Small screens adjustments */
    @media (max-width: 800px) {
      .theme-icon { width: 20px !important; height: 20px !important; }
    }
    """.format(root_vars=root_vars)

    # Use st.markdown with unsafe_allow_html to inject CSS into the DOM
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# --- Toggle callback that mutates state and triggers rerun ---
def _toggle_and_rerun():
    # flip theme
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"
    # re-inject CSS for immediate effect
    inject_theme_css(st.session_state["theme"])
    # attempt to rerun to ensure full re-render; try st.rerun() first as requested, fallback to experimental_rerun
    try:
        # Some Streamlit versions expose st.rerun; call it if available
        rerun_fn = getattr(st, "rerun", None)
        if callable(rerun_fn):
            rerun_fn()
            return
    except Exception:
        pass
    try:
        st.experimental_rerun()
    except Exception:
        # If rerun is unavailable, do nothing further; injected CSS will apply for subsequent interactions.
        return


# Inject initial CSS immediately (before widgets)
inject_theme_css(st.session_state["theme"])

# --- Header layout: use st.columns([0.9, 0.1]) to isolate toggle on the right ---
left_col, right_col = st.columns([0.9, 0.1])
with left_col:
    # Render the app title (kept minimal to verify UI rendering)
    st.markdown(
        '<div style="font-weight:700;font-size:18px;color:var(--text-color)">Générateur officiel de permis CA</div>',
        unsafe_allow_html=True,
    )

with right_col:
    # Encapsulate toggle in a flex container (ensures right alignment)
    st.markdown('<div class="header-toggle-container">', unsafe_allow_html=True)
    # Display the icon image (represents the target mode visually)
    # We show the icon corresponding to the mode that will be activated when clicked
    target_mode = "light" if st.session_state["theme"] == "dark" else "dark"
    icon_to_show = ICON_LIGHT if target_mode == "light" else ICON_DARK
    # Use st.image for the icon and place the button directly next to it
    st.image(icon_to_show, width=22)
    # Minimal label button for an "epuré" look; label is intentionally empty string
    if st.button("", key="__theme_switch_button__", help=f"Basculer en {target_mode} mode"):
        _toggle_and_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
