"""Startup logs report actual connectivity without exposing connection details."""
import unittest
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from Backend.main import check_database_connection, create_app


class StartupLoggingTests(unittest.IsolatedAsyncioTestCase):
    async def test_success_is_logged_after_database_check(self):
        app = create_app()
        with patch('Backend.main.check_database_connection') as check:
            with self.assertLogs('uvicorn.error', level='INFO') as logs:
                async with app.router.lifespan_context(app):
                    check.assert_called_once_with()
        self.assertIn('Checking database connection...', logs.output[0])
        self.assertIn('Database connected successfully.', logs.output[1])

    async def test_database_failure_allows_file_workflows_without_leaking_secrets(self):
        app = create_app()
        error = OperationalError('SELECT 1', {}, Exception('private-password-and-host'))
        with patch('Backend.main.check_database_connection', side_effect=error):
            with self.assertLogs('uvicorn.error', level='INFO') as logs:
                async with app.router.lifespan_context(app):
                    pass
        output = '\n'.join(logs.output)
        self.assertIn('Database connection failed.', output)
        self.assertNotIn('Database connected successfully.', output)
        self.assertNotIn('private-password-and-host', output)

    async def test_connectivity_check_executes_read_only_query_and_closes_connection(self):
        with patch('Backend.main.engine') as engine:
            check_database_connection()
        connection = engine.connect.return_value.__enter__.return_value
        self.assertEqual(str(connection.execute.call_args.args[0]), 'SELECT 1')
        engine.connect.return_value.__exit__.assert_called_once()
