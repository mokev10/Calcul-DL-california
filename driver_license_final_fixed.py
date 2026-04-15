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

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Permis CA", layout="wide", initial_sidebar_state="collapsed")

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# --- LOGIQUE CSS DYNAMIQUE ---
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
  --control-border: rgba(255,255,255,0.06);
  --photo-bg: #1e293b;
}
"""

COMMON_CSS = """
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* Card Style */
.card {
    width: 100%;
    max-width: 520px;
    margin: 18px auto;
    padding: 20px;
    border-radius: 12px;
    background: var(--card-bg);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    border: 1px solid var(--control-border);
    color: var(--text);
}

/* Photo Placeholder */
.photo {
    width: 96px;
    height: 120px;
    background: var(--photo-bg);
    border-radius: 10px;
    border: 1px dashed var(--muted);
}

/* Widgets Streamlit */
.stTextInput input, .stSelectbox select, .stNumberInput input {
    background-color: var(--control-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--control-border) !important;
}

.stButton button {
    background: linear-gradient(135deg, var(--accent), #1e40af) !important;
    color: white !important;
    border: none !important;
    width: 100%;
}

[data-testid="stSidebar"] {
    background-color: var(--card-bg) !important;
}
</style>
"""

# Injection des styles
theme_vars = DARK_VARS if st.session_state.theme == 'dark' else LIGHT_VARS
st.markdown(f"<style>{theme_vars}</style>", unsafe_allow_html=True)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# --- ENTÊTE ET TOGGLE ---
col_t1, col_t2 = st.columns([0.9, 0.1])
with col_t2:
    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    st.button(icon, on_click=toggle_theme)

with col_t1:
    st.title("Système de Permis Californie")

# --- BASE DE DONNÉES ZIP ---
ZIP_DB = {
    "94925": {"city": "Corte Madera", "state": "CA"},
    "95818": {"city": "Sacramento", "state": "CA"},
    "94102": {"city": "San Francisco", "state": "CA"},
    "90001": {"city": "Los Angeles", "state": "CA"},
}

# --- FORMULAIRE ---
st.subheader("Informations du titulaire")
col1, col2 = st.columns(2)

with col1:
    last_name = st.text_input("Nom de famille", "DOE")
    first_name = st.text_input("Prénom", "JOHN")
    zip_code = st.text_input("Code ZIP", "94102")

with col2:
    dob = st.date_input("Date de naissance", datetime.date(1990, 1, 1))
    sex = st.selectbox("Sexe", ["M", "F", "X"])
    eye_color = st.selectbox("Yeux", ["BRN", "BLU", "GRN", "HAZ"])

# --- APERÇU ---
st.markdown("---")
st.subheader("Aperçu de la carte")

city_info = ZIP_DB.get(zip_code, {"city": "UNKNOWN", "state": "CA"})

st.markdown(f"""
<div class="card">
    <div style="display: flex; justify-content: space-between;">
        <div>
            <div class="photo"></div>
            <p style="font-size:10px; text-align:center; margin-top:5px;">PHOTO</p>
        </div>
        <div style="flex-grow: 1; margin-left: 20px;">
            <h2 style="margin:0; color:var(--accent);">CALIFORNIA</h2>
            <p style="margin:0; font-weight:bold; font-size:1.2em;">DL {random.randint(1000000, 9999999)}</p>
            <div style="margin-top:10px;">
                <span class="label">LN:</span> <span class="value">{last_name}</span><br>
                <span class="label">FN:</span> <span class="value">{first_name}</span><br>
                <span class="label">DOB:</span> <span class="value">{dob}</span><br>
                <span class="label">SEX:</span> <span class="value">{sex}</span> | 
                <span class="label">EYES:</span> <span class="value">{eye_color}</span>
            </div>
            <div style="margin-top:10px; font-size:0.9em; opacity:0.8;">
                {city_info['city']}, {city_info['state']} {zip_code}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.success(f"Mode actuel : {st.session_state.theme.upper()}")
