# THEME TOGGLE SAFE BLOCK — Coller en tout début du script (avant tout widget)
# - Injection CSS ciblée et sûre (n'écrase pas tout le DOM)
# - st.session_state pour persister le thème
# - Toggle discret en en-tête avec icônes fournies
# - Affiche un en-tête visible immédiatement pour vérifier le rendu

import streamlit as st

# Icônes fournies
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# Initialisation du thème
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"

def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    inject_theme_css(st.session_state["theme"])
    try:
        st.experimental_rerun()
    except Exception:
        # fallback non bloquant : afficher un petit message
        st.toast = getattr(st, "toast", None)
        try:
            st.success(f"Thème changé en {st.session_state['theme']}. Rechargez la page si nécessaire (Ctrl+R).")
        except Exception:
            pass

def inject_theme_css(theme: str) -> None:
    """
    Injection CSS ciblée et sûre.
    Appeler AVANT la création des widgets pour garantir l'application.
    """
    if theme == "dark":
        vars_css = """
        :root{
          --bg: #0b1220;
          --card-bg: #0f172a;
          --text: #e6eef8;
          --muted: #9aa6bf;
          --accent: #60a5fa;
          --control-bg: #0f172a;
          --control-border: rgba(255,255,255,0.06);
        }
        """
    else:
        vars_css = """
        :root{
          --bg: #f5f7fa;
          --card-bg: #ffffff;
          --text: #0f172a;
          --muted: #6b7280;
          --accent: #2563eb;
          --control-bg: #ffffff;
          --control-border: #e6eef8;
        }
        """

    # CSS ciblé — n'utilise pas html, body global pour éviter de masquer l'UI
    common_css = r"""
    /* Appliquer le fond à la zone Streamlit principale */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
      background: var(--bg) !important;
      color: var(--text) !important;
    }

    /* Titres / markdown */
    .stMarkdown, .stText, [data-testid="stMarkdownContainer"] { color: var(--text) !important; }

    /* Inputs textuels */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    textarea {
      background: var(--control-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
    }

    /* Selectbox visible */
    .stSelectbox>div>div>select, select {
      background: var(--control-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 8px !important;
      padding: 6px 8px !important;
    }

    /* Boutons */
    .stButton>button, .stDownloadButton>button {
      background: linear-gradient(135deg,var(--accent),#1e40af) !important;
      color: #ffffff !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      border: none !important;
      font-weight: 600 !important;
    }

    /* Sidebar (lisibilité) */
    section[data-testid="stSidebar"] { background: linear-gradient(180deg,#071033,#0f172a) !important; color: var(--text) !important; }

    /* Expander / panels */
    .stExpander { background: var(--card-bg) !important; border-radius: 8px !important; border: 1px solid var(--control-border) !important; }

    /* Aperçu SVG */
    [data-testid="stMarkdownContainer"] > div > div > svg { max-width:100% !important; height:auto !important; display:block !important; margin:8px auto !important; }

    /* Header toggle area */
    .header-toggle { display:flex; justify-content:flex-end; align-items:center; gap:8px; }
    .header-toggle img { width:22px; height:22px; border-radius:6px; }

    @media (max-width:800px) {
      .header-toggle img { width:20px; height:20px; }
    }
    """

    full_css = f"<style>{vars_css}\n{common_css}</style>"
    # Injection via st.markdown (plus sûre pour éviter certains comportements de components.html)
    st.markdown(full_css, unsafe_allow_html=True)

# Injecter le CSS initial AVANT la création des widgets
inject_theme_css(st.session_state["theme"])

# Affichage immédiat d'un en-tête visible pour vérifier que l'UI est rendue
# (Si tu ne vois pas ce titre, l'app est bloquée avant d'arriver ici)
st.markdown(
    f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
      <div style="font-weight:700;font-size:18px;color:var(--text)">Générateur officiel de permis CA</div>
      <div class="header-toggle">
        <img src="{ICON_DARK if st.session_state['theme']=='light' else ICON_LIGHT}" alt="theme" />
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Toggle discret (bouton Streamlit minimal) — placer après l'en-tête si tu veux un contrôle actif
cols = st.columns([9,1])
with cols[1]:
    # bouton minimal ; label " " pour rester discret
    if st.button(" ", key="__theme_toggle_button__", help="Basculer thème"):
        toggle_theme()
