import unittest
from contextlib import contextmanager
from unittest.mock import patch

import pandas as pd
from fastapi import HTTPException

from app.routes.file_workflow_routes import email_mapping
from app.schemas.file_workflow import EmailInput


class EmailSourceSelectionTests(unittest.TestCase):
    def state(self, with_admission=False):
        state = {
            'saved_admission_school': {'name': 'school.csv', 'data': b'email,first\na@x.com,A\n'},
            'admission_settings': {'workspace_school_index': '25'},
        }
        if with_admission:
            state['admission_exports'] = {
                'not_matched.xlsx': {'data': b'admission workbook', 'count': 1},
            }
        return state

    @staticmethod
    def workspace_for(state):
        @contextmanager
        def workspace(_session_id, **_kwargs):
            yield state
        return workspace

    def test_admission_source_requires_admission_mapping(self):
        state = self.state()
        payload = EmailInput(source='admission_not_matched', email_column='email', name_column='first')
        with patch.object(email_mapping, 'workspace', self.workspace_for(state)):
            with self.assertRaises(HTTPException) as raised:
                email_mapping.email_map('session', 0, payload)
        self.assertEqual(raised.exception.status_code, 422)
        self.assertIn('Run Admission mapping first', raised.exception.detail)

    def test_admission_source_maps_the_not_matched_workbook(self):
        state = self.state(with_admission=True)
        admission_rows = pd.DataFrame({'email': ['not-matched@x.com'], 'first': ['Nina']})
        dump = pd.DataFrame({'user_email': ['not-matched@x.com']})
        exports = {'email_matched.xlsx': {'data': b'result', 'count': 1}}
        payload = EmailInput(source='admission_not_matched', email_column='email', name_column='first')
        with patch.object(email_mapping, 'workspace', self.workspace_for(state)), \
                patch.object(email_mapping, 'read_snapshot', return_value=admission_rows) as read, \
                patch.object(email_mapping, 'fetch_email_dump', return_value=dump), \
                patch.object(email_mapping, 'map_by_email', return_value=exports) as mapper, \
                patch.object(email_mapping, 'summary', return_value={'ok': True}):
            self.assertEqual(email_mapping.email_map('session', 0, payload), {'ok': True})
        self.assertEqual(read.call_args.args[0]['name'], 'not_matched.xlsx')
        self.assertIs(mapper.call_args.args[0], admission_rows)
        self.assertEqual(state['admission_settings']['email_input_source'], 'admission_not_matched')
        self.assertEqual(state['email_result_signature'][1], 'admission_not_matched')

    def test_school_source_remains_independent(self):
        state = self.state()
        school_rows = pd.DataFrame({'email': ['school@x.com'], 'first': ['Sam']})
        payload = EmailInput(email_column='email', name_column='first')
        with patch.object(email_mapping, 'workspace', self.workspace_for(state)), \
                patch.object(email_mapping, 'read_snapshot', return_value=school_rows), \
                patch.object(email_mapping, 'fetch_email_dump', return_value=pd.DataFrame()), \
                patch.object(email_mapping, 'map_by_email', return_value={}), \
                patch.object(email_mapping, 'summary', return_value={'ok': True}):
            email_mapping.email_map('session', 0, payload)
        self.assertEqual(state['admission_settings']['email_input_source'], 'school_file')


if __name__ == '__main__':
    unittest.main()
