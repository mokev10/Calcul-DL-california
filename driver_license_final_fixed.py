#!/usr/bin/env python3
# driver_license_final_fixed.py
# Générateur de permis CA + intégration AAMVA validation/correction automatique
# Dépendances recommandées: streamlit, requests, reportlab, pdf417gen, pillow
# Place aamva_utils.py dans le même dossier.

import streamlit as st
import datetime
import random
import hashlib
import io
import base64
import requests
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any

import streamlit.components.v1 as components

# Import des utilitaires AAMVA (validation + correction)
from aamva_utils import validate_aamva_payload, auto_correct_payload, example_payload, GS

# ReportLab pour PDF export
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Pillow pour rasterisation
try:
    from PIL import Image, ImageDraw, ImageOps
    _PIL_AVAILABLE = True
except Exception:
    _PIL_AVAILABLE = False

# pdf417gen (optionnel)
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    _PDF417_AVAILABLE = False

st.set_page_config(page_title="Permis CA (avec validation AAMVA)", layout="centered")

# -------------------------
# Field offices (inchangé)
field_offices = {
    "Baie de San Francisco": {
        "Corte Madera": 525,
        "Daly City": 599,
        "El Cerrito": 585,
        "Fremont": 643,
        "Hayward": 521,
        "Los Gatos": 641,
        "Novato": 647,
        "Oakland (Claremont)": 501,
        "Oakland (Coliseum)": 604,
        "Pittsburg": 651,
        "Pleasanton": 639,
        "Redwood City": 542,
        "San Francisco": 503,
        "San Jose (Alma)": 516,
        "San Jose (Driver License Center)": 607,
        "San Mateo": 594,
        "Santa Clara": 632,
        "Vallejo": 538
    },
    "Grand Los Angeles": {
        "Arleta": 628, "Bellflower": 610, "Culver City": 514, "Glendale": 540,
        "Hollywood": 633, "Inglewood": 544, "Long Beach": 507, "Los Angeles (Hope St)": 502,
        "Montebello": 531, "Pasadena": 510, "Santa Monica": 548, "Torrance": 592, "West Covina": 591
    },
    "Orange County / Sud": {
        "Costa Mesa": 627, "Fullerton": 547, "Laguna Hills": 642, "Santa Ana": 529,
        "San Clemente": 652, "Westminster": 623, "Chula Vista": 609, "El Cajon": 549,
        "Oceanside": 593, "San Diego (Clairemont)": 618, "San Diego (Normal St)": 504,
        "San Marcos": 637, "San Ysidro": 649, "Auburn": 533, "Chico": 534, "Eureka": 522,
        "Redding": 550, "Roseville": 635, "Sacramento (Broadway)": 500, "Sacramento (South)": 603, "Woodland": 535
    },
    "Vallée Centrale": {
        "Bakersfield": 511, "Fresno": 505, "Lodi": 595, "Modesto": 536, "Stockton": 517, "Visalia": 519
    }
}

FIELD_OFFICE_MAP: Dict[str, str] = {}
for region, cities in field_offices.items():
    for city, code in cities.items():
        label = f"{region} — {city} ({code})"
        FIELD_OFFICE_MAP[city.upper()] = label

# -------------------------
# Utilitaires locaux (identiques à ton script)
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
# PDF417 helper (si pdf417gen présent)
def generate_pdf417_svg_from_bytes(data_bytes: bytes, columns:int, security_level:int, scale:int, ratio:int, color:str) -> str:
    if not _PDF417_AVAILABLE:
        raise RuntimeError("Module pdf417gen non disponible.")
    codes = encode(data_bytes, columns=columns, security_level=security_level, force_binary=False)
    svg_tree = render_svg(codes, scale=scale, ratio=ratio, color=color)
    try:
        svg_bytes = ET.tostring(svg_tree.getroot(), encoding="utf-8", method="xml")
        return svg_bytes.decode("utf-8")
    except Exception:
        return str(svg_tree)

