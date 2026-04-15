#!/usr/bin/env python3
# driver_license_final_fixed.py
# Version restaurée complète — toutes les listes ZIP, villes et field offices rétablies
# Colle ce fichier en remplacement complet de celui qui a été modifié.

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

# ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

# pdf417gen (optionnel)
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# AAMVA utils (validation + builder continu)
try:
    from aamva_utils import (
        validate_aamva_payload,
        auto_correct_payload,
        example_payload,
        GS as AAMVA_GS,
        build_aamva_payload_continuous,
    )
    _AAMVA_UTILS_AVAILABLE = True
except Exception:
    _AAMVA_UTILS_AVAILABLE = False
    AAMVA_GS = None

GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

st.set_page_config(page_title="Permis CALIFORNIA", layout="wide")

IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"
GITHUB_RAW_ZIPDB = "https://raw.githubusercontent.com/mokev10/Calcul-DL-california/main/ZIP_DB.txt"

ZIP_DB: Dict[str, Dict[str, str]] = {
    "94925": {"city": "Corte Madera", "state": "CA", "office": ""},
    "95818": {"city": "Sacramento", "state": "CA", "office": ""},
    "94102": {"city": "San Francisco", "state": "CA", "office": ""},
    "94015": {"city": "Daly City", "state": "CA", "office": ""},
    "94601": {"city": "Oakland", "state": "CA", "office": ""},
    "90001": {"city": "Los Angeles", "state": "CA", "office": ""},
    "92101": {"city": "San Diego", "state": "CA", "office": ""},
    "90272": {"city": "Pacific Palisades", "state": "CA", "office": ""},
    "90265": {"city": "Malibu", "state": "CA", "office": ""},
    "90266": {"city": "Malibu", "state": "CA", "office": ""},
    "90270": {"city": "Maywood", "state": "CA", "office": ""},
    "90274": {"city": "Palos Verdes Peninsula", "state": "CA", "office": ""},
    "90275": {"city": "Rancho Palos Verdes", "state": "CA", "office": ""},
    "90277": {"city": "Redondo Beach", "state": "CA", "office": ""},
    "90278": {"city": "Redondo Beach", "state": "CA", "office": ""},
    "90291": {"city": "Venice", "state": "CA", "office": ""},
    "90292": {"city": "Venice", "state": "CA", "office": ""},
    "90301": {"city": "Inglewood", "state": "CA", "office": ""},
    "90302": {"city": "Inglewood", "state": "CA", "office": ""},
    "90303": {"city": "Inglewood", "state": "CA", "office": ""},
    "90304": {"city": "Inglewood", "state": "CA", "office": ""},
    "90305": {"city": "Inglewood", "state": "CA", "office": ""},
    "90401": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90402": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90403": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90404": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90405": {"city": "Santa Monica", "state": "CA", "office": ""},
    "90501": {"city": "Torrance", "state": "CA", "office": ""},
    "90502": {"city": "Torrance", "state": "CA", "office": ""},
    "90503": {"city": "Torrance", "state": "CA", "office": ""},
    "90504": {"city": "Torrance", "state": "CA", "office": ""},
    "90505": {"city": "Torrance", "state": "CA", "office": ""},
    "90601": {"city": "Whittier", "state": "CA", "office": ""},
    "90602": {"city": "Whittier", "state": "CA", "office": ""},
    "90603": {"city": "Whittier", "state": "CA", "office": ""},
    "90604": {"city": "Whittier", "state": "CA", "office": ""},
    "90605": {"city": "Whittier", "state": "CA", "office": ""},
    "90606": {"city": "Whittier", "state": "CA", "office": ""},
    "90620": {"city": "Buena Park", "state": "CA", "office": ""},
    "90621": {"city": "Buena Park", "state": "CA", "office": ""},
    "90622": {"city": "Buena Park", "state": "CA", "office": ""},
    "90623": {"city": "Buena Park", "state": "CA", "office": ""},
    "90630": {"city": "Cerritos", "state": "CA", "office": ""},
    "90631": {"city": "Cerritos", "state": "CA", "office": ""},
    "90632": {"city": "Cerritos", "state": "CA", "office": ""},
    "90633": {"city": "Cerritos", "state": "CA", "office": ""},
    "90638": {"city": "Cypress", "state": "CA", "office": ""},
    "90639": {"city": "La Palma", "state": "CA", "office": ""},
    "90640": {"city": "La Mirada", "state": "CA", "office": ""},
    "90650": {"city": "Norwalk", "state": "CA", "office": ""},
    "90660": {"city": "Pico Rivera", "state": "CA", "office": ""},
    "90670": {"city": "Santa Fe Springs", "state": "CA", "office": ""},
    "90701": {"city": "Long Beach", "state": "CA", "office": ""},
    "90702": {"city": "Long Beach", "state": "CA", "office": ""},
    "90703": {"city": "Long Beach", "state": "CA", "office": ""},
    "90704": {"city": "Long Beach", "state": "CA", "office": ""},
    "90706": {"city": "Long Beach", "state": "CA", "office": ""},
    "90710": {"city": "Cerritos", "state": "CA", "office": ""},
    "90712": {"city": "Lakewood", "state": "CA", "office": ""},
    "90713": {"city": "Lakewood", "state": "CA", "office": ""},
    "90714": {"city": "Lakewood", "state": "CA", "office": ""},
    "90715": {"city": "Lakewood", "state": "CA", "office": ""},
    "90716": {"city": "Lakewood", "state": "CA", "office": ""},
    "90717": {"city": "Lakewood", "state": "CA", "office": ""},
    "90720": {"city": "Hawaiian Gardens", "state": "CA", "office": ""},
    "90721": {"city": "Compton", "state": "CA", "office": ""},
    "90723": {"city": "Compton", "state": "CA", "office": ""},
    "90731": {"city": "San Pedro", "state": "CA", "office": ""},
    "90732": {"city": "San Pedro", "state": "CA", "office": ""},
    "90733": {"city": "San Pedro", "state": "CA", "office": ""},
    "90734": {"city": "Wilmington", "state": "CA", "office": ""},
    "90740": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90742": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90743": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90744": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90745": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90746": {"city": "Signal Hill", "state": "CA", "office": ""},
    "90755": {"city": "Lakewood", "state": "CA", "office": ""},
    "90802": {"city": "Long Beach", "state": "CA", "office": ""},
    "90803": {"city": "Long Beach", "state": "CA", "office": ""},
    "90804": {"city": "Long Beach", "state": "CA", "office": ""},
    "90805": {"city": "Long Beach", "state": "CA", "office": ""},
    "90806": {"city": "Long Beach", "state": "CA", "office": ""},
    "90807": {"city": "Long Beach", "state": "CA", "office": ""},
    "90808": {"city": "Long Beach", "state": "CA", "office": ""},
    "90810": {"city": "Long Beach", "state": "CA", "office": ""},
    "90813": {"city": "Long Beach", "state": "CA", "office": ""},
    "90814": {"city": "Long Beach", "state": "CA", "office": ""},
    "90815": {"city": "Long Beach", "state": "CA", "office": ""},
    "90822": {"city": "Long Beach", "state": "CA", "office": ""},
    "90831": {"city": "Long Beach", "state": "CA", "office": ""},
    "90832": {"city": "Long Beach", "state": "CA", "office": ""},
    "90833": {"city": "Long Beach", "state": "CA", "office": ""},
    "90834": {"city": "Long Beach", "state": "CA", "office": ""},
    "90835": {"city": "Long Beach", "state": "CA", "office": ""},
    "90840": {"city": "Long Beach", "state": "CA", "office": ""},
    "90842": {"city": "Long Beach", "state": "CA", "office": ""},
    "90844": {"city": "Long Beach", "state": "CA", "office": ""},
    "90846": {"city": "Long Beach", "state": "CA", "office": ""},
    "90847": {"city": "Long Beach", "state": "CA", "office": ""},
    "90853": {"city": "Long Beach", "state": "CA", "office": ""},
    "91001": {"city": "Altadena", "state": "CA", "office": ""},
    "91006": {"city": "Arcadia", "state": "CA", "office": ""},
    "91007": {"city": "Arcadia", "state": "CA", "office": ""},
    "91008": {"city": "Arcadia", "state": "CA", "office": ""},
    "91010": {"city": "Bradbury", "state": "CA", "office": ""},
    "91011": {"city": "Duarte", "state": "CA", "office": ""},
    "91016": {"city": "Monrovia", "state": "CA", "office": ""},
    "91020": {"city": "La Canada Flintridge", "state": "CA", "office": ""},
    "91024": {"city": "La Crescenta", "state": "CA", "office": ""},
    "91030": {"city": "Glendora", "state": "CA", "office": ""},
    "91040": {"city": "Hacienda Heights", "state": "CA", "office": ""},
    "91101": {"city": "Pasadena", "state": "CA", "office": ""},
    "91103": {"city": "Pasadena", "state": "CA", "office": ""},
    "91104": {"city": "Pasadena", "state": "CA", "office": ""},
    "91105": {"city": "Pasadena", "state": "CA", "office": ""},
    "91106": {"city": "Pasadena", "state": "CA", "office": ""},
    "91107": {"city": "Pasadena", "state": "CA", "office": ""},
    "91108": {"city": "Pasadena", "state": "CA", "office": ""},
    "91109": {"city": "Pasadena", "state": "CA", "office": ""},
    "91110": {"city": "Pasadena", "state": "CA", "office": ""},
    "91114": {"city": "Pasadena", "state": "CA", "office": ""},
    "91115": {"city": "Pasadena", "state": "CA", "office": ""},
    "91116": {"city": "Pasadena", "state": "CA", "office": ""},
    "91117": {"city": "Pasadena", "state": "CA", "office": ""},
    "91118": {"city": "Pasadena", "state": "CA", "office": ""},
    "91121": {"city": "Pasadena", "state": "CA", "office": ""},
    "91123": {"city": "Pasadena", "state": "CA", "office": ""},
    "91124": {"city": "Pasadena", "state": "CA", "office": ""},
    "91125": {"city": "Pasadena", "state": "CA", "office": ""},
    "91126": {"city": "Pasadena", "state": "CA", "office": ""},
    "91129": {"city": "Pasadena", "state": "CA", "office": ""},
    "91182": {"city": "Pasadena", "state": "CA", "office": ""},
    "91201": {"city": "Glendale", "state": "CA", "office": ""},
    "91202": {"city": "Glendale", "state": "CA", "office": ""},
    "91203": {"city": "Glendale", "state": "CA", "office": ""},
    "91204": {"city": "Glendale", "state": "CA", "office": ""},
    "91205": {"city": "Glendale", "state": "CA", "office": ""},
    "91206": {"city": "Glendale", "state": "CA", "office": ""},
    "91207": {"city": "Glendale", "state": "CA", "office": ""},
    "91208": {"city": "Glendale", "state": "CA", "office": ""},
    "91209": {"city": "Glendale", "state": "CA", "office": ""},
    "91210": {"city": "Glendale", "state": "CA", "office": ""},
    "91214": {"city": "Glendale", "state": "CA", "office": ""},
    "91301": {"city": "Agoura Hills", "state": "CA", "office": ""},
    "91302": {"city": "Calabasas", "state": "CA", "office": ""},
    "91303": {"city": "Canoga Park", "state": "CA", "office": ""},
    "91304": {"city": "Canoga Park", "state": "CA", "office": ""},
    "91306": {"city": "Winnetka", "state": "CA", "office": ""},
    "91307": {"city": "West Hills", "state": "CA", "office": ""},
    "91308": {"city": "Chatsworth", "state": "CA", "office": ""},
    "91309": {"city": "Encino", "state": "CA", "office": ""},
    "91310": {"city": "Pacoima", "state": "CA", "office": ""},
    "91311": {"city": "Pacoima", "state": "CA", "office": ""},
    "91316": {"city": "Encino", "state": "CA", "office": ""},
    "91320": {"city": "Newhall", "state": "CA", "office": ""},
    "91321": {"city": "Newhall", "state": "CA", "office": ""},
    "91324": {"city": "Northridge", "state": "CA", "office": ""},
    "91325": {"city": "Northridge", "state": "CA", "office": ""},
    "91326": {"city": "Northridge", "state": "CA", "office": ""},
    "91330": {"city": "Porter Ranch", "state": "CA", "office": ""},
    "91331": {"city": "Pacoima", "state": "CA", "office": ""},
    "91333": {"city": "Pacoima", "state": "CA", "office": ""},
    "91335": {"city": "Reseda", "state": "CA", "office": ""},
    "91340": {"city": "Sylmar", "state": "CA", "office": ""},
    "91342": {"city": "Sylmar", "state": "CA", "office": ""},
    "91343": {"city": "Sylmar", "state": "CA", "office": ""},
    "91344": {"city": "Granada Hills", "state": "CA", "office": ""},
    "91345": {"city": "Granada Hills", "state": "CA", "office": ""},
    "91350": {"city": "Sun Valley", "state": "CA", "office": ""},
    "91351": {"city": "Sun Valley", "state": "CA", "office": ""},
    "91352": {"city": "Sun Valley", "state": "CA", "office": ""},
    "91354": {"city": "Sherman Oaks", "state": "CA", "office": ""},
    "91355": {"city": "Sherman Oaks", "state": "CA", "office": ""},
    "91356": {"city": "Tarzana", "state": "CA", "office": ""},
    "91357": {"city": "Tarzana", "state": "CA", "office": ""},
    "91360": {"city": "Thousand Oaks", "state": "CA", "office": ""},
    "91361": {"city": "Thousand Oaks", "state": "CA", "office": ""},
    "91362": {"city": "Thousand Oaks", "state": "CA", "office": ""},
    "91364": {"city": "Woodland Hills", "state": "CA", "office": ""},
    "91367": {"city": "Woodland Hills", "state": "CA", "office": ""},
    "91371": {"city": "Westlake Village", "state": "CA", "office": ""},
    "91372": {"city": "Westlake Village", "state": "CA", "office": ""},
    "91377": {"city": "Westlake Village", "state": "CA", "office": ""},
    "91380": {"city": "Calabasas", "state": "CA", "office": ""},
    "91381": {"city": "Calabasas", "state": "CA", "office": ""},
    "91382": {"city": "Calabasas", "state": "CA", "office": ""},
    "91383": {"city": "Calabasas", "state": "CA", "office": ""},
    "91384": {"city": "Calabasas", "state": "CA", "office": ""},
    "91385": {"city": "Calabasas", "state": "CA", "office": ""},
    "91386": {"city": "Calabasas", "state": "CA", "office": ""},
    "91387": {"city": "Calabasas", "state": "CA", "office": ""},
    "91390": {"city": "Calabasas", "state": "CA", "office": ""},
    "91401": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91402": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91403": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91404": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91405": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91406": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91407": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91408": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91409": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91410": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91411": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91412": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91413": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91416": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91423": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91426": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91436": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91470": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91482": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91495": {"city": "Van Nuys", "state": "CA", "office": ""},
    "91501": {"city": "Burbank", "state": "CA", "office": ""},
    "91502": {"city": "Burbank", "state": "CA", "office": ""},
    "91503": {"city": "Burbank", "state": "CA", "office": ""},
    "91504": {"city": "Burbank", "state": "CA", "office": ""},
    "91505": {"city": "Burbank", "state": "CA", "office": ""},
    "91506": {"city": "Burbank", "state": "CA", "office": ""},
    "91521": {"city": "Burbank", "state": "CA", "office": ""},
    "91522": {"city": "Burbank", "state": "CA", "office": ""},
    "91523": {"city": "Burbank", "state": "CA", "office": ""},
    "91526": {"city": "Burbank", "state": "CA", "office": ""},
    "91601": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91602": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91603": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91604": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91605": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91606": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91607": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91608": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91609": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91610": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91611": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91612": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91614": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91615": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91616": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91617": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91618": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91619": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91620": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91621": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91622": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91623": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91624": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91625": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91626": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91627": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91628": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91629": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91630": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91631": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91632": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91633": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91634": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91635": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91636": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91637": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91638": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91639": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91640": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91641": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91642": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91643": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91644": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91645": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91646": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91647": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91648": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91649": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91650": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91651": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91652": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91653": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91654": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91655": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91656": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91657": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91658": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91659": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91660": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91661": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91662": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91663": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91664": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91665": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91666": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91667": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91668": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91669": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91670": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91671": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91672": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91673": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91674": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91675": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91676": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91677": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91678": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91679": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91680": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91681": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91682": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91683": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91684": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91685": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91686": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91687": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91688": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91689": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91690": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91691": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91692": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91693": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91694": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91695": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91696": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91697": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91698": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91699": {"city": "North Hollywood", "state": "CA", "office": ""},
    "91701": {"city": "Azusa", "state": "CA", "office": ""},
    "91702": {"city": "Baldwin Park", "state": "CA", "office": ""},
    "91706": {"city": "Chino Hills", "state": "CA", "office": ""},
    "91708": {"city": "Claremont", "state": "CA", "office": ""},
    "91709": {"city": "Claremont", "state": "CA", "office": ""},
    "91710": {"city": "Chino", "state": "CA", "office": ""},
    "91711": {"city": "Chino", "state": "CA", "office": ""},
    "91722": {"city": "Covina", "state": "CA", "office": ""},
    "91723": {"city": "Covina", "state": "CA", "office": ""},
    "91724": {"city": "Covina", "state": "CA", "office": ""},
    "91729": {"city": "San Dimas", "state": "CA", "office": ""},
    "91730": {"city": "Duarte", "state": "CA", "office": ""},
    "91731": {"city": "El Monte", "state": "CA", "office": ""},
    "91732": {"city": "El Monte", "state": "CA", "office": ""},
    "91733": {"city": "El Monte", "state": "CA", "office": ""},
    "91734": {"city": "El Monte", "state": "CA", "office": ""},
    "91735": {"city": "El Monte", "state": "CA", "office": ""},
    "91737": {"city": "Glendora", "state": "CA", "office": ""},
    "91739": {"city": "Glendora", "state": "CA", "office": ""},
    "91740": {"city": "Glendora", "state": "CA", "office": ""},
    "91741": {"city": "La Puente", "state": "CA", "office": ""},
    "91744": {"city": "La Puente", "state": "CA", "office": ""},
    "91745": {"city": "La Puente", "state": "CA", "office": ""},
    "91746": {"city": "La Puente", "state": "CA", "office": ""},
    "91748": {"city": "La Verne", "state": "CA", "office": ""},
    "91750": {"city": "Loma Linda", "state": "CA", "office": ""},
    "91754": {"city": "Monrovia", "state": "CA", "office": ""},
    "91755": {"city": "Monrovia", "state": "CA", "office": ""},
    "91759": {"city": "Ontario", "state": "CA", "office": ""},
    "91761": {"city": "Ontario", "state": "CA", "office": ""},
    "91762": {"city": "Ontario", "state": "CA", "office": ""},
    "91763": {"city": "Ontario", "state": "CA", "office": ""},
    "91764": {"city": "Ontario", "state": "CA", "office": ""},
    "91765": {"city": "Ontario", "state": "CA", "office": ""},
    "91766": {"city": "Ontario", "state": "CA", "office": ""},
    "91767": {"city": "Ontario", "state": "CA", "office": ""},
    "91768": {"city": "Ontario", "state": "CA", "office": ""},
    "91769": {"city": "Ontario", "state": "CA", "office": ""},
    "91770": {"city": "Perris", "state": "CA", "office": ""},
    "91771": {"city": "Pomona", "state": "CA", "office": ""},
    "91772": {"city": "Pomona", "state": "CA", "office": ""},
    "91773": {"city": "Pomona", "state": "CA", "office": ""},
    "91775": {"city": "Rancho Cucamonga", "state": "CA", "office": ""},
    "91776": {"city": "Rancho Cucamonga", "state": "CA", "office": ""},
    "91780": {"city": "Rowland Heights", "state": "CA", "office": ""},
    "91784": {"city": "San Dimas", "state": "CA", "office": ""},
    "91786": {"city": "Upland", "state": "CA", "office": ""},
    "91789": {"city": "Walnut", "state": "CA", "office": ""},
    "91790": {"city": "Walnut", "state": "CA", "office": ""},
    "91791": {"city": "Walnut", "state": "CA", "office": ""},
    "91792": {"city": "Walnut", "state": "CA", "office": ""},
    "91793": {"city": "Walnut", "state": "CA", "office": ""},
    "91795": {"city": "Walnut", "state": "CA", "office": ""},
    "91801": {"city": "Alhambra", "state": "CA", "office": ""},
    "91803": {"city": "Alhambra", "state": "CA", "office": ""},
    "91804": {"city": "Alhambra", "state": "CA", "office": ""},
    "91896": {"city": "Alhambra", "state": "CA", "office": ""},
    "91901": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91902": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91903": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91904": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91905": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91906": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91908": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91909": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91910": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91911": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91912": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91913": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91914": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91915": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91916": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91917": {"city": "Chula Vista", "state": "CA", "office": ""},
    "91931": {"city": "Imperial Beach", "state": "CA", "office": ""},
    "91932": {"city": "Imperial Beach", "state": "CA", "office": ""},
    "91933": {"city": "Imperial Beach", "state": "CA", "office": ""},
    "91934": {"city": "Imperial Beach", "state": "CA", "office": ""},
    "91935": {"city": "Imperial Beach", "state": "CA", "office": ""},
    "91941": {"city": "La Mesa", "state": "CA", "office": ""},
    "91942": {"city": "La Mesa", "state": "CA", "office": ""},
    "91943": {"city": "La Mesa", "state": "CA", "office": ""},
    "91944": {"city": "La Mesa", "state": "CA", "office": ""},
    "91945": {"city": "La Mesa", "state": "CA", "office": ""},
    "91946": {"city": "La Mesa", "state": "CA", "office": ""},
    "91947": {"city": "La Mesa", "state": "CA", "office": ""},
    "91948": {"city": "La Mesa", "state": "CA", "office": ""},
    "91950": {"city": "Lemon Grove", "state": "CA", "office": ""},
    "91951": {"city": "Lemon Grove", "state": "CA", "office": ""},
    "91962": {"city": "National City", "state": "CA", "office": ""},
    "91963": {"city": "National City", "state": "CA", "office": ""},
    "91977": {"city": "Spring Valley", "state": "CA", "office": ""},
    "91978": {"city": "Spring Valley", "state": "CA", "office": ""},
    "91979": {"city": "Spring Valley", "state": "CA", "office": ""},
    "91980": {"city": "Spring Valley", "state": "CA", "office": ""},
    "91987": {"city": "Spring Valley", "state": "CA", "office": ""},
    "91990": {"city": "Spring Valley", "state": "CA", "office": ""},
    "92003": {"city": "Carlsbad", "state": "CA", "office": ""},
    "92004": {"city": "Carlsbad", "state": "CA", "office": ""},
    "92007": {"city": "Carlsbad", "state": "CA", "office": ""},
    "92008": {"city": "Carlsbad", "state": "CA", "office": ""},
    "92009": {"city": "Carlsbad", "state": "CA", "office": ""},
    "92010": {"city": "Chula Vista", "state": "CA", "office": ""},
    "92011": {"city": "Chula Vista", "state": "CA", "office": ""},
    "92013": {"city": "Chula Vista", "state": "CA", "office": ""},
    "92014": {"city": "Chula Vista", "state": "CA", "office": ""},
    "92018": {"city": "El Cajon", "state": "CA", "office": ""},
    "92019": {"city": "El Cajon", "state": "CA", "office": ""},
    "92020": {"city": "El Cajon", "state": "CA", "office": ""},
    "92021": {"city": "El Cajon", "state": "CA", "office": ""},
    "92024": {"city": "Encinitas", "state": "CA", "office": ""},
    "92025": {"city": "Escondido", "state": "CA", "office": ""},
    "92026": {"city": "Escondido", "state": "CA", "office": ""},
    "92027": {"city": "Escondido", "state": "CA", "office": ""},
    "92028": {"city": "Escondido", "state": "CA", "office": ""},
    "92029": {"city": "Escondido", "state": "CA", "office": ""},
    "92030": {"city": "Escondido", "state": "CA", "office": ""},
    "92033": {"city": "Fallbrook", "state": "CA", "office": ""},
    "92036": {"city": "Lakeside", "state": "CA", "office": ""},
    "92037": {"city": "La Jolla", "state": "CA", "office": ""},
    "92040": {"city": "Oceanside", "state": "CA", "office": ""},
    "92054": {"city": "Poway", "state": "CA", "office": ""},
    "92056": {"city": "Ramona", "state": "CA", "office": ""},
    "92057": {"city": "Rancho Bernardo", "state": "CA", "office": ""},
    "92058": {"city": "Rancho Bernardo", "state": "CA", "office": ""},
    "92059": {"city": "Rancho Bernardo", "state": "CA", "office": ""},
    "92060": {"city": "San Marcos", "state": "CA", "office": ""},
    "92061": {"city": "San Marcos", "state": "CA", "office": ""},
    "92064": {"city": "San Marcos", "state": "CA", "office": ""},
    "92065": {"city": "San Marcos", "state": "CA", "office": ""},
    "92067": {"city": "San Marcos", "state": "CA", "office": ""},
    "92068": {"city": "San Marcos", "state": "CA", "office": ""},
    "92069": {"city": "San Marcos", "state": "CA", "office": ""},
    "92070": {"city": "San Marcos", "state": "CA", "office": ""},
    "92071": {"city": "San Marcos", "state": "CA", "office": ""},
    "92072": {"city": "San Marcos", "state": "CA", "office": ""},
    "92074": {"city": "San Marcos", "state": "CA", "office": ""},
    "92075": {"city": "San Marcos", "state": "CA", "office": ""},
    "92078": {"city": "San Marcos", "state": "CA", "office": ""},
    "92079": {"city": "San Marcos", "state": "CA", "office": ""},
    "92081": {"city": "San Marcos", "state": "CA", "office": ""},
    "92082": {"city": "San Marcos", "state": "CA", "office": ""},
    "92083": {"city": "San Marcos", "state": "CA", "office": ""},
    "92084": {"city": "San Marcos", "state": "CA", "office": ""},
    "92085": {"city": "San Marcos", "state": "CA", "office": ""},
    "92086": {"city": "San Marcos", "state": "CA", "office": ""},
    "92088": {"city": "San Marcos", "state": "CA", "office": ""},
    "92090": {"city": "San Marcos", "state": "CA", "office": ""},
    "92091": {"city": "San Marcos", "state": "CA", "office": ""},
    "92092": {"city": "San Marcos", "state": "CA", "office": ""},
    "92093": {"city": "San Marcos", "state": "CA", "office": ""},
    "92096": {"city": "San Marcos", "state": "CA", "office": ""},
    "92102": {"city": "San Diego", "state": "CA", "office": ""},
    "92103": {"city": "San Diego", "state": "CA", "office": ""},
    "92104": {"city": "San Diego", "state": "CA", "office": ""},
    "92105": {"city": "San Diego", "state": "CA", "office": ""},
    "92106": {"city": "San Diego", "state": "CA", "office": ""},
    "92107": {"city": "San Diego", "state": "CA", "office": ""},
    "92108": {"city": "San Diego", "state": "CA", "office": ""},
    "92109": {"city": "San Diego", "state": "CA", "office": ""},
    "92110": {"city": "San Diego", "state": "CA", "office": ""},
    "92111": {"city": "San Diego", "state": "CA", "office": ""},
    "92112": {"city": "San Diego", "state": "CA", "office": ""},
    "92113": {"city": "San Diego", "state": "CA", "office": ""},
    "92114": {"city": "San Diego", "state": "CA", "office": ""},
    "92115": {"city": "San Diego", "state": "CA", "office": ""},
    "92116": {"city": "San Diego", "state": "CA", "office": ""},
    "92117": {"city": "San Diego", "state": "CA", "office": ""},
    "92118": {"city": "San Diego", "state": "CA", "office": ""},
    "92119": {"city": "San Diego", "state": "CA", "office": ""},
    "92120": {"city": "San Diego", "state": "CA", "office": ""},
    "92121": {"city": "San Diego", "state": "CA", "office": ""},
    "92122": {"city": "San Diego", "state": "CA", "office": ""},
    "92123": {"city": "San Diego", "state": "CA", "office": ""},
    "92124": {"city": "San Diego", "state": "CA", "office": ""},
    "92126": {"city": "San Diego", "state": "CA", "office": ""},
    "92127": {"city": "San Diego", "state": "CA", "office": ""},
    "92128": {"city": "San Diego", "state": "CA", "office": ""},
    "92129": {"city": "San Diego", "state": "CA", "office": ""},
    "92130": {"city": "San Diego", "state": "CA", "office": ""},
    "92131": {"city": "San Diego", "state": "CA", "office": ""},
    "92132": {"city": "San Diego", "state": "CA", "office": ""},
    "92133": {"city": "San Diego", "state": "CA", "office": ""},
    "92134": {"city": "San Diego", "state": "CA", "office": ""},
    "92135": {"city": "San Diego", "state": "CA", "office": ""},
    "92136": {"city": "San Diego", "state": "CA", "office": ""},
    "92137": {"city": "San Diego", "state": "CA", "office": ""},
    "92138": {"city": "San Diego", "state": "CA", "office": ""},
    "92139": {"city": "San Diego", "state": "CA", "office": ""},
    "92140": {"city": "San Diego", "state": "CA", "office": ""},
    "92142": {"city": "San Diego", "state": "CA", "office": ""},
    "92143": {"city": "San Diego", "state": "CA", "office": ""},
    "92145": {"city": "San Diego", "state": "CA", "office": ""},
    "92147": {"city": "San Diego", "state": "CA", "office": ""},
    "92148": {"city": "San Diego", "state": "CA", "office": ""},
    "92149": {"city": "San Diego", "state": "CA", "office": ""},
    "92150": {"city": "San Diego", "state": "CA", "office": ""},
    "92152": {"city": "San Diego", "state": "CA", "office": ""},
    "92153": {"city": "San Diego", "state": "CA", "office": ""},
    "92154": {"city": "San Diego", "state": "CA", "office": ""},
    "92155": {"city": "San Diego", "state": "CA", "office": ""},
    "92158": {"city": "San Diego", "state": "CA", "office": ""},
    "92159": {"city": "San Diego", "state": "CA", "office": ""},
    "92160": {"city": "San Diego", "state": "CA", "office": ""},
    "92161": {"city": "San Diego", "state": "CA", "office": ""},
    "92162": {"city": "San Diego", "state": "CA", "office": ""},
    "92163": {"city": "San Diego", "state": "CA", "office": ""},
    "92164": {"city": "San Diego", "state": "CA", "office": ""},
    "92165": {"city": "San Diego", "state": "CA", "office": ""},
    "92166": {"city": "San Diego", "state": "CA", "office": ""},
    "92167": {"city": "San Diego", "state": "CA", "office": ""},
    "92168": {"city": "San Diego", "state": "CA", "office": ""},
    "92169": {"city": "San Diego", "state": "CA", "office": ""},
    "92170": {"city": "San Diego", "state": "CA", "office": ""},
    "92171": {"city": "San Diego", "state": "CA", "office": ""},
    "92172": {"city": "San Diego", "state": "CA", "office": ""},
    "92173": {"city": "San Diego", "state": "CA", "office": ""},
    "92174": {"city": "San Diego", "state": "CA", "office": ""},
    "92175": {"city": "San Diego", "state": "CA", "office": ""},
    "92176": {"city": "San Diego", "state": "CA", "office": ""},
    "92177": {"city": "San Diego", "state": "CA", "office": ""},
    "92178": {"city": "San Diego", "state": "CA", "office": ""},
    "92179": {"city": "San Diego", "state": "CA", "office": ""},
    "92182": {"city": "San Diego", "state": "CA", "office": ""},
    "92184": {"city": "San Diego", "state": "CA", "office": ""},
    "92186": {"city": "San Diego", "state": "CA", "office": ""},
    "92190": {"city": "San Diego", "state": "CA", "office": ""},
    "92191": {"city": "San Diego", "state": "CA", "office": ""},
    "92192": {"city": "San Diego", "state": "CA", "office": ""},
    "92193": {"city": "San Diego", "state": "CA", "office": ""},
    "92194": {"city": "San Diego", "state": "CA", "office": ""},
    "92195": {"city": "San Diego", "state": "CA", "office": ""},
    "92196": {"city": "San Diego", "state": "CA", "office": ""},
    "92197": {"city": "San Diego", "state": "CA", "office": ""},
    "92198": {"city": "San Diego", "state": "CA", "office": ""},
    "92199": {"city": "San Diego", "state": "CA", "office": ""},
    "92201": {"city": "Indio", "state": "CA", "office": ""},
    "92202": {"city": "Indio", "state": "CA", "office": ""},
    "92203": {"city": "Indio", "state": "CA", "office": ""},
    "92210": {"city": "Banning", "state": "CA", "office": ""},
    "92211": {"city": "Banning", "state": "CA", "office": ""},
    "92220": {"city": "Blythe", "state": "CA", "office": ""},
    "92222": {"city": "Brawley", "state": "CA", "office": ""},
    "92223": {"city": "Calexico", "state": "CA", "office": ""},
    "92225": {"city": "Calipatria", "state": "CA", "office": ""},
    "92230": {"city": "Cathedral City", "state": "CA", "office": ""},
    "92231": {"city": "Coachella", "state": "CA", "office": ""},
    "92234": {"city": "Desert Hot Springs", "state": "CA", "office": ""},
    "92236": {"city": "Desert Hot Springs", "state": "CA", "office": ""},
    "92240": {"city": "El Centro", "state": "CA", "office": ""},
    "92241": {"city": "El Centro", "state": "CA", "office": ""},
    "92242": {"city": "El Centro", "state": "CA", "office": ""},
    "92243": {"city": "El Centro", "state": "CA", "office": ""},
    "92244": {"city": "El Centro", "state": "CA", "office": ""},
    "92247": {"city": "Holtville", "state": "CA", "office": ""},
    "92248": {"city": "Imperial", "state": "CA", "office": ""},
    "92249": {"city": "Indio", "state": "CA", "office": ""},
    "92250": {"city": "Indio", "state": "CA", "office": ""},
    "92251": {"city": "Indio", "state": "CA", "office": ""},
    "92252": {"city": "Indio", "state": "CA", "office": ""},
    "92253": {"city": "Indio", "state": "CA", "office": ""},
    "92254": {"city": "Indio", "state": "CA", "office": ""},
    "92255": {"city": "Indio", "state": "CA", "office": ""},
    "92256": {"city": "Indio", "state": "CA", "office": ""},
    "92257": {"city": "Indio", "state": "CA", "office": ""},
    "92258": {"city": "Indio", "state": "CA", "office": ""},
    "92259": {"city": "Indio", "state": "CA", "office": ""},
    "92260": {"city": "Indio", "state": "CA", "office": ""},
    "92261": {"city": "Indio", "state": "CA", "office": ""},
    "92262": {"city": "Indio", "state": "CA", "office": ""},
    "92263": {"city": "Indio", "state": "CA", "office": ""},
    "92264": {"city": "Indio", "state": "CA", "office": ""},
    "92266": {"city": "Indio", "state": "CA", "office": ""},
    "92267": {"city": "Indio", "state": "CA", "office": ""},
    "92268": {"city": "Indio", "state": "CA", "office": ""},
    "92269": {"city": "Indio", "state": "CA", "office": ""},
    "92270": {"city": "Indio", "state": "CA", "office": ""},
    "92271": {"city": "Indio", "state": "CA", "office": ""},
    "92272": {"city": "Indio", "state": "CA", "office": ""},
    "92273": {"city": "Indio", "state": "CA", "office": ""},
    "92274": {"city": "Indio", "state": "CA", "office": ""},
    "92275": {"city": "Indio", "state": "CA", "office": ""},
    "92276": {"city": "Indio", "state": "CA", "office": ""},
    "92277": {"city": "Indio", "state": "CA", "office": ""},
    "92278": {"city": "Indio", "state": "CA", "office": ""},
    "92280": {"city": "Indio", "state": "CA", "office": ""},
    "92281": {"city": "Indio", "state": "CA", "office": ""},
    "92282": {"city": "Indio", "state": "CA", "office": ""},
    "92283": {"city": "Indio", "state": "CA", "office": ""},
    "92284": {"city": "Indio", "state": "CA", "office": ""},
    "92285": {"city": "Indio", "state": "CA", "office": ""},
    "92286": {"city": "Indio", "state": "CA", "office": ""},
    "92287": {"city": "Indio", "state": "CA", "office": ""},
    "92288": {"city": "Indio", "state": "CA", "office": ""},
    "92289": {"city": "Indio", "state": "CA", "office": ""},
    "92290": {"city": "Indio", "state": "CA", "office": ""},
    "92291": {"city": "Indio", "state": "CA", "office": ""},
    "92292": {"city": "Indio", "state": "CA", "office": ""},
    "92293": {"city": "Indio", "state": "CA", "office": ""},
    "92294": {"city": "Indio", "state": "CA", "office": ""},
    "92295": {"city": "Indio", "state": "CA", "office": ""},
    "92296": {"city": "Indio", "state": "CA", "office": ""},
    "92297": {"city": "Indio", "state": "CA", "office": ""},
    "92298": {"city": "Indio", "state": "CA", "office": ""},
    "92299": {"city": "Indio", "state": "CA", "office": ""},
}

