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
