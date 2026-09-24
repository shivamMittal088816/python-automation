# Create missing ORM tables in the configured database.
# Model imports register tables on Base.metadata; running this file performs database writes.

from pathlib import Path
import sys

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from Backend.config.database import Base
from Backend.config.database import engine

from Backend.models.student_model import Student

Base.metadata.create_all(bind=engine)

print("Tables created")