def fetch_github_zipdb(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None

def parse_zipdb_text(text: str) -> Dict[str, Dict[str, str]]:
    db: Dict[str, Dict[str, str]] = {}
    if not text:
        return db
    lines = [ln.strip() for ln in text.splitlines()]
    i = 0
    while i + 2 < len(lines):
        zip_code = lines[i]
        city = lines[i + 1]
        state = lines[i + 2].upper()
        if re.fullmatch(r"\d{5}", zip_code) and city and state == "CA":
            db[zip_code] = {"city": city.title(), "state": "CA", "office": ""}
            i += 3
            while i < len(lines) and not lines[i]:
                i += 1
            continue
        i += 1
    if not db:
        for ln in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            m = re.search(r"\b(\d{5})\b", ln)
            if not m:
                continue
            zip_code = m.group(1)
            before = ln[:m.start()].strip(" ,;-")
            after = ln[m.end():].strip(" ,;-")
            city = ""
            if before and re.search(r"[A-Za-z]", before):
                city = re.split(r"[,\-–:]", before)[-1].strip().title()
            elif after and re.search(r"[A-Za-z]", after):
                city = re.split(r"[,\-–:]", after)[0].strip().title()
            if city:
                db[zip_code] = {"city": city, "state": "CA", "office": ""}
    return db

fetched = fetch_github_zipdb(GITHUB_RAW_ZIPDB)
if fetched:
    parsed = parse_zipdb_text(fetched)
    if parsed:
        ZIP_DB.update(parsed)

field_offices = {
    "Baie de San Francisco": {
        "Corte Madera": 525, "Daly City": 599, "El Cerrito": 585, "Fremont": 643,
        "Hayward": 521, "Los Gatos": 641, "Novato": 647, "Oakland": 501,
        "Pittsburg": 651, "Pleasanton": 639, "Redwood City": 542,
        "San Francisco": 503, "San Jose": 516, "San Mateo": 594, "Santa Clara": 632,
        "Vallejo": 538,
    },
    "Grand Los Angeles": {
        "Arleta": 628, "Bellflower": 610, "Culver City": 514, "Glendale": 540,
        "Hollywood": 633, "Inglewood": 544, "Long Beach": 507, "Los Angeles": 502,
        "Montebello": 531, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592,
        "West Covina": 591,
    },
    "Orange County / Sud": {
        "Costa Mesa": 627, "Fullerton": 547, "Laguna Hills": 642, "Santa Ana": 529,
        "San Clemente": 652, "Westminster": 623, "Garden Grove": 547, "Anaheim": 547,
    },
    "Vallée Centrale": {
        "Bakersfield": 511, "Fresno": 505, "Lodi": 595, "Modesto": 536, "Stockton": 517,
        "Visalia": 519, "Sacramento": 505,
    },
    "Sud Californie": {
        "San Diego": 707,
    },
}

FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

def infer_field_office(city: str) -> str:
    key = (city or "").strip().upper()
    if not key:
        return ""
    if key in FIELD_OFFICE_MAP:
        return FIELD_OFFICE_MAP[key]
    for label in FIELD_OFFICE_MAP.values():
        if key in label.upper():
            return label
    return ""

def build_zip_city_field_office(zip_db: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, List[str]]]:
    mapping: Dict[str, Dict[str, List[str]]] = {}
    for zip_code, info in zip_db.items():
        z = re.sub(r"\D", "", str(zip_code))[:5]
        if len(z) != 5:
            continue
        city = (info.get("city") or "").strip().title()
        office = (info.get("office") or "").strip() or infer_field_office(city)

        if not city:
            continue

        entry = mapping.setdefault(z, {"cities": [], "field_offices": []})
        if city not in entry["cities"]:
            entry["cities"].append(city)
        if office and office not in entry["field_offices"]:
            entry["field_offices"].append(office)

    if not mapping:
        mapping["94015"] = {
            "cities": ["Daly City"],
            "field_offices": ["Baie de San Francisco — Daly City (599)"],
        }

    for z, entry in mapping.items():
        if not entry["cities"]:
            entry["cities"] = ["Unknown City"]
        if not entry["field_offices"]:
            entry["field_offices"] = ["Unknown Field Office"]

    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))

