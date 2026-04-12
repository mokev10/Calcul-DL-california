#!/usr/bin/env python3
# driver_license_final_fixed.py

import streamlit as st
import datetime, random, hashlib, io, base64, requests, re
import streamlit.components.v1 as components
from typing import Dict, List, Optional

# ReportLab (PDF)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    _REPORTLAB_AVAILABLE = True
except Exception:
    ImageReader = None
    _REPORTLAB_AVAILABLE = False

# Pillow (optionnel)
try:
    from PIL import Image, ImageDraw, ImageOps
    _PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageDraw = None
    _PIL_AVAILABLE = False

# pdf417gen (optionnel)
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

# Optional aamva_utils (validation + autocorrection)
try:
    from aamva_utils import validate_aamva_payload, auto_correct_payload, example_payload, GS as AAMVA_GS
    _AAMVA_UTILS_AVAILABLE = True
except Exception:
    _AAMVA_UTILS_AVAILABLE = False
    AAMVA_GS = None

GS = AAMVA_GS if AAMVA_GS is not None else "\x1E"

st.set_page_config(page_title="Permis CA", layout="wide")

# -------------------------
# Assets
# -------------------------
IMAGE_M_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah-22.png"
IMAGE_F_URL = "https://img.icons8.com/external-avatar-andi-nur-abdillah/200/external-avatar-business-avatar-avatar-andi-nur-abdillah.png"

