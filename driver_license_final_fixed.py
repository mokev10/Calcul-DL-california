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

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except:
    _REPORTLAB_AVAILABLE = False
    ImageReader = None

try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except:
    _PDF417_AVAILABLE = False

GS = "\x1E"

st.set_page_config(page_title="Permis CA", layout="wide")

# -------------------------
# DATA
# -------------------------
ZIP_DB = {
    "94015": {"city": "Daly City"},
    "94601": {"city": "Oakland"},
    "94102": {"city": "San Francisco"},
    "90001": {"city": "Los Angeles"},
    "92101": {"city": "San Diego"},
}

ZIP_TO_CITIES = {z: [v["city"]] for z, v in ZIP_DB.items()}
CITY_TO_ZIPS = {}
for z, v in ZIP_DB.items():
    CITY_TO_ZIPS.setdefault(v["city"], []).append(z)

FIELD_OFFICES = [
    "San Francisco (503)",
    "Oakland (501)",
    "Los Angeles (502)",
    "San Diego (707)"
]

# -------------------------
# CSS (injecté proprement)
# -------------------------
CSS = """
.card {
  width:520px;
  margin:auto;
  padding:16px;
  border-radius:12px;
  background:#fff;
  box-shadow:0 10px 30px rgba(0,0,0,0.08);
}
.photo {
  width:90px;
  height:110px;
  background:#eee;
}
"""

components.html(f"<style>{CSS}</style>", height=0)

# -------------------------
# UTILS
# -------------------------
def seed(*args):
    return int(hashlib.md5("|".join(map(str, args)).encode()).hexdigest()[:8], 16)

def rdigits(rng, n):
    return "".join(rng.choice("0123456789") for _ in range(n))

def rletter(rng, initial):
    return initial[0].upper() if initial else rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# -------------------------
# CALLBACKS
# -------------------------
def on_zip_change():
    z = st.session_state["zip"]
    if z in ZIP_TO_CITIES:
        st.session_state["city"] = ZIP_TO_CITIES[z][0]

def on_city_change():
    c = st.session_state["city"]
    if c in CITY_TO_ZIPS:
        st.session_state["zip"] = CITY_TO_ZIPS[c][0]

# -------------------------
# UI
# -------------------------
st.title("Générateur permis CA")

ln = st.text_input("Nom", "DOE")
fn = st.text_input("Prénom", "JOHN")
sex = st.selectbox("Sexe", ["M", "F"])
dob = st.date_input("Naissance", datetime.date(1990,1,1))

zip_options = ["Choisir"] + list(ZIP_TO_CITIES.keys())
city_options = ["Choisir"] + list(CITY_TO_ZIPS.keys())

if "zip" not in st.session_state:
    st.session_state["zip"] = "Choisir"
if "city" not in st.session_state:
    st.session_state["city"] = "Choisir"

col1, col2 = st.columns(2)

with col1:
    st.selectbox("ZIP", zip_options, key="zip", on_change=on_zip_change)

with col2:
    st.selectbox("Ville", city_options, key="city", on_change=on_city_change)

office = st.selectbox("Field Office", ["Choisir"] + FIELD_OFFICES)

generate = st.button("Générer")

# -------------------------
# GENERATION
# -------------------------
if generate:

    if st.session_state["zip"] == "Choisir" or st.session_state["city"] == "Choisir":
        st.error("ZIP et Ville obligatoires")
        st.stop()

    rng = random.Random(seed(ln, fn, dob))

    dl = rletter(rng, ln) + rdigits(rng, 7)

    iss = datetime.date.today()
    exp = datetime.date(iss.year + 5, dob.month, min(dob.day, 28))

    fields = {
        "DAQ": dl,
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAI": st.session_state["city"].upper(),
        "DAK": st.session_state["zip"],
    }

    payload = "@ANSI" + "".join(f"{k}{v}" for k,v in fields.items())

    # UI CARD
    html = f"""
    <div class="card">
        <h3>Driver License</h3>
        <b>{ln} {fn}</b><br>
        {st.session_state["city"]} / {st.session_state["zip"]}<br>
        DL: {dl}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # PDF417
    if _PDF417_AVAILABLE:
        codes = encode(payload.encode(), columns=6, security_level=2)
        svg = render_svg(codes)
        st.components.v1.html(str(svg), height=200)

    # PDF
    if _REPORTLAB_AVAILABLE:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer)
        c.drawString(100,750,"DRIVER LICENSE")
        c.drawString(100,730,f"{ln} {fn}")
        c.drawString(100,710,f"{st.session_state['city']} {st.session_state['zip']}")
        c.save()
        buffer.seek(0)

        st.download_button("Télécharger PDF", buffer, "dl.pdf")
