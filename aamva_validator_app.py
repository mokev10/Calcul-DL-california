#!/usr/bin/env python3
# aamva_validator_app.py
# Streamlit app — Validateur et générateur d'exemples AAMVA / PDF417
# But: vérifier header, séparateurs, dates, encodage, champs obligatoires et donner recommandations.
#
# Usage: streamlit run aamva_validator_app.py

import streamlit as st
import re
import datetime
from typing import List, Tuple, Dict, Optional, Any

st.set_page_config(page_title="AAMVA Validator & Example", layout="centered")

# -------------------------
# Utilitaires de validation
GS = "\x1E"  # Group Separator (AAMVA uses 0x1E between data elements)
REQUIRED_TAGS = [
    "DAQ",  # Driver License / ID Number
    "DCS",  # Family Name
    "DAC",  # Given Name
    "DBB",  # DOB MMDDYYYY
    "DBA",  # Expiration MMDDYYYY
    "DBD",  # Issue Date MMDDYYYY
    "DAG",  # Address 1
    "DAI",  # City
    "DAJ",  # State
    "DAK",  # Postal code
    "DCF",  # Document discriminator (often present)
]

DATE_TAGS = ["DBB", "DBA", "DBD"]


def has_valid_header(payload: str) -> Tuple[bool, str]:
    """
    Vérifie la présence d'un header AAMVA correct.
    Exemples d'en-tête valides : '@\\r\\nANSI 636014080102DL' ou '@\\n\\rANSI 636014080102DL'
    On vérifie la présence de 'ANSI' et 'DL' et d'un code AAMVA (6360...).
    """
    if not payload:
        return False, "Payload vide."
    head = payload[:200].upper()
    if "ANSI" not in head or "DL" not in head:
        return False, "Header manquant ou incorrect (attendu 'ANSI ... DL')."
    if not re.search(r"ANSI\s+63\d{2}", head):
        return False, "Header AAMVA non conforme (code version absent ou invalide)."
    return True, "Header OK."


def uses_group_separator(payload: str) -> Tuple[bool, str]:
    if GS in payload:
        return True, "Séparateur de groupe (0x1E) présent."
    if "\\u001e" in payload or "\\x1E" in payload:
        return False, "Séparateur trouvé sous forme d'échappement (\\u001e). Remplacer par le caractère 0x1E réel."
    return False, "Séparateur de groupe (0x1E) absent. Les parseurs AAMVA exigent 0x1E entre champs."


def ends_with_cr(payload: str) -> Tuple[bool, str]:
    if payload.endswith("\r") or payload.endswith("\r\n") or payload.endswith("\n\r"):
        return True, "Fin de record OK (CR présent)."
    return False, "Fin de record manquante (ajouter un CR '\\r' à la fin)."


def find_tags(payload: str) -> List[str]:
    tags = re.findall(r"([A-Z]{3})(?=[^\r\n\x1E]*)", payload)
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def check_required_tags(payload: str) -> Tuple[bool, List[str]]:
    missing = []
    for tag in REQUIRED_TAGS:
        if tag not in payload:
            missing.append(tag)
    return (len(missing) == 0, missing)


def check_date_format(value: str) -> bool:
    if not re.fullmatch(r"\d{8}", value):
        return False
    try:
        mm = int(value[0:2])
        dd = int(value[2:4])
        yyyy = int(value[4:8])
        datetime.date(yyyy, mm, dd)
        return True
    except Exception:
        return False


def extract_tag_value(payload: str, tag: str) -> Optional[str]:
    m = re.search(re.escape(tag) + r"([^\x1E\r\n]*)", payload)
    if m:
        return m.group(1).strip()
    return None


def check_dates_in_payload(payload: str) -> List[str]:
    errors = []
    for tag in DATE_TAGS:
        val = extract_tag_value(payload, tag)
        if val is None:
            errors.append(f"{tag} absent.")
            continue
        if not check_date_format(val):
            errors.append(f"{tag} a un format invalide (attendu MMDDYYYY) : '{val}'")
    return errors


