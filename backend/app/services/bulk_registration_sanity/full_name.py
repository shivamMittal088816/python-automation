"""Check that each input record provides a full name."""
from .common import name_characters, required_field


def check(records):
    return required_field(records, key='full_name', column='FULL NAME', label='Full name')


def check_characters(records):
    return name_characters(records, key='full_name', column='FULL NAME', label='Full name')
