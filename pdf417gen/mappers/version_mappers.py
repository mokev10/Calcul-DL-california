"""
Version-specific field mappers for AAMVA payload parsing.

Design:
- Start from the base FieldMapper (roughly v8-style mapping).
- Override only what differs for specific versions.
- Keep explicit classes for all supported versions used by LicenseParser.
"""

from .field_mapping import FieldMapper


class VersionOneFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        # v1 historical differences
        self._fields.update(
            {
                "driversLicenseId": "DBJ",
                "lastName": "DAB",
                "driverLicenseName": "DAA",
            }
        )


class VersionTwoFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        # v2 uses DCT for first name
        self._fields["firstName"] = "DCT"


class VersionThreeFieldMapper(FieldMapper):
    """v3 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionFourFieldMapper(FieldMapper):
    """v4 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionFiveFieldMapper(FieldMapper):
    """v5 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionSixFieldMapper(FieldMapper):
    """v6 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionSevenFieldMapper(FieldMapper):
    """v7 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionEightFieldMapper(FieldMapper):
    """v8 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionNineFieldMapper(FieldMapper):
    """v9 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionTenFieldMapper(FieldMapper):
    """v10 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionElevenFieldMapper(FieldMapper):
    """v11 uses base mapping."""
    def __init__(self):
        super().__init__()


class VersionTwelveFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        # v12+ fields (CDS updates)
        self._fields.update(
            {
                "cdlIndicator": "DDM",
                "nonDomiciledIndicator": "DDN",
                "enhancedCredentialIndicator": "DDO",
                "permitIndicator": "DDP",
            }
        )
        # Deprecated alias fields removed in newer spec variants
        for key in ("lastNameAlias", "firstNameAlias", "suffixAlias"):
            self._fields.pop(key, None)
