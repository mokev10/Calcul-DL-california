from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from ..enums import Gender, EyeColor, IssuingCountry, Truncation, HairColor, NameSuffix

@dataclass
class License:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    expiration_date: Optional[datetime] = None
    issue_date: Optional[datetime] = None
    date_of_birth: Optional[datetime] = None
    gender: Gender = Gender.Unknown
    eye_color: EyeColor = EyeColor.Unknown
    height: Optional[int] = None
    street_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    drivers_license_id: Optional[str] = None
    document_id: Optional[str] = None
    country: IssuingCountry = IssuingCountry.Unknown
    middle_name_truncation: Truncation = Truncation.None_
    first_name_truncation: Truncation = Truncation.None_
    last_name_truncation: Truncation = Truncation.None_
    street_address_supplement: Optional[str] = None
    hair_color: HairColor = HairColor.Unknown
    place_of_birth: Optional[str] = None
    audit_information: Optional[str] = None
    inventory_control_number: Optional[str] = None
    last_name_alias: Optional[str] = None
    first_name_alias: Optional[str] = None
    suffix_alias: Optional[str] = None
    suffix: NameSuffix = NameSuffix.Unknown
    cdl_indicator: Optional[str] = None
    non_domiciled_indicator: Optional[str] = None
    enhanced_credential_indicator: Optional[str] = None
    permit_indicator: Optional[str] = None
    version: Optional[str] = None
    pdf417: Optional[str] = None

    def is_expired(self) -> bool:
        return self.expiration_date is not None and datetime.now() > self.expiration_date

    def has_been_issued(self) -> bool:
        return self.issue_date is not None and datetime.now() > self.issue_date

    def is_acceptable(self) -> bool:
        required = [
            self.expiration_date, self.issue_date, self.last_name, self.first_name,
            self.middle_name, self.date_of_birth, self.height, self.street_address,
            self.city, self.state, self.postal_code, self.document_id
        ]
        return all(x is not None for x in required) and not self.is_expired()
