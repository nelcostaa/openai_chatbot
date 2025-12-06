from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.message import Message

router = APIRouter()


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str

    class Config:
        orm_mode = True  # Pydantic v1


@router.post("/", response_model=MessageResponse)
def create_message(msg: MessageCreate, db: Session = Depends(get_db)):
    db_msg = Message(role=msg.role, content=msg.content)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg


@router.get("/")
def read_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Message).offset(skip).limit(limit).all()