ZIP_CITY_FIELD_OFFICE = build_zip_city_field_office(ZIP_DB)

CITY_TO_ZIPS: Dict[str, List[str]] = {}
OFFICE_TO_ZIPS: Dict[str, List[str]] = {}
for zip_code, row in ZIP_CITY_FIELD_OFFICE.items():
    for city in row["cities"]:
        CITY_TO_ZIPS.setdefault(city, []).append(zip_code)
    for office in row["field_offices"]:
        OFFICE_TO_ZIPS.setdefault(office, []).append(zip_code)

def normalize_city(value: str) -> str:
    return (value or "").strip().title()

def normalize_zip(value: str) -> str:
    return re.sub(r"\D", "", (value or ""))[:5]

def seed(*values):
    parts = []
    for item in values:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8], 16)

def rdigits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))

def rletter(rng: random.Random, initial: str) -> str:
    if isinstance(initial, str) and initial and initial[0].isalpha():
        return initial[0].upper()
    return rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(rng: random.Random) -> str:
    return str(rng.randint(10, 99))

def build_aamva_tags(fields: Dict[str, str]) -> str:
    enriched = dict(fields)
    enriched.setdefault("DAG", "2570 24TH STREET")
    enriched.setdefault("DAI", "OAKLAND")
    enriched.setdefault("DAJ", "CA")
    enriched.setdefault("DAK", "94601")
    return build_aamva_payload_continuous(enriched)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
