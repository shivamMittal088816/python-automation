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