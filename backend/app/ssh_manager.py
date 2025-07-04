import os
import subprocess
import paramiko
from concurrent.futures import ThreadPoolExecutor, as_completed
import socket
import ipaddress
from typing import List, Optional, Tuple


def kerberos_kinit(principal: str, password: str):
    # 1) 캐시를 쓸 경로 지정
    ccache = "/tmp/krb5cc"
    # 2) 기존 캐시가 있으면 지워 줍니다
    try:
        os.remove(ccache)
    except FileNotFoundError:
        pass
    # Python 프로세스 전체가 이 캐시를 쓰도록 환경변수 설정
    os.environ["KRB5CCNAME"] = ccache

    # 3) kinit -c <ccache> principal
    proc = subprocess.Popen(
        ["/usr/bin/kinit", "-c", ccache, principal],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = proc.communicate(input=(password + "\n").encode())
    if proc.returncode != 0:
        raise RuntimeError(f"kinit failed: {err.decode().strip()}")


def is_ssh_open(host: str, port: int = 22, timeout: float = 1.0) -> bool:
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
    net = ipaddress.ip_network(subnet, strict=False)
    hosts = [str(ip) for ip in net.hosts()]
    reachable: List[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(is_ssh_open, h, port, timeout): h for h in hosts}
        for fut in as_completed(futures):
            if fut.result():
                reachable.append(futures[fut])
    return reachable


class SSHManager:
    def __init__(self):
        self.clients: dict[str, paramiko.SSHClient] = {}

    def connect(
        self,
        host: str,
        ssh_user: str,
        principal: Optional[str] = None,
        kinit_password: Optional[str] = None,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 5.0
    ) -> None:
        # 1) Kerberos 인증이 필요한 경우
        if principal and not key_path and not password:
            kerberos_kinit(principal, kinit_password)

        # 2) SSH 연결 설정
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # GSSAPI (Kerberos) 인증
        if principal and not key_path and not password:
            client.connect(
                hostname=host,
                username=ssh_user,
                gss_auth=True,
                gss_kex=True,
                timeout=timeout,
            )
        # 키페어 인증
        elif key_path:
            key = paramiko.RSAKey.from_private_key_file(key_path)
            client.connect(
                hostname=host,
                username=ssh_user,
                pkey=key,
                timeout=timeout
            )
        # 비밀번호 인증
        else:
            client.connect(
                hostname=host,
                username=ssh_user,
                password=password,
                timeout=timeout
            )

        self.clients[host] = client

    def disconnect(self, host: str) -> None:
        client = self.clients.pop(host, None)
        if client:
            client.close()

    def exec_command(self, host: str, cmd: str, timeout: float = 30.0) -> Tuple[str, str]:
        client = self.clients.get(host)
        if not client:
            raise RuntimeError(f"Host '{host}' not connected")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        return stdout.read().decode(), stderr.read().decode()


ssh_mgr = SSHManager()
