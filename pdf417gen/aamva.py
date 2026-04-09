# pdf417gen/aamva.py
from datetime import datetime
from typing import Optional

from .license_parser import LicenseParser
from .models.license import License

__all__ = [
    "parse",
    "get_version",
    "is_expired",
    "get_age",
    "is_under21",
    "is_under18",
    "is_acceptable",
    "get_full_name",
    "get_state",
    "is_cdl",
]

def parse(barcode: str) -> License:
    parser = LicenseParser(barcode)
    return parser.parse()

def get_version(barcode: str) -> Optional[str]:
    parser = LicenseParser(barcode)
    return parser.parse_version()

def is_expired(barcode: str) -> bool:
    parser = LicenseParser(barcode)
    return parser.is_expired()

def get_age(barcode: str) -> Optional[int]:
    lic = parse(barcode)
    if not lic.date_of_birth:
        return None
    today = datetime.now()
    dob = lic.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

def is_under21(barcode: str) -> bool:
    age = get_age(barcode)
    return age is not None and age < 21

def is_under18(barcode: str) -> bool:
    age = get_age(barcode)
    return age is not None and age < 18

def is_acceptable(barcode: str) -> bool:
    lic = parse(barcode)
    return lic.is_acceptable()

def get_full_name(barcode: str) -> Optional[str]:
    lic = parse(barcode)
    parts = [p for p in (lic.first_name, lic.middle_name, lic.last_name) if p]
    return " ".join(parts) if parts else None

def get_state(barcode: str) -> Optional[str]:
    lic = parse(barcode)
    return lic.state

def is_cdl(barcode: str) -> bool:
    lic = parse(barcode)
    return lic.cdl_indicator == "1"
