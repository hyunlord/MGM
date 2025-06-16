import csv
import asyncio
import os
import httpx
import psutil
import shutil
import tempfile
from pathlib import Path
from pydantic import BaseModel
import subprocess
import socket
from typing import Optional

from fastapi import BackgroundTasks
from fastapi import FastAPI

app = FastAPI()

MASTER_URL = os.getenv("MASTER_URL", "http://localhost:8000")  # 환경 변수에서 마스터 주소 가져오기


class JobRequest(BaseModel):
    experiment_id: int
    git_repo: Optional[str] = None
    git_commit: Optional[str] = None
    command: str


async def run_job_in_background(job: JobRequest):
    """백그라운드에서 실제 작업을 수행하는 함수"""
    exp_id = job.experiment_id
    work_dir = Path(tempfile.mkdtemp(prefix=f"exp_{exp_id}_"))
    print(f"Starting job {exp_id} in {work_dir}")

    async def update_status(status: str):
        async with httpx.AsyncClient() as client:
            await client.post(f"{MASTER_URL}/api/experiments/{exp_id}/status", json={"status": status})

    async def append_log(line: str):
        async with httpx.AsyncClient() as client:
            await client.post(f"{MASTER_URL}/api/experiments/{exp_id}/log", json={"content": line + "\n"})

    try:
        await update_status('running')

        # Git Clone & Checkout
        if job.git_repo:
            await append_log(f"Cloning repository: {job.git_repo}")
            git_clone_proc = await asyncio.create_subprocess_shell(f"git clone {job.git_repo} .", cwd=work_dir)
            await git_clone_proc.wait()

            if job.git_commit:
                await append_log(f"Checking out commit: {job.git_commit}")
                git_checkout_proc = await asyncio.create_subprocess_shell(f"git checkout {job.git_commit}",
                                                                          cwd=work_dir)
                await git_checkout_proc.wait()

        # Command 실행 및 실시간 로그 스트리밍
        await append_log(f"Executing command: {job.command}")
        proc = await asyncio.create_subprocess_shell(
            job.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=work_dir
        )

        while proc.stdout and not proc.stdout.at_eof():
            line = await proc.stdout.readline()
            if not line:
                break
            await append_log(line.decode().strip())

        await proc.wait()

        if proc.returncode == 0:
            await update_status('completed')
        else:
            await update_status('failed')

    except Exception as e:
        await append_log(f"An unexpected error occurred: {str(e)}")
        await update_status('failed')
    finally:
        # 작업 완료 후 임시 폴더 삭제
        shutil.rmtree(work_dir)
        print(f"Finished job {exp_id}, cleaned up {work_dir}")


@app.post("/api/jobs")
async def create_job(job: JobRequest, background_tasks: BackgroundTasks):
    """Master로부터 작업 요청을 받아 백그라운드에서 실행합니다."""
    background_tasks.add_task(run_job_in_background, job)
    return {"message": "Job received and started in background", "experiment_id": job.experiment_id}


def get_hostname():
    return os.getenv("AGENT_HOST_NAME", socket.gethostname())


def get_ip_address():
    # 이 함수는 Docker 내부 IP를 반환할 수 있으므로,
    # 실제 서버 IP가 필요하다면 다른 방법을 고려해야 할 수 있습니다.
    # 현재는 호스트 이름으로 서버를 구분하므로 큰 문제는 없습니다.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 이 IP는 외부로 나가는 경로를 찾기 위한 임시 IP입니다.
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def get_gpu_info():
    """nvidia-smi 명령을 실행하여 GPU 상태를 딕셔너리 리스트로 반환합니다."""
    try:
        # Master의 schemas.GPUStatus 와 필드 이름을 정확히 일치시켜야 함
        query_fields = [
            'uuid', 'name', 'temperature.gpu', 'utilization.gpu',
            'memory.used', 'memory.total'
        ]
        cmd = f'nvidia-smi --query-gpu={",".join(query_fields)} --format=csv,noheader,nounits'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)

        reader = csv.reader(result.stdout.strip().split('\n'))
        gpus = []
        for row in reader:
            # Pydantic 모델(schemas.py)의 필드 이름과 키를 정확히 일치시킵니다.
            gpu_info = {
                'uuid': row[0].strip(),
                'gpu_name': row[1].strip(),  # 'name' -> 'gpu_name'
                'temperature': int(row[2].strip()),
                'utilization_percent': int(row[3].strip()),
                'memory_used': int(row[4].strip()),
                'memory_total': int(row[5].strip())
            }
            gpus.append(gpu_info)
        return gpus
    except Exception as e:
        print(f"Error parsing GPU info: {e}")
        return []


def get_status_payload():
    """Master의 schemas.ServerStatus 형식에 정확히 맞는 딕셔너리를 생성합니다."""
    mem = psutil.virtual_memory()

    # 중첩 구조 없이, 모든 정보를 최상위 레벨에 둡니다.
    payload = {
        "hostname": get_hostname(),
        "ip_address": get_ip_address(),
        "alias": os.getenv("AGENT_ALIAS"),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": mem.percent,
        "gpus": get_gpu_info()
    }
    return payload


async def report_status_periodically():
    """10초마다 마스터 서버로 상태를 보고하는 백그라운드 작업"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                # 수정된 함수를 호출하여 정확한 구조의 데이터를 생성합니다.
                status_payload = get_status_payload()
                print(f"Reporting status for: {status_payload['hostname']}")
                await client.post(f"{MASTER_URL}/api/agents/status", json=status_payload, timeout=5)
            except httpx.RequestError as e:
                print(f"Could not report status to master: {e}")
            except Exception as e:
                print(f"An error occurred during reporting: {e}")

            await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(report_status_periodically())


@app.get("/status")
def get_current_status():
    """Agent의 현재 상태를 즉시 반환하는 엔드포인트"""
    return get_status_payload()
