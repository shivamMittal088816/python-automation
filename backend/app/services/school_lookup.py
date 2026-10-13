"""Shared school lookup error translation for HTTP workflows."""

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.services.bulk_registration import SchoolNotFoundError


def resolve_school(fetcher, school_index):
    try:
        return fetcher(school_index)
    except SchoolNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            503,
            'School verification failed. Check the database connection and try again.',
        ) from exc
