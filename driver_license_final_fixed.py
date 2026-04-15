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

# --- PACKAGES OPTIONNELS ---
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    _REPORTLAB_AVAILABLE = False

_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

try:
    from aamva_utils import GS as AAMVA_GS
    _AAMVA_UTILS_AVAILABLE = True
except Exception:
    _AAMVA_UTILS_AVAILABLE = False
    AAMVA_GS = None

GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Permis CA", layout="wide")

# --- GESTION DU THÈME ---
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

def toggle_theme():
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'

# --- CSS DYNAMIQUE ---
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
.card {{
    background: var(--card-bg); border: 1px solid var(--control-border);
    border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}
</style>
""", unsafe_allow_html=True)

# --- ZIP DB LOGIC ---
ZIP_DB = {"94102": {"city": "San Francisco", "state": "CA"}, "95818": {"city": "Sacramento", "state": "CA"}}

def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=5)
        return resp.text if resp.status_code == 200 else None
    except: return None

def parse_zipdb_text(text: str) -> Dict:
    db = {}
    if not text: return db
    lines =
    i = 0
    while i + 2 < len(lines):
        z, c, s = lines[i], lines[i+1], lines[i+2].upper()
        if re.fullmatch(r"\d{5}", z) and s == "CA":
            db[z] = {"city": c.title(), "state": "CA"}
            i += 3
        else: i += 1
    return db

# --- UI HEADER ---
c_title, c_tk = st.columns([0.9, 0.1])
with c_title: st.title("Générateur officiel de permis CA")
with c_tk: 
    st.button("☀️" if st.session_state.theme == "dark" else "🌙", on_click=toggle_theme)

# --- FORMULAIRE ---
last_name = st.text_input("Nom de famille", "HAMMS")
first_name = st.text_input("Prénom", "AVIVA")
sex = st.selectbox("Sexe", ["M", "F", "X"])
dob = st.text_input("Date de naissance", "1980/01/01")

col_dim1, col_dim2 = st.columns(2)
with col_dim1:
    feet = st.number_input("Pieds", value=5)
    weight = st.number_input("Poids (lbs)", value=160)
with col_dim2:
    inches = st.number_input("Pouces", value=10)
    eyes = st.selectbox("Yeux", ["BRN", "BLU", "GRN", "HAZ"])

hair = st.text_input("Cheveux", "BRN")
dl_class = st.text_input("Classe", "C")
restrictions = st.text_input("Restrictions", "NONE")
endorsements = st.text_input("Endorsements", "NONE")
issue_date = st.text_input("Date d'émission", "2026/04/15")
address = st.text_input("Address Line", "1570 24TH STREET")
zip_code = st.text_input("Code postal", "95818")

# --- APERÇU ---
st.markdown("---")
st.markdown(f"""
<div class="card">
    <h3 style="color:var(--accent); margin:0;">CALIFORNIA DRIVER LICENSE</h3>
    <div style="display: flex; margin-top:15px;">
        <div style="width:100px; height:120px; background:var(--bg); border:1px dashed var(--muted); border-radius:8px;"></div>
        <div style="margin-left:20px;">
            <p style="margin:0;"><b>{last_name.upper()}, {first_name.upper()}</b></p>
            <p style="margin:0; font-size:0.9em;">{address}<br>CA {zip_code}</p>
            <p style="font-size:0.8em; margin-top:10px; opacity:0.8;">
                DOB: {dob} | SEX: {sex} | HT: {feet}'{inches}" | WGT: {weight} lb<br>
                EYES: {eyes} | HAIR: {hair} | CLASS: {dl_class}
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