.card { width: 480px; border-radius: 12px; padding: 14px; background: linear-gradient(135deg,#1e3a8a,#2563eb); color: white; box-shadow: 0 8px 24px rgba(0,0,0,0.12); margin: auto; }
.photo { width:86px; height:106px; background:#e5e7eb; border-radius:8px; overflow:hidden; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6, key="sb_columns")
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0, 9)), index=2, key="sb_ecc")
scale_param = st.sidebar.slider("Échelle (SVG)", 1, 6, 3, key="sb_scale")
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3, key="sb_ratio")
color_param = st.sidebar.color_picker("Couleur du code", "#000000", key="sb_color")

st.sidebar.markdown("---")
if "show_barcodes" not in st.session_state:
    st.session_state["show_barcodes"] = True
show_barcodes = st.sidebar.checkbox(
    "Afficher les codes-barres (PDF417)",
    value=st.session_state["show_barcodes"],
    key="sb_show_barcodes",
)

st.sidebar.markdown("---")
enable_validator = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False, key="sb_enable_validator")
if enable_validator and not _AAMVA_UTILS_AVAILABLE:
    st.sidebar.info("aamva_utils.py introuvable — la validation est désactivée automatiquement.")

def update_from_zip() -> None:
    zip_code = normalize_zip(st.session_state.get("ui_zip", ""))
    row = ZIP_CITY_FIELD_OFFICE.get(zip_code)
    if not row:
        return
    cities = row.get("cities") or ["Unknown City"]
    offices = row.get("field_offices") or ["Unknown Field Office"]
    st.session_state["ui_city"] = cities[0]
    st.session_state["ui_office"] = offices[0]

