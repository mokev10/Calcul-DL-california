# tests/test_pdf417_import.py
import importlib

def test_pdf417_import():
    mod = importlib.import_module("pdf417gen")
    assert hasattr(mod, "encode")
    assert hasattr(mod, "render_svg")
