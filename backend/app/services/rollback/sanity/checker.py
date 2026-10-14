"""Orchestrates rollback sanity rules and formats their API report."""

from app.services.rollback.header_validation import validate_rollback_headers
from app.services.rollback.sanity.columns import prepare_source
from app.services.rollback.sanity.gender_rules import (
    append_gender_problems, evaluate_gender,
)
from app.services.rollback.sanity.name_rules import (
    append_name_problems, evaluate_names,
)
from app.services.rollback.sanity.subscription_rules import (
    append_subscription_problems, evaluate_subscriptions,
)
from app.services.rollback.sanity.user_id_rules import (
    append_user_id_problems, evaluate_user_ids,
)


def _optional_checks(checks, names, gender, subscriptions):
    labels = {
        'first': ('first_name_required', 'Every supplied record has a first name',
                  'first_name_characters', 'First name contains only A-Z and a-z'),
        'last': (None, None, 'last_name_characters',
                 'Supplied last name contains only letters and spaces'),
        'full': ('full_name_required', 'Every supplied record has a full name',
                 'full_name_characters', 'Full name contains only letters and spaces'),
    }
    for key, result in names.items():
        if not result:
            continue
        required_id, required_label, invalid_id, invalid_label = labels[key]
        if required_id:
            checks.append((required_id, required_label, result['missing']))
        checks.append((invalid_id, invalid_label, result['invalid']))

    if gender:
        checks.extend([
            ('gender_required', 'Every supplied record has a gender', gender['missing']),
            ('gender_value', 'Gender is exactly Male, Female or Others', gender['invalid']),
        ])
    for header, result in subscriptions.items():
        checks.extend([
            (f'{header}_required', f'Every supplied record has {header}', result['missing']),
            (f'{header}_value', f"{header} is exactly {result['expected']}", result['invalid']),
        ])


def check_rollback_input(frame):
    """Return bulk-registration-shaped results for rollback-specific rules."""
    source = prepare_source(frame)
    columns = [str(column).strip() for column in source.columns]
    header_result = validate_rollback_headers(columns)
    positions = frozenset(range(len(source)))
    unsupported = positions if header_result['unsupported_headers'] else frozenset()
    missing_header = positions if header_result['missing_headers'] else frozenset()

    user_ids = evaluate_user_ids(source)
    names = evaluate_names(source)
    gender = evaluate_gender(source)
    subscriptions = evaluate_subscriptions(source)

    checks = [
        ('allowed_headers', 'Only supported rollback headers are included', unsupported),
        ('user_id_header', 'user_id header is present', missing_header),
        ('user_id_present', 'Every record has a user_id', user_ids['missing']),
        ('user_id_unsigned_int', 'Every user_id is a valid unsigned integer',
         user_ids['invalid']),
        ('unique_user_id', 'Every normalized user_id is unique', user_ids['duplicates']),
    ]
    _optional_checks(checks, names, gender, subscriptions)

    rows = []
    for position, values in enumerate(source.values.tolist()):
        problems = []
        if position in unsupported:
            problems.append(
                'Unsupported header(s): ' + ', '.join(header_result['unsupported_headers'])
            )
        if position in missing_header:
            problems.append(
                'user_id is required for rollback activity because it is the unique identifier'
            )
        else:
            append_user_id_problems(problems, position, user_ids)
        append_name_problems(problems, position, names)
        append_gender_problems(problems, position, gender)
        append_subscription_problems(problems, position, subscriptions)
        rows.append({'row_number': position + 2, 'values': values, 'problems': problems})

    failed_groups = [unsupported, missing_header]
    failed_groups.extend(user_ids.values())
    for result in names.values():
        if result:
            failed_groups.extend(result.values())
    if gender:
        failed_groups.extend(gender.values())
    for result in subscriptions.values():
        failed_groups.extend((result['missing'], result['invalid']))
    valid = not any(failed_groups)

    if valid:
        message = 'Sanity check passed. Every rollback record has a unique user_id.'
    elif header_result['missing_headers']:
        message = 'user_id is required for rollback activity because it is the unique identifier.'
    else:
        message = 'Sanity check failed. Fix the reported records and re-upload the file.'

    return {
        'valid': valid,
        'message': message,
        'missing_headers': header_result['missing_headers'],
        'unsupported_headers': header_result['unsupported_headers'],
        'row_count': len(source),
        'failed_count': sum(bool(row['problems']) for row in rows),
        'columns': columns,
        'checks': [
            {
                'id': check_id,
                'label': label,
                'failed_count': len(failed_positions),
                'passed': not failed_positions,
            }
            for check_id, label, failed_positions in checks
        ],
        'rows': rows,
    }
