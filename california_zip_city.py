"""
california_zip_city.py
----------------------

Référentiel ZIP -> ville pour la Californie.

Note:
- Ce module est prêt à l'emploi tel quel.
- Il charge automatiquement un fichier local `ZIP_DB.txt` si présent (couverture large).
- Sans ce fichier, il utilise un fallback interne (couverture partielle mais fonctionnelle).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

MIN_CA_ZIP = 90001
MAX_CA_ZIP = 96162

_ZIP_RE = re.compile(r"\b\d{5}\b")
_HEADER_RE = re.compile(r"(ZipCode|City State|State Salesmen|Page)", re.IGNORECASE)
_CITY_RE = re.compile(r"[A-Za-z][A-Za-z .\-']*")


def _is_valid_ca_zip(zip_code: str) -> bool:
    if not zip_code.isdigit() or len(zip_code) != 5:
        return False
    z = int(zip_code)
    return MIN_CA_ZIP <= z <= MAX_CA_ZIP


def _is_valid_city(city: str) -> bool:
    city = city.strip()
    if not city:
        return False
    if _HEADER_RE.search(city):
        return False
    return bool(_CITY_RE.fullmatch(city))


def _normalize_city(city: str) -> str:
    return city.strip().title()


def _parse_zip_db_text(text: str) -> Dict[str, str]:
    """
    Parse plusieurs formats d'exports texte:
    - 90001 / Los Angeles / CA ...
    - Los Angeles / CA / 90001
    - 96161 Truckee CA ...
    - Zamora CA 95698 ...
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    mapping: Dict[str, str] = {}

    # Format 1
    for i, line in enumerate(lines):
        if _ZIP_RE.fullmatch(line) and i + 2 < len(lines):
            zip_code = line
            city = lines[i + 1]
            state_line = lines[i + 2]
            if (
                _is_valid_ca_zip(zip_code)
                and _is_valid_city(city)
                and state_line.upper().startswith("CA")
            ):
                mapping[zip_code] = _normalize_city(city)

    # Format 2
    for i, line in enumerate(lines):
        if i + 2 >= len(lines):
            continue
        city = line
        state = lines[i + 1]
        zip_code = lines[i + 2]
        if (
            state.upper() == "CA"
            and _ZIP_RE.fullmatch(zip_code)
            and _is_valid_ca_zip(zip_code)
            and _is_valid_city(city)
        ):
            mapping[zip_code] = _normalize_city(city)

    # Format 3 compact
    for m in re.finditer(r"\b(\d{5})\s+([A-Za-z][A-Za-z .\-']+?)\s+CA\b", text):
        zip_code, city = m.group(1), m.group(2).strip()
        if _is_valid_ca_zip(zip_code) and _is_valid_city(city):
            mapping.setdefault(zip_code, _normalize_city(city))

    # Format 4 compact inversé
    for m in re.finditer(r"\b([A-Za-z][A-Za-z .\-']+?)\s+CA\s+(\d{5})\b", text):
        city, zip_code = m.group(1).strip(), m.group(2)
        if _is_valid_ca_zip(zip_code) and _is_valid_city(city):
            mapping.setdefault(zip_code, _normalize_city(city))

    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))


def _load_from_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    return _parse_zip_db_text(text)


# Fallback interne (non exhaustif)
_FALLBACK_ZIP_TO_CITY: Dict[str, str] = {
    "90001": "Los Angeles",
    "90210": "Beverly Hills",
    "90401": "Santa Monica",
    "90802": "Long Beach",
    "91910": "Chula Vista",
    "92101": "San Diego",
    "92612": "Irvine",
    "92701": "Santa Ana",
    "92802": "Anaheim",
    "94015": "Daly City",
    "94102": "San Francisco",
    "94501": "Alameda",
    "94601": "Oakland",
    "94704": "Berkeley",
    "94925": "Corte Madera",
    "95014": "Cupertino",
    "95112": "San Jose",
    "95814": "Sacramento",
    "95818": "Sacramento",
    "96150": "South Lake Tahoe",
}


def _build_mapping() -> Dict[str, str]:
    mapping = dict(_FALLBACK_ZIP_TO_CITY)
    zip_db_path = Path(__file__).with_name("ZIP_DB.txt")
    file_mapping = _load_from_file(zip_db_path)
    if file_mapping:
        mapping.update(file_mapping)
    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))


CALIFORNIA_ZIP_TO_CITY: Dict[str, str] = _build_mapping()


def get_city_from_zip(zip_code: str) -> str:
    return CALIFORNIA_ZIP_TO_CITY.get(str(zip_code).strip(), "")


def find_zips_by_city(city_name: str) -> List[str]:
    target = city_name.strip().lower()
    if not target:
        return []
    return [z for z, c in CALIFORNIA_ZIP_TO_CITY.items() if c.lower() == target]


def is_california_zip(zip_code: str) -> bool:
    return _is_valid_ca_zip(str(zip_code).strip())


def get_stats() -> Tuple[int, int, int]:
    if not CALIFORNIA_ZIP_TO_CITY:
        return (0, MIN_CA_ZIP, MAX_CA_ZIP)
    keys = [int(k) for k in CALIFORNIA_ZIP_TO_CITY.keys()]
    return (len(keys), min(keys), max(keys))


if __name__ == "__main__":
    count, zmin, zmax = get_stats()
    print(f"Loaded {count} CA ZIP entries (range in mapping: {zmin}-{zmax}).")
    for z in ["94015", "94102", "95818", "90210", "92101"]:
        print(f"{z} -> {get_city_from_zip(z) or '(unknown)'}")
