# tests/test_aamva_builder.py
from driver_license_final_fixed import build_aamva_tags

def test_aamva_builder_minimal():
    fields = {
        "DCS": "DOE",
        "DAC": "JOHN",
        "DBB": "01011990",
        "DBA": "01012025",
        "DBD": "01012020",
        "DAQ": "A1234567"
    }
    s = build_aamva_tags(fields)
    assert "DCSDOE" in s
    assert "DACJOHN" in s
    assert s.startswith("@")
