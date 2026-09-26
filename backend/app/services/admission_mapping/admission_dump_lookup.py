"""Index dump admissions and retain every source row for duplicate review."""



def build_dump_lookup(dump, dump_admission_column, username_column, dump_first_name_column):
    # Keep identifiers as text: e.g. 00123 and 123 remain different keys.
    lookup = {}
    counts = {}
    occurrence_rows = {}
    # Start at Excel row 2 because row 1 contains headers, not a student.
    for row_number, (_, row) in enumerate(dump.iterrows(), start=2):
        admission = str(row[dump_admission_column]).strip()
        if not admission:
            continue
        counts[admission] = counts.get(admission, 0) + 1
        occurrence_rows.setdefault(admission, []).append(row_number)
        # setdefault keeps the first duplicate; counts still records every occurrence.
        lookup.setdefault(admission, (str(row[username_column]).strip(), row_number, row[dump_first_name_column], row.get("user_id", "")))
    return lookup, counts, occurrence_rows