def check_ascii(payload: str) -> Tuple[bool, str]:
    try:
        payload.encode("ascii")
        return True, "Encodage ASCII OK."
    except UnicodeEncodeError as e:
        return False, f"Caractères non-ASCII détectés (accents ou symboles). Détail: {str(e)}"


def minimal_length_check(payload: str) -> Tuple[bool, str]:
    if len(payload) < 40:
        return False, "Payload très court — probablement incomplet."
    return True, "Longueur minimale OK."


def svg_basic_checks(svg_text: str) -> List[str]:
    issues = []
    if "<svg" not in svg_text.lower():
        issues.append("Le texte collé ne semble pas être un SVG.")
        return issues
    if not re.search(r"viewBox|viewbox|width=\"\d+\"|height=\"\d+\"", svg_text, flags=re.IGNORECASE):
        issues.append("SVG sans width/height ni viewBox explicite — vérifier dimensions.")
    if not re.search(r"<rect\b", svg_text, flags=re.IGNORECASE):
        issues.append("SVG sans <rect> détecté — le rasteriseur simple peut échouer si le SVG est complexe.")
    issues.append("Recommandation : utiliser un scale entier (2–4) et laisser une marge blanche (quiet zone) autour du PDF417.")
    return issues


def validate_aamva_payload(payload: str) -> Dict[str, List[str]]:
    errors = []
    warnings = []
    infos = []

    if not payload or not payload.strip():
        errors.append("Payload vide.")
        return {"errors": errors, "warnings": warnings, "infos": infos}

    ok, msg = has_valid_header(payload)
    if not ok:
        errors.append(msg)
    else:
        infos.append(msg)

    ok_gs, msg_gs = uses_group_separator(payload)
    if not ok_gs:
        errors.append(msg_gs)
    else:
        infos.append(msg_gs)

    ok_end, msg_end = ends_with_cr(payload)
    if not ok_end:
        warnings.append(msg_end)
    else:
        infos.append(msg_end)

    ok_len, msg_len = minimal_length_check(payload)
    if not ok_len:
        warnings.append(msg_len)
    else:
        infos.append(msg_len)

    ok_tags, missing = check_required_tags(payload)
    if not ok_tags:
        errors.append("Champs obligatoires manquants: " + ", ".join(missing))
    else:
        infos.append("Tous les champs obligatoires sont présents (au moins en apparence).")

    date_errors = check_dates_in_payload(payload)
    if date_errors:
        errors.extend(date_errors)
    else:
        infos.append("Formats de date OK (MMDDYYYY).")

    ok_ascii, ascii_msg = check_ascii(payload)
    if not ok_ascii:
        warnings.append(ascii_msg)
    else:
        infos.append(ascii_msg)

    tags = find_tags(payload)
    infos.append("Tags détectés (extrait) : " + ", ".join(tags[:20]) + ("..." if len(tags) > 20 else ""))

    if "<svg" in payload.lower():
        svg_issues = svg_basic_checks(payload)
        for s in svg_issues:
            warnings.append("SVG: " + s)

    if "\\u001e" in payload or "\\x1E" in payload:
        errors.append("Séparateur trouvé sous forme d'échappement (\\u001e ou \\x1E). Remplacer par le caractère 0x1E réel.")
    return {"errors": errors, "warnings": warnings, "infos": infos}


