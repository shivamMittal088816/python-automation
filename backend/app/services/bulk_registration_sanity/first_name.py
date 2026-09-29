"""Check that each input record provides a first name."""
from .common import name_characters, required_field


def check(records):
    return required_field(records, key='first_name', column='FIRST NAME', label='First name')


def check_characters(records):
    return name_characters(records, key='first_name', column='FIRST NAME', label='First name',
                           allow_spaces=False)
