"""Shared check results and whitespace-aware required-field validation."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CheckResult:
    id: str
    label: str
    problem: str
    failed_positions: frozenset[int]

    def summary(self):
        return {'id': self.id, 'label': self.label,
                'failed_count': len(self.failed_positions),
                'passed': not self.failed_positions}


def required_field(records, *, key, column, label):
    """Report missing values without modifying the original input records."""
    failed = frozenset(position for position, record in enumerate(records)
                       if not str(record.get(column, '')).strip())
    return CheckResult(key, f'{label} present', f'{label} missing', failed)


def name_characters(records, *, key, column, label, allow_spaces=True):
    """Validate name characters after normalization; blanks use presence checks."""
    pattern = r'[A-Za-z ]+' if allow_spaces else r'[A-Za-z]+'
    allowed = 'A-Z, a-z and spaces' if allow_spaces else 'A-Z and a-z (no spaces)'
    failed = frozenset(position for position, record in enumerate(records)
                       if str(record.get(column, '')).strip()
                       and re.fullmatch(pattern, str(record.get(column, ''))) is None)
    return CheckResult(f'{key}_characters', f'{label} letters only',
                       f'{label}: only {allowed} allowed', failed)
