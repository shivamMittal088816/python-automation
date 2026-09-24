"""Generic disk-backed file snapshots shared by mapping services and the frontend."""

from collections.abc import Mapping
from pathlib import Path
import re
import tempfile
from threading import Lock


# Expose a persisted snapshot as metadata plus lazily loaded file bytes.
class StoredFile(Mapping):
    # Initialize the snapshot metadata and its backing file.
    def __init__(self, path, metadata):
        self.path = Path(path)
        self.metadata = metadata

    # Read bytes on demand for data; return metadata for other keys.
    def __getitem__(self, key):
        return self.path.read_bytes() if key == "data" else self.metadata[key]

    # Expose the metadata keys and the virtual data entry.
    def __iter__(self):
        return iter((*self.metadata, "data"))

    # Count metadata entries plus the virtual data entry.
    def __len__(self):
        return len(self.metadata) + 1


class SessionFile(Mapping):
    """Keep metadata in memory and load file bytes only when requested.

    The temporary file is owned by this snapshot. Python closes it when the
    snapshot is released. A sanitized label and unique suffix identify the file
    without allowing user-supplied paths outside the temporary folder.
    """

    # Initialize the snapshot metadata and its backing file.
    def __init__(self, snapshot, filename=None):
        self._metadata = {key: value for key, value in snapshot.items() if key != "data"}
        folder = Path(__file__).resolve().parents[2] / "storage" / "temp" / "session_files"
        folder.mkdir(parents=True, exist_ok=True)
        self._storage_label = filename or snapshot.get("name", "session_file.bin")
        label = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", self._storage_label).strip(" .")
        suffix = Path(label).suffix
        prefix = Path(label).stem[:120] or "session_file"
        self._file = tempfile.NamedTemporaryFile(
            mode="w+b", dir=folder, prefix=f"{prefix}__", suffix=suffix,
            delete_on_close=False,
        )
        self._lock = Lock()
        try:
            self._file.write(snapshot["data"])
            self._file.flush()
        except Exception:
            self._file.close()
            raise

    # Read bytes on demand for data; return metadata for other keys.
    def __getitem__(self, key):
        if key == "data":
            with self._lock:
                self._file.seek(0)
                return self._file.read()
        return self._metadata[key]

    # Expose the metadata keys and the virtual data entry.
    def __iter__(self):
        return iter((*self._metadata, "data"))

    # Count metadata entries plus the virtual data entry.
    def __len__(self):
        return len(self._metadata) + 1


# Reuse disk-backed snapshots where possible; otherwise offload bytes to a temporary file.
def store_file(snapshot, filename=None):
    if isinstance(snapshot, StoredFile):
        return snapshot
    label = filename or snapshot.get("name", "session_file.bin")
    if isinstance(snapshot, SessionFile) and getattr(snapshot, "_storage_label", None) == label:
        return snapshot
    return SessionFile(snapshot, label)


# Wrap each workbook as a disk-backed snapshot using its export filename.
def store_exports(exports):
    return {name: store_file(snapshot, name) for name, snapshot in exports.items()}
