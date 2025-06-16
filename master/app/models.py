from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    alias = Column(String, unique=True, index=True, nullable=True)

    experiments = relationship("Experiment")

    cpu_percent = Column(Float)
    memory_percent = Column(Float)

    # timezone=True: 시간대 정보를 포함하여 저장
    # server_default: 행이 처음 생성될 때 DB 서버의 현재 시간을 기본값으로 사용
    # onupdate: 행이 업데이트될 때마다 DB 서버의 현재 시간으로 자동 갱신
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    gpus = relationship("GPU", back_populates="server", cascade="all, delete-orphan")


class GPU(Base):
    __tablename__ = "gpus"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    gpu_name = Column(String)
    temperature = Column(Integer)
    utilization_percent = Column(Integer)
    memory_used = Column(Integer)
    memory_total = Column(Integer)
    server_id = Column(Integer, ForeignKey("servers.id"))
    server = relationship("Server", back_populates="gpus")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default='queued')  # 'queued', 'running', 'completed', 'failed'
    git_repo = Column(String, nullable=True)
    git_commit = Column(String, nullable=True)
    command = Column(String)
    log = Column(Text, default='')  # 실시간 로그를 저장할 컬럼
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # 어떤 서버에서 실행되었는지 연결
    server_id = Column(Integer, ForeignKey("servers.id"))
    server = relationship("Server", back_populates="experiments")
