"""Password generation rules for bulk-registration records."""

from secrets import randbelow

def generate_password():
    """Return the six-digit value produced by the spreadsheet formula."""
    digits = [randbelow(9) + 1]
    digits.extend(randbelow(10) for _ in range(4))
    digits.append(randbelow(9) + 1)
    return ''.join(str(digit) for digit in digits)

# Purpose: Password generation rules for bulk-registration records.
# Its public interface includes generate_password.
# It keeps declarative conversion rules separate from orchestration and HTTP code.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.services.bulk_registration.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
