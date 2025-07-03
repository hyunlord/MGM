import os
from pathlib import Path
import ujson

root = Path(__file__).parent.parent


def make_dirs(dirs):
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

make_dirs([
    'backend/app',
    'frontend/public',
    'frontend/src/components',
])


servers = [
    {"id": 1, "name": "server-A", "host": "1.2.3.4", "user": "ubuntu", "key_path": "~/.ssh/id_rsa"},
]

with open(root / 'backend/servers.json', 'w') as f:
    ujson.dump(servers, f, indent=2)

print("프로젝트 기본 구조가 생성되었습니다.")
