"""
california_zip_city.py

Référentiel ZIP -> ville pour la Californie.

IMPORTANT (limite de fiabilité) :
- Inclure manuellement et de façon fiable *tous* les ZIP californiens dans le code source
  n'est pas réaliste sans source officielle à jour.
- Ce module est donc conçu pour charger automatiquement une table complète depuis
  un fichier local `ZIP_DB.txt` (si présent), puis fournir un fallback interne minimal.
- Il reste 100% utilisable tel quel : si `ZIP_DB.txt` existe, la couverture est large ;
  sinon, le fallback permet au module de fonctionner immédiatement.

Plage ZIP CA ciblée : 90001 -> 96162.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Plage usuelle des ZIP de Californie
MIN_CA_ZIP = 90001
MAX_CA_ZIP = 96162

# Expressions utiles
_ZIP_RE = re.compile(r"\b\d{5}\b")
_HEADER_RE = re.compile(r"(ZipCode|City State|State Salesmen|Page)", re.IGNORECASE)
_ALLOWED_CITY_RE = re.compile(r"[A-Za-z][A-Za-z .\-']*")


def _is_valid_ca_zip(zip_code: str) -> bool:
    if not zip_code.isdigit() or len(zip_code) != 5:
        return False
    z = int(zip_code)
    return MIN_CA_ZIP <= z <= MAX_CA_ZIP


def _normalize_city(city: str) -> str:
    city = city.strip()
    # title() gère correctement la majorité des villes; on garde simple/lisible
    return city.title()


def _is_plausible_city(value: str) -> bool:
    city = value.strip()
    if not city:
        return False
    if _HEADER_RE.search(city):
        return False
    return bool(_ALLOWED_CITY_RE.fullmatch(city))


def _parse_zip_db_text(text: str) -> Dict[str, str]:
    """
    Extrait un mapping ZIP->Ville depuis du texte brut.
    Tolère plusieurs formats rencontrés dans des exports "ZIP_DB".
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    mapping: Dict[str, str] = {}

    # Format A:
    #   90001
    #   Los Angeles
    #   CA ...
    for i, line in enumerate(lines):
        if i + 2 >= len(lines):
            continue
        if _ZIP_RE.fullmatch(line):
            zip_code = line
            city = lines[i + 1]
            state_line = lines[i + 2]
            if (
                _is_valid_ca_zip(zip_code)
                and _is_plausible_city(city)
                and state_line.upper().startswith("CA")
            ):
                mapping[zip_code] = _normalize_city(city)

    # Format B:
    #   Los Angeles
    #   CA
    #   90001
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
            and _is_plausible_city(city)
        ):
            mapping[zip_code] = _normalize_city(city)

    # Format C compact:
    #   96161 Truckee CA Rob Doolittle
    for m in re.finditer(r"\b(\d{5})\s+([A-Za-z][A-Za-z .\-']+?)\s+CA\b", text):
        zip_code, city = m.group(1), m.group(2).strip()
        if _is_valid_ca_zip(zip_code) and _is_plausible_city(city):
            mapping.setdefault(zip_code, _normalize_city(city))

    # Format D inversé compact:
    #   Zamora CA 95698 Rob Doolittle
    for m in re.finditer(r"\b([A-Za-z][A-Za-z .\-']+?)\s+CA\s+(\d{5})\b", text):
        city, zip_code = m.group(1).strip(), m.group(2)
        if _is_valid_ca_zip(zip_code) and _is_plausible_city(city):
            mapping.setdefault(zip_code, _normalize_city(city))

    # Tri par ZIP numérique
    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))


