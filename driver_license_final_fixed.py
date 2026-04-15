# THEME TOGGLE BLOCK — Coller intégralement en haut de votre script Streamlit (avant tout widget)
# - Gestion du thème via st.session_state
# - Injection CSS dynamique (:root variables) pour light / dark
# - Sélecteurs ciblés pour st.button, st.text_input, st.selectbox (lisibilité)
# - Toggle discret en en-tête utilisant les icônes fournies (liens)
# - Prêt à copier-coller, bloc complet et autonome

import streamlit as st
import streamlit.components.v1 as components

# Icônes fournies (utiliser ces URLs pour l'icône du toggle)
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# --- Initialisation de l'état du thème ---
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"  # valeur par défaut

# --- Fonction pour basculer le thème ---
def toggle_theme():
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    inject_theme_css(st.session_state["theme"])
    # Essayer de forcer un rerun pour appliquer immédiatement (protégé)
    try:
        st.experimental_rerun()
    except Exception:
        # Si rerun indisponible, on met un petit flag query param (non bloquant)
        try:
            st.experimental_set_query_params(_theme_changed=st.session_state["theme"])
        except Exception:
            pass

# --- Fonction d'injection CSS dynamique (variables :root + règles ciblées) ---
def inject_theme_css(theme: str) -> None:
    """
    Injecte du CSS complet adapté au thème.
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

    # CSS complet et explicite pour widgets courants (st.button, st.text_input, st.selectbox)
    common_css = r"""
    /* Global */
    html, body, [class*="css"] { background: var(--bg) !important; color: var(--text) !important; font-family: Inter, sans-serif !important; }

    /* Card / container personnalisé */
    .card { background: var(--card-bg) !important; color: var(--text) !important; border: 1px solid var(--control-border) !important; border-radius: 10px !important; padding: 12px !important; }

    /* Inputs / selects / textareas : forcer lisibilité */
    input[type="text"], input[type="number"], textarea, select,
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>select {
      background: var(--control-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
      box-shadow: none !important;
      caret-color: var(--text) !important;
    }

    /* Placeholder and option colors */
    input::placeholder, textarea::placeholder, select::placeholder, .stSelectbox select option {
      color: var(--muted) !important;
      background: var(--control-bg) !important;
    }

    /* Select truncation */
    .stSelectbox select, select {
      white-space: nowrap !important;
      overflow: hidden !important;
      text-overflow: ellipsis !important;
      max-width: 100% !important;
      color: var(--text) !important;
      background: var(--control-bg) !important;
    }

    /* Buttons Streamlit : couleur d'accent et texte lisible */
    .stButton>button, .stDownloadButton>button {
      background: linear-gradient(135deg,var(--accent),#1e40af) !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
      font-weight: 600 !important;
    }

    /* Focus visible pour accessibilité */
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus, textarea:focus {
      outline: none !important;
      box-shadow: 0 6px 18px rgba(37,99,235,0.12) !important;
      border-color: var(--accent) !important;
    }

    /* Sidebar styling (force lisibilité) */
    section[data-testid="stSidebar"] { background: linear-gradient(180deg,#071033,#0f172a) !important; color: var(--text) !important; }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .css-1d391kg { color: var(--text) !important; }

    /* Expander / panels */
    .stExpander { background: var(--card-bg) !important; border-radius: 8px !important; border: 1px solid var(--control-border) !important; }

    /* Progress bar */
    div[data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,var(--accent),#1e40af) !important; border-radius:8px !important; }

    /* PDF417 / SVG preview */
    [data-testid="stMarkdownContainer"] > div > div > svg { max-width: 100% !important; height: auto !important; display: block !important; margin: 8px auto !important; }

    /* Header toggle area (icône) */
    .header-toggle { display:flex; justify-content:flex-end; align-items:center; gap:8px; }
    .header-toggle img.theme-icon { width:22px; height:22px; border-radius:6px; display:inline-block; }

    /* Small screens adjustments */
    @media (max-width:800px) {
      .card { width:92% !important; padding:10px !important; }
      .header-toggle img.theme-icon { width:20px; height:20px; }
    }
    """

    full_css = f"<style>{vars_css}\n{common_css}</style>"
    # Injection invisible (height=0) pour ne pas afficher le CSS brut
    components.html(full_css, height=0)

# --- Injecter le CSS initial AVANT la création des widgets ---
inject_theme_css(st.session_state["theme"])

# --- Interface de contrôle discrète (icône seule en en-tête) ---
# Placez ce bloc juste après l'injection CSS et avant vos widgets principaux
header_col_left, header_col_right = st.columns([9, 1])
with header_col_left:
    # Optionnel : titre principal (laisser vide si vous préférez)
    pass
with header_col_right:
    current = st.session_state["theme"]
    # On affiche l'icône correspondant au mode qui sera activé au clic (affiche l'icône du mode cible)
    target = "dark" if current == "light" else "light"
    icon_to_show = ICON_DARK if target == "dark" else ICON_LIGHT
    # Rendu de l'icône cliquable : image + bouton invisible pour déclencher toggle côté serveur
    st.markdown(f'''
        <div class="header-toggle">
          <a href="javascript:void(0)" onclick="document.getElementById('__theme_toggle_button__').click();" title="Basculer en {target} mode">
            <img src="{icon_to_show}" class="theme-icon" alt="theme-toggle" />
          </a>
        </div>
        ''', unsafe_allow_html=True)
    # Bouton Streamlit invisible (label minimal) pour déclencher la fonction Python côté serveur
    if st.button(" ", key="__theme_toggle_button__", help="Basculer thème"):
        toggle_theme()
