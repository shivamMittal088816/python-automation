"""Optional gender validation rules."""

from app.services.rollback.sanity.columns import find_column


VALID_GENDERS = frozenset({'Male', 'Female', 'Others'})


def evaluate_gender(source):
    column = find_column(source, 'GENDER')
    if column is None:
        return None
    values = source[column]
    return {
        'missing': frozenset(
            position for position, value in enumerate(values) if not value
        ),
        'invalid': frozenset(
            position for position, value in enumerate(values)
            if value and value not in VALID_GENDERS
        ),
    }


def append_gender_problems(problems, position, result):
    if not result:
        return
    if position in result['missing']:
        problems.append('Gender missing')
    elif position in result['invalid']:
        problems.append('Gender invalid: use exactly Male, Female or Others')
