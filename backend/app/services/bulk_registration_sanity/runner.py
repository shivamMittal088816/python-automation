"""Run all input checks and assemble summaries and original-row results."""
from . import class_number, email, first_name, full_name, gender, last_name, section, username
from .normalization import normalize_input


CHECKS = (first_name.check, section.check, class_number.check,
          full_name.check, gender.check, first_name.check_characters,
          last_name.check_characters, full_name.check_characters, username.check,
          email.check_format, email.check)


def check_input(frame):
    source = normalize_input(frame)
    records = source.to_dict('records')
    values = source.astype(str).values.tolist()
    results = [check(records) for check in CHECKS]
    rows = []
    for position, record in enumerate(records):
        problems = [result.problem for result in results if position in result.failed_positions]
        rows.append({'row_number': position + 2,
                     'values': values[position],
                     'admission_number': str(record.get('admission_number', '')),
                     'first_name': str(record.get('FIRST NAME', '')),
                     'last_name': str(record.get('LAST NAME', '')),
                     'full_name': str(record.get('FULL NAME', '')),
                     'email': str(record.get('EMAIL', '')),
                     'username': str(record.get('user_name', '')),
                     'problems': problems})
    return {'row_count': len(rows), 'failed_count': sum(bool(row['problems']) for row in rows),
            'columns': [str(column) for column in source.columns],
            'checks': [result.summary() for result in results], 'rows': rows}
