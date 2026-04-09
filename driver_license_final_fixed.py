# driver_license_final_fixed.py
# Version complète et autonome : validations, health check intégré et intégration PDF417 si disponible

import streamlit as st
import datetime, random, hashlib
import streamlit.components.v1 as components
from typing import Dict

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# CSS pour la carte
# -------------------------
st.markdown("""
<style>
.card {
    width: 450px;
    border-radius: 14px;
    padding: 16px;
    background: linear-gradient(135deg,#1e3a8a,#2563eb);
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    margin: auto;
}
.header {
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-weight:700;
    font-size:14px;
    margin-bottom:10px;
}
.body {
    display:flex;
    gap:12px;
}
.photo {
    width:90px;
    height:110px;
    background:#e5e7eb;
    border-radius:8px;
}
.info {
    flex:1;
    font-size:12px;
}
.label {
    opacity:0.7;
    font-size:10px;
}
.value {
    font-weight:700;
    margin-bottom:4px;
}
.footer {
    margin-top:10px;
    display:flex;
    justify-content:space-between;
    font-size:11px;
}
.badge {
    background:white;
    color:#1e3a8a;
    padding:2px 6px;
    border-radius:6px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar: paramètres PDF417 (optionnel)
# -------------------------
st.sidebar.header("Paramètres PDF417 (optionnel)")
columns_param = st.sidebar.slider("Colonnes", 1, 30, 6)
security_level_param = st.sidebar.selectbox("Niveau ECC", list(range(0,9)), index=2)
scale_param = st.sidebar.slider("Échelle", 1, 6, 3)
ratio_param = st.sidebar.slider("Ratio", 1, 6, 3)
color_param = st.sidebar.color_picker("Couleur du code", "#000000")
st.sidebar.markdown("Si pdf417gen n'est pas complet, l'app affichera un message d'avertissement.")

# -------------------------
# Debug / health check intégré (Option A)
# Coche la case dans la sidebar pour exécuter uniquement le health check
# -------------------------
if st.sidebar.checkbox("Activer health check (debug)"):
    st.sidebar.markdown("### Health Check pdf417gen")
    try:
        import pdf417gen
        from pdf417gen import encode, render_svg
        st.sidebar.success("Import pdf417gen OK")
        st.sidebar.write("pdf417gen path:", getattr(pdf417gen, "__file__", "n/a"))
        try:
            codes = encode(b"TEST", columns=3, security_level=2, force_binary=False)
            st.sidebar.write("encode() OK, type:", type(codes).__name__)
        except Exception as e:
            st.sidebar.warning("encode() raised: " + str(e))
        st.sidebar.write("render_svg callable:", callable(render_svg))
    except Exception as exc:
        st.sidebar.error("Import pdf417gen failed: " + str(exc))
        st.sidebar.info("Vérifie que pdf417gen/ est à la racine et contient __init__.py")
    st.stop()

# -------------------------
# Utilitaires
# -------------------------
def seed(*x):
    parts = []
    for item in x:
        if isinstance(item, (datetime.date, datetime.datetime)):
            parts.append(item.isoformat())
        else:
            parts.append(str(item))
    return int(hashlib.md5("|".join(parts).encode()).hexdigest()[:8],16)

def rdigits(r,n):
    return "".join(r.choice("0123456789") for _ in range(n))

def rletter(r, initial):
    try:
        if isinstance(initial, str) and initial and initial[0].isalpha():
            return initial[0].upper()
    except Exception:
        pass
    return r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(r):
    return str(r.randint(10,99))

# -------------------------
# Bureaux Field Office
# -------------------------
offices = {
    "Baie de San Francisco — Corte Madera (525)": 525,
    "Baie de San Francisco — Daly City (599)": 599,
    "Baie de San Francisco — El Cerrito (585)": 585,
    "Baie de San Francisco — Fremont (643)": 643,
    "Baie de San Francisco — Hayward (521)": 521,
    "Baie de San Francisco — Los Gatos (641)": 641,
    "Baie de San Francisco — Novato (647)": 647,
    "Baie de San Francisco — Oakland (Claremont) (501)": 501,
    "Baie de San Francisco — Oakland (Coliseum) (604)": 604,
    "Baie de San Francisco — Pittsburg (651)": 651,
    "Baie de San Francisco — Pleasanton (639)": 639,
    "Baie de San Francisco — Redwood City (542)": 542,
    "Baie de San Francisco — San Francisco (503)": 503,
    "Baie de San Francisco — San Jose (Alma) (516)": 516,
    "Baie de San Francisco — San Jose (Driver License Center) (607)": 607,
    "Baie de San Francisco — San Mateo (594)": 594,
    "Baie de San Francisco — Santa Clara (632)": 632,
    "Baie de San Francisco — Vallejo (538)": 538,
    "Grand Los Angeles — Arleta (628)": 628,
    "Grand Los Angeles — Bellflower (610)": 610,
    "Grand Los Angeles — Culver City (514)": 514,
    "Grand Los Angeles — Glendale (540)": 540,
    "Grand Los Angeles — Hollywood (633)": 633,
    "Grand Los Angeles — Inglewood (544)": 544,
    "Grand Los Angeles — Long Beach (507)": 507,
    "Grand Los Angeles — Los Angeles (Hope St) (502)": 502,
    "Grand Los Angeles — Montebello (531)": 531,
    "Grand Los Angeles — Pasadena (510)": 510,
    "Grand Los Angeles — Santa Monica (548)": 548,
    "Grand Los Angeles — Torrance (592)": 592,
    "Grand Los Angeles — West Covina (591)": 591,
    "Orange County / Sud — Costa Mesa (627)": 627,
    "Orange County / Sud — Fullerton (547)": 547,
    "Orange County / Sud — Laguna Hills (642)": 642,
    "Orange County / Sud — Santa Ana (529)": 529,
    "Orange County / Sud — San Clemente (652)": 652,
    "Orange County / Sud — Westminster (623)": 623,
    "San Diego & Environs — Chula Vista (609)": 609,
    "San Diego & Environs — El Cajon (549)": 549,
    "San Diego & Environs — Oceanside (593)": 593,
    "San Diego & Environs — San Diego (Clairemont) (618)": 618,
    "San Diego & Environs — San Diego (Normal St) (504)": 504,
    "San Diego & Environs — San Marcos (637)": 637,
    "San Diego & Environs — San Ysidro (649)": 649,
    "Sacramento / Nord — Auburn (533)": 533,
    "Sacramento / Nord — Chico (534)": 534,
    "Sacramento / Nord — Eureka (522)": 522,
    "Sacramento / Nord — Redding (550)": 550,
    "Sacramento / Nord — Roseville (635)": 635,
    "Sacramento / Nord — Sacramento (Broadway) (500)": 500,
    "Sacramento / Nord — Sacramento (South) (603)": 603,
    "Sacramento / Nord — Woodland (535)": 535,
    "Vallée Centrale — Bakersfield (511)": 511,
    "Vallée Centrale — Fresno (505)": 505,
    "Vallée Centrale — Lodi (595)": 595,
    "Vallée Centrale — Modesto (536)": 536,
    "Vallée Centrale — Stockton (517)": 517,
    "Vallée Centrale — Visalia (519)": 519
}

# -------------------------
# FORMULAIRE
# -------------------------
st.title("Générateur officiel de permis CA")

ln = st.text_input("Nom de famille", "HARMS")
fn = st.text_input("Prénom", "ROSA")
sex = st.selectbox("Sexe", ["M","F"])
dob = st.date_input("Date de naissance", datetime.date(1990,1,1))

col1, col2 = st.columns(2)
with col1:
    h1 = st.number_input("Pieds",0,8,5)
    w = st.number_input("Poids (lb)",30,500,160)
with col2:
    h2 = st.number_input("Pouces",0,11,10)
    eyes = st.text_input("Yeux","BRN")
hair = st.text_input("Cheveux","BRN")
cls = st.text_input("Classe","C")
rstr = st.text_input("Restrictions","NONE")
endorse = st.text_input("Endorsements","NONE")
iss = st.date_input("Date d'émission", datetime.date.today())

office_choice = st.selectbox("Field Office", list(offices.keys()))

generate = st.button("Générer la carte")

# -------------------------
# VALIDATIONS MINIMALES
# -------------------------
def validate_inputs():
    errors = []
    if not ln or not ln.strip():
        errors.append("Nom de famille requis.")
    if not fn or not fn.strip():
        errors.append("Prénom requis.")
    if dob > datetime.date.today():
        errors.append("Date de naissance ne peut pas être dans le futur.")
    if iss > datetime.date.today():
        errors.append("Date d'émission ne peut pas être dans le futur.")
    if w < 30 or w > 500:
        errors.append("Poids hors plage attendue.")
    if h1 < 0 or h1 > 8 or h2 < 0 or h2 > 11:
        errors.append("Taille hors plage attendue.")
    return errors

# -------------------------
# AAMVA builder (texte pour PDF417)
# -------------------------
def build_aamva_tags(fields: Dict[str,str]) -> str:
    header = "@\n\rANSI 636014080102DL"
    parts = [header]
    for tag in ("DCS","DAC","DBB","DBA","DBD","DAQ","DAG","DAI","DAJ","DAK","DCF","DAU","DAY","DAZ"):
        val = fields.get(tag)
        if val:
            parts.append(f"{tag}{val}")
    return "\u001e\r".join(parts) + "\r"

# -------------------------
# Import pdf417gen (vendorisé) si disponible
# -------------------------
_PDF417_AVAILABLE = False
try:
    from pdf417gen import encode, render_svg
    _PDF417_AVAILABLE = True
except Exception:
    try:
        import pdf417gen
        from pdf417gen import encode, render_svg
        _PDF417_AVAILABLE = True
    except Exception:
        _PDF417_AVAILABLE = False

def generate_pdf417_svg(data_bytes: bytes, columns:int, security_level:int, scale:int, ratio:int, color:str) -> str:
    if not _PDF417_AVAILABLE:
        raise RuntimeError("Module pdf417gen non disponible.")
    codes = encode(data_bytes, columns=columns, security_level=security_level, force_binary=False)
    svg_tree = render_svg(codes, scale=scale, ratio=ratio, color=color)
    # si render_svg renvoie un ElementTree, convertir en string
    try:
        import xml.etree.ElementTree as ET
        svg_bytes = ET.tostring(svg_tree.getroot(), encoding="utf-8", method="xml")
        return svg_bytes.decode("utf-8")
    except Exception:
        # si render_svg renvoie déjà une string
        return str(svg_tree)

# -------------------------
# GÉNÉRATION DE LA CARTE
# -------------------------
if generate:
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
        st.stop()

    r = random.Random(seed(ln,fn,dob))
    dl = rletter(r, ln[0] if ln else "") + rdigits(r,7)

    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        if dob.month == 2 and dob.day == 29:
            exp = datetime.date(exp_year, 2, 28)
        else:
            last_day = (datetime.date(exp_year, dob.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            exp = datetime.date(exp_year, dob.month, min(dob.day, last_day))

    office_code = offices[office_choice]
    seq = next_sequence(r).zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}{seq}FD/{iss.year%100}"

    eyes_disp = (eyes or "").upper()
    hair_disp = (hair or "").upper()
    cls_disp = (cls or "").upper()
    rstr_disp = (rstr or "").upper()
    endorse_disp = (endorse or "").upper()
    height_str = f"{int(h1)}'{int(h2)}\""

    # champs AAMVA
    fields = {
        "DCS": ln.upper(),
        "DAC": fn.upper(),
        "DBB": dob.strftime("%m%d%Y"),
        "DBA": exp.strftime("%m%d%Y"),
        "DBD": iss.strftime("%m%d%Y"),
        "DAQ": dl,
        "DAG": "2570 24TH STREET",
        "DAI": "ANYTOWN",
        "DAJ": "CA",
        "DAK": "95818",
        "DCF": dd,
        "DAU": f"{int(h1)}{int(h2)}",
        "DAY": eyes_disp,
        "DAZ": hair_disp,
    }

    aamva = build_aamva_tags(fields)
    data_bytes = aamva.encode("utf-8")

    # HTML carte (affichage)
    html = f"""
    <div class="card">
        <div class="header">
            <div>CALIFORNIA USA DRIVER LICENSE</div>
            <div class="badge">{dl}</div>
        </div>
        <div class="body">
            <div class="photo"></div>
            <div class="info">
                <div class="label">Nom</div>
                <div class="value">{ln}</div>
                <div class="label">Prénom</div>
                <div class="value">{fn}</div>
                <div class="label">Sexe</div>
                <div class="value">{sex}</div>
                <div class="label">DOB</div>
                <div class="value">{dob.strftime('%m/%d/%Y')}</div>
                <div class="label">Field Office</div>
                <div class="value">{office_choice}</div>
                <div class="label">DD</div>
                <div class="value">{dd}</div>
                <div class="label">ISS</div>
                <div class="value">{iss.strftime('%m/%d/%Y')}</div>
                <div class="label">EXP</div>
                <div class="value">{exp.strftime('%m/%d/%Y')}</div>
                <div class="label">Classe</div>
                <div class="value">{cls_disp}</div>
                <div class="label">Restrictions</div>
                <div class="value">{rstr_disp}</div>
                <div class="label">Endorsements</div>
                <div class="value">{endorse_disp}</div>
                <div class="label">Yeux / Cheveux / Taille / Poids</div>
                <div class="value">{eyes_disp} / {hair_disp} / {height_str} / {w} lb</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Génération et affichage du PDF417 sous la carte
    if _PDF417_AVAILABLE:
        try:
            svg_str = generate_pdf417_svg(data_bytes,
                                         columns=columns_param,
                                         security_level=security_level_param,
                                         scale=scale_param,
                                         ratio=ratio_param,
                                         color=color_param)
            svg_html = f"<div style='background:#fff;padding:8px;border-radius:6px;margin-top:12px;display:flex;justify-content:center'>{svg_str}</div>"
            components.html(svg_html, height=220, scrolling=True)
        except Exception as e:
            st.error("Erreur génération PDF417 : " + str(e))
            st.info("Vérifiez le module pdf417gen dans le dossier vendorisé.")
    else:
        st.warning("pdf417gen non disponible. Vendorisez le module ou complétez pdf417gen/__init__.py pour exposer encode et render_svg.")
