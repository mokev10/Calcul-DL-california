# THEME TOGGLE SAFE BLOCK — Coller intégralement en haut du script (avant tout widget)
# - Gestion du thème via st.session_state
# - Injection CSS ciblée et sûre (évite sélecteurs trop larges)
# - Compatibilité st.button, st.text_input, st.selectbox
# - Toggle discret en en-tête utilisant les icônes fournies

import streamlit as st
import streamlit.components.v1 as components

# Icônes fournies
ICON_DARK = "https://img.icons8.com/external-inkubators-glyph-inkubators/24/external-night-mode-ecommerce-user-interface-inkubators-glyph-inkubators.png"
ICON_LIGHT = "https://img.icons8.com/external-flat-icons-inmotus-design/24/external-bright-printer-control-ui-elements-flat-icons-inmotus-design.png"

# Initialisation du thème dans la session
if "theme" not in st.session_state:
    st.session_state["theme"] = "light"  # valeur par défaut

def toggle_theme():
    """Basculer le thème et réinjecter le CSS. Essayer de rerun si possible."""
    st.session_state["theme"] = "dark" if st.session_state["theme"] == "light" else "light"
    inject_theme_css(st.session_state["theme"])
    try:
        st.experimental_rerun()
    except Exception:
        # fallback non bloquant : on met un petit flag query param si possible
        try:
            st.experimental_set_query_params(_theme_changed=st.session_state["theme"])
        except Exception:
            pass

def inject_theme_css(theme: str) -> None:
    """
    Injecte du CSS ciblé et sûr.
    - Ne pas utiliser des sélecteurs globaux qui affectent tout le DOM.
    - Appliquer le fond sur .stApp et cibler explicitement widgets et markdown.
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

    # CSS ciblé — évite d'écraser tout le DOM
    common_css = r"""
    /* Appliquer le fond uniquement à la zone principale Streamlit */
    .stApp, .main, [data-testid="stAppViewContainer"] {
      background: var(--bg) !important;
    }

    /* Conteneurs personnalisés (cartes) */
    .card {
      background: var(--card-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 10px !important;
      padding: 12px !important;
    }

    /* Markdown / textes explicatifs */
    .stMarkdown, .stText, .css-1d391kg, [data-testid="stMarkdownContainer"] {
      color: var(--text) !important;
    }

    /* Inputs textuels */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    textarea {
      background: var(--control-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 8px !important;
      padding: 8px 10px !important;
      box-shadow: none !important;
    }

    /* Selectbox visible */
    .stSelectbox>div>div>select, select {
      background: var(--control-bg) !important;
      color: var(--text) !important;
      border: 1px solid var(--control-border) !important;
      border-radius: 8px !important;
      padding: 6px 8px !important;
      text-overflow: ellipsis !important;
    }

    /* Placeholder / options */
    .stSelectbox select option, select option {
      color: var(--text) !important;
      background: var(--control-bg) !important;
    }

    /* Boutons Streamlit */
    .stButton>button, .stDownloadButton>button {
      background: linear-gradient(135deg,var(--accent),#1e40af) !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 8px 12px !important;
      font-weight: 600 !important;
      box-shadow: 0 6px 18px rgba(0,0,0,0.08) !important;
    }

    /* Sidebar (force lisibilité) */
    section[data-testid="stSidebar"] {
      background: linear-gradient(180deg,#071033,#0f172a) !important;
      color: var(--text) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] .css-1d391kg {
      color: var(--text) !important;
    }

    /* Expander / panels */
    .stExpander {
      background: var(--card-bg) !important;
      border-radius: 8px !important;
      border: 1px solid var(--control-border) !important;
    }

    /* Aperçu SVG / PDF417 */
    [data-testid="stMarkdownContainer"] > div > div > svg {
      max-width: 100% !important;
      height: auto !important;
      display: block !important;
      margin: 8px auto !important;
    }

    /* Header toggle area */
    .header-toggle { display:flex; justify-content:flex-end; align-items:center; gap:8px; }
    .header-toggle img.theme-icon { width:22px; height:22px; border-radius:6px; display:inline-block; }

    /* Small screens */
    @media (max-width:800px) {
      .card { width:92% !important; padding:10px !important; }
      .header-toggle img.theme-icon { width:20px; height:20px; }
    }
    """

    full_css = f"<style>{vars_css}\n{common_css}</style>"
    # Injection invisible (height=0) pour ne pas afficher le CSS brut
    components.html(full_css, height=0)

# Injecter le CSS initial AVANT la création des widgets
inject_theme_css(st.session_state["theme"])

# --- Toggle discret en en-tête (icône cliquable) ---
# Placer ce bloc juste après l'injection CSS et avant vos widgets principaux
header_col_left, header_col_right = st.columns([9, 1])
with header_col_left:
    # Optionnel : titre principal (laisser vide si vous préférez)
    pass
with header_col_right:
    current = st.session_state["theme"]
    # Affiche l'icône du mode cible (cliquer active ce mode)
    target = "dark" if current == "light" else "light"
    icon_to_show = ICON_DARK if target == "dark" else ICON_LIGHT
    # Affiche l'image (icône) et un bouton discret pour déclencher la bascule côté serveur
    st.image(icon_to_show, width=22)
    if st.button(" ", key="__theme_toggle_button__", help=f"Basculer en {target} mode"):
        toggle_theme()
