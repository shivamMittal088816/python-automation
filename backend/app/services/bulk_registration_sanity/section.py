"""Check that each input record provides a section."""
from .common import required_field


def check(records):
    return required_field(records, key='section', column='Section', label='Section')
