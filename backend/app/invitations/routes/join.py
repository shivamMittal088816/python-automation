"""Accept invitations without issuing another credential cookie."""
import logging
from app.invitations.schemas import JoinInvitationRequest, JoinInvitationResponse
from app.invitations.services.redemption import redeem_invitation
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.dependencies import get_db

router = APIRouter()
logger = logging.getLogger('uvicorn.error')


@router.post('/join', response_model=JoinInvitationResponse)
def join_invitation(payload: JoinInvitationRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        result = redeem_invitation(db, payload.token, request)
    except SQLAlchemyError:
        logger.exception('Invitation redemption database operation failed')
        raise HTTPException(503, 'Invitations are temporarily unavailable. Please try again shortly.')
    response.headers['Cache-Control'] = 'no-store'
    return result
