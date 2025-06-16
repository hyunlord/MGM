from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schemas


def update_server_status(db: Session, status: schemas.ServerStatus):
    # 1. 호스트 이름으로 서버를 찾거나, 없으면 새로 생성합니다.
    server = db.query(models.Server).filter(models.Server.hostname == status.hostname).first()
    if not server:
        server = models.Server(hostname=status.hostname)
        db.add(server)
        # 새 서버인 경우, 바로 commit하여 id를 부여받도록 합니다.
        db.commit()
        db.refresh(server)

    # 2. 서버의 기본 정보를 업데이트합니다.
    server.alias = status.alias
    server.ip_address = status.ip_address
    server.cpu_percent = status.cpu_percent
    server.memory_percent = status.memory_percent

    # 3. GPU 정보를 "Upsert" 로직으로 업데이트합니다.
    for gpu_status in status.gpus:
        # 해당 UUID를 가진 GPU가 DB에 이미 있는지 찾습니다.
        gpu = db.query(models.GPU).filter(models.GPU.uuid == gpu_status.uuid).first()
        if gpu:
            # --- UPDATE: 이미 존재하면 정보만 업데이트 ---
            gpu.temperature = gpu_status.temperature
            gpu.utilization_percent = gpu_status.utilization_percent
            gpu.memory_used = gpu_status.memory_used
            gpu.memory_total = gpu_status.memory_total
        else:
            # --- INSERT: 존재하지 않으면 새로 생성하여 추가 ---
            new_gpu = models.GPU(**gpu_status.dict(), server_id=server.id)
            db.add(new_gpu)

    # 4. 모든 변경사항을 한번에 commit 합니다.
    db.commit()
    db.refresh(server)
    return server


def get_all_servers(db: Session):
    return db.query(models.Server).all()


def create_experiment(db: Session, exp: schemas.ExperimentCreate, server_id: int):
    db_exp = models.Experiment(
        git_repo=exp.git_repo,
        git_commit=exp.git_commit,
        command=exp.command,
        server_id=server_id
    )
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    return db_exp


def update_experiment_status(db: Session, exp_id: int, status: str):
    db_exp = db.query(models.Experiment).filter(models.Experiment.id == exp_id).first()
    if db_exp:
        db_exp.status = status
        if status == 'running':
            db_exp.start_time = datetime.now()
        elif status in ['completed', 'failed']:
            db_exp.end_time = datetime.now()
        db.commit()
    return db_exp


def append_log_to_experiment(db: Session, exp_id: int, log_content: str):
    db_exp = db.query(models.Experiment).filter(models.Experiment.id == exp_id).first()
    if db_exp:
        db_exp.log += log_content
        db.commit()
    return db_exp


def get_experiment(db: Session, exp_id: int):
    return db.query(models.Experiment).filter(models.Experiment.id == exp_id).first()


def get_all_experiments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Experiment).offset(skip).limit(limit).all()
