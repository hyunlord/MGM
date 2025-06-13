from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class Server(Base):
    __tablename__ = "servers"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True)
    ip_address = Column(String)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
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
