import re
from typing import Optional
from .mappers.field_mapping import FieldMapper
from .mappers.version_mappers import (
    VersionOneFieldMapper, VersionTwoFieldMapper, VersionThreeFieldMapper,
    VersionFourFieldMapper, VersionFiveFieldMapper, VersionSixFieldMapper,
    VersionSevenFieldMapper, VersionEightFieldMapper, VersionNineFieldMapper,
    VersionTenFieldMapper, VersionElevenFieldMapper, VersionTwelveFieldMapper
)
from .field_parser import FieldParser
from .models.license import License

class LicenseParser:
    def __init__(self, data: str):
        self.data = self._clean_and_format_string(data)
        self.field_parser = FieldParser(self.data)

    def _clean_and_format_string(self, data: str) -> str:
        data = data.replace('\u001e', '').replace('\r', '')
        lines = [line.strip() for line in data.split('\n') if line.strip()]
        data = '\n'.join(lines)
        if not data.startswith('@'):
            data = '@\n' + data
        return data

    def parse_version(self) -> Optional[str]:
        # pattern: ANSI 6360xxVV... where VV is version
        m = re.search(r"\d{6}(\d{2})\w+", self.data)
        return m.group(1) if m else None

    def version_based_field_parser(self, version: Optional[str]) -> FieldParser:
        if not version:
            return FieldParser(self.data)
        mapping = {
            "01": VersionOneFieldMapper,
            "02": VersionTwoFieldMapper,
            "03": VersionThreeFieldMapper,
            "04": VersionFourFieldMapper,
            "05": VersionFiveFieldMapper,
            "06": VersionSixFieldMapper,
            "07": VersionSevenFieldMapper,
            "08": VersionEightFieldMapper,
            "09": VersionNineFieldMapper,
            "10": VersionTenFieldMapper,
            "11": VersionElevenFieldMapper,
            "12": VersionTwelveFieldMapper,
        }
        mapper_cls = mapping.get(version, FieldMapper)
        return FieldParser(self.data, mapper_cls())

    def parse(self) -> License:
        self.field_parser = self.version_based_field_parser(self.parse_version())
        l = License(
            first_name=self.field_parser.parse_first_name(),
            last_name=self.field_parser.parse_last_name(),
            middle_name=self.field_parser.parse_middle_name(),
            expiration_date=self.field_parser.parse_expiration_date(),
            issue_date=self.field_parser.parse_issue_date(),
            date_of_birth=self.field_parser.parse_date_of_birth(),
            gender=self.field_parser.parse_gender(),
            eye_color=self.field_parser.parse_eye_color(),
            height=self.field_parser.parse_height(),
            street_address=self.field_parser.parse_string("streetAddress"),
            city=self.field_parser.parse_string("city"),
            state=self.field_parser.parse_string("state"),
            postal_code=self.field_parser.parse_string("postalCode"),
            drivers_license_id=self.field_parser.parse_string("driversLicenseId"),
            document_id=self.field_parser.parse_string("documentId"),
            country=self.field_parser.parse_country(),
            middle_name_truncation=self.field_parser.parse_truncation_status("middleNameTruncation"),
            first_name_truncation=self.field_parser.parse_truncation_status("firstNameTruncation"),
            last_name_truncation=self.field_parser.parse_truncation_status("lastNameTruncation"),
            street_address_supplement=self.field_parser.parse_string("streetAddressSupplement"),
            hair_color=self.field_parser.parse_hair_color(),
            place_of_birth=self.field_parser.parse_string("placeOfBirth"),
            audit_information=self.field_parser.parse_string("auditInformation"),
            inventory_control_number=self.field_parser.parse_string("inventoryControlNumber"),
            last_name_alias=self.field_parser.parse_string("lastNameAlias"),
            first_name_alias=self.field_parser.parse_string("firstNameAlias"),
            suffix_alias=self.field_parser.parse_string("suffixAlias"),
            suffix=self.field_parser.parse_name_suffix() if hasattr(self.field_parser, "parse_name_suffix") else None,
            version=self.parse_version(),
            pdf417=self.data,
            cdl_indicator=self.field_parser.parse_string("cdlIndicator"),
            non_domiciled_indicator=self.field_parser.parse_string("nonDomiciledIndicator"),
            enhanced_credential_indicator=self.field_parser.parse_string("enhancedCredentialIndicator"),
            permit_indicator=self.field_parser.parse_string("permitIndicator"),
            weight=self.field_parser.parse_string("weight"),
        )
        return l

    def is_expired(self) -> bool:
        return self.field_parser.parse_is_expired()
