# Simple version-specific mappers that extend FieldMapper.
# Only differences from base are applied.

from .field_mapping import FieldMapper

class VersionOneFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        # v1 uses DBJ for driversLicenseId and DAB for lastName, DAA for driverLicenseName
        self._fields.update({
            "driversLicenseId": "DBJ",
            "lastName": "DAB",
            "driverLicenseName": "DAA",
        })

class VersionTwoFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        self._fields["firstName"] = "DCT"

# ... similarly create VersionThreeFieldMapper ... VersionTwelveFieldMapper
# For v12, add DDM, DDN, DDO, DDP and remove alias fields DBN/DBG/DBS
class VersionTwelveFieldMapper(FieldMapper):
    def __init__(self):
        super().__init__()
        self._fields.update({
            "cdlIndicator": "DDM",
            "nonDomiciledIndicator": "DDN",
            "enhancedCredentialIndicator": "DDO",
            "permitIndicator": "DDP",
        })
        # remove deprecated alias fields per CDS 2025
        for k in ("lastNameAlias", "firstNameAlias", "suffixAlias"):
            self._fields.pop(k, None)