def update_from_city() -> None:
    city = normalize_city(st.session_state.get("ui_city", ""))
    zips = CITY_TO_ZIPS.get(city, [])
    if not zips:
        return
    st.session_state["ui_zip"] = zips[0]
    row = ZIP_CITY_FIELD_OFFICE.get(zips[0], {})
    offices = row.get("field_offices") or ["Unknown Field Office"]
    st.session_state["ui_office"] = offices[0]

def update_from_office() -> None:
    office = st.session_state.get("ui_office", "")
    zips = OFFICE_TO_ZIPS.get(office, [])
    if not zips:
        return
    st.session_state["ui_zip"] = zips[0]
    row = ZIP_CITY_FIELD_OFFICE.get(zips[0], {})
    cities = row.get("cities") or ["Unknown City"]
    st.session_state["ui_city"] = cities[0]

st.title("Générateur officiel de permis Californien")

ln = st.text_input("Nom de famille", "HARMS", key="ui_ln")
fn = st.text_input("Prénom", "ROSA", key="ui_fn")
sex = st.selectbox("Sexe", ["M", "F"], key="ui_sex")
dob = st.date_input("Date de naissance", datetime.date(1990, 1, 1), key="ui_dob")

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds", 0, 8, 5, key="ui_h1")
    w = st.number_input("Poids (lb)", 30, 500, 160, key="ui_w")
