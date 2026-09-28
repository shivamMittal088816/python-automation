# Build the common API response envelope: success flag, message, data and optional pagination.

class ApiResponseDTO:

    # Build a success response, adding pagination only when provided.
    @staticmethod
    def success(
        data=None,
        message="Success",
        pagination=None
    ):
        response = {
            "success": True,
            "message": message,
            "data": data
        }

        if pagination:
            response[
                "pagination"
            ] = pagination

        return response

# Purpose: Defines the common API response data-transfer object.
# Its public interface includes ApiResponseDTO.
# It documents and validates data crossing the HTTP boundary.
# Callers receive focused behavior without duplicating this module's implementation details.
# Keeping this responsibility isolated makes changes easier to test and review.
# Used by: app.routes.student_mapping.
# Those callers use its public interface instead of reproducing its logic.
# Tests and higher-level workflows exercise this behavior through its public callers.
