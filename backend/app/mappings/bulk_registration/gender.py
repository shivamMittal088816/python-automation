"""Map source gender labels to bulk-registration numeric identifiers."""

GENDER_NUMBERS = {
    'male': '1',
    'female': '2',
    'others': '3',
}


def gender_number(value):
    """Return the numeric gender identifier, or blank for an unknown value."""
    return GENDER_NUMBERS.get(str(value).strip().casefold(), '')
