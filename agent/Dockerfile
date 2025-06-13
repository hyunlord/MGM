FROM python:3.11-slim
WORKDIR /usr/src/app
RUN pip install uv
COPY ./master/requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY ./master/ ./
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]