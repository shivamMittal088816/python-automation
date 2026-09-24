from io import BytesIO
import unittest
import pandas as pd

from Backend.services.admission_mapping.admission_file_mapping import map_students, build_exports
from Backend.services.admission_mapping.admission_second_pass import map_admission_second_pass


class AdmissionSecondPassTests(unittest.TestCase):
    def first(self, school, dump):
        return build_exports(map_students(school, dump, 'admission', 'admission', 'user_name', 'first'))

    def second(self, exports, dump):
        return map_admission_second_pass(exports, dump, 'full', 'admission', 'user_name')

    def read(self, exports, name):
        return pd.read_excel(BytesIO(exports[name + '.xlsx']['data']), dtype=str, keep_default_na=False)

    def test_sorted_names_unique_admission_and_repeat_runs(self):
        school = pd.DataFrame({'admission': ['001', '002', '003', '004', '005'],
            'first': ['wrong', 'wrong', 'wrong', 'wrong', 'Eva'],
            'full': [' A nn\tA ', 'Different', '', 'Anna', 'Eva']})
        dump = pd.DataFrame({'admission': ['001', '002', '003', '005'],
            'user_firstname': ['Ann', 'Bob', 'Carol', 'Eva'], 'fullname': ['Anna', 'Bob', '', 'Eva'],
            'user_name': ['ann', 'bob', 'carol', 'eva'], 'user_id': ['0001', '0002', '0003', '0005']})
        first = self.first(school, dump)
        second = self.second(first, dump)
        self.assertEqual(second['matched.xlsx']['count'], 2)
        self.assertEqual(second['review.xlsx']['count'], 2)
        self.assertEqual(second['not_matched.xlsx']['data'], first['not_matched.xlsx']['data'])
        row = self.read(second, 'matched').set_index('admission').loc['001']
        self.assertEqual(row['mapping_user_id'], '0001')
        self.assertEqual(row['full'], ' A nn\tA ')
        self.assertIn('Pass 2', row['mapping_status'])
        again = self.second(second, dump)
        self.assertEqual(again['matched.xlsx']['data'], second['matched.xlsx']['data'])

    def test_other_review_reasons_and_nonunique_admissions_are_excluded(self):
        school = pd.DataFrame({'admission': ['001', '001', '002', '', '003', '004'],
            'first': ['wrong', 'other', 'wrong', 'wrong', '', 'wrong'],
            'full': ['Anna'] * 6})
        dump = pd.DataFrame({'admission': ['001', '002', '002', '003', '004'],
            'user_firstname': ['Ann'] * 5, 'fullname': ['Anna'] * 5,
            'user_name': ['a', 'b', 'c', 'd', ''], 'user_id': ['1', '2', '3', '4', '5']})
        first = self.first(school, dump)
        second = self.second(first, dump)
        self.assertEqual(second['matched.xlsx']['count'], 0)
        self.assertEqual(second['review.xlsx']['count'], 5)
        self.assertEqual(second['not_matched.xlsx']['count'], 1)
        missing = self.read(second, 'not_matched')
        self.assertEqual(missing['mapping_admission_number'].tolist(), [''])
        self.assertIn('Admission number missing', missing.iloc[0]['mapping_status'])
        for filename in ('matched.xlsx', 'review.xlsx', 'not_matched.xlsx'):
            self.assertEqual(second[filename]['data'], first[filename]['data'])

    def test_missing_dump_fullname_is_rejected(self):
        school = pd.DataFrame({'admission': ['001'], 'first': ['wrong'], 'full': ['Anna']})
        dump = pd.DataFrame({'admission': ['001'], 'user_firstname': ['Ann'], 'user_name': ['ann']})
        with self.assertRaisesRegex(ValueError, 'fullname'):
            self.second(self.first(school, dump), dump)

    def test_matching_initials_remain_in_review_after_second_pass(self):
        school = pd.DataFrame({'admission': ['001', '002'],
                               'first': [' A ', 'B.'], 'full': ['Alice Smith', 'Bob Jones']})
        dump = pd.DataFrame({'admission': ['001', '002'],
                             'user_firstname': ['a', 'b.'], 'fullname': ['Alice Smith', 'Bob Jones'],
                             'user_name': ['alice', 'bob'], 'user_id': ['1', '2']})
        for exports in (self.first(school, dump), self.second(self.first(school, dump), dump)):
            self.assertEqual(exports['matched.xlsx']['count'], 0)
            review = self.read(exports, 'review')
            self.assertEqual(len(review), 2)
            self.assertTrue(review.mapping_status.str.contains('First name matches but is only 1 character', regex=False).all())
            self.assertEqual(review.mapping_user_id.tolist(), ['', ''])
