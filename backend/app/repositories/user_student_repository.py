# Read existing users for the student browsing API.

from sqlalchemy import text


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
        query = """
            SELECT
                user_id,
                user_firstname,
                user_lastname,
                user_email,
                user_edu_class,
                user_package
            FROM users
        """

        conditions = []

        params = {
            "limit": limit
        }

        if cursor:

            conditions.append(
                "user_id > :cursor"
            )

            params["cursor"] = cursor

        if conditions:

            query += (
                " WHERE "
                + " AND ".join(conditions)
            )

        query += """
            ORDER BY user_id ASC
            LIMIT :limit
        """

        result = self.db.execute(
            text(query),
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
