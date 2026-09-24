"""Health and existing-student browsing; file workflows use their own router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from Backend.config.dependencies import get_db
from Backend.repositories.user_student_repository import UserStudentRepository
from Backend.schemas.api_response import ApiResponseDTO
from Backend.schemas.student_mapping_student import StudentMappingStudentDTO

router = APIRouter(prefix="/mapping", tags=["Student Mapping"])


@router.get("/health")
async def health():
    return {"success": True, "message": "Mapping API Running"}


@router.get("/students")
async def get_students(cursor: int | None = Query(None, ge=0), limit: int = Query(25, ge=1, le=100),
                       db: Session = Depends(get_db)):
    response = UserStudentRepository(db).get_students(cursor=cursor, limit=limit)
    return ApiResponseDTO.success(
        data=StudentMappingStudentDTO.transform_many(response["data"]),
        pagination=response["pagination"],
    )