# -------------------------
# ZIP -> City intégré en dur
# -------------------------
CALIFORNIA_ZIP_TO_CITY: Dict[str, str] = {
    "90001": "Los Angeles", "90002": "Los Angeles", "90003": "Los Angeles", "90004": "Los Angeles",
    "90005": "Los Angeles", "90006": "Los Angeles", "90007": "Los Angeles", "90008": "Los Angeles",
    "90010": "Los Angeles", "90011": "Los Angeles", "90012": "Los Angeles", "90013": "Los Angeles",
    "90014": "Los Angeles", "90015": "Los Angeles", "90016": "Los Angeles", "90017": "Los Angeles",
    "90018": "Los Angeles", "90019": "Los Angeles", "90020": "Los Angeles", "90021": "Los Angeles",
    "90022": "Los Angeles", "90023": "Los Angeles", "90024": "Los Angeles", "90025": "Los Angeles",
    "90026": "Los Angeles", "90027": "Los Angeles", "90028": "Los Angeles", "90029": "Los Angeles",
    "90031": "Los Angeles", "90032": "Los Angeles", "90033": "Los Angeles", "90034": "Los Angeles",
    "90035": "Los Angeles", "90036": "Los Angeles", "90037": "Los Angeles", "90038": "Los Angeles",
    "90039": "Los Angeles", "90040": "Los Angeles", "90041": "Los Angeles", "90042": "Los Angeles",
    "90043": "Los Angeles", "90044": "Los Angeles", "90045": "Los Angeles", "90046": "Los Angeles",
    "90047": "Los Angeles", "90048": "Los Angeles", "90049": "Los Angeles", "90056": "Los Angeles",
    "90057": "Los Angeles", "90058": "Los Angeles", "90059": "Los Angeles", "90061": "Los Angeles",
    "90062": "Los Angeles", "90063": "Los Angeles", "90064": "Los Angeles", "90065": "Los Angeles",
    "90066": "Los Angeles", "90067": "Los Angeles", "90068": "Los Angeles", "90069": "Los Angeles",
    "90071": "Los Angeles", "90077": "Los Angeles", "90094": "Los Angeles",
    "90210": "Beverly Hills", "90211": "Beverly Hills", "90212": "Beverly Hills",
    "90230": "Culver City", "90232": "Culver City", "90245": "El Segundo", "90247": "Gardena",
    "90250": "Hawthorne", "90254": "Hermosa Beach", "90260": "Lawndale", "90262": "Lynwood",
    "90265": "Malibu", "90266": "Manhattan Beach", "90272": "Pacific Palisades",
    "90277": "Redondo Beach", "90278": "Redondo Beach", "90291": "Venice", "90292": "Marina Del Rey",
    "90301": "Inglewood", "90302": "Inglewood", "90303": "Inglewood", "90304": "Inglewood", "90305": "Inglewood",
    "90401": "Santa Monica", "90402": "Santa Monica", "90403": "Santa Monica", "90404": "Santa Monica", "90405": "Santa Monica",
    "90501": "Torrance", "90502": "Torrance", "90503": "Torrance", "90504": "Torrance", "90505": "Torrance",
    "90710": "Harbor City", "90731": "San Pedro", "90732": "San Pedro",
    "90802": "Long Beach", "90803": "Long Beach", "90804": "Long Beach", "90805": "Long Beach", "90806": "Long Beach",
    "90807": "Long Beach", "90808": "Long Beach", "90810": "Long Beach", "90813": "Long Beach",
    "91006": "Arcadia", "91101": "Pasadena", "91103": "Pasadena", "91104": "Pasadena", "91105": "Pasadena", "91106": "Pasadena", "91107": "Pasadena",
    "91201": "Glendale", "91202": "Glendale", "91203": "Glendale", "91204": "Glendale", "91205": "Glendale", "91206": "Glendale",
    "91303": "Canoga Park", "91304": "Canoga Park", "91306": "Winnetka", "91307": "West Hills", "91311": "Chatsworth",
    "91316": "Encino", "91324": "Northridge", "91325": "Northridge", "91331": "Pacoima", "91335": "Reseda",
    "91342": "Sylmar", "91343": "North Hills", "91344": "Granada Hills", "91356": "Tarzana",
    "91360": "Thousand Oaks", "91361": "Thousand Oaks", "91362": "Thousand Oaks", "91364": "Woodland Hills", "91367": "Woodland Hills",
    "91401": "Van Nuys", "91402": "Panorama City", "91403": "Sherman Oaks", "91405": "Van Nuys", "91406": "Van Nuys",
    "91411": "Van Nuys", "91423": "Sherman Oaks", "91501": "Burbank", "91502": "Burbank", "91504": "Burbank", "91505": "Burbank",
    "91601": "North Hollywood", "91602": "North Hollywood", "91604": "Studio City", "91605": "North Hollywood", "91606": "North Hollywood",
    "91702": "Azusa", "91706": "Baldwin Park", "91710": "Chino", "91711": "Claremont", "91722": "Covina", "91723": "Covina", "91724": "Covina",
    "91730": "Rancho Cucamonga", "91737": "Rancho Cucamonga", "91739": "Rancho Cucamonga", "91740": "Glendora", "91741": "Glendora",
    "91744": "La Puente", "91745": "Hacienda Heights", "91748": "Rowland Heights", "91750": "La Verne",
    "91754": "Monterey Park", "91755": "Monterey Park", "91761": "Ontario", "91762": "Ontario", "91764": "Ontario",
    "91765": "Diamond Bar", "91766": "Pomona", "91767": "Pomona", "91768": "Pomona", "91770": "Rosemead", "91773": "San Dimas",
    "91775": "San Gabriel", "91776": "San Gabriel", "91780": "Temple City", "91784": "Upland", "91786": "Upland",
    "91790": "West Covina", "91791": "West Covina", "91792": "West Covina", "91801": "Alhambra", "91803": "Alhambra",
    "91910": "Chula Vista", "91911": "Chula Vista", "91913": "Chula Vista", "91914": "Chula Vista", "91915": "Chula Vista",
    "91932": "Imperial Beach", "91941": "La Mesa", "91942": "La Mesa",
    "92007": "Cardiff By The Sea", "92008": "Carlsbad", "92009": "Carlsbad", "92010": "Carlsbad", "92011": "Carlsbad",
    "92014": "Del Mar", "92019": "El Cajon", "92020": "El Cajon", "92021": "El Cajon",
    "92024": "Encinitas", "92025": "Escondido", "92026": "Escondido", "92027": "Escondido", "92028": "Fallbrook", "92029": "Escondido",
    "92037": "La Jolla", "92040": "Lakeside", "92054": "Oceanside", "92056": "Oceanside", "92057": "Oceanside", "92058": "Oceanside",
    "92064": "Poway", "92065": "Ramona", "92069": "San Marcos", "92071": "Santee", "92075": "Solana Beach", "92078": "San Marcos",
    "92081": "Vista", "92083": "Vista", "92084": "Vista",
    "92101": "San Diego", "92102": "San Diego", "92103": "San Diego", "92104": "San Diego", "92105": "San Diego", "92106": "San Diego",
    "92107": "San Diego", "92108": "San Diego", "92109": "San Diego", "92110": "San Diego", "92111": "San Diego", "92113": "San Diego",
    "92114": "San Diego", "92115": "San Diego", "92116": "San Diego", "92117": "San Diego", "92119": "San Diego", "92120": "San Diego",
    "92121": "San Diego", "92122": "San Diego", "92123": "San Diego", "92124": "San Diego", "92126": "San Diego", "92127": "San Diego",
    "92128": "San Diego", "92129": "San Diego", "92130": "San Diego", "92131": "San Diego", "92139": "San Diego", "92154": "San Diego",
    "92173": "San Diego",
    "92602": "Irvine", "92603": "Irvine", "92604": "Irvine", "92606": "Irvine", "92612": "Irvine", "92614": "Irvine", "92617": "Irvine",
    "92618": "Irvine", "92620": "Irvine", "92626": "Costa Mesa", "92627": "Costa Mesa", "92629": "Dana Point", "92630": "Lake Forest",
    "92646": "Huntington Beach", "92647": "Huntington Beach", "92648": "Huntington Beach", "92649": "Huntington Beach",
    "92651": "Laguna Beach", "92653": "Laguna Hills", "92656": "Aliso Viejo", "92657": "Newport Coast",
    "92660": "Newport Beach", "92661": "Newport Beach", "92663": "Newport Beach",
    "92672": "San Clemente", "92673": "San Clemente", "92675": "San Juan Capistrano", "92677": "Laguna Niguel",
    "92679": "Trabuco Canyon", "92683": "Westminster", "92688": "Rancho Santa Margarita", "92691": "Mission Viejo", "92692": "Mission Viejo",
    "92701": "Santa Ana", "92703": "Santa Ana", "92704": "Santa Ana", "92705": "Santa Ana", "92706": "Santa Ana", "92707": "Santa Ana",
    "92708": "Fountain Valley", "92780": "Tustin", "92782": "Tustin",
    "92801": "Anaheim", "92802": "Anaheim", "92804": "Anaheim", "92805": "Anaheim", "92806": "Anaheim", "92807": "Anaheim", "92808": "Anaheim",
    "92831": "Fullerton", "92832": "Fullerton", "92833": "Fullerton", "92835": "Fullerton",
    "92840": "Garden Grove", "92841": "Garden Grove", "92843": "Garden Grove", "92844": "Garden Grove", "92845": "Garden Grove",
    "92860": "Norco", "92865": "Orange", "92866": "Orange", "92867": "Orange", "92868": "Orange", "92869": "Orange", "92870": "Placentia",
    "92879": "Corona", "92880": "Corona", "92881": "Corona", "92882": "Corona", "92883": "Corona", "92886": "Yorba Linda", "92887": "Yorba Linda",
    "94010": "Burlingame", "94014": "Daly City", "94015": "Daly City", "94016": "Daly City", "94019": "Half Moon Bay",
    "94022": "Los Altos", "94024": "Los Altos", "94025": "Menlo Park", "94027": "Atherton", "94030": "Millbrae",
    "94040": "Mountain View", "94041": "Mountain View", "94043": "Mountain View",
    "94061": "Redwood City", "94062": "Redwood City", "94063": "Redwood City", "94065": "Redwood City",
    "94066": "San Bruno", "94070": "San Carlos", "94080": "South San Francisco",
    "94085": "Sunnyvale", "94086": "Sunnyvale", "94087": "Sunnyvale", "94089": "Sunnyvale",
    "94102": "San Francisco", "94103": "San Francisco", "94104": "San Francisco", "94105": "San Francisco", "94107": "San Francisco",
    "94108": "San Francisco", "94109": "San Francisco", "94110": "San Francisco", "94111": "San Francisco", "94112": "San Francisco",
    "94114": "San Francisco", "94115": "San Francisco", "94116": "San Francisco", "94117": "San Francisco", "94118": "San Francisco",
    "94121": "San Francisco", "94122": "San Francisco", "94123": "San Francisco", "94124": "San Francisco",
    "94127": "San Francisco", "94131": "San Francisco", "94132": "San Francisco", "94133": "San Francisco", "94134": "San Francisco",
    "94301": "Palo Alto", "94303": "Palo Alto", "94304": "Palo Alto", "94306": "Palo Alto",
    "94401": "San Mateo", "94402": "San Mateo", "94403": "San Mateo", "94404": "San Mateo",
    "94501": "Alameda", "94530": "El Cerrito", "94536": "Fremont", "94538": "Fremont", "94539": "Fremont",
    "94541": "Hayward", "94542": "Hayward", "94544": "Hayward", "94545": "Hayward", "94546": "Castro Valley",
    "94549": "Lafayette", "94550": "Livermore", "94551": "Livermore", "94553": "Martinez", "94555": "Fremont",
    "94558": "Napa", "94559": "Napa", "94560": "Newark", "94563": "Orinda", "94564": "Pinole", "94565": "Pittsburg",
    "94566": "Pleasanton", "94568": "Dublin", "94577": "San Leandro", "94578": "San Leandro", "94579": "San Leandro",
    "94582": "San Ramon", "94583": "San Ramon", "94587": "Union City", "94588": "Pleasanton",
    "94589": "Vallejo", "94590": "Vallejo", "94591": "Vallejo", "94592": "Vallejo",
    "94601": "Oakland", "94602": "Oakland", "94603": "Oakland", "94605": "Oakland", "94606": "Oakland", "94607": "Oakland",
    "94608": "Oakland", "94609": "Oakland", "94610": "Oakland", "94611": "Oakland", "94612": "Oakland", "94618": "Oakland",
    "94619": "Oakland", "94621": "Oakland", "94702": "Berkeley", "94703": "Berkeley", "94704": "Berkeley", "94705": "Berkeley",
    "94706": "Albany", "94707": "Berkeley", "94708": "Berkeley", "94709": "Berkeley", "94710": "Berkeley",
    "94801": "Richmond", "94803": "El Sobrante", "94804": "Richmond", "94805": "Richmond",
    "94901": "San Rafael", "94903": "San Rafael", "94904": "Greenbrae", "94920": "Belvedere Tiburon",
    "94925": "Corte Madera", "94930": "Fairfax", "94939": "Larkspur", "94941": "Mill Valley", "94945": "Novato", "94947": "Novato", "94949": "Novato",
    "95008": "Campbell", "95014": "Cupertino", "95035": "Milpitas", "95037": "Morgan Hill",
    "95050": "Santa Clara", "95051": "Santa Clara", "95054": "Santa Clara",
    "95110": "San Jose", "95111": "San Jose", "95112": "San Jose", "95113": "San Jose", "95116": "San Jose",
    "95117": "San Jose", "95118": "San Jose", "95119": "San Jose", "95120": "San Jose", "95121": "San Jose",
    "95122": "San Jose", "95123": "San Jose", "95124": "San Jose", "95125": "San Jose", "95126": "San Jose",
    "95127": "San Jose", "95128": "San Jose", "95129": "San Jose", "95130": "San Jose", "95131": "San Jose", "95132": "San Jose",
    "95133": "San Jose", "95134": "San Jose", "95135": "San Jose", "95136": "San Jose", "95138": "San Jose", "95139": "San Jose", "95148": "San Jose",
    "95202": "Stockton", "95204": "Stockton", "95205": "Stockton", "95206": "Stockton", "95207": "Stockton",
    "95209": "Stockton", "95210": "Stockton", "95212": "Stockton", "95219": "Stockton",
    "95350": "Modesto", "95351": "Modesto", "95354": "Modesto", "95355": "Modesto", "95356": "Modesto", "95357": "Modesto",
    "95376": "Tracy", "95377": "Tracy", "95382": "Turlock", "95401": "Santa Rosa", "95403": "Santa Rosa", "95404": "Santa Rosa", "95405": "Santa Rosa",
    "95608": "Carmichael", "95610": "Citrus Heights", "95616": "Davis", "95618": "Davis", "95624": "Elk Grove",
    "95630": "Folsom", "95632": "Galt", "95648": "Lincoln", "95661": "Roseville", "95662": "Orangevale", "95670": "Rancho Cordova",
    "95677": "Rocklin", "95678": "Roseville", "95687": "Vacaville", "95688": "Vacaville", "95691": "West Sacramento",
    "95742": "Rancho Cordova", "95747": "Roseville", "95757": "Elk Grove", "95758": "Elk Grove",
    "95811": "Sacramento", "95814": "Sacramento", "95815": "Sacramento", "95816": "Sacramento", "95817": "Sacramento",
    "95818": "Sacramento", "95819": "Sacramento", "95820": "Sacramento", "95821": "Sacramento", "95822": "Sacramento",
    "95823": "Sacramento", "95824": "Sacramento", "95825": "Sacramento", "95826": "Sacramento", "95827": "Sacramento",
    "95828": "Sacramento", "95829": "Sacramento", "95831": "Sacramento", "95833": "Sacramento", "95834": "Sacramento",
    "95835": "Sacramento", "95838": "Sacramento", "95841": "Sacramento", "95842": "Sacramento", "95843": "Antelope", "95864": "Sacramento",
    "95926": "Chico", "95928": "Chico", "95991": "Yuba City",
    "96001": "Redding", "96002": "Redding", "96003": "Redding", "96150": "South Lake Tahoe", "96161": "Truckee"
}

