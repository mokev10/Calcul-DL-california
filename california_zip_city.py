"""Référentiel ZIP -> ville pour la Californie.

Ce module charge automatiquement les couples ZIP/Ville depuis ``ZIP_DB.txt``
(au root du dépôt) au lieu de stocker une grosse table statique.

Plage ciblée: 90001 à 96162.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

MIN_CA_ZIP = 90001
MAX_CA_ZIP = 96162

_HEADER_RE = re.compile(r"ZipCode|City State|State Salesmen|Page", re.IGNORECASE)
_ZIP_RE = re.compile(r"\d{5}")


def _is_valid_city(value: str) -> bool:
    city = value.strip()
    if not city:
        return False
    if _HEADER_RE.search(city):
        return False
    # Ville = lettres/espaces/ponctuation simple.
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .\-']*", city))


def _in_target_range(zip_code: str) -> bool:
    z = int(zip_code)
    return MIN_CA_ZIP <= z <= MAX_CA_ZIP


def _parse_zip_db_text(text: str) -> Dict[str, str]:
    """Extrait un mapping ZIP -> ville depuis le contenu de ZIP_DB.txt."""
    lines = [line.strip() for line in text.splitlines()]
    mapping: Dict[str, str] = {}

    for i, line in enumerate(lines):
        if not line:
            continue

        # Format 1:
        # 90001
        # Los Angeles
        # CA Rob Felter
        if _ZIP_RE.fullmatch(line) and i + 2 < len(lines):
            city = lines[i + 1].strip()
            state_and_sales = lines[i + 2].strip()
            if (
                _is_valid_city(city)
                and state_and_sales.startswith("CA")
                and _in_target_range(line)
            ):
                mapping[line] = city.title()

        # Format 2:
        # Los Angeles
        # CA
        # 90001
        if i + 2 < len(lines):
            city = line
            state = lines[i + 1].strip()
            zip_code = lines[i + 2].strip()
            if (
                state == "CA"
                and _ZIP_RE.fullmatch(zip_code)
                and _is_valid_city(city)
                and _in_target_range(zip_code)
            ):
                mapping[zip_code] = city.title()

    # Format 3 (lignes compactes), ex:
    # 96161 Truckee CA Rob Doolittle
    for m in re.finditer(r"\b(\d{5})\s+([A-Za-z][A-Za-z .\-']+?)\s+CA\b", text):
        zip_code, city = m.group(1), m.group(2).strip()
        if _is_valid_city(city) and _in_target_range(zip_code):
            mapping.setdefault(zip_code, city.title())

    # Format 4 (inversé), ex:
    # Zamora CA 95698 Rob Doolittle
    for m in re.finditer(r"\b([A-Za-z][A-Za-z .\-']+?)\s+CA\s+(\d{5})\b", text):
        city, zip_code = m.group(1).strip(), m.group(2)
        if _is_valid_city(city) and _in_target_range(zip_code):
            mapping.setdefault(zip_code, city.title())

    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))


def _load_from_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    return _parse_zip_db_text(path.read_text(encoding="utf-8", errors="ignore"))


# Chargement par défaut depuis le root du projet.
CALIFORNIA_ZIP_TO_CITY: Dict[str, str] = _load_from_file(Path(__file__).with_name("ZIP_DB.txt"))


def get_city_from_zip(zip_code: str) -> str:
    """Retourne la ville associée au ZIP californien (ou chaîne vide)."""
    return CALIFORNIA_ZIP_TO_CITY.get(str(zip_code).strip(), "")
