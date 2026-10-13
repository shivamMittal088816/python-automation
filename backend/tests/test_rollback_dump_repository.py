import unittest
from unittest.mock import MagicMock, patch

from app.repositories.rollback_dump_repository import ROLLBACK_DUMP_QUERY, fetch_rollback_dump


class RollbackDumpRepositoryTests(unittest.TestCase):
    def test_query_is_parameterized_and_uses_required_filters(self):
        query = str(ROLLBACK_DUMP_QUERY)
        self.assertIn('u.user_edu_school = :school_index', query)
        self.assertIn("u.user_type = '0'", query)
        self.assertIn("u.user_package = '14'", query)
        self.assertNotIn("u.user_edu_school = '399'", query)

    def test_fetch_binds_verified_school_and_normalizes_values(self):
        result = MagicMock()
        result.keys.return_value = ['user_id', 'admission_number']
        result.__iter__.return_value = iter([(1, '0007'), (2, None)])
        connection = MagicMock()
        connection.execution_options.return_value.execute.return_value = result
        engine = MagicMock()
        engine.connect.return_value.__enter__.return_value = connection

        with patch('app.config.database.engine', engine):
            dump = fetch_rollback_dump('399')

        self.assertEqual(dump, {
            'columns': ['user_id', 'admission_number'],
            'rows': [['1', '0007'], ['2', '']],
        })
        execute = connection.execution_options.return_value.execute
        self.assertEqual(execute.call_args.args[1], {'school_index': '399'})


if __name__ == '__main__':
    unittest.main()