# -------------------------
# Field offices mapping
# -------------------------
field_offices = {
    "Baie de San Francisco": {
        "Corte Madera": 525, "Daly City": 599, "El Cerrito": 585, "Fremont": 643,
        "Hayward": 521, "Los Gatos": 641, "Novato": 647, "Oakland (Claremont)": 501,
        "Oakland (Coliseum)": 604, "Pittsburg": 651, "Pleasanton": 639, "Redwood City": 542,
        "San Francisco": 503, "San Jose (Alma)": 516, "San Jose (Driver License Center)": 607,
        "San Mateo": 594, "Santa Clara": 632, "Vallejo": 538
    },
    "Grand Los Angeles": {
        "Arleta": 628, "Bellflower": 610, "Culver City": 514, "Glendale": 540,
        "Hollywood": 633, "Inglewood": 544, "Long Beach": 507, "Los Angeles (Hope St)": 502,
        "Montebello": 531, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592, "West Covina": 591
    },
    "Orange County / Sud": {
        "Costa Mesa": 627, "Fullerton": 547, "Laguna Hills": 642, "Santa Ana": 529,
        "San Clemente": 652, "Westminster": 623
    },
    "Vallée Centrale": {
        "Bakersfield": 511, "Fresno": 505, "Lodi": 595, "Modesto": 536, "Stockton": 517, "Visalia": 519,
        "Sacramento": 505
    },
    "Sud Californie": {
        "San Diego": 707
    }
}
FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        FIELD_OFFICE_MAP[city.upper()] = f"{region} — {city} ({code})"

