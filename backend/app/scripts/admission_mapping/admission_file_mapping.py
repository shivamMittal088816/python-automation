"""Public entry point for admission mapping imports and direct CLI execution.

Implementation lives in app/services/admission_mapping; the CLI lives in app/scripts/.
"""

# Direct execution starts in this folder; add the project root for package imports.
if not __package__:
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.admission_mapping.admission_file_reader import read_file
from app.services.admission_mapping.admission_mapping_pipeline import map_students
from app.services.admission_mapping.admission_result_exports import build_exports
from app.scripts.admission_mapping_cli import main

__all__ = ["read_file", "map_students", "build_exports", "main"]

if __name__ == "__main__":
    main()
