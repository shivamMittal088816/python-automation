"""Name, section, class, and gender rules for the final generated file."""

from app.mappings.bulk_registration.gender import gender_number

from .common import row_stage


def final_sanity_stages(frame):
    first_name = frame['FIRST NAME'].fillna('').astype(str).str.strip()
    last_name = frame['LAST NAME'].fillna('').astype(str).str.strip()
    full_name = frame['FULL NAME'].fillna('').astype(str).str.strip()
    section = frame['Section'].fillna('').astype(str).str.strip()
    section_index = frame['section_index'].fillna('').astype(str).str.strip()
    class_name = frame['Class Number'].fillna('').astype(str).str.strip()
    class_index = frame['CLASS'].fillna('').astype(str).str.strip()
    gender = frame['GENDER'].fillna('').astype(str).str.strip()
    gender_index = frame['Gender Number'].fillna('').astype(str).str.strip()

    return [
        row_stage(frame, 'first_name_required', 'Every final record has a first name', first_name.eq('')),
        row_stage(frame, 'first_name_characters', 'First name contains only A-Z and a-z', first_name.ne('') & ~first_name.str.fullmatch(r'[A-Za-z]+')),
        row_stage(frame, 'last_name_characters', 'Supplied last name contains only letters and spaces', last_name.ne('') & ~last_name.str.fullmatch(r'[A-Za-z ]+')),
        row_stage(frame, 'full_name_required', 'Every final record has a full name', full_name.eq('')),
        row_stage(frame, 'full_name_characters', 'Full name contains only letters and spaces', full_name.ne('') & ~full_name.str.fullmatch(r'[A-Za-z ]+')),
        row_stage(frame, 'section_index', 'Every section resolves to a database index', section.eq('') | section_index.eq('')),
        row_stage(frame, 'class_index', 'Every Class Number resolves to a stored index', class_name.eq('') | class_index.eq('')),
        row_stage(frame, 'gender_index', 'Every gender is predefined and resolves to an index', gender.map(gender_number).eq('') | gender_index.eq('')),
    ]
