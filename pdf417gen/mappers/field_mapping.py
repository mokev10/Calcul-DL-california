from typing import Dict

class FieldMapping:
    def fields(self) -> Dict[str, str]:
        raise NotImplementedError

    def field_for(self, key: str) -> str:
        raise NotImplementedError

class FieldMapper(FieldMapping):
    def __init__(self):
        # Base mapping (v8-style) — keys are human readable names
        self._fields = {
            "firstName": "DAC",
            "lastName": "DCS",
            "middleName": "DAD",
            "expirationDate": "DBA",
            "issueDate": "DBD",
            "dateOfBirth": "DBB",
            "gender": "DBC",
            "eyeColor": "DAY",
            "height": "DAU",
            "streetAddress": "DAG",
            "streetAddressSupplement": "DAH",
            "city": "DAI",
            "state": "DAJ",
            "postalCode": "DAK",
            "driversLicenseId": "DAQ",
            "documentId": "DCF",
            "country": "DCG",
            "weight": "DAW",
            "hairColor": "DAZ",
            "placeOfBirth": "DCI",
            "auditInformation": "DCJ",
            "inventoryControlNumber": "DCK",
            "lastNameAlias": "DBN",
            "firstNameAlias": "DBG",
            "suffixAlias": "DBS",
            "suffix": "DCU",
            "middleNameTruncation": "DDG",
            "firstNameTruncation": "DDF",
            "lastNameTruncation": "DDE",
        }

    @property
    def fields(self):
        return self._fields

    def field_for(self, key: str) -> str:
        return self._fields.get(key, key)