# -------------------------
# Rasterisation simple via Pillow (rects + simple paths)
def parse_svg_shapes(svg_text: str):
    # Fonction simplifiée : on cherche <rect> et <path> simples
    try:
        root = ET.fromstring(svg_text)
    except Exception:
        return None, []
    width = root.get('width'); height = root.get('height'); viewBox = root.get('viewBox') or root.get('viewbox')
    canvas_size = None
    if width and height:
        try:
            w = int(float(re.sub(r'[^\d\.]', '', width))); h = int(float(re.sub(r'[^\d\.]', '', height)))
            canvas_size = (w,h)
        except Exception:
            canvas_size = None
    if not canvas_size and viewBox:
        parts = re.split(r'[,\s]+', viewBox.strip())
        if len(parts) >= 4:
            try:
                canvas_size = (int(float(parts[2])), int(float(parts[3])))
            except Exception:
                canvas_size = None
    shapes = []
    for rect in root.findall('.//{http://www.w3.org/2000/svg}rect') + root.findall('.//rect'):
        try:
            x = float(rect.get('x') or 0); y = float(rect.get('y') or 0)
            w = float(rect.get('width') or 0); h = float(rect.get('height') or 0)
            fill = rect.get('fill') or rect.get('style') or '#000'
            if 'fill:' in fill and ';' in fill:
                m = re.search(r'fill:\s*([^;]+)', fill)
                if m: fill = m.group(1).strip()
            shapes.append({'type':'rect','x':x,'y':y,'w':w,'h':h,'fill':fill})
        except Exception:
            continue
    # paths simple (M/L/Z)
    for path in root.findall('.//{http://www.w3.org/2000/svg}path') + root.findall('.//path'):
        d = path.get('d') or ''
        fill = path.get('fill') or path.get('style') or '#000'
        if 'fill:' in fill and ';' in fill:
            m = re.search(r'fill:\s*([^;]+)', fill)
            if m: fill = m.group(1).strip()
        pts = parse_path_d_simple(d)
        if pts:
            shapes.append({'type':'path','points':pts,'fill':fill})
    return canvas_size, shapes

def parse_path_d_simple(d: str):
    if not d or not re.search(r'[MLZmlz]', d):
        return None
    s = d.replace(',', ' ')
    tokens = re.findall(r'[MLZmlz]|-?\d+\.?\d*', s)
    pts = []
    i = 0; cur_cmd = None
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r'[MLZmlz]', t):
            cur_cmd = t; i += 1; continue
        if cur_cmd is None:
            return None
        if cur_cmd.upper() == 'Z':
            cur_cmd = None; continue
        try:
            x = float(t); y = float(tokens[i+1])
            pts.append((x,y)); i += 2
            if cur_cmd.islower():
                return None
        except Exception:
            return None
    if not pts: return None
    return pts

def color_to_rgba(color_str: str):
    s = (color_str or "").strip()
    if not s: return (0,0,0,255)
    if s.startswith('#'):
        s = s.lstrip('#')
        if len(s) == 3:
            r = int(s[0]*2,16); g = int(s[1]*2,16); b = int(s[2]*2,16)
        else:
            r = int(s[0:2],16); g = int(s[2:4],16); b = int(s[4:6],16)
        return (r,g,b,255)
    m = re.match(r'rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)', s)
    if m: return (int(m.group(1)),int(m.group(2)),int(m.group(3)),255)
    named = {'black':(0,0,0,255),'white':(255,255,255,255),'red':(255,0,0,255)}
    return named.get(s.lower(), (0,0,0,255))

def rasterize_shapes_to_png_bytes(svg_text: str, scale: int = 3, bg=(255,255,255,255)):
    if not _PIL_AVAILABLE:
        raise RuntimeError("Pillow (PIL) non disponible.")
    canvas_size, shapes = parse_svg_shapes(svg_text)
    if not shapes:
        raise RuntimeError("Aucun élément pris en charge (<rect> ou <path> simple) trouvé dans le SVG.")
    if not canvas_size:
        max_x = max_y = 0
        for s in shapes:
            if s['type']=='rect':
                max_x = max(max_x, s['x']+s['w']); max_y = max(max_y, s['y']+s['h'])
            else:
                for (px,py) in s['points']:
                    max_x = max(max_x, px); max_y = max(max_y, py)
        canvas_size = (int(max_x), int(max_y))
    w0,h0 = canvas_size; w = max(1,int(w0*scale)); h = max(1,int(h0*scale))
    img = Image.new("RGBA",(w,h),bg); draw = ImageDraw.Draw(img)
    for s in shapes:
        if s['type']=='rect':
            x1=int(s['x']*scale); y1=int(s['y']*scale); x2=int((s['x']+s['w'])*scale); y2=int((s['y']+s['h'])*scale)
            rgba = color_to_rgba(s.get('fill')); draw.rectangle([x1,y1,x2,y2], fill=rgba)
        else:
            pts = [(int(px*scale), int(py*scale)) for (px,py) in s['points']]
            rgba = color_to_rgba(s.get('fill'))
            try:
                draw.polygon(pts, fill=rgba)
            except Exception:
                for i in range(len(pts)-1):
                    draw.line([pts[i], pts[i+1]], fill=rgba)
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()

