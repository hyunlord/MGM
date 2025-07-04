import ujson
import logging
import asyncio
import threading
import webbrowser
from typing import List, Optional
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.ssh_manager import discover_servers, ssh_mgr
from app.db import init_db, SessionLocal
from app.models import Metric


app = FastAPI(title="Remote MLOps UI Backend")
logger = logging.getLogger("uvicorn.error")

init_db()
with SessionLocal() as db:
    metric = Metric(
        host=host,
        cpu=metrics['cpu'],
        memory=metrics['memory'],
    )
    metric.set_gpus(metrics.get('gpus', []))
    db.add(metric)
    db.commit()


async def collect_metrics():
    while True:
        for host in ssh_mgr.clients.keys():
            try:
                out, _ = ssh_mgr.exec_command(host, "python3 /tmp/collect_metrics.py")
                metrics = ujson.loads(out.strip().splitlines()[0])
                with SessionLocal() as db:
                    db.add(Metric(
                        host=host,
                        cpu=metrics['cpu'],
                        memory=metrics['memory'],
                        gpu0_util=metrics['gpus'][0]['utilization'],
                        gpu0_mem=metrics['gpus'][0]['memory_used'],
                    ))
                    db.commit()
            except Exception as e:
                print(f"[{host}] metric fetch error: {e}")
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(collect_metrics())


class ConnectRequest(BaseModel):
    host: str
    ssh_user: str
    principal: Optional[str] = None
    kinit_password: Optional[str] = None
    key_path: Optional[str] = None
    password: Optional[str] = None

@app.get("/api/servers/{host}/metrics")
async def api_metrics(host: str):
    # 1) SSH 연결 확인
    if host not in ssh_mgr.clients:
        raise HTTPException(400, f"Server '{host}' is not connected")

    # 2) 원격에서 pip 설치 후 메트릭 스크립트 실행
    cmd = r'''
    bash -lc "
source /hanmail/users/rexxa.som/uv/siglip/bin/activate
# 필요 라이브러리 설치 (표준 출력/오류 억제)
uv pip install psutil pynvml ujson

# Python으로 메트릭 수집
python - << 'EOF'
import psutil, ujson

# 기본 메트릭
metrics = {
    'cpu_percent': psutil.cpu_percent(),
    'mem_percent': psutil.virtual_memory().percent,
    'disk': [
        {
            'filesystem': p.device,
            'size':        round(psutil.disk_usage(p.mountpoint).total   /1024/1024/1024),
            'used':        round(psutil.disk_usage(p.mountpoint).used    /1024/1024/1024),
            'avail':       round(psutil.disk_usage(p.mountpoint).free    /1024/1024/1024),
            'use_percent': psutil.disk_usage(p.mountpoint).percent,
            'mountpoint':  p.mountpoint
        }
        for p in psutil.disk_partitions(all=False)
    ],
    'gpus': []
}

# GPU 정보 추가 (pynvml)
try:
    import pynvml
    pynvml.nvmlInit()
    for i in range(pynvml.nvmlDeviceGetCount()):
        h = pynvml.nvmlDeviceGetHandleByIndex(i)
        info = pynvml.nvmlDeviceGetMemoryInfo(h)
        util = pynvml.nvmlDeviceGetUtilizationRates(h)
        metrics['gpus'].append({
            'index': i,
            'memory_used':  info.used  //1024//1024,
            'memory_total': info.total //1024//1024,
            'utilization':  util.gpu
        })
except:
    pass
print(ujson.dumps(metrics))
EOF
"
'''.strip()

    # 3) 커맨드 실행
    out, err = ssh_mgr.exec_command(host, cmd, timeout=20.0)
    if err:
        logger.debug(f"[{host}] remote stderr (ignored):\n{err}")

    txt = out
    import re
    m = re.search(r"(\{.*\})", txt, re.DOTALL)
    if not m:
        logger.error(f"[{host}] JSON not found in stdout:\n{out!r}")
        raise HTTPException(502, "Invalid JSON from remote")
    json_text = m.group(1)

    try:
        data = ujson.loads(json_text)
    except Exception as e:
        logger.exception(f"[{host}] JSON parse error: {e}\n{text}")
        raise HTTPException(502, f"JSON parse error: {e}")

    return JSONResponse(content=data)


@app.get("/api/servers/discover", response_model=List[str])
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


@app.post("/api/servers/connect")
async def api_connect(req: ConnectRequest):
    try:
        ssh_mgr.connect(
            host=req.host,
            ssh_user=req.ssh_user,
            principal=req.principal,
            kinit_password=req.kinit_password,
            key_path=req.key_path,
            password=req.password
        )
        return {"status": "connected", "host": req.host}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    # 1) 에러 세부 정보 로그
    errors = exc.errors()
    logger.error(f"Validation error: {errors}")

    # 2) 클라이언트에 돌려줄 JSON
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": errors})
    )


@app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    logger.error("Unhandled error:", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


app.mount("/", StaticFiles(directory="static", html=True), name="static")


def _open_browser():
    webbrowser.open("http://localhost:8000")


if __name__ == "__main__":
    threading.Timer(1.0, _open_browser).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
