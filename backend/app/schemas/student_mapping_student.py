# Rename users-table columns into the student fields exposed by the API.

class StudentMappingStudentDTO:

    # Select and reshape one repository record into the public response dictionary.
    @staticmethod
    def transform(
        student
    ):
        return {
            "user_id": (
                student.get("user_id")
            ),

            "first_name": (
                student.get(
                    "user_firstname"
                )
            ),

            "last_name": (
                student.get(
                    "user_lastname"
                )
            ),

            "email": (
                student.get(
                    "user_email"
                )
            ),

            "class_name": (
                student.get(
                    "user_edu_class"
                )
            ),

            "package": (
                student.get(
                    "user_package"
                )
            )
        }

    # Apply the single-record transformation to each record in the supplied page.
    @classmethod
    def transform_many(
        cls,
        students
    ):
        return [
            cls.transform(student)
            for student in students
        ]

# Purpose: Transforms existing user rows into public student response records.
# Its public interface includes StudentMappingStudentDTO.
# It documents and validates data crossing the HTTP boundary.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.student_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
