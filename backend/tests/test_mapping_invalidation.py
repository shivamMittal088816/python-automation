import unittest

from app.api.file_workflow_invalidation import (
    clear_all_mappings,
    clear_class_mapping,
    clear_email_and_class_mapping,
)


class MappingInvalidationTests(unittest.TestCase):
    def state(self):
        return {
            'admission_exports': {'matched.xlsx': {}},
            'admission_signature': ('admission',),
            'saved_email_dump': {'data': b'email'},
            'email_exports': {'email_matched.xlsx': {}},
            'email_result_signature': ('email',),
            'email_source_signature': 'school',
            'full_name_class_exports': {'full_name_class_matched.xlsx': {}},
            'full_name_class_result_signature': ('class',),
        }

    def test_email_rerun_clears_only_class_mapping(self):
        state = self.state()
        clear_class_mapping(state)
        self.assertIn('admission_exports', state)
        self.assertIn('email_exports', state)
        self.assertNotIn('full_name_class_exports', state)

    def test_admission_rerun_clears_email_and_class(self):
        state = self.state()
        clear_email_and_class_mapping(state)
        self.assertIn('admission_exports', state)
        self.assertNotIn('email_exports', state)
        self.assertNotIn('saved_email_dump', state)
        self.assertNotIn('full_name_class_exports', state)

    def test_input_change_clears_every_mapping(self):
        state = self.state()
        clear_all_mappings(state)
        self.assertNotIn('admission_exports', state)
        self.assertNotIn('email_exports', state)
        self.assertNotIn('full_name_class_exports', state)


if __name__ == '__main__':
    unittest.main()
