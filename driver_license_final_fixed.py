#!/usr/bin/env python3
# driver_license_final_fixed.py

import base64
import datetime
import hashlib
import io
import random
import re
from typing import Dict, List, Optional

import requests
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
st.set_page_config(page_title="Permis CA", layout="wide")

# ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    _REPORTLAB_AVAILABLE = False

# pdf417gen
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# ---------- CSS DYNAMIQUE ----------
LIGHT_VARS = """
:root {
  --bg: #f5f7fa;
  --card-bg: #ffffff;
  --text: #0f172a;
  --muted: #6b7280;
  --accent: #2563eb;
  --control-bg: #ffffff;
  --control-border: #e6eef8;
  --photo-bg: #eef2ff;
}
"""
DARK_VARS = """
:root {
  --bg: #0b1220;
  --card-bg: #0f172a;
  --text: #e6eef8;
  --muted: #9aa6bf;
  --accent: #60a5fa;
  --control-bg: #0f172a;
  --control-border: rgba(255,255,255,0.1);
  --photo-bg: #1e293b;
}
"""

COMMON_CSS = """
<style>
/* Global App Container */
.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Card Container */
.card {
    width: 520px;
    margin: 18px auto;
    padding: 20px;
    border-radius: 12px;
    background: var(--card-bg);
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    border: 1px solid var(--control-border);
    color: var(--text);
}

/* Photo Box */
.photo {
    width: 96px;
    height: 120px;
    background: var(--photo-bg);
    border-radius: 10px;
    border: 1px dashed var(--muted);
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Labels and Values */
.label { opacity: 0.7; font-size: 11px; color: var(--muted); }
.value { font-weight: 600; color: var(--text); }

/* Inputs / Selects / Widgets */
input[type="text"], input[type="number"], select, .stTextInput div div, .stSelectbox div div {
    background-color: var(--control-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--control-border) !important;
    border-radius: 8px !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, var(--accent), #1e40af) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    transition: 0.3s;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--card-bg) !important;
}
</style>
"""

# Injection CSS
theme_vars = DARK_VARS if st.session_state.theme == 'dark' else LIGHT_VARS
st.markdown(f"<style>{theme_vars}</style>", unsafe_allow_html=True)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ---------- DATA ----------
ZIP_DB = {
    "94925": {"city": "Corte Madera", "state": "CA"},
    "95818": {"city": "Sacramento", "state": "CA"},
    "94102": {"city": "San Francisco", "state": "CA"},
    "90001": {"city": "Los Angeles", "state": "CA"},
}

# ---------- HEADER & TOGGLE ----------
col_head, col_switch = st.columns([0.85, 0.15])
with col_switch:
    label = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
    st.button(label, on_click=toggle_theme)

with col_head:
    st.title("California Driver License System")

# ---------- FORMULAIRE ----------
with st.expander("📝 Informations du Titulaire", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        last_name = st.text_input("Nom", "DOE")
        first_name = st.text_input("Prénom", "JOHN")
        zip_input = st.text_input("Code ZIP", "94102")
    with c2:
        dob = st.date_input("Date de naissance", datetime.date(1995, 5, 20))
        sex = st.selectbox("Sexe", ["M", "F", "X"])
        eyes = st.selectbox("Yeux", ["BRN", "BLU", "GRN", "HAZ"])

# ---------- APERÇU DE LA CARTE ----------
st.markdown("---")
city_data = ZIP_DB.get(zip_input, {"city": "UNKNOWN", "state": "CA"})

st.markdown(f"""
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div>
            <div class="photo">
                <span style="font-size: 10px; color: var(--muted);">PHOTO</span>
            </div>
        </div>
        <div style="flex-grow: 1; margin-left: 20px;">
            <h2 style="margin:0; color:var(--accent); font-family: sans-serif; letter-spacing: 2px;">CALIFORNIA</h2>
            <p style="margin:0; font-weight:bold; font-size:1.1em; color: var(--text);">DL {random.randint(1000000, 9999999)}</p>
            
            <div style="margin-top:12px; line-height: 1.4;">
                <span class="label">LN:</span> <span class="value">{last_name.upper()}</span><br>
                <span class="label">FN:</span> <span class="value">{first_name.upper()}</span><br>
                <span class="label">DOB:</span> <span class="value">{dob}</span><br>
                <span class="label">SEX:</span> <span class="value">{sex}</span> | 
                <span class="label">EYES:</span> <span class="value">{eyes}</span>
            </div>
            
            <div style="margin-top:10px; font-size:0.85em; text-transform: uppercase;">
                {city_data['city']}, {city_data['state']} {zip_input}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- FOOTER / STATUS ----------
st.markdown("---")
st.caption(f"Système opérationnel | Mode : {st.session_state.theme.upper()} | PDF Engine : {'OK' if _REPORTLAB_AVAILABLE else 'Missing'}")
