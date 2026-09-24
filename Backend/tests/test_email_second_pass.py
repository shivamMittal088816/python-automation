from io import BytesIO
import unittest
import pandas as pd
from Backend.services.email_mapping.email_file_mapping import map_by_email
from Backend.services.email_mapping.email_second_pass import map_email_second_pass


class EmailSecondPassTests(unittest.TestCase):
    def test_only_review_name_mismatches_are_promoted_and_reruns_are_stable(self):
        school = pd.DataFrame({'email': ['a@x', 'b@x', 'c@x', 'd@x', 'e@x'],
                               'first': ['Wrong', 'Bob', 'Wrong', 'Other', 'Missing'],
                               'name': ['Ann A', 'Bob', 'No match', 'Other school', 'Missing']})
        dump = pd.DataFrame({'user_email': ['a@x', 'b@x', 'c@x', 'd@x'],
                             'user_firstname': ['Ann', 'Bob', 'Different', 'Other'],
                             'fullname': ['a n n a', 'Bob', 'Different', 'Otherschool'],
                             'user_name': ['a', 'b', 'c', 'd'], 'user_id': ['1', '2', '3', '4'],
                             'user_edu_school': ['914', '914', '914', '915']})
        first = map_by_email(school, dump, 'email', 'user_email', 'first', school_index='914')
        self.assertEqual(first['email_review.xlsx']['count'], 3)
        second = map_email_second_pass(first, dump, 'email', 'name', '914')
        self.assertEqual(second['email_matched.xlsx']['count'], 2)
        self.assertEqual(second['email_review.xlsx']['count'], 2)
        self.assertEqual(second['email_not_matched.xlsx']['data'], first['email_not_matched.xlsx']['data'])
        matched = pd.read_excel(BytesIO(second['email_matched.xlsx']['data']))
        self.assertEqual(list(matched['email']), ['b@x', 'a@x'])
        again = map_email_second_pass(second, dump, 'email', 'name', '914')
        self.assertEqual(again['email_matched.xlsx']['count'], 2)
        self.assertEqual(again['email_review.xlsx']['count'], 2)

    def test_duplicate_emails_and_missing_names_stay_in_review(self):
        school = pd.DataFrame({'email': ['a@x', 'a@x', 'b@x'],
                               'first': ['Ann', 'Ann', ''], 'name': ['Ann A', 'Ann A', '']})
        dump = pd.DataFrame({'user_email': ['a@x', 'b@x'], 'user_firstname': ['Ann', 'Bob'],
                             'fullname': ['Anna', ''],
                             'user_name': ['a', 'b'], 'user_id': ['1', '2'], 'user_edu_school': ['914', '914']})
        first = map_by_email(school, dump, 'email', 'user_email', 'first', school_index='914')
        second = map_email_second_pass(first, dump, 'email', 'name', '914')
        self.assertEqual(second['email_matched.xlsx']['count'], 0)
        self.assertEqual(second['email_review.xlsx']['count'], 3)
