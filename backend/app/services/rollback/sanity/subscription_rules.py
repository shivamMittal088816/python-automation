"""Rules for optional fixed-value subscription columns."""

from app.services.rollback.sanity.columns import find_column


EXPECTED_VALUES = {
    'user_subscription_date': '2026-04-01 00:00:00',
    'user_package': '14',
    'user_activated': '1',
    'user_subscribed': '1',
}


def evaluate_subscriptions(source):
    results = {}
    for header, expected in EXPECTED_VALUES.items():
        column = find_column(source, header)
        if column is None:
            continue
        values = source[column]
        results[header] = {
            'expected': expected,
            'missing': frozenset(
                position for position, value in enumerate(values) if not value
            ),
            'invalid': frozenset(
                position for position, value in enumerate(values)
                if value and value != expected
            ),
        }
    return results


def append_subscription_problems(problems, position, results):
    for header, result in results.items():
        if position in result['missing']:
            problems.append(f'{header} missing')
        elif position in result['invalid']:
            problems.append(
                f"{header} invalid: use exactly {result['expected']}"
            )
