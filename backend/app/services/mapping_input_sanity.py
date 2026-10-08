"""Validate school mapping columns without imposing the bulk-import schema."""
import pandas as pd

from app.api.file_workflow_configuration import suggest
from app.mappings.bulk_registration.class_name import class_id
from app.services.bulk_registration_sanity import check_input
from app.services.bulk_registration_sanity import email, first_name, full_name, gender, last_name, section
from app.services.bulk_registration_sanity.common import CheckResult


ALIASES = {
    'admission_number': ['admission_number', 'admission_no', 'admission', 'admission_id', 'adm_no', 'adm_number', 'admno'],
    'FIRST NAME': ['first_name', 'firstname', 'first'],
    'LAST NAME': ['last_name', 'lastname', 'last'],
    'FULL NAME': ['full_name', 'fullname', 'student_name', 'name'],
    'Section': ['section'],
    'Class Number': ['classNumber', 'class_number', 'class', 'grade'],
    'GENDER': ['gender'],
    'EMAIL': ['email', 'email_address', 'user_email'],
    'house': ['house'],
}


def check_class(records):
    def valid(value):
        value = str(value).strip()
        return class_id(value) != '' or (value.isascii() and value.isdecimal() and int(value) > 0)

    failed = frozenset(position for position, record in enumerate(records)
                       if not valid(record.get('Class Number', '')))
    return CheckResult('class', 'Class name or number present',
                       'Class missing or invalid: use a class name or positive number', failed)


def check_school_input(frame, *, name_column=None, admission_column=None, houses=()):
    columns = list(frame.columns)
    selected = {}
    for target, aliases in ALIASES.items():
        preferred = name_column if target == 'FIRST NAME' else admission_column if target == 'admission_number' else None
        column = suggest(columns, aliases, preferred, optional=True)
        if column is not None:
            selected[target] = frame[column]
    validation = pd.DataFrame(selected, index=frame.index)
    checks = [first_name.check, first_name.check_characters]
    for column, rules in (
        ('LAST NAME', (last_name.check_characters,)),
        ('FULL NAME', (full_name.check, full_name.check_characters)),
        ('Section', (section.check,)),
        ('Class Number', (check_class,)),
        ('GENDER', (gender.check,)),
        ('EMAIL', (email.check_format, email.check)),
    ):
        if column in validation:
            checks.extend(rules)
    return check_input(frame, houses=houses, validation_frame=validation, checks=checks)
