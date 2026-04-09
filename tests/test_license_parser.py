from pdf417gen import parse, get_version, is_expired, get_age, get_full_name

SAMPLE = """@
ANSI 636026080102DL00410288ZA03290015DLDAQD12345678
DCSPUBLIC
DDEN
DACJOHN
DDFN
DADQUINCY
DDGN
DCAD
DCBNONE
DCDNONE
DBD08242015
DBB01311970
DBA01312035
DBC1
DAU069 in
DAYGRN
DAG789 E OAK ST
DAIANYTOWN
DAJCA
DAK902230000
DCF83D9BN217QO983B1
DCGUSA
DAW180
DAZBRO
DCK12345678900000000000
DDB02142014
DDK1
ZAZAAN
ZAB
ZAC
"""

def test_parse_basic():
    lic = parse(SAMPLE)
    assert lic.first_name == "JOHN"
    assert lic.last_name == "PUBLIC"
    assert lic.version == "08"

def test_helpers():
    assert get_version(SAMPLE) == "08"
    assert get_full_name(SAMPLE) == "JOHN QUINCY PUBLIC"
    assert get_age(SAMPLE) is not None
