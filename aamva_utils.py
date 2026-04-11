# aamva_utils.py
# Utilitaires de validation et d'auto-correction pour payload AAMVA / PDF417
# Fournit : validate_aamva_payload(payload: str) -> dict
#           auto_correct_payload(payload: str) -> (corrected_payload:str, applied:list)
#           example_payload() -> str
#           GS constant (séparateur de groupe 0x1E)

import re
from typing import List, Tuple, Dict

GS = "\x1E"  # group separator 0x1E

RE_TAG = re.compile(r"\b([A-Z]{3})([^\x1E\r\n]*)")

RE_DATE = re.compile(r"^(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{4}$")  # MMDDYYYY

RE_HEADER = re.compile(r"^@[\r\n]*ANSI\s+636014080102DL", re.IGNORECASE)

RE_RECORD_TERMINATOR = re.compile(r"\r$")

RE_GS_PRESENT = re.compile(r"\x1E")

RE_ASCII = re.compile(r"^[\x00-\x7F]*$")

RE_TAG_REQUIRED = ["DAQ","DCS","DAC","DBB","DBA","DBD"]

def example_payload() -> str:
    parts = [
        "@",
        "ANSI 636014080102DL",
        f"DAQH40759",
        f"DCSHARMS",
        f"DACROSA",
        f"DBB01011990",
        f"DBA01012031",
        f"DBD04102026",
        f"DAG2570 24TH STREET",
        f"DAIOAKLAND",
        f"DAJCA",
        f"DAK94601",
        f"DCF1234567890",
        f"DAU510",
        f"DAYBRN",
        f"DAZBRN"
    ]
    return GS.join(parts) + "\r"

def parse_tags(payload: str) -> Dict[str,str]:
    tags = {}
    for m in RE_TAG.finditer(payload):
        tag = m.group(1)
        val = m.group(2).strip()
        tags[tag] = val
    return tags

def validate_aamva_payload(payload: str) -> Dict[str, List[str]]:
    """
    Retourne dict {errors:[], warnings:[], infos:[]}
    Non-raise : utile pour UI.
    """
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []

    if not isinstance(payload, str) or not payload.strip():
        errors.append("Payload vide ou non fourni.")
        return {"errors": errors, "warnings": warnings, "infos": infos}

    # Header
    if not RE_HEADER.search(payload):
        errors.append("Header ANSI manquant ou mal formé (attendu 'ANSI 636014080102DL').")
    else:
        infos.append("Header OK.")

    # GS presence
    if not RE_GS_PRESENT.search(payload):
        warnings.append("Séparateur de groupe 0x1E absent. Les champs peuvent être collés.")
    else:
        infos.append("Séparateur de groupe (0x1E) présent.")

    # Record terminator CR
    if not RE_RECORD_TERMINATOR.search(payload):
        warnings.append("Fin de record manquante (ajouter un CR '\\r' à la fin).")
    else:
        infos.append("Terminaison CR présente.")

    # ASCII check
    if not RE_ASCII.match(payload):
        errors.append("Encodage non-ASCII détecté. Utiliser ASCII/UTF-8 sans caractères non-ASCII.")
    else:
        infos.append("Encodage ASCII OK.")

    # Tags parse
    tags = parse_tags(payload)
    if not tags:
        warnings.append("Aucun tag détecté (parsing échoué).")
    else:
        infos.append(f"Tags détectés (extrait) : {', '.join(list(tags.keys())[:10])}.")

    # Required tags
    missing = [t for t in RE_TAG_REQUIRED if t not in tags]
    if missing:
        errors.append("Champs obligatoires manquants: " + ", ".join(missing))
    else:
        infos.append("Tous les champs obligatoires semblent présents.")

    # Date formats check (DBB, DBA, DBD)
    for dt_tag in ("DBB","DBA","DBD"):
        v = tags.get(dt_tag)
        if v:
            if not RE_DATE.match(v):
                errors.append(f"Format date invalide pour {dt_tag} (attendu MMDDYYYY) : '{v}'")
            else:
                infos.append(f"{dt_tag} format OK.")
        else:
            warnings.append(f"{dt_tag} absent (vérifier si requis).")

    return {"errors": errors, "warnings": warnings, "infos": infos}

def auto_correct_payload(payload: str) -> Tuple[str, List[str]]:
    """
    Tente des corrections simples et sûres :
    - Remplace les séparateurs visibles (literal '' ou séquences) par GS
    - Ajoute CR final si manquant
    - Nettoie doubles espaces dans les valeurs
    - Normalise header (ANSI ...)
    Retourne (corrected_payload, list_of_applied_corrections)
    """
    applied: List[str] = []
    if not isinstance(payload, str):
        return payload, applied

    p = payload

    # Normalize header: ensure '@' + CRLF + ANSI...
    if not RE_HEADER.search(p):
        # try to find 'ANSI' and prepend '@\r\n' if missing
        if "ANSI 636014080102DL" in p.upper():
            p = re.sub(r"(?i)ANSI\s+636014080102DL", "ANSI 636014080102DL", p)
            if not p.strip().startswith("@"):
                p = "@\r\n" + p
            applied.append("Normalisé header ANSI (ajouté préfixe si nécessaire).")
        else:
            # do not invent header if totally missing
            pass

    # Replace visible GS characters (some editors show as '␞' or literal 0x1E)
    # Replace sequences of literal group separators or the unicode U+241E symbol
    if "\u241E" in p or "␞" in p:
        p = p.replace("\u241E", GS).replace("␞", GS)
        applied.append("Remplacé symboles visibles GS par 0x1E.")

    # Replace occurrences of the two-character sequence '\x1E' written as backslash + x + 1E
    p = re.sub(r"\\x1E", GS, p)
    # Replace common mistaken separators (vertical bar, pipe) only as non-destructive suggestion:
    if "|" in p and GS not in p:
        # only replace pipes between tags like 'DAQH40759|DCSHARMS' -> use GS
        p2 = re.sub(r"([A-Z]{3}[^\|]{0,50})\|(?=[A-Z]{3})", r"\1" + GS, p)
        if p2 != p:
            p = p2
            applied.append("Remplacé '|' entre tags par 0x1E.")

    # Ensure CR at end
    if not RE_RECORD_TERMINATOR.search(p):
        p = p + "\r"
        applied.append("Ajouté CR final.")

    # Collapse multiple spaces inside tag values (safe)
    def _collapse_vals(m):
        tag = m.group(1)
        val = m.group(2)
        newval = re.sub(r"\s{2,}", " ", val).strip()
        return f"{tag}{newval}"
    p_new = RE_TAG.sub(_collapse_vals, p)
    if p_new != p:
        p = p_new
        applied.append("Nettoyé espaces multiples dans valeurs de tags.")

    # If no GS present but tags appear concatenated, try to insert GS between tags
    if GS not in p:
        # naive insertion: insert GS before each 3-letter tag that is followed by uppercase letters/digits
        p_try = re.sub(r"(?<!\x1E)(?<!\r)(?<!\n)(?P<tag>[A-Z]{3})(?=[A-Z0-9])", GS + r"\g<tag>", p)
        # only accept if it increases recognisable tags
        if len(RE_TAG.findall(p_try)) > len(RE_TAG.findall(p)):
            p = p_try
            applied.append("Inséré séparateurs GS entre tags collés (heuristique).")

    # Final safety: ensure payload ends with CR only once
    p = re.sub(r"(\r)+$", "\r", p)

    return p, applied