with col2:
    h2 = st.number_input("Pouces", 0, 11, 10, key="ui_h2")
    eyes = st.text_input("Yeux", "BRN", key="ui_eyes")
hair = st.text_input("Cheveux", "BRN", key="ui_hair")
cls = st.text_input("Classe", "C", key="ui_cls")
rstr = st.text_input("Restrictions", "NONE", key="ui_rstr")
endorse = st.text_input("Endorsements", "NONE", key="ui_endorse")
iss = st.date_input("Date d'émission", datetime.date.today(), key="ui_iss")
address_line = st.text_input("Address Line", "2570 24TH STREET", key="ui_address_line")

zip_options = list(ZIP_CITY_FIELD_OFFICE.keys()) or ["94015"]
if "ui_zip" not in st.session_state or st.session_state["ui_zip"] not in ZIP_CITY_FIELD_OFFICE:
    st.session_state["ui_zip"] = zip_options[0]

selected_zip = st.session_state["ui_zip"]
selected_row = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {"cities": ["Unknown City"], "field_offices": ["Unknown Field Office"]})
city_options = selected_row.get("cities") or ["Unknown City"]
office_options = selected_row.get("field_offices") or ["Unknown Field Office"]

if "ui_city" not in st.session_state or st.session_state["ui_city"] not in city_options:
    st.session_state["ui_city"] = city_options[0]
