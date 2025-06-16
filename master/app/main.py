import httpx
from typing import List

from fastapi import FastAPI, Depends, Request, HTTPException
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


@app.post("/api/experiments", response_model=schemas.ExperimentInfo)
async def run_experiment(exp: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    """새로운 실험(작업)을 생성하고 에이전트에게 전달합니다."""
    target_server = db.query(models.Server).filter(models.Server.hostname == exp.server_hostname).first()
    if not target_server:
        raise HTTPException(status_code=404, detail="Server not found")

    # 1. DB에 Experiment 기록 생성
    db_exp = crud.create_experiment(db=db, exp=exp, server_id=target_server.id)

    # 2. Agent에 작업 실행 요청
    agent_url = f"http://{target_server.ip_address}:8001/api/jobs"
    job_payload = {
        "experiment_id": db_exp.id,
        "git_repo": db_exp.git_repo,
        "git_commit": db_exp.git_commit,
        "command": db_exp.command
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(agent_url, json=job_payload, timeout=10)
            response.raise_for_status()
    except httpx.RequestError as e:
        crud.update_experiment_status(db, db_exp.id, 'failed')
        raise HTTPException(status_code=500, detail=f"Could not send job to agent: {e}")

    return db_exp


@app.post("/api/experiments/{exp_id}/status")
def post_experiment_status(exp_id: int, status_update: schemas.StatusUpdate, db: Session = Depends(get_db)):
    """Agent가 실험 상태를 업데이트합니다."""
    return crud.update_experiment_status(db, exp_id, status_update.status)


@app.post("/api/experiments/{exp_id}/log")
def post_experiment_log(exp_id: int, log_update: schemas.LogUpdate, db: Session = Depends(get_db)):
    """Agent가 로그를 추가합니다."""
    return crud.append_log_to_experiment(db, exp_id, log_update.content)


@app.get("/api/experiments", response_model=List[schemas.ExperimentInfo])
def read_all_experiments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """모든 실험 목록을 반환합니다."""
    return crud.get_all_experiments(db, skip=skip, limit=limit)


@app.get("/api/experiments/{exp_id}", response_model=schemas.ExperimentInfo)
def read_experiment_details(exp_id: int, db: Session = Depends(get_db)):
    """특정 실험의 상세 정보를 반환합니다."""
    db_exp = crud.get_experiment(db, exp_id)
    if db_exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return db_exp
