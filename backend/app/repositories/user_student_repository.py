# Read existing users for the student browsing API.

from app.queries import load_query


STUDENTS_PAGE_QUERY = load_query('students_page.sql')


# Query existing user/student records for API consumers.
class UserStudentRepository:

    # Keep the injected collaborators on this instance so methods can reuse them.
    def __init__(
        self,
        db
    ):
        self.db = db

    # =====================================
    # GET STUDENTS
    # =====================================

    # Use the request database session to retrieve a page of existing students.
    def get_students(
        self,
        cursor: int | None = None,
        limit: int = 25
    ):
        params = {
            "cursor": cursor if cursor else None,
            "limit": limit,
        }

        result = self.db.execute(
            STUDENTS_PAGE_QUERY,
            params
        )

        rows = [
            dict(row)
            for row in result.mappings().all()
        ]


        next_cursor = None

        if rows:
            next_cursor = rows[-1][
                "user_id"
            ]

        return {
            "data": rows,
            "pagination": {
                "limit": limit,
                "next_cursor": (
                    next_cursor
                )
            }
        }

# Purpose: Reads paginated student records from the existing users table.
# Its public interface includes UserStudentRepository.
# It isolates SQL and database access from services and route handlers.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.student_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
