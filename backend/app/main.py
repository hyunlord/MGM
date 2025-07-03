# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from app.ssh_manager import discover_servers, ssh_mgr

app = FastAPI(title="Remote MLOps UI Backend")

class ConnectRequest(BaseModel):
    host: str
    user: str
    key_path: Optional[str] = None
    password: Optional[str] = None

@app.get("/servers/discover", response_model=List[str])
async def api_discover(
    subnet: str = Query(..., description="CIDR, 예: '192.168.1.0/24'"),
    port: int = Query(22),
    timeout: float = Query(1.0),
    max_workers: int = Query(100)
):
    try:
        return discover_servers(subnet, port, timeout, max_workers)
    except Exception as e:
        raise HTTPException(500, f"Discovery error: {e}")

@app.post("/servers/connect")
async def api_connect(req: ConnectRequest):
    try:
        ssh_mgr.connect(
            host=req.host,
            user=req.user,
            key_path=req.key_path,
            password=req.password
        )
        return {"status": "connected", "host": req.host}
    except Exception as e:
        raise HTTPException(500, f"SSH connect failed: {e}")