def infer_field_office(city: str) -> str:
    if not city:
        return ""
    exact = FIELD_OFFICE_MAP.get(city.upper())
    if exact:
        return exact
    for lbl in FIELD_OFFICE_MAP.values():
        if city.upper() in lbl.upper():
            return lbl
    return ""

# -------------------------
# Structure unifiée ZIP -> City -> Field Office
# -------------------------
ZIP_CITY_FIELD_OFFICE: Dict[str, Dict[str, str]] = {}
for z, city in CALIFORNIA_ZIP_TO_CITY.items():
    ZIP_CITY_FIELD_OFFICE[z] = {
        "city": city,
        "field_office": infer_field_office(city)
    }

def build_indices(data: Dict[str, Dict[str, str]]):
    city_to_zips: Dict[str, List[str]] = {}
    office_to_zips: Dict[str, List[str]] = {}
    for z, row in data.items():
        city = (row.get("city") or "").strip().title()
        office = (row.get("field_office") or "").strip()
        if city:
            city_to_zips.setdefault(city, []).append(z)
        if office:
            office_to_zips.setdefault(office, []).append(z)
    return city_to_zips, office_to_zips

CITY_TO_ZIPS, OFFICE_TO_ZIPS = build_indices(ZIP_CITY_FIELD_OFFICE)