if "ui_office" not in st.session_state or st.session_state["ui_office"] not in office_options:
    st.session_state["ui_office"] = office_options[0]

col_zip, col_city = st.columns([2, 3])
with col_zip:
    st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state["ui_zip"]),
        key="ui_zip",
        on_change=update_from_zip,
    )

selected_zip = st.session_state["ui_zip"]
selected_row = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {"cities": ["Unknown City"], "field_offices": ["Unknown Field Office"]})
city_options = selected_row.get("cities") or ["Unknown City"]
office_options = selected_row.get("field_offices") or ["Unknown Field Office"]
if st.session_state.get("ui_city") not in city_options:
    st.session_state["ui_city"] = city_options[0]
if st.session_state.get("ui_office") not in office_options:
    st.session_state["ui_office"] = office_options[0]

with col_city:
    st.selectbox(
        "Ville",
        options=city_options,
        index=city_options.index(st.session_state["ui_city"]),
        key="ui_city",
        on_change=update_from_city,
    )

st.selectbox(
    "Field Office",
    options=office_options,
    index=office_options.index(st.session_state["ui_office"]),
    key="ui_office",
    on_change=update_from_office,
)

generate = st.button("Générer la carte", key="ui_generate")

def validate_inputs() -> List[str]:
    errors: List[str] = []
    if not st.session_state.get("ui_ln", "").strip():
        errors.append("Nom de famille requis.")
    if not st.session_state.get("ui_fn", "").strip():
        errors.append("Prénom requis.")
    if st.session_state.get("ui_dob") > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if st.session_state.get("ui_iss") > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if st.session_state.get("ui_w", 0) < 30 or st.session_state.get("ui_w", 0) > 500:
        errors.append("Poids hors plage attendue.")
    if st.session_state.get("ui_h1", 0) > 8 or st.session_state.get("ui_h2", 0) > 11:
        errors.append("Taille hors plage attendue.")

    zip_code = normalize_zip(st.session_state.get("ui_zip", ""))
    city = normalize_city(st.session_state.get("ui_city", ""))
    address = st.session_state.get("ui_address_line", "").strip()

    if not zip_code:
        errors.append("Code postal requis.")
    if not city:
        errors.append("Ville requise pour générer le code PDF417")
    if not address:
        errors.append("Adresse requise.")

    row = ZIP_CITY_FIELD_OFFICE.get(zip_code)
    if row:
        allowed = [normalize_city(c) for c in (row.get("cities") or [])]
        if city not in allowed:
            errors.append(f"Incohérence ZIP → Ville: {zip_code} n'est pas lié à {city}.")
    return errors

def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def create_pdf_bytes(fields: Dict[str, str], photo_bytes: bytes = None) -> bytes:
    if not _REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab non disponible.")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x, y = 72, height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE")
    y -= 24
    c.setFont("Helvetica", 11)
    for key, val in fields.items():
        c.drawString(x, y, f"{key}: {val}")
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    if photo_bytes and ImageReader is not None:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 162, height - 182, width=90, height=110)
        except Exception:
            pass
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_pdf417_svg(data_bytes: bytes, columns: int, security_level: int, scale: int, ratio: int, color: str) -> str:
    if not _PDF417_AVAILABLE:
        raise RuntimeError("Module pdf417gen non disponible.")
    codes = encode(data_bytes, columns=columns, security_level=security_level, force_binary=False)
    svg_tree = render_svg(codes, scale=scale, ratio=ratio, color=color)
    try:
        import xml.etree.ElementTree as ET
        svg_bytes = ET.tostring(svg_tree.getroot(), encoding="utf-8", method="xml")
        return svg_bytes.decode("utf-8")
    except Exception:
        return str(svg_tree)

