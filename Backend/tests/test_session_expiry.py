import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from Backend.api import file_workflow_state as sessions


class SessionExpiryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / ".tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "workflow_sessions"
        replacement = patch.object(sessions, "ROOT", self.root)
        replacement.start()
        self.addCleanup(replacement.stop)

    def age(self, session_id, seconds):
        timestamp = time.time() - seconds
        os.utime(self.root / session_id / "state.json", (timestamp, timestamp))

    def test_expired_session_is_deleted_when_accessed(self):
        session_id = sessions.create_session()
        folder = self.root / session_id
        self.age(session_id, sessions.SESSION_TTL_SECONDS + 1)

        with self.assertRaises(HTTPException) as error:
            with sessions.workspace(session_id):
                pass

        self.assertEqual(error.exception.status_code, 404)
        self.assertIn("expired", error.exception.detail.lower())
        self.assertFalse(folder.exists())

    def test_new_session_removes_expired_folders_only(self):
        expired = sessions.create_session()
        active = sessions.create_session()
        self.age(expired, sessions.SESSION_TTL_SECONDS + 1)
        self.age(active, sessions.SESSION_TTL_SECONDS - 60)

        sessions.create_session()

        self.assertFalse((self.root / expired).exists())
        self.assertTrue((self.root / active).exists())

    def test_read_only_access_refreshes_activity(self):
        session_id = sessions.create_session()
        self.age(session_id, sessions.SESSION_TTL_SECONDS - 60)
        before = (self.root / session_id / "state.json").stat().st_mtime

        with sessions.workspace(session_id, persist=False):
            pass

        self.assertGreater((self.root / session_id / "state.json").stat().st_mtime, before)

    def test_corrupt_manifest_returns_recoverable_conflict(self):
        session_id = sessions.create_session()
        (self.root / session_id / "state.json").write_text("{not-json", encoding="utf-8")

        with self.assertRaises(HTTPException) as error:
            with sessions.workspace(session_id):
                pass

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("new session", error.exception.detail.lower())

    def test_invalid_snapshot_reference_returns_conflict(self):
        session_id = sessions.create_session()
        manifest = self.root / session_id / "state.json"
        manifest.write_text(
            '{"admission_settings": {}, "saved_admission_school": {"file": "missing.bin"}}',
            encoding="utf-8",
        )

        with self.assertRaises(HTTPException) as error:
            with sessions.workspace(session_id):
                pass

        self.assertEqual(error.exception.status_code, 409)
        self.assertIn("reference", error.exception.detail.lower())


if __name__ == "__main__":
    unittest.main()
