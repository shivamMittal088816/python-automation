import unittest
from contextlib import nullcontext
from unittest.mock import patch

from fastapi import HTTPException
from app.routes.file_workflow_routes.file_inputs import clear_file


class ClearMappingFileTests(unittest.TestCase):
    def test_clear_source_invalidates_results_and_preserves_other_file(self):
        for kind, removed, retained in [('school', 'saved_admission_school', 'saved_admission_dump'),
                                         ('dump', 'saved_admission_dump', 'saved_admission_school')]:
            state = {key: {'data': b'input'} for key in ('saved_admission_school', 'saved_admission_dump', 'saved_email_dump')}
            state.update({key: {'result': 1} for key in ('admission_exports', 'email_exports', 'full_name_class_exports')})
            with patch('app.routes.file_workflow_routes.file_inputs.workspace', return_value=nullcontext(state)) as workspace, patch('app.routes.file_workflow_routes.file_inputs.summary', return_value={}):
                clear_file('session', 5, kind)
                workspace.assert_called_once_with('session', expected_revision=5)
            self.assertNotIn(removed, state)
            self.assertIn(retained, state)
            for key in ('saved_email_dump', 'admission_exports', 'email_exports', 'full_name_class_exports'):
                self.assertNotIn(key, state)

    def test_clear_email_dump_preserves_admission(self):
        state = {'saved_email_dump': {}, 'admission_exports': {'matched': 1}, 'email_exports': {}, 'full_name_class_exports': {}}
        with patch('app.routes.file_workflow_routes.file_inputs.workspace', return_value=nullcontext(state)), patch('app.routes.file_workflow_routes.file_inputs.summary', return_value={}):
            clear_file('session', 1, 'email_dump')
        self.assertEqual(state, {'admission_exports': {'matched': 1}})

    def test_unknown_file_rejected(self):
        with self.assertRaises(HTTPException):
            clear_file('session', 1, 'unknown')
