# pdf417gen/__init__.py
"""
Package d'export pour pdf417gen.
Expose l'API d'encodage/rendu existante ainsi que les helpers AAMVA (parse, get_version, ...).
"""

# Encodage / rendu (API existante)
try:
    from .encoding import encode, encode_macro
    from .rendering import render_image, render_svg
except Exception:
    # Si le package vendorisé n'a pas ces modules, on laisse l'import échouer plus tard
    # mais on définit des placeholders pour éviter ImportError immédiat lors de l'import du package.
    def _missing(*args, **kwargs):
        raise RuntimeError("pdf417gen: encoding/rendering functions are not available in this installation.")
    encode = encode_macro = render_image = render_svg = _missing

# Helpers AAMVA (façade)
# aamva.py utilise des imports paresseux à l'intérieur des fonctions pour éviter les import cycles,
# donc l'import du module aamva est sûr ici.
try:
    from .aamva import (
        parse,
        get_version,
        is_expired,
        get_age,
        get_full_name,
        is_under21,
        is_under18,
        is_acceptable,
        get_state,
        is_cdl,
    )
except Exception:
    # Si aamva.py est absent ou a une erreur, on définit des placeholders explicites
    def _not_available(*args, **kwargs):
        raise RuntimeError("pdf417gen.aamva helpers are not available: ensure pdf417gen/aamva.py exists and is valid.")
    parse = get_version = is_expired = get_age = get_full_name = is_under21 = is_under18 = is_acceptable = get_state = is_cdl = _not_available

# Exports publics
__all__ = [
    "encode",
    "encode_macro",
    "render_image",
    "render_svg",
    "parse",
    "get_version",
    "is_expired",
    "get_age",
    "get_full_name",
    "is_under21",
    "is_under18",
    "is_acceptable",
    "get_state",
    "is_cdl",
]
