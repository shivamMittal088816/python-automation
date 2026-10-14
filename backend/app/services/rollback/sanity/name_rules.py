"""Optional first-name, last-name, and full-name validation rules."""

import re

from app.services.rollback.sanity.columns import find_column


def _evaluate(source, header, pattern, required):
    column = find_column(source, header)
    if column is None:
        return None
    values = source[column]
    return {
        'missing': frozenset(
            position for position, value in enumerate(values)
            if required and not value
        ),
        'invalid': frozenset(
            position for position, value in enumerate(values)
            if value and re.fullmatch(pattern, value) is None
        ),
    }


def evaluate_names(source):
    return {
        'first': _evaluate(source, 'FIRST NAME', r'[A-Za-z]+', True),
        'last': _evaluate(source, 'LAST NAME', r'[A-Za-z ]+', False),
        'full': _evaluate(source, 'FULL NAME', r'[A-Za-z ]+', True),
    }


def append_name_problems(problems, position, results):
    first = results['first']
    if first:
        if position in first['missing']:
            problems.append('First name missing')
        elif position in first['invalid']:
            problems.append('First name: only A-Z and a-z (no spaces) allowed')

    last = results['last']
    if last and position in last['invalid']:
        problems.append('Last name: only A-Z, a-z and spaces allowed')

    full = results['full']
    if full:
        if position in full['missing']:
            problems.append('Full name missing')
        elif position in full['invalid']:
            problems.append('Full name: only A-Z, a-z and spaces allowed')
