import ipaddress
import socket
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

# --- 서버 탐색 (Port 22 open 여부 확인) ---
def is_ssh_open(host: str, port: int = 22, timeout: float = 1.0) -> bool:
    """해당 호스트의 SSH 포트가 열려 있는지 확인."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except:
        return False

def discover_servers(
    subnet: str,
    port: int = 22,
    timeout: float = 1.0,
    max_workers: int = 100
) -> List[str]:
    """
    주어진 subnet (예: '192.168.1.0/24') 내에서
    SSH 포트가 열려 있는 호스트 목록을 반환.
    """
    net = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(ip) for ip in net.hosts()]

    reachable: List[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(is_ssh_open, h, port, timeout): h for h in hosts}
        for fut in as_completed(futures):
            host = futures[fut]
            if fut.result():
                reachable.append(host)
    return reachable


# --- SSH 연결 관리 ---
class SSHManager:
    def __init__(self):
        self.clients: dict[str, paramiko.SSHClient] = {}

    def connect(
        self,
        host: str,
        user: str,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 5.0
    ) -> None:
        """
        host, user, key_path/password 중 하나로 SSH 연결.
        성공 시 internal dict에 저장.
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key_path:
            key = paramiko.RSAKey.from_private_key_file(key_path)
            client.connect(hostname=host, username=user, pkey=key, timeout=timeout)
        else:
            client.connect(hostname=host, username=user, password=password, timeout=timeout)

        self.clients[host] = client

    def disconnect(self, host: str) -> None:
        """저장된 SSH 연결을 종료."""
        client = self.clients.pop(host, None)
        if client:
            client.close()

    def exec_command(self, host: str, cmd: str, timeout: float = 30.0) -> Tuple[str, str]:
        """
        지정된 호스트에 명령 실행.
        stdout, stderr 문자열로 반환.
        """
        client = self.clients.get(host)
        if not client:
            raise RuntimeError(f"Host '{host}' not connected")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        return stdout.read().decode(), stderr.read().decode()


# 싱글톤 형태로 인스턴스 생성
ssh_mgr = SSHManager()