# -------------------------
# Générateur d'exemple AAMVA (valeurs fictives)
def build_aamva_tags(fields: Dict[str, str]) -> str:
    header = "@\r\nANSI 636014080102DL"
    parts = [header]
    order = ["DAQ", "DCS", "DAC", "DAD", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF", "DAU", "DAY", "DAZ"]
    for tag in order:
        val = fields.get(tag)
        if val is not None:
            parts.append(f"{tag}{val}")
    payload = GS.join(parts) + "\r"
    return payload


def example_payload() -> str:
    fields = {
        "DAQ": "H40759",
        "DCS": "HARMS",
        "DAC": "ROSA",
        "DAD": "MARIE",
        "DBB": "01011990",
        "DBA": "01012031",
        "DBD": "04102026",
        "DAG": "2570 24TH STREET",
        "DAI": "OAKLAND",
        "DAJ": "CA",
        "DAK": "94601",
        "DCF": "1234567890",
        "DAU": "510",
        "DAY": "BRN",
        "DAZ": "BRN",
    }
    return build_aamva_tags(fields)


# -------------------------
# Streamlit UI
st.title("Validateur AAMVA / PDF417 — Vérifier payload et éviter les pièges")

st.markdown(
    "Colle ici le **payload AAMVA brut** (texte encodé pour le PDF417) ou clique sur **Générer un exemple** pour tester. "
    "Le validateur vérifie header, séparateurs (0x1E), formats de date, encodage et signale les erreurs courantes."
)

# Initialise la clé session si elle n'existe pas
if "payload_input" not in st.session_state:
    st.session_state["payload_input"] = ""

col1, col2 = st.columns([3, 1])
with col1:
    # Lier le text_area à st.session_state["payload_input"]
    st.text_area(
        "Payload AAMVA (brut)",
        height=220,
        value=st.session_state["payload_input"],
        placeholder="Colle le payload AAMVA ici (commence par @ et ANSI ... DL).",
        key="payload_input"
    )
with col2:
    if st.button("Générer un exemple"):
        # Mettre à jour la valeur liée au widget via session_state
        st.session_state["payload_input"] = example_payload()

if not st.session_state["payload_input"]:
    st.info("Aucun payload collé. Clique sur 'Générer un exemple' pour insérer un payload de test.")
else:
    if st.button("Valider le payload"):
        payload_input = st.session_state["payload_input"]
        results = validate_aamva_payload(payload_input)
        errors = results["errors"]
        warnings = results["warnings"]
        infos = results["infos"]

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

        st.markdown("### Suggestions automatiques pour corriger les pièges fréquents")
        suggs = []
        ok_head, _ = has_valid_header(payload_input)
        if not ok_head:
            suggs.append("Vérifier l'en-tête : il doit contenir 'ANSI' et 'DL' (ex: '@\\r\\nANSI 636014080102DL').")
        ok_gs, _ = uses_group_separator(payload_input)
        if not ok_gs:
            suggs.append("Remplacer les séquences '\\\\u001e' ou '\\\\x1E' par le caractère réel 0x1E (Group Separator).")
        date_errs = check_dates_in_payload(payload_input)
        if date_errs:
            suggs.append("Corriger les dates au format MMDDYYYY (ex: 01011990).")
        ok_ascii, ascii_msg = check_ascii(payload_input)
        if not ok_ascii:
            suggs.append("Supprimer ou translittérer les caractères accentués / non-ASCII (ex: é -> e).")
        if "<svg" in payload_input.lower():
            suggs.append("Si tu fournis un SVG, assure-toi qu'il contient <rect> (PDF417 simple) ou utilise la conversion côté navigateur si le SVG est complexe.")
        suggs.append("Pour l'impression/scan, viser ≥300 DPI et utiliser un scale entier (2–4) lors de la rasterisation; laisser une quiet zone blanche autour du code.")
        for s in suggs:
            st.write("- " + s)

        st.markdown("### Exemple de payload (fictif) — prêt à copier")
        st.code(example_payload(), language="text")

st.markdown("---")
st.markdown(
    "**Notes** :\n\n"
    "- Ce validateur effectue des contrôles syntaxiques et des recommandations pratiques; il ne remplace pas un test réel sur les SDKs de Verisoul/Persona/Samsub.\n"
    "- Pour des tests finaux, génère le PDF417 (SVG/PNG) et testez avec les outils/sandboxes des fournisseurs de vérification.\n"
    "- Si tu veux, j'intègre une vérification automatique du PDF417 (génération SVG via pdf417gen) et une rasterisation avancée (prise en charge complète des <path>) — dis‑moi si tu veux que j'ajoute cela dans ce fichier."
)
