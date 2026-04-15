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

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Générateur officiel de permis CA", layout="wide")

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# --- CSS DYNAMIQUE ---
theme_vars = """
:root {
  --bg: #0b1220;
  --card-bg: #0f172a;
  --text: #e6eef8;
  --muted: #9aa6bf;
  --accent: #60a5fa;
  --control-bg: #1e293b;
  --control-border: rgba(255,255,255,0.1);
}
""" if st.session_state.theme == 'dark' else """
:root {
  --bg: #f8fafc;
  --card-bg: #ffffff;
  --text: #0f172a;
  --muted: #64748b;
  --accent: #2563eb;
  --control-bg: #ffffff;
  --control-border: #e2e8f0;
}
"""

COMMON_CSS = """
<style>
/* Background global */
.stApp { background-color: var(--bg) !important; color: var(--text) !important; }

/* Inputs et Widgets */
input, select, textarea, .stTextInput div div, .stSelectbox div div, .stNumberInput div div {
    background-color: var(--control-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--control-border) !important;
    border-radius: 4px !important;
}

/* Boutons */
.stButton button {
    background-color: var(--control-bg) !important;
    border: 1px solid var(--control-border) !important;
    color: var(--text) !important;
    border-radius: 4px !important;
    font-size: 20px !important;
    padding: 0px 10px !important;
}

/* Labels */
label, .stMarkdown p { color: var(--text) !important; font-weight: 500; }

/* Aperçu de la carte */
.dl-card {
    background: var(--card-bg);
    border: 1px solid var(--control-border);
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
</style>
"""

st.markdown(f"<style>{theme_vars}</style>", unsafe_allow_html=True)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# --- ENTÊTE ---
col_title, col_toggle = st.columns([0.9, 0.1])
with col_title:
    st.title("Générateur officiel de permis CA")
with col_toggle:
    # Bouton avec icône Lune/Soleil
    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    st.button(icon, on_click=toggle_theme)

# --- FORMULAIRE COMPLET (REPRODUCTION DE L'IMAGE) ---
last_name = st.text_input("Nom de famille", "HAMMS")
first_name = st.text_input("Prénom", "AVIVA")
sex = st.selectbox("Sexe", ["M", "F", "X"], index=0)
dob = st.text_input("Date de naissance", "1980/01/01")

# Taille et Poids sur la même ligne
col_ht1, col_ht2 = st.columns(2)
with col_ht1:
    feet = st.number_input("Pieds", value=5)
    weight = st.number_input("Poids (lbs)", value=160)
with col_ht2:
    inches = st.number_input("Pouces", value=10)
    eyes = st.selectbox("Yeux", ["BRN", "BLU", "GRN", "HAZ"], index=0)

hair = st.text_input("Cheveux", "BRN")
dl_class = st.text_input("Classe", "C")
restrictions = st.text_input("Restrictions", "NONE")
endorsements = st.text_input("Endorsements", "NONE")
issue_date = st.text_input("Date d'émission", "2026/04/15")
address = st.text_input("Address Line", "1570 24TH STREET")
zip_code = st.text_input("Code postal", "95818")

# --- ZONE D'APERÇU ---
st.markdown("---")
st.subheader("Aperçu visuel")
st.markdown(f"""
<div class="dl-card">
    <h3 style="color:var(--accent); margin-top:0;">CALIFORNIA DRIVER LICENSE</h3>
    <div style="display: flex; justify-content: space-between;">
        <div>
            <p><b>{last_name.upper()}, {first_name.upper()}</b></p>
            <p>{address}<br>SACRAMENTO, CA {zip_code}</p>
            <p style="font-size: 0.9em; opacity: 0.8;">
                DOB: {dob} | SEX: {sex} | HAIR: {hair} | EYES: {eyes}<br>
                HT: {feet}'{inches}" | WGT: {weight} lb | CLASS: {dl_class}
            </p>
        </div>
        <div style="text-align: right; color: var(--accent); font-weight: bold;">
            DL No: {random.randint(1000000, 9999999)}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.info(f"Mode actuel : {st.session_state.theme.upper()}")
