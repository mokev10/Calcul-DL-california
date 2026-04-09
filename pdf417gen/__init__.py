# pdf417gen/__init__.py
"""
pdf417gen package exports.
This file provides safe, lazy wrappers so that:
- importing `pdf417gen` never triggers heavy imports or import cycles
- tests can do `from pdf417gen import parse, get_version, ...`
"""

# --- encoding/rendering placeholders (existing API) ---
try:
    from .encoding import encode, encode_macro
    from .rendering import render_image, render_svg
except Exception:
    # Provide clear runtime error if someone tries to call these when not available.
    def _missing_encoding(*args, **kwargs):
        raise RuntimeError("pdf417gen: encoding/rendering functions are not available in this installation.")
    encode = encode_macro = render_image = render_svg = _missing_encoding

# --- AAMVA helpers: define lazy wrappers that import aamva only when called ---
def parse(barcode: str):
    """
    Parse barcode and return License-like object.
    Lazy import to avoid import cycles and heavy imports at package import time.
    """
    from .aamva import parse as _parse
    return _parse(barcode)

def get_version(barcode: str):
    from .aamva import get_version as _get_version
    return _get_version(barcode)

def is_expired(barcode: str):
    from .aamva import is_expired as _is_expired
    return _is_expired(barcode)

def get_age(barcode: str):
    from .aamva import get_age as _get_age
    return _get_age(barcode)

def is_under21(barcode: str):
    from .aamva import is_under21 as _is_under21
    return _is_under21(barcode)

def is_under18(barcode: str):
    from .aamva import is_under18 as _is_under18
    return _is_under18(barcode)

def is_acceptable(barcode: str):
    from .aamva import is_acceptable as _is_acceptable
    return _is_acceptable(barcode)

def get_full_name(barcode: str):
    from .aamva import get_full_name as _get_full_name
    return _get_full_name(barcode)

def get_state(barcode: str):
    from .aamva import get_state as _get_state
    return _get_state(barcode)

def is_cdl(barcode: str):
    from .aamva import is_cdl as _is_cdl
    return _is_cdl(barcode)

# --- Public API exports ---
__all__ = [
    "encode",
    "encode_macro",
    "render_image",
    "render_svg",
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
