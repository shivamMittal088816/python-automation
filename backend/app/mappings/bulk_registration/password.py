"""Password generation rules for bulk-registration records."""

from secrets import randbelow

PASSWORD_FORMULA = (
    '=(RANDBETWEEN(1,9))&(RANDBETWEEN(0,9))&RANDBETWEEN(0,9)&'
    'RANDBETWEEN(0,9)&RANDBETWEEN(0,9)&RANDBETWEEN(1,9)'
)


def generate_password():
    """Return the six-digit value produced by the spreadsheet formula."""
    digits = [randbelow(9) + 1]
    digits.extend(randbelow(10) for _ in range(4))
    digits.append(randbelow(9) + 1)
    return ''.join(str(digit) for digit in digits)
