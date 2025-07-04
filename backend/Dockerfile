# 1) Build stage: React 앱 빌드
FROM node:18-alpine AS frontend-build
WORKDIR /app
RUN mkdir -p /app

# 1-1) package.json 먼저 복사해서 의존성 캐시 활용
COPY ../frontend/package.json ../frontend/package-lock.json ./
RUN npm install

# 1-2) 앱 소스 복사 후 빌드
COPY frontend/ ./
RUN npm run build

# 2) Run stage: FastAPI + 정적 파일 서빙
FROM python:3.10-slim
ENV KRB5CCNAME=/tmp/krb5cc
WORKDIR /app

# 1) 시스템 의존성 (Kerberos, 빌드툴, 그리고 SSH 클라이언트)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      krb5-user \
      libkrb5-dev \
      gcc \
      python3-dev \
      openssh-client && \
    rm -rf /var/lib/apt/lists/*

# 2) krb5.conf 내 default_ccache_name 과 ccache_type 을 파일로 강제
RUN sed -i \
    -e 's|default_ccache_name = .*$|default_ccache_name = FILE:/tmp/krb5cc|' \
    -e 's|ccache_type = .*$|ccache_type = 1|' \
    /etc/krb5.conf

# 2-1) Python 의존성 설치
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2-2) FastAPI 소스 복사
COPY backend/app ./app

# 2-3) React 빌드 결과를 FastAPI 정적 폴더로 복사
COPY --from=frontend-build /app/build ./static

# 2-4) 포트 오픈 및 서버 실행
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
