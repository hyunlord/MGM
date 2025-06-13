import csv
import asyncio
import os
import httpx
import psutil
import subprocess
import socket
from fastapi import FastAPI

app = FastAPI()

MASTER_URL = os.getenv("MASTER_URL", "http://localhost:8000")  # 환경 변수에서 마스터 주소 가져오기


def get_hostname():
    return socket.gethostname()


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
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
        query_fields = ['name', 'uuid', 'temperature.gpu', 'utilization.gpu', 'memory.total', 'memory.used', 'memory.free']
        cmd = f'nvidia-smi --query-gpu={",".join(query_fields)} --format=csv,noheader,nounits'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        reader = csv.reader(result.stdout.strip().split('\n'))
        gpus = []
        for row in reader:
            row = [item.strip() for item in row]
            gpu_info = dict(zip(query_fields, row))
            gpu_info['temperature.gpu'] = int(gpu_info['temperature.gpu'])
            gpu_info['utilization.gpu'] = int(gpu_info['utilization.gpu'])
            gpu_info['memory.total'] = int(gpu_info['memory.total'])
            gpu_info['memory.used'] = int(gpu_info['memory.used'])
            gpu_info['memory.free'] = int(gpu_info['memory.free'])
            gpus.append(gpu_info)
        return gpus
    except FileNotFoundError:
        return {"error": "nvidia-smi not found"}
    except Exception as e:
        return {"error": str(e)}


def get_system_info():
    """psutil을 사용하여 CPU, Memory, Disk 정보를 딕셔너리로 반환합니다."""
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    mem_total_gb = round(mem.total / (1024**3), 2)
    mem_used_gb = round(mem.used / (1024**3), 2)
    mem_percent = mem.percent
    disk = psutil.disk_usage('/')
    disk_total_gb = round(disk.total / (1024**3), 2)
    disk_used_gb = round(disk.used / (1024**3), 2)
    disk_percent = disk.percent
    return {
        "hostname": get_hostname(),
        "ip_address": get_ip_address(),
        "cpu": {"percent": cpu_percent},
        "memory": {"total_gb": mem_total_gb, "used_gb": mem_used_gb, "percent": mem_percent},
        "disk": {"total_gb": disk_total_gb, "used_gb": disk_used_gb, "percent": disk_percent}
    }


def get_server_status():
    """서버의 전체 상태(시스템 + GPU)를 종합하여 반환합니다."""
    system_info = get_system_info()
    gpu_info = get_gpu_info()

    return {
        "system": system_info,
        "gpus": gpu_info
    }


async def report_status_periodically():
    """10초마다 마스터 서버로 상태를 보고하는 백그라운드 작업"""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                status = get_server_status()
                print(f"Reporting status: {status['system']['hostname']}")
                await client.post(f"{MASTER_URL}/api/agents/status", json=status, timeout=5)
            except httpx.RequestError as e:
                print(f"Could not report status to master: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")
            await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event():
    # FastAPI 앱 시작 시 백그라운드 작업 실행
    asyncio.create_task(report_status_periodically())


@app.get("/status")
def get_current_status():
    """Agent의 현재 상태를 즉시 반환하는 엔드포인트"""
    return get_server_status()
