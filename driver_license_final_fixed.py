# driver_license_final_fixed.py
# Version robuste : validations et gestion des cas limites
# Interface et règles inchangées

import streamlit as st
import datetime, random, hashlib

st.set_page_config(page_title="Permis CA", layout="centered")

# -------------------------
# CSS pour la carte (inchangé)
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
# Utilitaires (améliorés mais comportement identique)
# -------------------------
def seed(*x):
    # Utiliser une représentation stable des dates pour seed
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
    # Si initial est une lettre, l'utiliser en majuscule, sinon choisir aléatoirement
    try:
        if isinstance(initial, str) and initial and initial[0].isalpha():
            return initial[0].upper()
    except Exception:
        pass
    return r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def next_sequence(r):
    # Conserver le comportement existant (2 chiffres)
    return str(r.randint(10,99))

# -------------------------
# Bureaux Field Office (inchangé)
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
# FORMULAIRE (inchangé visuellement)
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
# VALIDATIONS MINIMALES (non invasives)
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
    # poids/taille raisonnables
    if w < 30 or w > 500:
        errors.append("Poids hors plage attendue.")
    if h1 < 0 or h1 > 8 or h2 < 0 or h2 > 11:
        errors.append("Taille hors plage attendue.")
    return errors

# -------------------------
# GÉNÉRATION DE LA CARTE (logique inchangée mais plus robuste)
# -------------------------
if generate:
    # validations
    errs = validate_inputs()
    if errs:
        for e in errs:
            st.error(e)
        st.stop()

    # Random déterministe
    r = random.Random(seed(ln,fn,dob))

    # DL : lettre + 7 chiffres (même règle)
    dl = rletter(r, ln[0] if ln else "") + rdigits(r,7)

    # EXP : 5 ans après ISS, aligné sur mois/jour de DOB (même règle)
    exp_year = iss.year + 5
    try:
        exp = datetime.date(exp_year, dob.month, dob.day)
    except ValueError:
        # Cas 29 février -> fallback au 28 février (gestion non invasive)
        if dob.month == 2 and dob.day == 29:
            exp = datetime.date(exp_year, 2, 28)
        else:
            # fallback général : utiliser le dernier jour du mois
            last_day = (datetime.date(exp_year, dob.month % 12 + 1, 1) - datetime.timedelta(days=1)).day
            exp = datetime.date(exp_year, dob.month, min(dob.day, last_day))

    # Field office code et DD (même logique, format conservé)
    office_code = offices[office_choice]
    seq = next_sequence(r)
    # garantir que seq est 2 chiffres
    seq = seq.zfill(2)
    dd = f"{iss.strftime('%m/%d/%Y')}{office_code}{seq}FD/{iss.year%100}"

    # Normalisations d'affichage (MAJ pour codes, format taille)
    eyes_disp = (eyes or "").upper()
    hair_disp = (hair or "").upper()
    cls_disp = (cls or "").upper()
    rstr_disp = (rstr or "").upper()
    endorse_disp = (endorse or "").upper()
    # Format taille standard (ex: 5'10")
    height_str = f"{int(h1)}'{int(h2)}\""

    # HTML inchangé visuellement, mêmes champs et labels
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


