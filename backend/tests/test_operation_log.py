"""Persistent operation events are safe, append-only, and restorable."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import uuid4

from app.services import operation_log


class OperationLogTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name) / 'operations.jsonl'
        path = patch.object(operation_log, 'LOG_PATH', target)
        path.start()
        self.addCleanup(path.stop)

    def test_started_and_completed_events_are_append_only_and_restorable(self):
        started = operation_log.operation_for_request(
            'POST', '/api/v1/mapping/admission-mapping/run',
            mapping_session='private-session-cookie', request_id='request-1',
        )
        completed = operation_log.finish_operation(started, 200)

        events = [json.loads(line) for line in operation_log.LOG_PATH.read_text(encoding='utf-8').splitlines()]
        self.assertEqual([event['status'] for event in events], ['started', 'completed'])
        self.assertNotIn('private-session-cookie', operation_log.LOG_PATH.read_text(encoding='utf-8'))
        self.assertEqual(completed['operation_id'], started['operation_id'])
        restored = operation_log.recent_operations('mapping', 'private-session-cookie')[0]
        self.assertEqual(restored['status'], 'completed')
        self.assertEqual(restored['request_id'], 'request-1')
        self.assertNotIn('workspace_id', restored)

    def test_failed_event_uses_safe_generic_message(self):
        started = operation_log.operation_for_request(
            'POST', '/custom-prefix/bulk-reg/convert', bulk_workspace='bulk-cookie',
        )
        failed = operation_log.finish_operation(started, 500)
        self.assertEqual(failed['status'], 'failed')
        self.assertNotIn('500', failed['message'])
        self.assertEqual(operation_log.recent_operations('bulk', 'bulk-cookie')[0]['status'], 'failed')

    def test_read_only_and_untracked_routes_do_not_create_events(self):
        self.assertIsNone(operation_log.operation_for_request(
            'GET', '/api/v1/mapping/session', mapping_session='session',
        ))
        self.assertFalse(operation_log.LOG_PATH.exists())

    def test_recent_operations_returns_ten_newest_final_statuses(self):
        for number in range(12):
            started = operation_log.operation_for_request(
                'POST', '/api/v1/mapping/admission-mapping/run',
                mapping_session='session', request_id=f'request-{number}',
            )
            operation_log.finish_operation(started, 200)
        events = operation_log.recent_operations('mapping', 'session')
        self.assertEqual(len(events), 10)
        self.assertTrue(all(event['status'] == 'completed' for event in events))
        self.assertEqual(events[0]['request_id'], 'request-11')
        self.assertEqual(events[-1]['request_id'], 'request-2')

    def test_client_id_lookup_returns_latest_status_only_for_own_workspace(self):
        client_id = str(uuid4())
        started = operation_log.operation_for_request(
            'POST', '/api/v1/mapping/files/school', mapping_session='session-a',
            client_operation_id=client_id,
        )
        operation_log.finish_operation(started, 200)

        events = operation_log.operations_by_client_id('mapping', 'session-a', [client_id])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['client_operation_id'], client_id)
        self.assertEqual(events[0]['status'], 'completed')
        self.assertEqual(operation_log.operations_by_client_id('mapping', 'session-b', [client_id]), [])
        self.assertEqual(operation_log.operations_by_client_id('bulk', 'session-a', [client_id]), [])

    def test_invalid_or_non_v4_client_id_is_not_persisted(self):
        for value in ('not-a-uuid', '00000000-0000-1000-8000-000000000000'):
            started = operation_log.operation_for_request(
                'POST', '/api/v1/mapping/files/dump', mapping_session='session',
                client_operation_id=value,
            )
            self.assertNotIn('client_operation_id', started)
            operation_log.finish_operation(started, 200)


if __name__ == '__main__':
    unittest.main()