def _load_mapping_from_file(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8", errors="ignore")
    return _parse_zip_db_text(content)


# Fallback interne minimal (utilisable immédiatement même sans ZIP_DB.txt)
# NB: ce n'est pas une liste exhaustive des ZIP CA.
_FALLBACK_ZIP_TO_CITY: Dict[str, str] = {
    # Los Angeles area
    "90001": "Los Angeles",
    "90002": "Los Angeles",
    "90003": "Los Angeles",
    "90011": "Los Angeles",
    "90012": "Los Angeles",
    "90017": "Los Angeles",
    "90024": "Los Angeles",
    "90025": "Los Angeles",
    "90026": "Los Angeles",
    "90027": "Los Angeles",
    "90028": "Los Angeles",
    "90034": "Los Angeles",
    "90036": "Los Angeles",
    "90044": "Los Angeles",
    "90045": "Los Angeles",
    "90046": "Los Angeles",
    "90048": "Los Angeles",
    "90049": "Los Angeles",
    "90057": "Los Angeles",
    "90064": "Los Angeles",
    "90066": "Los Angeles",
    "90067": "Los Angeles",
    "90068": "Los Angeles",
    "90071": "Los Angeles",
    "90077": "Los Angeles",
    "90089": "Los Angeles",
    "90210": "Beverly Hills",
    "90211": "Beverly Hills",
    "90212": "Beverly Hills",
    "90230": "Culver City",
    "90232": "Culver City",
    "90245": "El Segundo",
    "90247": "Gardena",
    "90250": "Hawthorne",
    "90254": "Hermosa Beach",
    "90260": "Lawndale",
    "90266": "Manhattan Beach",
    "90272": "Pacific Palisades",
    "90277": "Redondo Beach",
    "90278": "Redondo Beach",
    "90301": "Inglewood",
    "90302": "Inglewood",
    "90304": "Inglewood",
    "90305": "Inglewood",
    "90401": "Santa Monica",
    "90402": "Santa Monica",
    "90403": "Santa Monica",
    "90404": "Santa Monica",
    "90405": "Santa Monica",
    "90501": "Torrance",
    "90503": "Torrance",
    "90504": "Torrance",
    "90505": "Torrance",
    "90710": "Harbor City",
    "90731": "San Pedro",
    "90732": "San Pedro",
    "90802": "Long Beach",
    "90803": "Long Beach",
    "90804": "Long Beach",
    "90805": "Long Beach",
    "90806": "Long Beach",
    "90807": "Long Beach",
    "90808": "Long Beach",

    # Orange County
    "92602": "Irvine",
    "92603": "Irvine",
    "92604": "Irvine",
    "92606": "Irvine",
    "92612": "Irvine",
    "92614": "Irvine",
    "92617": "Irvine",
    "92618": "Irvine",
    "92620": "Irvine",
    "92626": "Costa Mesa",
    "92627": "Costa Mesa",
    "92629": "Dana Point",
    "92647": "Huntington Beach",
    "92648": "Huntington Beach",
    "92649": "Huntington Beach",
    "92651": "Laguna Beach",
    "92653": "Laguna Hills",
    "92656": "Aliso Viejo",
    "92657": "Newport Coast",
    "92660": "Newport Beach",
    "92661": "Newport Beach",
    "92663": "Newport Beach",
    "92672": "San Clemente",
    "92673": "San Clemente",
    "92675": "San Juan Capistrano",
    "92677": "Laguna Niguel",
    "92679": "Trabuco Canyon",
    "92701": "Santa Ana",
    "92703": "Santa Ana",
    "92704": "Santa Ana",
    "92705": "Santa Ana",
    "92706": "Santa Ana",
    "92707": "Santa Ana",
    "92801": "Anaheim",
    "92802": "Anaheim",
    "92804": "Anaheim",
    "92805": "Anaheim",
    "92806": "Anaheim",
    "92807": "Anaheim",
    "92808": "Anaheim",

    # San Diego County
    "91910": "Chula Vista",
    "91911": "Chula Vista",
    "91913": "Chula Vista",
    "92007": "Cardiff By The Sea",
    "92008": "Carlsbad",
    "92009": "Carlsbad",
    "92010": "Carlsbad",
    "92011": "Carlsbad",
    "92014": "Del Mar",
    "92024": "Encinitas",
    "92025": "Escondido",
    "92026": "Escondido",
    "92027": "Escondido",
    "92028": "Fallbrook",
    "92037": "La Jolla",
    "92054": "Oceanside",
    "92056": "Oceanside",
    "92057": "Oceanside",
    "92064": "Poway",
    "92071": "Santee",
    "92075": "Solana Beach",
    "92078": "San Marcos",
    "92081": "Vista",
    "92083": "Vista",
    "92084": "Vista",
    "92101": "San Diego",
    "92103": "San Diego",
    "92104": "San Diego",
    "92105": "San Diego",
    "92106": "San Diego",
    "92107": "San Diego",
    "92108": "San Diego",
    "92109": "San Diego",
    "92110": "San Diego",
    "92111": "San Diego",
    "92113": "San Diego",
    "92114": "San Diego",
    "92115": "San Diego",
    "92116": "San Diego",
    "92117": "San Diego",
    "92119": "San Diego",
    "92120": "San Diego",
    "92121": "San Diego",
    "92122": "San Diego",
    "92123": "San Diego",
    "92124": "San Diego",
    "92126": "San Diego",
    "92127": "San Diego",
    "92128": "San Diego",
    "92129": "San Diego",
    "92130": "San Diego",
    "92131": "San Diego",
    "92139": "San Diego",

    # Bay Area
    "94010": "Burlingame",
    "94014": "Daly City",
    "94015": "Daly City",
    "94016": "Daly City",
    "94019": "Half Moon Bay",
    "94025": "Menlo Park",
    "94027": "Atherton",
    "94030": "Millbrae",
    "94040": "Mountain View",
    "94041": "Mountain View",
    "94043": "Mountain View",
    "94061": "Redwood City",
    "94062": "Redwood City",
    "94063": "Redwood City",
    "94065": "Redwood City",
    "94066": "San Bruno",
    "94070": "San Carlos",
    "94080": "South San Francisco",
    "94085": "Sunnyvale",
    "94086": "Sunnyvale",
    "94087": "Sunnyvale",
    "94089": "Sunnyvale",
    "94102": "San Francisco",
    "94103": "San Francisco",
    "94104": "San Francisco",
    "94105": "San Francisco",
    "94107": "San Francisco",
    "94108": "San Francisco",
    "94109": "San Francisco",
    "94110": "San Francisco",
    "94111": "San Francisco",
    "94112": "San Francisco",
    "94114": "San Francisco",
    "94115": "San Francisco",
    "94116": "San Francisco",
    "94117": "San Francisco",
    "94118": "San Francisco",
    "94121": "San Francisco",
    "94122": "San Francisco",
    "94123": "San Francisco",
    "94124": "San Francisco",
    "94127": "San Francisco",
    "94131": "San Francisco",
    "94132": "San Francisco",
    "94133": "San Francisco",
    "94134": "San Francisco",
    "94501": "Alameda",
    "94536": "Fremont",
    "94538": "Fremont",
    "94539": "Fremont",
    "94541": "Hayward",
    "94542": "Hayward",
    "94544": "Hayward",
    "94545": "Hayward",
    "94546": "Castro Valley",
    "94549": "Lafayette",
    "94550": "Livermore",
    "94551": "Livermore",
    "94552": "Castro Valley",
    "94555": "Fremont",
    "94568": "Dublin",
    "94577": "San Leandro",
    "94578": "San Leandro",
    "94579": "San Leandro",
    "94582": "San Ramon",
    "94583": "San Ramon",
    "94587": "Union City",
    "94601": "Oakland",
    "94602": "Oakland",
    "94603": "Oakland",
    "94605": "Oakland",
    "94606": "Oakland",
    "94607": "Oakland",
    "94608": "Oakland",
    "94609": "Oakland",
    "94610": "Oakland",
    "94611": "Oakland",
    "94612": "Oakland",
    "94618": "Oakland",
    "94619": "Oakland",
    "94621": "Oakland",
    "94702": "Berkeley",
    "94703": "Berkeley",
    "94704": "Berkeley",
    "94705": "Berkeley",
    "94706": "Albany",
    "94707": "Berkeley",
    "94708": "Berkeley",
    "94709": "Berkeley",
    "94710": "Berkeley",

    # Sacramento & Central Valley (échantillon utile)
    "94203": "Sacramento",
    "94204": "Sacramento",
    "94205": "Sacramento",
    "94206": "Sacramento",
    "94207": "Sacramento",
    "94208": "Sacramento",
    "94209": "Sacramento",
    "94211": "Sacramento",
    "94229": "Sacramento",
    "94230": "Sacramento",
    "94232": "Sacramento",
    "94234": "Sacramento",
    "94235": "Sacramento",
    "94236": "Sacramento",
    "94237": "Sacramento",
    "94239": "Sacramento",
    "94240": "Sacramento",
    "94242": "Sacramento",
    "94244": "Sacramento",
    "94245": "Sacramento",
    "94246": "Sacramento",
    "94247": "Sacramento",
    "94248": "Sacramento",
    "94249": "Sacramento",
    "94250": "Sacramento",
    "94252": "Sacramento",
    "94254": "Sacramento",
    "94256": "Sacramento",
    "94257": "Sacramento",
    "94258": "Sacramento",
    "94259": "Sacramento",
    "94261": "Sacramento",
    "94262": "Sacramento",
    "94263": "Sacramento",
    "94267": "Sacramento",
    "94268": "Sacramento",
    "94269": "Sacramento",
    "94271": "Sacramento",
    "94273": "Sacramento",
    "94274": "Sacramento",
    "94277": "Sacramento",
    "94278": "Sacramento",
    "94279": "Sacramento",
    "94280": "Sacramento",
    "94282": "Sacramento",
    "94283": "Sacramento",
    "94284": "Sacramento",
    "94285": "Sacramento",
    "94286": "Sacramento",
    "94287": "Sacramento",
    "94288": "Sacramento",
    "94289": "Sacramento",
    "94290": "Sacramento",
    "94291": "Sacramento",
    "94293": "Sacramento",
    "94294": "Sacramento",
    "94295": "Sacramento",
    "94296": "Sacramento",
    "94297": "Sacramento",
    "94298": "Sacramento",
    "94299": "Sacramento",
    "95811": "Sacramento",
    "95814": "Sacramento",
    "95815": "Sacramento",
    "95816": "Sacramento",
    "95817": "Sacramento",
    "95818": "Sacramento",
    "95819": "Sacramento",
    "95820": "Sacramento",
    "95821": "Sacramento",
    "95822": "Sacramento",
    "95823": "Sacramento",
    "95824": "Sacramento",
    "95825": "Sacramento",
    "95826": "Sacramento",
    "95827": "Sacramento",
    "95828": "Sacramento",
    "95829": "Sacramento",
    "95831": "Sacramento",
    "95833": "Sacramento",
    "95834": "Sacramento",
    "95835": "Sacramento",
    "95838": "Sacramento",
    "95841": "Sacramento",
    "95842": "Sacramento",
    "95843": "Antelope",
    "95864": "Sacramento",
}


def _build_mapping() -> Dict[str, str]:
    """
    Charge la meilleure table possible :
    1) fallback interne minimal
    2) surcouche avec ZIP_DB.txt s'il existe (prioritaire)
    """
    mapping = dict(_FALLBACK_ZIP_TO_CITY)
    zip_db_path = Path(__file__).with_name("ZIP_DB.txt")
    file_mapping = _load_mapping_from_file(zip_db_path)
    if file_mapping:
        mapping.update(file_mapping)
    return dict(sorted(mapping.items(), key=lambda kv: int(kv[0])))


# Mapping principal exporté
CALIFORNIA_ZIP_TO_CITY: Dict[str, str] = _build_mapping()


def get_city_from_zip(zip_code: str) -> str:
    """
    Retourne la ville associée au ZIP californien.
    Retourne '' si inconnu/non trouvé.
    """
    z = str(zip_code).strip()
    return CALIFORNIA_ZIP_TO_CITY.get(z, "")


def is_california_zip(zip_code: str) -> bool:
    """Vérifie si un ZIP appartient à la plage californienne cible."""
    return _is_valid_ca_zip(str(zip_code).strip())


def find_zips_by_city(city_name: str) -> List[str]:
    """
    Recherche tous les ZIP correspondant exactement à une ville
    (insensible à la casse, trim des espaces).
    """
    target = city_name.strip().lower()
    if not target:
        return []
    return [
        z
        for z, city in CALIFORNIA_ZIP_TO_CITY.items()
        if city.lower() == target
    ]


def city_exists(city_name: str) -> bool:
    """True si la ville existe dans le mapping."""
    return len(find_zips_by_city(city_name)) > 0


def get_coverage_stats() -> Tuple[int, int, int]:
    """
    Retourne (nb_zip_mappés, min_zip, max_zip) dans le mapping courant.
    """
    if not CALIFORNIA_ZIP_TO_CITY:
        return (0, MIN_CA_ZIP, MAX_CA_ZIP)
    keys = [int(z) for z in CALIFORNIA_ZIP_TO_CITY.keys()]
    return (len(keys), min(keys), max(keys))


if __name__ == "__main__":
    count, zmin, zmax = get_coverage_stats()
    print(f"California ZIP mapping loaded: {count} entries")
    print(f"ZIP range in mapping: {zmin} -> {zmax}")
    demo = ["90001", "90210", "92101", "94102", "95818", "96162"]
    for z in demo:
        print(f"{z}: {get_city_from_zip(z) or '(unknown)'}")
