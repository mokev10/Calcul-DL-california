# aamva_utils.py
# Utilitaires de validation et d'auto-correction pour payload AAMVA / PDF417
# Fournit :
#   - validate_aamva_payload(payload: str) -> dict
#   - auto_correct_payload(payload: str) -> (corrected_payload: str, applied: list)
#   - example_payload() -> str
#   - build_aamva_payload_continuous(fields: Dict[str, str]) -> str
#   - GS constant (séparateur de groupe 0x1E)

import re
import datetime
from typing import List, Tuple, Dict

GS = "\x1E"  # group separator 0x1E

RE_TAG = re.compile(r"\b([A-Z]{3})([^\x1E\r\n]*)")
RE_DATE = re.compile(r"^(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{4}$")  # MMDDYYYY
RE_HEADER = re.compile(r"^@[\r\n]*ANSI\s+636014080102DL", re.IGNORECASE)
RE_RECORD_TERMINATOR = re.compile(r"\r$")
RE_GS_PRESENT = re.compile(r"\x1E")
RE_ASCII = re.compile(r"^[\x00-\x7F]*$")
RE_TAG_REQUIRED = ["DAQ", "DCS", "DAC", "DBB", "DBA", "DBD"]

# Header continu demandé
AAMVA_HEADER_CONTINUOUS = "@ANSI 636014080102DL00410288ZA03290015DL"
REQUIRED_ORDER_CONTINUOUS = [
    "DAQ", "DCS", "DAC", "DBB", "DBA", "DBD",
    "DAG", "DAI", "DAJ", "DAK"
]
OPTIONAL_ORDER_CONTINUOUS = ["DCF", "DAU", "DAY", "DAZ"]


def _to_ascii_upper_clean(value: str, allow_spaces: bool = True) -> str:
    if value is None:
        value = ""
    v = str(value).strip().upper()
    v = v.replace("\r", "").replace("\n", "").replace("\t", " ")
    v = re.sub(r"\s+", " ", v)

    try:
        v.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError(f"Caractères non ASCII détectés dans: {value!r}")

    pattern = r"[^A-Z0-9 .\-/' ]" if allow_spaces else r"[^A-Z0-9.\-/' ]"
    v = re.sub(pattern, "", v).strip()
    return v


def _validate_date_mmddyyyy(tag: str, value: str) -> None:
    if not re.fullmatch(r"\d{8}", value):
        raise ValueError(f"{tag} invalide: attendu MMDDYYYY, reçu {value!r}")
    mm = int(value[0:2])
    dd = int(value[2:4])
    yyyy = int(value[4:8])
    try:
        datetime.date(yyyy, mm, dd)
    except ValueError as exc:
        raise ValueError(f"{tag} date impossible: {value!r}") from exc


def _validate_state(tag: str, value: str) -> None:
    if not re.fullmatch(r"[A-Z]{2}", value):
        raise ValueError(f"{tag} invalide: attendu code état 2 lettres, reçu {value!r}")


def _validate_zip(tag: str, value: str) -> None:
    if not re.fullmatch(r"\d{5}(\d{4})?", value):
        raise ValueError(f"{tag} invalide: attendu ZIP 5 ou 9 chiffres, reçu {value!r}")


def _validate_dl_number(tag: str, value: str) -> None:
    if not re.fullmatch(r"[A-Z0-9]{5,20}", value):
        raise ValueError(f"{tag} invalide: attendu alphanum 5-20, reçu {value!r}")


def _validate_name(tag: str, value: str) -> None:
    if not value:
        raise ValueError(f"{tag} vide")
    if len(value) > 40:
        raise ValueError(f"{tag} trop long (>40)")


def _validate_not_empty(tag: str, value: str) -> None:
    if not value:
        raise ValueError(f"{tag} vide")


