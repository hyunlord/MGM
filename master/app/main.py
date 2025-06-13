from typing import List

from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine) # DB 테이블 생성

app = FastAPI()


@app.post("/api/agents/status", response_model=schemas.ServerInfo)
def receive_agent_status(status: schemas.ServerStatus, db: Session = Depends(get_db)):
    """Agent로부터 상태 정보를 받아 DB에 업데이트"""
    return crud.update_server_status(db=db, status=status)


@app.get("/api/servers", response_model=List[schemas.ServerInfo])
def get_servers_status(db: Session = Depends(get_db)):
    """모든 서버의 현재 상태를 반환"""
    return crud.get_all_servers(db=db)


@app.get("/")
def read_root():
    return {"message": "GPU Server Manager is running!"}