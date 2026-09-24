import unittest
import sqlite3

import pandas as pd
from Backend.repositories.admission_dump_service import SCHOOL_DUMP_QUERY, _normalize_dump_rows
from Backend.utils.school_statistics import dump_overview


class AdmissionDumpCountTests(unittest.TestCase):
    """Exercise the production SELECT on isolated data, without a live database.

    SQLite supplies the relational operations; CONCAT_WS is registered locally.
    These tests cover row cardinality, not MySQL-specific collation behavior.
    """

    def test_school_record_count_cases(self):
        cases = [
            # label, school, user type, paid admission values, DB count, dump count
            ('one admission', '914', '0', ['0007'], 1, 1),
            ('no paid row', '914', '0', [], 1, 1),
            ('non student', '914', '1', ['0007'], 1, 0),
            ('null user type', '914', None, ['0007'], 1, 0),
            ('different school', '915', '0', ['0007'], 0, 0),
            ('null school', None, '0', ['0007'], 0, 0),
            ('repeated admission', '914', '0', ['0007', '0007'], 1, 1),
            ('multiple admissions', '914', '0', ['0007', '0008'], 1, 2),
            ('valid replaces missing', '914', '0', [None, '', ' ', 'null', 'NULL', '0007'], 1, 1),
            ('only null admission', '914', '0', [None], 1, 1),
            ('normalized duplicates', '914', '0', [None, ''], 1, 1),
            ('different missing representations', '914', '0', [None, '', ' ', 'null'], 1, 3),
        ]
        for label, school, user_type, admissions, expected_db, expected_dump in cases:
            with self.subTest(case=label), sqlite3.connect(':memory:') as connection:
                connection.create_function('CONCAT_WS', -1,
                    lambda separator, *values: separator.join(str(v) for v in values if v is not None))
                connection.execute('''CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY, user_edu_school TEXT, user_type TEXT,
                    user_firstname TEXT, user_lastname TEXT, user_name TEXT,
                    user_edu_class INTEGER, user_edu_major TEXT, user_package INTEGER,
                    user_email TEXT)''')
                connection.execute('CREATE TABLE paid_users (user_id INTEGER, admission_number TEXT)')
                connection.execute("INSERT INTO users VALUES (1, ?, ?, 'Test', 'Student', 'test', 5, 'A', 14, '')",
                                   (school, user_type))
                connection.executemany('INSERT INTO paid_users VALUES (1, ?)', [(a,) for a in admissions])
                database_count = connection.execute(
                    'SELECT COUNT(*) FROM users WHERE user_edu_school = ?', ('914',)).fetchone()[0]
                cursor = connection.execute(str(SCHOOL_DUMP_QUERY), {'school_index': '914'})
                dump = _normalize_dump_rows(pd.DataFrame(
                    cursor.fetchall(), columns=[column[0] for column in cursor.description], dtype=str))
                self.assertEqual(database_count, expected_db)
                self.assertEqual(len(dump), expected_dump)
                _, student_count = dump_overview(dump)
                self.assertEqual(student_count, int(expected_dump > 0))


class AdmissionDumpNormalizationTests(unittest.TestCase):
    def test_normalized_exact_duplicates_are_removed(self):
        rows = pd.DataFrame({
            'user_id': ['001', '001', '002'],
            'admission_number': [None, '', '0007'],
            'user_name': ['alice', 'alice', 'bob'],
        }, dtype=str)

        normalized = _normalize_dump_rows(rows)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized['user_id'].tolist(), ['001', '002'])
        self.assertEqual(normalized.loc[1, 'admission_number'], '0007')


if __name__ == '__main__':
    unittest.main()
