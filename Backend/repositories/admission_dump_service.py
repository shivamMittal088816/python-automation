"""Read the admission dump for one school from the configured MySQL database."""

import pandas as pd
from sqlalchemy import text


SCHOOL_NAME_QUERY = text("""
SELECT school FROM users_schools AS us WHERE us.school_id = :school_index
""")


SCHOOL_DUMP_QUERY = text("""
SELECT DISTINCT
    u.user_id,
    CONCAT_WS(' ', u.user_firstname, u.user_lastname) AS fullname,
    pu.admission_number,
    u.user_name,
    u.user_edu_class,
    u.user_edu_major,
    u.user_firstname,
    u.user_lastname,
    u.user_package,
    u.user_email,
    LOWER(
        REPLACE(
            CONCAT_WS(
                ' ',
                u.user_firstname,
                NULLIF(u.user_lastname, ''),
                CASE
                    WHEN u.user_package = 14 THEN u.user_edu_class
                    WHEN u.user_package = 12 THEN u.user_edu_class + 1
                    WHEN u.user_package = 11 THEN u.user_edu_class + 2
                    ELSE u.user_edu_class
                END
            ),
            ' ',
            ''
        )
    ) AS generated_col
FROM users u
LEFT JOIN paid_users pu ON u.user_id = pu.user_id
WHERE u.user_edu_school = :school_index
AND u.user_type = '0'
AND (
    (
        NULLIF(TRIM(pu.admission_number), '') IS NOT NULL
        AND LOWER(TRIM(pu.admission_number)) <> 'null'
    )
    OR NOT EXISTS (
        SELECT 1
        FROM paid_users AS pu_valid
        WHERE pu_valid.user_id = pu.user_id
        AND NULLIF(TRIM(pu_valid.admission_number), '') IS NOT NULL
        AND LOWER(TRIM(pu_valid.admission_number)) <> 'null'
    )
)
""")


def _normalize_dump_rows(frame):
    """Normalize missing cells and remove records that become identical."""
    return frame.fillna("").drop_duplicates().reset_index(drop=True)


def fetch_school_dump(school_index):
    """Return text columns, preserving admission numbers with leading zeros."""
    school_index = school_index.strip()
    if not school_index or not school_index.isascii() or not school_index.isdecimal():
        raise ValueError("Enter a numeric school index.")

    # Initialize database configuration only when SQL fetching is requested.
    from Backend.config.database import engine

    with engine.connect() as connection:
        school_name = connection.execute(SCHOOL_NAME_QUERY, {"school_index": school_index}).scalar()
        if school_name is None or not str(school_name).strip():
            raise ValueError(f"No school found for index {school_index}.")
        result = connection.execute(SCHOOL_DUMP_QUERY, {"school_index": school_index})
        frame = pd.DataFrame(result.fetchall(), columns=list(result.keys()), dtype=str)
        # SQL DISTINCT still treats NULL and an empty string as different. Once
        # missing values are normalized for mapping, remove rows that are now
        # completely identical so the dump contains one copy of each record.
        frame = _normalize_dump_rows(frame)
        frame.attrs["school_index"] = school_index
        frame.attrs["school_name"] = str(school_name).strip()
        return frame
