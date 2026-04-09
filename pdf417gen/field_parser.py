from datetime import datetime
from typing import Optional
from .utils.regex import Regex
from .mappers.field_mapping import FieldMapper, FieldMapping
from .enums import IssuingCountry, Gender, EyeColor, HairColor, Truncation, NameSuffix

class FieldParser:
    INCHES_PER_CENTIMETER = 0.393701

    def __init__(self, data: str, field_mapper: FieldMapping = None):
        self.data = data
        self.regex = Regex()
        self.field_mapper = field_mapper or FieldMapper()

    def parse_string(self, key: str) -> Optional[str]:
        identifier = self.field_mapper.field_for(key)
        return self.regex.first_match(rf"{identifier}(.+?)\b", self.data)

    def parse_double(self, key: str) -> Optional[float]:
        identifier = self.field_mapper.field_for(key)
        result = self.regex.first_match(rf"{identifier}(\w+)\b", self.data)
        return float(result) if result is not None else None

    def parse_date(self, field: str) -> Optional[datetime]:
        date_string = self.parse_string(field)
        if not date_string or len(date_string) != 8:
            return None
        try:
            month = int(date_string[0:2])
            day = int(date_string[2:4])
            year = int(date_string[4:8])
            return datetime(year, month, day)
        except ValueError:
            return None

    def parse_first_name(self) -> Optional[str]:
        return self.parse_string("firstName")

    def parse_last_name(self) -> Optional[str]:
        return self.parse_string("lastName")

    def parse_middle_name(self) -> Optional[str]:
        return self.parse_string("middleName")

    def parse_expiration_date(self) -> Optional[datetime]:
        return self.parse_date("expirationDate")

    def parse_issue_date(self) -> Optional[datetime]:
        return self.parse_date("issueDate")

    def parse_date_of_birth(self) -> Optional[datetime]:
        return self.parse_date("dateOfBirth")

    def parse_is_expired(self) -> bool:
        exp = self.parse_expiration_date()
        return exp is not None and datetime.now() > exp

    def parse_country(self) -> IssuingCountry:
        country = self.parse_string("country")
        if country is None:
            return IssuingCountry.Unknown
        if country.upper() in ("USA", "US", "UNITED STATES"):
            return IssuingCountry.UnitedStates
        if country.upper() in ("CAN", "CA", "CANADA"):
            return IssuingCountry.Canada
        return IssuingCountry.Unknown

    def parse_truncation_status(self, field: str) -> Truncation:
        trunc = self.parse_string(field)
        if trunc == "T":
            return Truncation.Truncated
        if trunc == "N":
            return Truncation.None_
        return Truncation.Unknown

    def parse_gender(self) -> Gender:
        g = self.parse_string("gender")
        if g == "1":
            return Gender.Male
        if g == "2":
            return Gender.Female
        return Gender.Other

    def parse_eye_color(self) -> EyeColor:
        code = self.parse_string("eyeColor")
        mapping = {
            "BLK": EyeColor.Black, "BLU": EyeColor.Blue, "BRO": EyeColor.Brown,
            "GRY": EyeColor.Gray, "GRN": EyeColor.Green, "HAZ": EyeColor.Hazel,
            "MAR": EyeColor.Maroon, "PNK": EyeColor.Pink, "DIC": EyeColor.Dichromatic
        }
        return mapping.get(code, EyeColor.Unknown)

    def parse_hair_color(self) -> HairColor:
        code = self.parse_string("hairColor")
        mapping = {
            "BAL": HairColor.Bald, "BLK": HairColor.Black, "BLN": HairColor.Blond,
            "BRO": HairColor.Brown, "GRY": HairColor.Grey, "RED": HairColor.Red,
            "SDY": HairColor.Sandy, "WHI": HairColor.White
        }
        return mapping.get(code, HairColor.Unknown)

    def parse_height(self) -> Optional[int]:
        height_string = self.parse_string("height")
        height = self.parse_double("height")
        if not height_string or height is None:
            return None
        if "cm" in height_string.lower():
            return round(height * FieldParser.INCHES_PER_CENTIMETER)
        return int(height)