# -------------------------
# Helpers
# -------------------------
def normalize_city(s: str) -> str:
    return (s or "").strip().title()

def normalize_zip(z: str) -> str:
    return re.sub(r"\D", "", (z or ""))[:5]

def seed(*x):
    parts = []
    for item in x:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8], 16)

def rdigits(r, n):
    return "".join(r.choice("0123456789") for _ in range(n))

def rletter(r, initial):
    try:
        if isinstance(initial, str) and initial and initial[0].isalpha():
            return initial[0].upper()
    except Exception:
        pass
    import random as _rand
    return _rand.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(r):
    return str(r.randint(10, 99))

# -------------------------
# UI styles / sidebar
# -------------------------
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
show_barcodes = st.sidebar.checkbox("Afficher les codes-barres (PDF417)", value=st.session_state["show_barcodes"], key="sb_show_barcodes")

st.sidebar.markdown("---")
enable_validator = st.sidebar.checkbox("Activer la validation AAMVA (optionnel)", value=False, key="sb_enable_validator")
if enable_validator and not _AAMVA_UTILS_AVAILABLE:
    st.sidebar.info("aamva_utils.py introuvable — la validation est désactivée automatiquement.")

st.sidebar.markdown("**Rasterisation (aperçu PNG/GIF)**")
raster_scale_ui = st.sidebar.selectbox("Scale raster (entier)", [1, 2, 3, 4, 5], index=2, key="sb_raster")
gif_delay_ui = st.sidebar.number_input("GIF delay (ms)", min_value=50, max_value=2000, value=200, step=50, key="sb_gif_delay")

