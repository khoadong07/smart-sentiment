FROM python:3.11-slim

RUN pip install --no-cache-dir fastapi[all] gunicorn uvicorn

WORKDIR /app
COPY . /app

CMD ["gunicorn", "server:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "60"]
