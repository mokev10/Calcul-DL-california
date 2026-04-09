# pdf417gen/aamva.py
from datetime import datetime
from typing import Optional

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

def parse(barcode: str):
    """
    Parse the raw PDF417 barcode string and return a License-like object.
    Lazy import to avoid circular import issues during package installation/tests.
    """
    from .license_parser import LicenseParser
    parser = LicenseParser(barcode)
    return parser.parse()

def get_version(barcode: str) -> Optional[str]:
    from .license_parser import LicenseParser
    parser = LicenseParser(barcode)
    return parser.parse_version()

def is_expired(barcode: str) -> bool:
    from .license_parser import LicenseParser
    parser = LicenseParser(barcode)
    return parser.is_expired()

def get_age(barcode: str) -> Optional[int]:
    lic = parse(barcode)
    # Support both snake_case and camelCase attributes on the License object
    dob = getattr(lic, "date_of_birth", None) or getattr(lic, "dateOfBirth", None)
    if not dob:
        return None
    today = datetime.now()
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
    # call method if present, otherwise fallback to False
    return getattr(lic, "is_acceptable", lambda: False)()

def get_full_name(barcode: str) -> Optional[str]:
    lic = parse(barcode)
    first = getattr(lic, "first_name", None) or getattr(lic, "firstName", None)
    middle = getattr(lic, "middle_name", None) or getattr(lic, "middleName", None)
    last = getattr(lic, "last_name", None) or getattr(lic, "lastName", None)
    parts = [p for p in (first, middle, last) if p]
    return " ".join(parts) if parts else None

def get_state(barcode: str) -> Optional[str]:
    lic = parse(barcode)
    return getattr(lic, "state", None) or getattr(lic, "stateCode", None)

def is_cdl(barcode: str) -> bool:
    lic = parse(barcode)
    cdl = getattr(lic, "cdl_indicator", None) or getattr(lic, "cdlIndicator", None)
    return cdl == "1"
