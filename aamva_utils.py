# aamva_utils.py
# Utilitaires pour validation et correction automatique de payload AAMVA (PDF417)
# Usage: from aamva_utils import validate_aamva_payload, auto_correct_payload, example_payload

import re
import datetime
from typing import List, Tuple, Dict, Optional, Any

GS = "\x1E"  # Group Separator (0x1E)

REQUIRED_TAGS = [
    "DAQ", "DCS", "DAC", "DBB", "DBA", "DBD", "DAG", "DAI", "DAJ", "DAK", "DCF"
]
DATE_TAGS = ["DBB", "DBA", "DBD"]


# -------------------------
# Fonctions de validation
def has_valid_header(payload: str) -> Tuple[bool, str]:
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
        return False, "Séparateur trouvé sous forme d'échappement (\\u001e ou \\x1E)."
    return False, "Séparateur de groupe (0x1E) absent."


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
        mm = int(value[0:2]); dd = int(value[2:4]); yyyy = int(value[4:8])
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
    errors = []; warnings = []; infos = []
    if not payload or not payload.strip():
        errors.append("Payload vide."); return {"errors": errors, "warnings": warnings, "infos": infos}

    ok, msg = has_valid_header(payload)
    (infos if ok else errors).append(msg)

    ok_gs, msg_gs = uses_group_separator(payload)
    (infos if ok_gs else errors).append(msg_gs)

    ok_end, msg_end = ends_with_cr(payload)
    (infos if ok_end else warnings).append(msg_end)

    ok_len, msg_len = minimal_length_check(payload)
    (infos if ok_len else warnings).append(msg_len)

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
    (infos if ok_ascii else warnings).append(ascii_msg)

    tags = find_tags(payload)
    infos.append("Tags détectés (extrait) : " + ", ".join(tags[:20]) + ("..." if len(tags) > 20 else ""))

    if "<svg" in payload.lower():
        svg_issues = svg_basic_checks(payload)
        for s in svg_issues:
            warnings.append("SVG: " + s)

    if "\\u001e" in payload or "\\x1E" in payload:
        errors.append("Séparateur trouvé sous forme d'échappement (\\u001e ou \\x1E).")
    return {"errors": errors, "warnings": warnings, "infos": infos}


# -------------------------
# Auto-correction (sûre et réversible)
def replace_escaped_separators(payload: str) -> str:
    return payload.replace("\\u001e", GS).replace("\\x1E", GS)


def ensure_trailing_cr(payload: str) -> str:
    if not (payload.endswith("\r") or payload.endswith("\r\n") or payload.endswith("\n\r")):
        return payload + "\r"
    return payload


def normalize_whitespace_around_tags(payload: str) -> str:
    # Supprime espaces superflus entre tag et valeur (prudence)
    def repl(m):
        tag = m.group(1)
        val = m.group(2)
        return f"{tag}{val}"
    return re.sub(r"([A-Z]{3})\s+([^\x1E\r\n]+)", repl, payload)


def auto_correct_payload(payload: str) -> Tuple[str, List[str]]:
    corrections = []
    p = payload

    # 1) Remplacer séquences échappées
    if "\\u001e" in p or "\\x1E" in p:
        p = replace_escaped_separators(p)
        corrections.append("Remplacement des séquences échappées '\\u001e' / '\\x1E' par le caractère 0x1E.")

    # 2) Normaliser espaces après tags (prudence)
    if re.search(r"[A-Z]{3}\s+[A-Z0-9\-]{1,20}(\x1E|$)", p):
        p2 = normalize_whitespace_around_tags(p)
        if p2 != p:
            p = p2
            corrections.append("Suppression d'espaces superflus entre tags et valeurs (ex: 'DAQ H407' -> 'DAQH407').")

    # 3) Ajouter CR final si absent
    if not (p.endswith("\r") or p.endswith("\r\n") or p.endswith("\n\r")):
        p = ensure_trailing_cr(p)
        corrections.append("Ajout d'un CR final '\\r'.")

    return p, corrections


# -------------------------
# Exemple de payload (fictif)
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
        "DAQ": "H40759", "DCS": "HARMS", "DAC": "ROSA", "DAD": "MARIE",
        "DBB": "01011990", "DBA": "01012031", "DBD": "04102026",
        "DAG": "2570 24TH STREET", "DAI": "OAKLAND", "DAJ": "CA", "DAK": "94601",
        "DCF": "1234567890", "DAU": "510", "DAY": "BRN", "DAZ": "BRN",
    }
    return build_aamva_tags(fields)


# Module prêt à être importé
__all__ = [
    "GS", "validate_aamva_payload", "auto_correct_payload", "example_payload",
    "replace_escaped_separators", "ensure_trailing_cr", "normalize_whitespace_around_tags"
]
