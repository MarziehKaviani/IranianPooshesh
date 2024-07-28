import re

from django.core.exceptions import ValidationError

from common import variables
from common.variables import *
from common.utils import load_countries_lazy


class PhoneNumberValidatorAdapter:
    def __init__(self, phone_number, country_code=98) -> None:
        self.phone_number = phone_number.strip()
        self.validator = PhoneNumberValidator(phone_number, country_code)
        self.country_code = country_code

    def validate(self):
        if self.country_code == '98':
            return self.validator.iran_number_validator()
        else:
            return self.validator.non_iranian_number_validator()


class PhoneNumberValidator:
    def __init__(
        self,
        phone_number,
        country_code="98",
        valid_digits=[
            920, 921, 922, 910, 911, 912, 913, 914,
            915, 916, 917, 918, 919, 990, 991, 992,
            993, 994, 931, 932, 933, 934, 901, 902,
            903, 904, 905, 930, 933, 935, 936, 937,
            938, 939,
        ],
        format="9xx xxx xxxx",
    ):
        super().__init__()
        self.phone_number = phone_number.strip()
        self.valid_digits = valid_digits
        self.country_code = country_code
        self.format = format

    def iran_number_validator(self):
        if not str(self.phone_number).strip().isdigit():
            return False
        if int(self.phone_number.strip()[:3]) not in self.valid_digits or len(self.phone_number.strip()) != 10:
            return False
        pattern = r"^0(?:9[0-9][0-9]|9[0-5]|9[013-9]|99|93)[0-9]{7}$"
        if not re.match(pattern, f"0{self.phone_number}"):
            return False
        return True

    def non_iranian_number_validator(self):
        countries_df = load_countries_lazy(
        )[[variables.CALLING_CODE, variables.NATIONAL_NUMBER_LENGTH]]
        phone_len = countries_df[countries_df[variables.CALLING_CODE]
                                 == self.country_code][variables.NATIONAL_NUMBER_LENGTH]
        if len(self.phone_number) != int(phone_len):
            return False
        return True


def country_code_validator(country_code):
    country_code = str(country_code).strip()
    if not int(country_code) in load_countries_lazy()[variables.CALLING_CODE]:
        return False
    return True