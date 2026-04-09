# pdf417gen/__init__.py
"""
pdf417gen package: safe, lazy exports for encoding/rendering and AAMVA helpers.
This file ensures `from pdf417gen import parse` always exists at import time.
"""

# encoding/rendering placeholders
try:
    from .encoding import encode, encode_macro
    from .rendering import render_image, render_svg
except Exception:
    def _missing_encoding(*args, **kwargs):
        raise RuntimeError("pdf417gen: encoding/rendering functions are not available.")
    encode = encode_macro = render_image = render_svg = _missing_encoding

# Lazy wrapper factory
def _wrap(name):
    def _fn(*args, **kwargs):
        mod = __import__(__name__ + ".aamva", fromlist=[name])
        real = getattr(mod, name)
        return real(*args, **kwargs)
    _fn.__name__ = name
    _fn.__doc__ = f"Lazy wrapper for pdf417gen.aamva.{name}"
    return _fn

# Bind wrappers
parse = _wrap("parse")
get_version = _wrap("get_version")
is_expired = _wrap("is_expired")
get_age = _wrap("get_age")
is_under21 = _wrap("is_under21")
is_under18 = _wrap("is_under18")
is_acceptable = _wrap("is_acceptable")
get_full_name = _wrap("get_full_name")
get_state = _wrap("get_state")
is_cdl = _wrap("is_cdl")

# Expose names
globals().update({
    "encode": encode,
    "encode_macro": encode_macro,
    "render_image": render_image,
    "render_svg": render_svg,
    "parse": parse,
    "get_version": get_version,
    "is_expired": is_expired,
    "get_age": get_age,
    "is_under21": is_under21,
    "is_under18": is_under18,
    "is_acceptable": is_acceptable,
    "get_full_name": get_full_name,
    "get_state": get_state,
    "is_cdl": is_cdl,
})

__all__ = [
    "encode", "encode_macro", "render_image", "render_svg",
    "parse", "get_version", "is_expired", "get_age",
    "is_under21", "is_under18", "is_acceptable",
    "get_full_name", "get_state", "is_cdl",
]
