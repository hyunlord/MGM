import ujson
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Metric(Base):
    __tablename__ = 'metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu = Column(Float)
    memory = Column(Float)
    gpus_json = Column(Text)

    def set_gpus(self, gpus: list[dict]):
        self.gpus_json = ujson.dumps(gpus)

    def get_gpus(self) -> list[dict]:
        return ujson.loads(self.gpus_json or "[]")