# -------------------------
# UI & paramètres
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>html, body, [class*="css"] { font-family: 'Inter', sans-serif; }</style>
""", unsafe_allow_html=True)

st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6)
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0,9)), index=2)
scale_param = st.sidebar.slider("Échelle (SVG generator)", 1, 6, 3)
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3)
color_param = st.sidebar.color_picker("Couleur du code", "#000000")
st.sidebar.markdown("**Rasterisation (aperçu PNG/GIF)**")
raster_scale_ui = st.sidebar.selectbox("Scale raster (entier)", [1,2,3,4,5], index=2)
gif_delay_ui = st.sidebar.number_input("GIF delay (ms)", min_value=50, max_value=2000, value=200, step=50)

# Session defaults
if "aamva_payload" not in st.session_state:
    st.session_state["aamva_payload"] = ""

# (Form fields simplified for brevity; tu peux réutiliser les champs complets de ton script)
st.title("Générateur officiel de permis CA (avec validation AAMVA)")

ln = st.text_input("Nom de famille", "HARMS", key="ln_input")
fn = st.text_input("Prénom", "ROSA", key="fn_input")
address1 = st.text_input("Adresse (ligne 1)", "2570 24TH STREET", key="address1_input")
zip_select = st.text_input("Code postal", "94925", key="zip_select")
city_select = st.text_input("Ville", "Corte Madera", key="city_select")
state = st.text_input("État (abbrev.)", "CA", key="state_input")
sex = st.selectbox("Sexe", ["M","F"], index=0, key="sex_input")
dob = st.date_input("Date de naissance", datetime.date(1990,1,1), key="dob_input")
iss = st.date_input("Date d'émission", datetime.date.today(), key="iss_input")

generate = st.button("Générer la carte (AAMVA + PDF417)")

# -------------------------
# Helpers PDF creation (PDF final)
def create_pdf_bytes(fields: Dict[str,str], photo_bytes: bytes = None) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 72; y = height - 72
    c.setFont("Helvetica-Bold", 14); c.drawString(x, y, "CALIFORNIA USA DRIVER LICENSE"); y -= 24
    c.setFont("Helvetica", 11)
    for k, v in fields.items():
        c.drawString(x, y, f"{k}: {v}"); y -= 16
        if y < 72:
            c.showPage(); y = height - 72
    if photo_bytes:
        try:
            img = ImageReader(io.BytesIO(photo_bytes))
            c.drawImage(img, width - 72 - 90, height - 72 - 110, width=90, height=110)
        except Exception:
            pass
    c.showPage(); c.save(); buffer.seek(0); return buffer.read()

# -------------------------
# Flux principal : génération -> validation -> correction -> régénération
if generate:
    # Construire champs AAMVA
    r = random.Random(seed(ln, fn, st.session_state["dob_input"]))
    dl = rletter(r, ln[0] if ln else "") + rdigits(r,7)
    exp_year = st.session_state["iss_input"].year + 5
    try:
        exp = datetime.date(exp_year, st.session_state["dob_input"].month, st.session_state["dob_input"].day)
    except Exception:
        exp = datetime.date(exp_year, 2, 28)

    fields = {
        "DAQ": dl,
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": st.session_state["dob_input"].strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": st.session_state["iss_input"].strftime("%m%d%Y"),
        "DAG": address1.upper(),
        "DAI": city_select.upper(),
        "DAJ": state.upper(),
        "DAK": re.sub(r"\D","", zip_select)[:10],
        "DCF": "1234567890",
        "DAU": "510",
        "DAY": "BRN",
        "DAZ": "BRN",
    }

    # Construire payload AAMVA (séparateurs GS)
    header = "@\r\nANSI 636014080102DL"
    parts = [header]
    order = ["DAQ","DCS","DAC","DBB","DBA","DBD","DAG","DAI","DAJ","DAK","DCF","DAU","DAY","DAZ"]
    for tag in order:
        val = fields.get(tag)
        if val is not None:
            parts.append(f"{tag}{val}")
    aamva = GS.join(parts) + "\r"

    # Stocker dans session pour persistance
    st.session_state["aamva_payload"] = aamva

    # Afficher carte visuelle (simplifiée)
    st.markdown("### Carte générée (aperçu)")
    st.markdown(f"**DL**: {dl}  •  **Nom**: {ln}  •  **Prénom**: {fn}")

    # --- Validation automatique via aamva_utils
    st.subheader("Validation AAMVA automatique")
    results = validate_aamva_payload(aamva)
    errors = results.get("errors", [])
    warnings = results.get("warnings", [])
    infos = results.get("infos", [])

    with st.expander("Afficher les résultats de validation AAMVA", expanded=True):
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

        # Proposer correction automatique si applicable
        corrected, applied = auto_correct_payload(aamva)
        if corrected and corrected != aamva:
            st.markdown("**Version corrigée proposée**")
            if applied:
                st.write("Corrections proposées :")
                for a in applied:
                    st.write("- " + a)
            st.text_area("Payload corrigé (modifiable)", value=corrected, height=200, key="aamva_corrected_preview")
            if st.button("Appliquer la correction et régénérer PDF417"):
                # Appliquer correction
                st.session_state["aamva_payload"] = st.session_state.get("aamva_corrected_preview", corrected)
                st.success("Correction appliquée. Régénération en cours...")
                # Mettre à jour aamva local et continuer pour régénérer
                aamva = st.session_state["aamva_payload"]
                # (Optionnel) régénérer SVG/PNG/GIF ici en réutilisant le code ci-dessous
        else:
            st.write("Aucune correction automatique proposée.")

    # --- Génération PDF417 (SVG) et rasterisation si possible
    st.subheader("PDF417 (génération)")
    if _PDF417_AVAILABLE:
        try:
            svg_str = generate_pdf417_svg_from_bytes(aamva.encode("utf-8"),
                                                    columns=columns_param,
                                                    security_level=security_level_param,
                                                    scale=scale_param,
                                                    ratio=ratio_param,
                                                    color=color_param)
            # Nettoyage SVG
            svg_str = svg_str.replace('<svg ', '<svg shape-rendering="crispEdges" vector-effect="non-scaling-stroke" style="image-rendering:pixelated; image-rendering:-moz-crisp-edges;" ')
            svg_str = re.sub(r'\sstroke="[^"]+"', '', svg_str)
            svg_str = re.sub(r'\sstroke-width="[^"]+"', '', svg_str)
            svg_str = re.sub(r'width="([\d\.]+)"', lambda m: f'width="{int(float(m.group(1)))}"', svg_str)
            svg_str = re.sub(r'height="([\d\.]+)"', lambda m: f'height="{int(float(m.group(1)))}"', svg_str)

            components.html(f"<div style='background:#fff;padding:8px;border-radius:6px'>{svg_str}</div>", height=260, scrolling=True)

            # Téléchargements SVG
            st.download_button("Télécharger PDF417 (SVG)", data=svg_str.encode("utf-8"), file_name="pdf417.svg", mime="image/svg+xml")

            # Rasterisation via Pillow si possible
            if _PIL_AVAILABLE:
                try:
                    png_bytes = rasterize_shapes_to_png_bytes(svg_str, scale=max(1,int(raster_scale_ui)))
                    st.image(png_bytes, caption="Aperçu PNG", width=320)
                    st.download_button("Télécharger PDF417 (PNG)", data=png_bytes, file_name="pdf417.png", mime="image/png")
                    # GIF mono-frame
                    img = Image.open(io.BytesIO(png_bytes)).convert("P", palette=Image.ADAPTIVE)
                    gif_buf = io.BytesIO(); img.save(gif_buf, format="GIF", save_all=True, loop=0, duration=int(gif_delay_ui))
                    gif_bytes = gif_buf.getvalue()
                    st.image(gif_bytes, caption="Aperçu GIF", width=320)
                    st.download_button("Télécharger PDF417 (GIF)", data=gif_bytes, file_name="pdf417.gif", mime="image/gif")
                except Exception as ex:
                    st.error("Erreur lors de la rasterisation PNG/GIF : " + str(ex))
            else:
                st.info("Pillow non installé : PNG/GIF non disponibles ici.")
        except Exception as e:
            st.error("Erreur génération PDF417 (pdf417gen) : " + str(e))
            st.info("Si pdf417gen n'est pas installé, tu peux coller le payload dans l'outil de validation séparé ou utiliser la page HTML/JS fournie pour rasteriser côté navigateur.")
    else:
        st.info("pdf417gen non disponible : SVG PDF417 non généré automatiquement. Tu peux coller le payload dans l'outil de validation séparé ou installer pdf417gen pour génération automatique.")

    # --- Générer PDF final (carte) et proposer téléchargement
    pdf_bytes = create_pdf_bytes({
        "Nom": ln, "Prénom": fn, "Sexe": st.session_state.get("sex_input"),
        "DOB": st.session_state["dob_input"].strftime("%m/%d/%Y"),
        "Adresse": address1, "Ville": city_select, "État": state, "Code postal": zip_select,
        "DD": "N/A", "ISS": st.session_state["iss_input"].strftime("%m/%d/%Y"),
        "EXP": exp.strftime("%m/%d/%Y")
    }, photo_bytes=None)
    st.download_button("Télécharger la carte (PDF)", data=pdf_bytes, file_name="permis_ca.pdf", mime="application/pdf")
