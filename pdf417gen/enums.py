from enum import Enum


class IssuingCountry(Enum):
    Unknown = "unknown"
    UnitedStates = "united_states"
    Canada = "canada"


class Gender(Enum):
    Unknown = "unknown"
    Male = "male"
    Female = "female"
    Other = "other"


class EyeColor(Enum):
    Unknown = "unknown"
    Black = "black"
    Blue = "blue"
    Brown = "brown"
    Gray = "gray"
    Green = "green"
    Hazel = "hazel"
    Maroon = "maroon"
    Pink = "pink"
    Dichromatic = "dichromatic"


class HairColor(Enum):
    Unknown = "unknown"
    Bald = "bald"
    Black = "black"
    Blond = "blond"
    Brown = "brown"
    Grey = "grey"
    Red = "red"
    Sandy = "sandy"
    White = "white"


class Truncation(Enum):
    Unknown = "unknown"
    None_ = "none"
    Truncated = "truncated"


class NameSuffix(Enum):
    Unknown = "unknown"
