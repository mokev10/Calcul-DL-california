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

# --- CONFIGURATION ---
st.set_page_config(page_title="Générateur officiel de permis CA", layout="wide")

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# ---------- CSS DYNAMIQUE COMPLET ----------
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
.stApp { background-color: var(--bg) !important; color: var(--text) !important; }

/* Champs de saisie */
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
}

/* Labels */
label, .stMarkdown p { color: var(--text) !important; font-weight: 500; font-size: 14px; }

/* Carte Aperçu */
.dl-card {
    background: var(--card-bg);
    border: 1px solid var(--control-border);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}
</style>
"""

st.markdown(f"<style>{theme_vars}</style>", unsafe_allow_html=True)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ---------- INTERFACE UTILISATEUR ----------
col_title, col_toggle = st.columns([0.9, 0.1])
with col_title:
    st.title("Générateur officiel de permis CA")
with col_switch := col_toggle:
    icon = "☀️" if st.session_state.theme == "dark" else "🌙"
    st.button(icon, on_click=toggle_theme)

# --- REPRODUCTION EXACTE DE TES CHAMPS ---
last_name = st.text_input("Nom de famille", "HAMMS")
first_name = st.text_input("Prénom", "AVIVA")
sex = st.selectbox("Sexe", ["M", "F", "X"], index=0)
dob = st.text_input("Date de naissance", "1980/01/01")

c1, c2 = st.columns(2)
with c1:
    feet = st.number_input("Pieds", value=5)
    weight = st.number_input("Poids (lbs)", value=160)
with c2:
    inches = st.number_input("Pouces", value=10)
    eyes = st.selectbox("Yeux", ["BRN", "BLU", "GRN", "HAZ"], index=0)

hair = st.text_input("Cheveux", "BRN")
dl_class = st.text_input("Classe", "C")
restrictions = st.text_input("Restrictions", "NONE")
endorsements = st.text_input("Endorsements", "NONE")
issue_date = st.text_input("Date d'émission", "2026/04/15")
address = st.text_input("Address Line", "1570 24TH STREET")
zip_code = st.text_input("Code postal", "95818")

# --- APERÇU (Optionnel pour vérifier les données) ---
st.markdown("---")
st.subheader("Aperçu des données")
st.markdown(f"""
<div class="dl-card">
    <b>{first_name} {last_name}</b><br>
    {address}, SACRAMENTO, CA {zip_code}<br><br>
    <small>DOB: {dob} | SEX: {sex} | HT: {feet}'{inches}" | WGT: {weight} lb</small><br>
    <small>ISS: {issue_date} | CLASS: {dl_class} | EYES: {eyes} | HAIR: {hair}</small>
</div>
""", unsafe_allow_html=True)

st.success(f"Mode {st.session_state.theme.upper()} activé.")
