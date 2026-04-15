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

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="California Driver License Generator", layout="wide")

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# --- CSS DYNAMIQUE (LIGHT/DARK) ---
theme_css = """
:root {
  --bg: #0b1220; --card-bg: #0f172a; --text: #e6eef8; --muted: #9aa6bf;
  --accent: #60a5fa; --control-bg: #1e293b; --control-border: rgba(255,255,255,0.1);
}
""" if st.session_state.theme == 'dark' else """
:root {
  --bg: #f8fafc; --card-bg: #ffffff; --text: #0f172a; --muted: #64748b;
  --accent: #2563eb; --control-bg: #ffffff; --control-border: #e2e8f0;
}
"""

st.markdown(f"""
<style>
{theme_css}
.stApp {{ background-color: var(--bg) !important; color: var(--text) !important; }}
input, select, textarea, .stTextInput div div, .stSelectbox div div, .stNumberInput div div {{
    background-color: var(--control-bg) !important; color: var(--text) !important;
    border: 1px solid var(--control-border) !important; border-radius: 4px !important;
}}
.stButton button {{
    background-color: var(--control-bg) !important; border: 1px solid var(--control-border) !important;
    color: var(--text) !important; border-radius: 4px !important;
}}
/* Bouton Générer spécifique */
.generate-btn button {{
    background-color: var(--accent) !important;
    color: white !important;
    font-weight: bold !important;
    border: none !important;
}}
.card {{
    background: var(--card-bg); border: 1px solid var(--control-border);
    border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    color: var(--text);
}}
</style>
""", unsafe_allow_html=True)

# --- DONNÉES & LOGIQUE ---
field_offices = ["Grand Los Angeles — Los Angeles (502)", "San Francisco (503)", "Sacramento (501)"]

# --- UI HEADER & TOGGLE ---
c_title, c_tk = st.columns([0.9, 0.1])
with c_title: 
    st.title("California Driver License System")
with c_tk: 
    st.button("☀️" if st.session_state.theme == "dark" else "🌙", on_click=toggle_theme)

# --- CHAMPS DE SAISIE (FIDÈLES À L'IMAGE) ---
st.subheader("Paramètres du document")
selected_office = st.selectbox("Field Office", field_offices)

# Bouton Générer la carte
st.markdown('<div class="generate-btn">', unsafe_allow_html=True)
if st.button("Générer la carte"):
    st.toast("Génération en cours...", icon="🎴")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Grille de saisie
col1, col2 = st.columns(2)
with col1:
    last_name = st.text_input("Nom de famille", "HARMS")
    first_name = st.text_input("Prénom", "AVIVA")
    address = st.text_input("Adresse", "1570 24TH STREET")
    city_zip = st.text_input("Ville / ZIP", "Los Angeles / 90001")

with col2:
    dob = st.text_input("Date de naissance (YYYY/MM/DD)", "1980/01/01")
    sex = st.selectbox("Sexe", ["M", "F", "X"])
    issue_exp = st.text_input("ISS / EXP", "04/15/2026 / 01/01/2031")
    dl_number = st.text_input("Numéro de permis (HXXXXXXX)", "H4075981")

# --- APERÇU FINAL ---
st.subheader("CALIFORNIA USA DRIVER LICENSE")
st.markdown(f"""
<div class="card">
    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
        <div style="display: flex;">
            <div style="width:110px; height:130px; background:var(--bg); border:1px dashed var(--muted); border-radius:8px; display:flex; align-items:center; justify-content:center;">
                <span style="font-size:10px; color:var(--muted);">PHOTO</span>
            </div>
            <div style="margin-left:25px; line-height:1.2;">
                <p style="margin:0; font-size:10px; opacity:0.6;">Nom</p>
                <p style="margin:0 0 8px 0; font-weight:bold;">{last_name.upper()}</p>
                <p style="margin:0; font-size:10px; opacity:0.6;">Prénom</p>
                <p style="margin:0 0 8px 0; font-weight:bold;">{first_name.upper()}</p>
                <p style="margin:0; font-size:10px; opacity:0.6;">Adresse</p>
                <p style="margin:0 0 8px 0;">{address.upper()}</p>
                <p style="margin:0; font-size:10px; opacity:0.6;">Ville / ZIP</p>
                <p style="margin:0 0 8px 0;">{city_zip.upper()}</p>
                <p style="margin:0; font-size:10px; opacity:0.6;">Field Office</p>
                <p style="margin:0 0 8px 0;">{selected_office}</p>
                <p style="margin:0; font-size:10px; opacity:0.6;">ISS / EXP</p>
                <p style="margin:0;">{issue_exp}</p>
            </div>
        </div>
        <div style="text-align: right;">
            <p style="margin:0; font-weight:bold; color:var(--accent); font-size:1.2em;">{dl_number}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- ZONE PDF417 (BAS DE L'IMAGE) ---
st.markdown("### PDF417")
with st.expander("Aperçu PDF417 (SVG)", expanded=True):
    st.info("Le code-barres PDF417 s'affichera ici après génération.")
    # Placeholder pour l'image du code-barres
    st.markdown('<div style="background:white; height:100px; width:100%; border-radius:4px; display:flex; align-items:center; justify-content:center; color:#333;">|||| ||| ||||| || |||| |||</div>', unsafe_allow_html=True)