# -------------------------
# Callbacks dynamiques ZIP -> Ville -> Field Office
# -------------------------
def update_from_zip():
    z = normalize_zip(st.session_state.get("ui_zip", ""))
    if not z:
        return
    row = ZIP_CITY_FIELD_OFFICE.get(z, {})
    city = row.get("city", "")
    office = row.get("field_office", "")
    if city:
        st.session_state["ui_city"] = city
    if office:
        st.session_state["ui_office"] = office

def update_from_city():
    city = normalize_city(st.session_state.get("ui_city", ""))
    if not city:
        return
    zips = CITY_TO_ZIPS.get(city, [])
    if zips:
        chosen = zips[0]
        st.session_state["ui_zip"] = chosen
        row = ZIP_CITY_FIELD_OFFICE.get(chosen, {})
        office = row.get("field_office", "")
        if office:
            st.session_state["ui_office"] = office

def update_from_office():
    office = st.session_state.get("ui_office", "")
    if not office:
        return
    zips = OFFICE_TO_ZIPS.get(office, [])
    if zips:
        chosen = zips[0]
        st.session_state["ui_zip"] = chosen
        city = ZIP_CITY_FIELD_OFFICE.get(chosen, {}).get("city", "")
        if city:
            st.session_state["ui_city"] = city

# -------------------------
# FORM
# -------------------------
st.title("Générateur officiel de permis CA")

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

# Nouveau champ libre demandé
address_line = st.text_input("Address Line", "2570 24TH STREET", key="ui_address_line")

hair = st.text_input("Cheveux", "BRN", key="ui_hair")
cls = st.text_input("Classe", "C", key="ui_cls")
rstr = st.text_input("Restrictions", "NONE", key="ui_rstr")
endorse = st.text_input("Endorsements", "NONE", key="ui_endorse")
iss = st.date_input("Date d'émission", datetime.date.today(), key="ui_iss")

zip_options = sorted(ZIP_CITY_FIELD_OFFICE.keys(), key=int)
if not zip_options:
    zip_options = ["90001"]

if "ui_zip" not in st.session_state or st.session_state["ui_zip"] not in zip_options:
    st.session_state["ui_zip"] = zip_options[0]
    update_from_zip()

if "ui_city" not in st.session_state:
    st.session_state["ui_city"] = ZIP_CITY_FIELD_OFFICE.get(st.session_state["ui_zip"], {}).get("city", "")

if "ui_office" not in st.session_state:
    st.session_state["ui_office"] = ZIP_CITY_FIELD_OFFICE.get(st.session_state["ui_zip"], {}).get("field_office", "")

