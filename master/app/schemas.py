from pydantic import BaseModel
from typing import List
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
    cpu_percent: float
    memory_percent: float
    updated_at: datetime
    gpus: List[GPUInfo] = []

    class Config:
        from_attributes = True
