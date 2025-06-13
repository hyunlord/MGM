from sqlalchemy.orm import Session
from . import models, schemas


def update_server_status(db: Session, status: schemas.ServerStatus):
    # 서버가 이미 존재하는지 확인, 없으면 새로 생성
    server = db.query(models.Server).filter(models.Server.hostname == status.hostname).first()
    if not server:
        server = models.Server(hostname=status.hostname)
        db.add(server)

    # 서버 정보 업데이트
    server.ip_address = status.ip_address
    server.cpu_percent = status.cpu_percent
    server.memory_percent = status.memory_percent

    # GPU 정보 업데이트 (기존 GPU 정보는 삭제 후 새로 추가)
    server.gpus = []
    for gpu_status in status.gpus:
        gpu = models.GPU(**gpu_status.dict(), server=server)
        server.gpus.append(gpu)

    db.commit()
    db.refresh(server)
    return server


def get_all_servers(db: Session):
    return db.query(models.Server).all()