col_zip, col_city = st.columns([2, 3])
with col_zip:
    st.selectbox(
        "Code postal",
        options=zip_options,
        index=zip_options.index(st.session_state["ui_zip"]) if st.session_state["ui_zip"] in zip_options else 0,
        key="ui_zip",
        on_change=update_from_zip
    )

selected_zip = st.session_state.get("ui_zip", zip_options[0])
linked_city = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {}).get("city", "")
city_options = [linked_city] if linked_city else []

with col_city:
    st.selectbox(
        "Ville",
        options=city_options,
        index=0 if city_options else None,
        key="ui_city",
        on_change=update_from_city
    )

office_current = ZIP_CITY_FIELD_OFFICE.get(selected_zip, {}).get("field_office", "")
office_options = [office_current] if office_current else sorted(set(v.get("field_office", "") for v in ZIP_CITY_FIELD_OFFICE.values() if v.get("field_office")))

st.selectbox(
    "Field Office",
    options=office_options if office_options else [""],
    index=0,
    key="ui_office",
    on_change=update_from_office
)

generate = st.button("Générer la carte", key="ui_generate")

# -------------------------
# Validation & generation helpers
# -------------------------
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
    if st.session_state.get("ui_h1", 0) < 0 or st.session_state.get("ui_h2", 0) < 0 or st.session_state.get("ui_h1", 0) > 8 or st.session_state.get("ui_h2", 0) > 11:
        errors.append("Taille hors plage attendue.")
    if not st.session_state.get("ui_zip"):
        errors.append("Code postal requis.")
    if not st.session_state.get("ui_city"):
        errors.append("Ville requise.")
    if not st.session_state.get("ui_address_line", "").strip():
        errors.append("Address Line requise.")
    return errors

def build_aamva_tags(fields: Dict[str, str]) -> str:
    header = "@\r\nANSI 636014080102DL"
    parts = [header]
    order = ["DAQ", "DCS", "DAC", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"]
    for tag in order:
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return GS.join(parts) + "\r"

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
    x = 72
    y = height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE")
    y -= 24
    c.setFont("Helvetica", 11)
    for k, v in fields.items():
        c.drawString(x, y, f"{k}: {v}")
        y -= 16
        if y < 72:
            c.showPage()
            y = height - 72
    if photo_bytes and ImageReader is not None:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 72 - 90, height - 72 - 110, width=90, height=110)
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

