"""Account registration and sign-in endpoints."""
from app.auth.schemas import Credentials, Registration
from app.auth.services.accounts import register_account, sign_in
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()


@router.post('/register', status_code=201)
def register(payload: Registration, request: Request, response: Response, db: Session = Depends(get_db)):
    return register_account(payload, request, response, db)


@router.post('/login')
def login(payload: Credentials, request: Request, response: Response, db: Session = Depends(get_db)):
    return sign_in(payload, request, response, db)