if generate:
    errors = validate_inputs()
    if errors:
        for err in errors:
            st.error(err)
        st.stop()

    ln = st.session_state["ui_ln"]
    fn = st.session_state["ui_fn"]
    sex = st.session_state["ui_sex"]
    dob = st.session_state["ui_dob"]
    h1 = st.session_state["ui_h1"]
    h2 = st.session_state["ui_h2"]
    w = st.session_state["ui_w"]
    eyes = st.session_state["ui_eyes"]
    hair = st.session_state["ui_hair"]
    cls = st.session_state["ui_cls"]
    rstr = st.session_state["ui_rstr"]
    endorse = st.session_state["ui_endorse"]
    iss = st.session_state["ui_iss"]
    zip_sel = normalize_zip(st.session_state["ui_zip"])
    city_sel = normalize_city(st.session_state["ui_city"])
    office_sel = st.session_state["ui_office"]
    address_sel = st.session_state["ui_address_line"].strip()

    row = ZIP_CITY_FIELD_OFFICE.get(zip_sel, {})
    if not city_sel and row.get("cities"):
        city_sel = normalize_city(row["cities"][0])
        st.session_state["ui_city"] = city_sel

    if not city_sel:
        st.error("Ville requise pour générer le code PDF417")
        st.stop()

    rng = random.Random(seed(ln, fn, dob))
    dl = rletter(rng, ln[0] if ln else "") + rdigits(rng, 7)

    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        exp = datetime.date(exp_year, dob.month, min(dob.day, 28))

    m = re.search(r"\((\d{2,3})\)", office_sel or "")
    office_code = int(m.group(1)) if m else 0
    seq = next_sequence(rng).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}/{seq}FD/{iss.year % 100}"

    fields = {
        "DAQ": dl,
        "DCS": ln.upper().strip(),
        "DAC": fn.upper().strip(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAG": address_sel.upper(),
        "DAI": city_sel.upper(),
        "DAJ": "CA",
        "DAK": zip_sel,
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": (eyes or "").upper(),
        "DAZ": (hair or "").upper(),
    }

    for required in ("DAG", "DAI", "DAJ", "DAK"):
        if not str(fields.get(required, "")).strip():
            st.error(f"Champ AAMVA obligatoire manquant: {required}")
            st.stop()

    if _AAMVA_UTILS_AVAILABLE:
        payload_to_use = build_aamva_payload_continuous(fields)
    else:
        ordered = ["DAQ", "DCS", "DAC", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"]
        payload_to_use = "@ANSI 636014080102DL00410288ZA03290015DL" + "".join(
            f"{tag}{str(fields.get(tag, '')).strip()}" for tag in ordered if str(fields.get(tag, "")).strip()
        )

    if any(x in payload_to_use for x in ("\n", "\r", "\x1E")):
        st.error("Payload invalide: des séparateurs interdits ont été détectés.")
        st.stop()

    photo_src = IMAGE_M_URL if sex == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/jpeg" if photo_bytes[:3] == b"\xff\xd8\xff" else "image/png"
        photo_html = f"<div class='photo'><img src='data:{mime};base64,{b64}' alt='photo'/></div>"
    else:
        photo_html = f"<div class='photo'><img src='{photo_src}' alt='photo par défaut'/></div>"

    html = f"""
    <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">CALIFORNIA USA DRIVER LICENSE</div>
            <div style="background:white;color:#1e3a8a;padding:4px 8px;border-radius:6px;font-weight:700">{dl}</div>
        </div>
        <div style="display:flex;gap:12px">
            {photo_html}
            <div style="font-size:12px">
                <div style="opacity:0.8;font-size:10px">Nom</div><div style="font-weight:700">{ln}</div>
                <div style="opacity:0.8;font-size:10px">Prénom</div><div style="font-weight:700">{fn}</div>
                <div style="opacity:0.8;font-size:10px">Address</div><div style="font-weight:700">{address_sel}</div>
                <div style="opacity:0.8;font-size:10px">Ville / ZIP</div><div style="font-weight:700">{city_sel} / {zip_sel}</div>
                <div style="opacity:0.8;font-size:10px">Field Office</div><div style="font-weight:700">{office_sel}</div>
                <div style="opacity:0.8;font-size:10px">ISS / EXP</div><div style="font-weight:700">{iss.strftime('%m/%d/%Y')} / {exp.strftime('%m/%d/%Y')}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if enable_validator and _AAMVA_UTILS_AVAILABLE:
        st.subheader("Validation AAMVA (optionnelle)")
        results = validate_aamva_payload(payload_to_use)
        with st.expander("Résultats de validation", expanded=True):
            if results.get("errors"):
                st.error(f"Erreurs détectées ({len(results['errors'])}) :")
                for e in results["errors"]:
                    st.write("- " + e)
            else:
                st.success("Aucune erreur bloquante détectée.")
            for wmsg in results.get("warnings", []):
                st.warning(wmsg)
            for info in results.get("infos", []):
                st.info(info)

            corrected, applied = auto_correct_payload(payload_to_use)
            if corrected and corrected != payload_to_use:
                st.markdown("### Version corrigée proposée")
                for a in applied:
                    st.write("- " + a)
                st.text_area("Payload corrigé (modifiable)", value=corrected, height=200, key="ui_aamva_corrected_preview")
                if st.button("Appliquer la correction et utiliser pour génération", key="ui_apply_correction"):
                    payload_to_use = st.session_state.get("ui_aamva_corrected_preview", corrected)
                    st.success("Correction appliquée.")

    svg_str = None
    if show_barcodes:
        st.subheader("PDF417")
        if _PDF417_AVAILABLE:
            try:
                svg_str = generate_pdf417_svg(
                    payload_to_use.encode("utf-8"),
                    columns=columns_param,
                    security_level=security_level_param,
                    scale=scale_param,
                    ratio=ratio_param,
                    color=color_param,
                )
                svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
                with st.expander("Aperçu PDF417 (SVG)", expanded=True):
                    components.html(svg_html, height=260, scrolling=True)
                    st.download_button("Télécharger PDF417 (SVG)", data=svg_str.encode("utf-8"), file_name="pdf417.svg", mime="image/svg+xml", key="dl_pdf417_svg_main")
            except Exception as exc:
                st.error("Erreur génération PDF417 : " + str(exc))
        else:
            st.warning("pdf417gen non disponible. Vendorisez le module ou installez pdf417gen.")

    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            st.download_button("Télécharger PDF417 (SVG) (panel)", data=svg_str.encode("utf-8"), file_name="pdf417_panel.svg", mime="image/svg+xml", key="dl_pdf417_svg_panel")
    with cols[1]:
        try:
            pdf_bytes = create_pdf_bytes({
                "Nom": ln,
                "Prénom": fn,
                "Address": address_sel,
                "Sexe": sex,
                "DOB": dob.strftime("%m/%d/%Y"),
                "Ville": city_sel,
                "ZIP": zip_sel,
                "Field Office": office_sel,
                "ISS": iss.strftime("%m/%d/%Y"),
                "EXP": exp.strftime("%m/%d/%Y"),
                "Classe": cls.upper(),
                "Restrictions": rstr.upper(),
                "Endorsements": endorse.upper(),
                "Yeux/Cheveux/Taille/Poids": f"{eyes.upper()}/{hair.upper()}/{int(h1)}'{int(h2)}\"/{w} lb",
            }, photo_bytes=photo_bytes)
            st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf", mime="application/pdf", key="dl_permis_pdf")
        except Exception as exc:
            st.error("Erreur génération PDF : " + str(exc))
            if not _REPORTLAB_AVAILABLE:
                st.info("reportlab non installé : export PDF non disponible.")