# -------------------------
# Generate card and outputs
# -------------------------
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
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
    zip_sel = st.session_state["ui_zip"]
    city_sel = st.session_state["ui_city"]
    office_sel = st.session_state["ui_office"]
    address_sel = st.session_state["ui_address_line"]

    r = random.Random(seed(ln, fn, dob))
    dl = rletter(r, ln[0] if ln else "") + rdigits(r, 7)

    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        if dob.month == 2 and dob.day == 29:
            exp = datetime.date(exp_year, 2, 28)
        else:
            last_day = (datetime.date(exp_year, dob.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            exp = datetime.date(exp_year, dob.month, min(dob.day, last_day))

    m = re.search(r"\((\d{2,3})\)", office_sel or "")
    office_code = int(m.group(1)) if m else 0

    seq = next_sequence(r).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}/{seq}FD/{iss.year%100}"

    eyes_disp = (eyes or "").upper()
    hair_disp = (hair or "").upper()
    cls_disp = (cls or "").upper()
    rstr_disp = (rstr or "").upper()
    endorse_disp = (endorse or "").upper()
    height_str = f"{int(h1)}'{int(h2)}\""

    fields = {
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAQ": dl,
        "DAG": address_sel.upper(),
        "DAI": city_sel.upper(),
        "DAJ": "CA",
        "DAK": normalize_zip(zip_sel),
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
    }

    aamva = build_aamva_tags(fields)
    payload_to_use = aamva

    photo_src = IMAGE_M_URL if sex == "M" else IMAGE_F_URL
    photo_bytes = fetch_image_bytes(photo_src)

    if photo_bytes:
        b64 = base64.b64encode(photo_bytes).decode("utf-8")
        mime = "image/png"
        if photo_bytes[:3] == b'\xff\xd8\xff':
            mime = "image/jpeg"
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
                <div style="opacity:0.8;font-size:10px">DOB</div><div style="font-weight:700">{dob.strftime('%m/%d/%Y')}</div>
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
        errors = results.get("errors", [])
        warnings = results.get("warnings", [])
        infos = results.get("infos", [])
        with st.expander("Résultats de validation", expanded=True):
            if errors:
                st.error(f"Erreurs détectées ({len(errors)}) :")
                for e in errors:
                    st.write("- " + e)
            else:
                st.success("Aucune erreur bloquante détectée.")
            if warnings:
                st.warning(f"Avertissements ({len(warnings)}) :")
                for w in warnings:
                    st.write("- " + w)
            if infos:
                st.info("Informations :")
                for i in infos:
                    st.write("- " + i)
            corrected, applied = auto_correct_payload(payload_to_use)
            if corrected and corrected != payload_to_use:
                st.markdown("### Version corrigée proposée")
                if applied:
                    st.write("Corrections proposées :")
                    for a in applied:
                        st.write("- " + a)
                st.text_area("Payload corrigé (modifiable)", value=corrected, height=200, key="ui_aamva_corrected_preview")
                if st.button("Appliquer la correction et utiliser pour génération", key="ui_apply_correction"):
                    st.session_state["aamva_payload"] = st.session_state.get("ui_aamva_corrected_preview", corrected)
                    st.success("Correction appliquée. Le payload corrigé sera utilisé pour la génération.")
                    payload_to_use = st.session_state["aamva_payload"]

    svg_str = None
    if st.session_state.get("show_barcodes", True):
        st.subheader("PDF417")
        if _PDF417_AVAILABLE:
            try:
                svg_str = generate_pdf417_svg(
                    payload_to_use.encode("utf-8"),
                    columns=columns_param,
                    security_level=security_level_param,
                    scale=scale_param,
                    ratio=ratio_param,
                    color=color_param
                )
                svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
                with st.expander("Aperçu PDF417 (SVG)", expanded=True):
                    components.html(svg_html, height=260, scrolling=True)
                    st.download_button(
                        "Télécharger PDF417 (SVG)",
                        data=svg_str.encode("utf-8"),
                        file_name="pdf417.svg",
                        mime="image/svg+xml",
                        key="dl_pdf417_svg_main"
                    )
            except Exception as e:
                st.error("Erreur génération PDF417 : " + str(e))
        else:
            st.warning("pdf417gen non disponible. Vendorisez le module ou installez pdf417gen pour génération automatique.")
    else:
        with st.expander("Codes-barres masqués (cliquer pour afficher)"):
            st.write("Les codes-barres PDF417 sont actuellement masqués. Active la case 'Afficher les codes-barres (PDF417)' dans la barre latérale pour les voir.")
            if st.button("Afficher maintenant", key="ui_show_now"):
                st.session_state["show_barcodes"] = True
                st.experimental_rerun()

    cols = st.columns(2)
    with cols[0]:
        if svg_str:
            st.download_button(
                "Télécharger PDF417 (SVG) (panel)",
                data=svg_str.encode("utf-8"),
                file_name="pdf417_panel.svg",
                mime="image/svg+xml",
                key="dl_pdf417_svg_panel"
            )
    with cols[1]:
        try:
            pdf_bytes = create_pdf_bytes({
                "Nom": ln, "Prénom": fn, "Address": address_sel, "Sexe": sex, "DOB": dob.strftime("%m/%d/%Y"),
                "Ville": city_sel, "ZIP": zip_sel, "Field Office": office_sel,
                "DD": dd, "ISS": iss.strftime("%m/%d/%Y"), "EXP": exp.strftime("%m/%d/%Y"),
                "Classe": cls_disp, "Restrictions": rstr_disp, "Endorsements": endorse_disp,
                "Yeux/Cheveux/Taille/Poids": f"{eyes_disp}/{hair_disp}/{height_str}/{w} lb"
            }, photo_bytes=photo_bytes)
            st.download_button(
                "Télécharger la carte (PDF)",
                data=pdf_bytes,
                file_name="permis_ca.pdf",
                mime="application/pdf",
                key="dl_permis_pdf"
            )
        except Exception as e:
            st.error("Erreur génération PDF : " + str(e))
            if not _REPORTLAB_AVAILABLE:
                st.info("reportlab non installé : export PDF non disponible.")
