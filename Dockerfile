FROM python:3.12-slim

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV FASTSURVEY_DB=/data/fastsurvey.sqlite
ENV FASTSURVEY_PORT=5019
EXPOSE 5019

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:5019/healthz || exit 1

CMD ["python", "web_app.py"]
