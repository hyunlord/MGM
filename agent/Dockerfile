FROM python:3.11-slim

# 빌드 시 사용할 프록시 변수를 선언 (docker-compose로부터 받음)
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY

# 컨테이너 환경 변수로 설정
ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV NO_PROXY=$NO_PROXY

WORKDIR /usr/src/app
RUN pip install --proxy $HTTP_PROXY uv
COPY ./agent/requirements.txt ./

# uv pip install 실행 시 프록시 설정을 사용하게 됨
RUN uv pip install --system -r requirements.txt

COPY ./agent/agent.py ./
EXPOSE 8001
CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8001"]