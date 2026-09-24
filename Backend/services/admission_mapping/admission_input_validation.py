"""Validate selected columns and reserve names for mapping evidence."""



RESULT_COLUMNS = [
    "mapping_admission_number", "mapping_username", "mapping_user_id",
    "mapping_first_name", "mapping_dump_first_name", "mapping_dump_row", "mapping_dump_count",
    "mapping_status", "mapping_reason",
]

def validate_inputs(school, dump, school_admission_column, dump_admission_column, username_column, name_column, dump_first_name_column):
    # Validate both inputs before producing any output, so missing headers give a clear error.
    for label, frame, columns in (
        ("school", school, [school_admission_column, name_column]),
        ("dump", dump, [dump_admission_column, username_column, dump_first_name_column]),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise ValueError(
                f"Missing {label} columns: {missing}. "
                f"Available columns: {list(frame.columns)}"
            )
    # Avoid silently overwriting school columns if an earlier export is uploaded again.
    conflicts = set(RESULT_COLUMNS).intersection(school.columns)
    if conflicts:
        raise ValueError(f"School file already contains output columns: {sorted(conflicts)}")
