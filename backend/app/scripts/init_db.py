# Create missing ORM tables in the configured database.
# Model imports register tables on Base.metadata; running this file performs database writes.

from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config.database import Base
from app.config.database import engine

from app.models import Student, WorkflowInvitation, WorkflowMember

Base.metadata.create_all(bind=engine)

print("Tables created")

# Purpose: Creates missing application-owned ORM tables in the configured database.
# It primarily establishes package exports, constants, or module-level configuration.
# It supports explicit command-line or maintenance execution outside HTTP requests.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: developers or the application server invoke this module as an entry point.
# It is intentionally callable without requiring another backend module to import it.
# Tests and higher-level workflows exercise this behavior through its public callers.
