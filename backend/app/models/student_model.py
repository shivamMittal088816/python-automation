# SQLAlchemy definition of the students table. Existing-user matching queries users/paid_users separately.

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.config.database import Base

# Represent the student table as SQLAlchemy-mapped attributes.
class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    first_name: Mapped[str] = mapped_column(String(255))

    last_name: Mapped[str] = mapped_column(String(255))

    full_name: Mapped[str] = mapped_column(String(255))

    class_name: Mapped[str] = mapped_column(String(100))

    package: Mapped[str] = mapped_column(String(100))

    year: Mapped[str] = mapped_column(String(20))

# Purpose: Defines the application-owned students SQLAlchemy table mapping.
# Its public interface includes Student.
# It represents persistence structure rather than API transport validation.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.scripts.init_db.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
