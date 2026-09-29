"""Validate characters in supplied last names without making last name required."""
from .common import name_characters


def check_characters(records):
    return name_characters(records, key='last_name', column='LAST NAME', label='Last name')
