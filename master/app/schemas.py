from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class GPUStatus(BaseModel):
    uuid: str
    gpu_name: str
    temperature: int
    utilization_percent: int
    memory_used: int
    memory_total: int


class ServerStatus(BaseModel):
    hostname: str
    ip_address: str
    alias: Optional[str] = None
    cpu_percent: float
    memory_percent: float
    gpus: List[GPUStatus]


class GPUInfo(BaseModel):
    id: int
    gpu_name: str
    temperature: int
    utilization_percent: int
    memory_used: int
    memory_total: int

    class Config:
        from_attributes = True


class ServerInfo(BaseModel):
    id: int
    hostname: str
    ip_address: str
    alias: Optional[str] = None
    cpu_percent: float
    memory_percent: float
    updated_at: datetime
    gpus: List[GPUInfo] = []

    class Config:
        from_attributes = True


# UI -> Master 로 작업 생성을 요청할 때의 데이터 형태
class ExperimentCreate(BaseModel):
    git_repo: Optional[str] = None
    git_commit: Optional[str] = None
    command: str
    server_hostname: str # 어느 서버에서 실행할지 지정


# Agent -> Master 로 로그를 보낼 때의 데이터 형태
class LogUpdate(BaseModel):
    content: str


# Agent -> Master 로 상태를 보낼 때의 데이터 형태
class StatusUpdate(BaseModel):
    status: str


# Master -> UI 로 실험 정보를 보낼 때의 데이터 형태
class ExperimentInfo(BaseModel):
    id: int
    status: str
    git_repo: Optional[str] = None
    git_commit: Optional[str] = None
    command: str
    log: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    server_id: int

    class Config:
        from_attributes = True