def build_aamva_payload_continuous(fields: Dict[str, str]) -> str:
    """
    Construit un payload AAMVA en flux continu (single string):
    - aucun \n
    - aucun \r
    - aucun GS (\x1E)
    - header continu + concat TAG+VALUE
    """
    cleaned: Dict[str, str] = {}
    for tag, value in fields.items():
        if tag in {"DBB", "DBA", "DBD", "DAK"}:
            cleaned[tag] = re.sub(r"\D", "", str(value or ""))
        elif tag in {"DAQ", "DAJ", "DAU", "DAY", "DAZ"}:
            cleaned[tag] = _to_ascii_upper_clean(str(value or ""), allow_spaces=False).replace(" ", "")
        else:
            cleaned[tag] = _to_ascii_upper_clean(str(value or ""), allow_spaces=True)

    missing = [t for t in REQUIRED_ORDER_CONTINUOUS if not cleaned.get(t)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants: {', '.join(missing)}")

    _validate_dl_number("DAQ", cleaned["DAQ"])
    _validate_name("DCS", cleaned["DCS"])
    _validate_name("DAC", cleaned["DAC"])
    _validate_date_mmddyyyy("DBB", cleaned["DBB"])
    _validate_date_mmddyyyy("DBA", cleaned["DBA"])
    _validate_date_mmddyyyy("DBD", cleaned["DBD"])
    _validate_not_empty("DAG", cleaned["DAG"])
    _validate_not_empty("DAI", cleaned["DAI"])
    _validate_state("DAJ", cleaned["DAJ"])
    _validate_zip("DAK", cleaned["DAK"])

    parts: List[str] = [AAMVA_HEADER_CONTINUOUS]
    for tag in REQUIRED_ORDER_CONTINUOUS:
        parts.append(f"{tag}{cleaned[tag]}")
    for tag in OPTIONAL_ORDER_CONTINUOUS:
        val = cleaned.get(tag, "")
        if val:
            parts.append(f"{tag}{val}")

    payload = "".join(parts)

    if "\n" in payload or "\r" in payload:
        raise ValueError("Payload invalide: contient retour ligne")
    if "\x1E" in payload:
        raise ValueError("Payload invalide: contient GS invisible")
    if not payload.startswith("@ANSI ") or "DL" not in payload:
        raise ValueError("Header ANSI/DL invalide")

    try:
        payload.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("Payload invalide: non ASCII") from exc

    return payload


def example_payload() -> str:
    # Conservé pour compatibilité UI existante (format GS + CR)
    parts = [
        "@",
        "ANSI 636014080102DL",
        "DAQH40759",
        "DCSHARMS",
        "DACROSA",
        "DBB01011990",
        "DBA01012031",
        "DBD04102026",
        "DAG2570 24TH STREET",
        "DAIOAKLAND",
        "DAJCA",
        "DAK94601",
        "DCF1234567890",
        "DAU510",
        "DAYBRN",
        "DAZBRN",
    ]
    return GS.join(parts) + "\r"


def parse_tags(payload: str) -> Dict[str, str]:
    tags = {}
    for m in RE_TAG.finditer(payload):
        tag = m.group(1)
        val = m.group(2).strip()
        tags[tag] = val
    return tags


def validate_aamva_payload(payload: str) -> Dict[str, List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []

    if not isinstance(payload, str) or not payload.strip():
        errors.append("Payload vide ou non fourni.")
        return {"errors": errors, "warnings": warnings, "infos": infos}

    if not RE_HEADER.search(payload):
        errors.append("Header ANSI manquant ou mal formé (attendu 'ANSI 636014080102DL').")
    else:
        infos.append("Header OK.")

    if not RE_GS_PRESENT.search(payload):
        warnings.append("Séparateur de groupe 0x1E absent. Les champs peuvent être collés.")
    else:
        infos.append("Séparateur de groupe (0x1E) présent.")

    if not RE_RECORD_TERMINATOR.search(payload):
        warnings.append("Fin de record manquante (ajouter un CR '\\r' à la fin).")
    else:
        infos.append("Terminaison CR présente.")

    if not RE_ASCII.match(payload):
        errors.append("Encodage non-ASCII détecté. Utiliser ASCII/UTF-8 sans caractères non-ASCII.")
    else:
        infos.append("Encodage ASCII OK.")

    tags = parse_tags(payload)
    if not tags:
        warnings.append("Aucun tag détecté (parsing échoué).")
    else:
        infos.append(f"Tags détectés (extrait) : {', '.join(list(tags.keys())[:10])}.")

    missing = [t for t in RE_TAG_REQUIRED if t not in tags]
    if missing:
        errors.append("Champs obligatoires manquants: " + ", ".join(missing))
    else:
        infos.append("Tous les champs obligatoires semblent présents.")

    for dt_tag in ("DBB", "DBA", "DBD"):
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
    applied: List[str] = []
    if not isinstance(payload, str):
        return payload, applied

    p = payload

    if not RE_HEADER.search(p):
        if "ANSI 636014080102DL" in p.upper():
            p = re.sub(r"(?i)ANSI\s+636014080102DL", "ANSI 636014080102DL", p)
            if not p.strip().startswith("@"):
                p = "@\r\n" + p
            applied.append("Normalisé header ANSI (ajouté préfixe si nécessaire).")

    if "\u241E" in p or "␞" in p:
        p = p.replace("\u241E", GS).replace("␞", GS)
        applied.append("Remplacé symboles visibles GS par 0x1E.")

    p = re.sub(r"\\x1E", GS, p)

    if "|" in p and GS not in p:
        p2 = re.sub(r"([A-Z]{3}[^\|]{0,50})\|(?=[A-Z]{3})", r"\1" + GS, p)
        if p2 != p:
            p = p2
            applied.append("Remplacé '|' entre tags par 0x1E.")

    if not RE_RECORD_TERMINATOR.search(p):
        p = p + "\r"
        applied.append("Ajouté CR final.")

    def _collapse_vals(m):
        tag = m.group(1)
        val = m.group(2)
        newval = re.sub(r"\s{2,}", " ", val).strip()
        return f"{tag}{newval}"

    p_new = RE_TAG.sub(_collapse_vals, p)
    if p_new != p:
        p = p_new
        applied.append("Nettoyé espaces multiples dans valeurs de tags.")

    if GS not in p:
        p_try = re.sub(r"(?<!\x1E)(?<!\r)(?<!\n)(?P<tag>[A-Z]{3})(?=[A-Z0-9])", GS + r"\g<tag>", p)
        if len(RE_TAG.findall(p_try)) > len(RE_TAG.findall(p)):
            p = p_try
            applied.append("Inséré séparateurs GS entre tags collés (heuristique).")

    p = re.sub(r"(\r)+$", "\r", p)
    return p, applied
