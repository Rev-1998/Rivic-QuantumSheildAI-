# Directory: project_root/docker-compose.yml
version: '3.8'

services:
  quantumshield_core:
    build:
      context: .
      dockerfile: docker/quantumshield/Dockerfile
    volumes:
      - ./quantumshield:/app/quantumshield
      - ./data:/app/data
    env_file: .env
    ports:
      - "8080:8080"
    depends_on:
      - quantum_redis
      - quantum_db
      - quantum_metrics
    networks:
      - quantum_net

  quantum_redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - quantum_redis_data:/data
    networks:
      - quantum_net

  quantum_db:
    image: postgres:13-alpine
    env_file: .env
    ports:
      - "5432:5432"
    volumes:
      - quantum_db_data:/var/lib/postgresql/data
    networks:
      - quantum_net

  quantum_metrics:
    image: prom/prometheus
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - quantum_metrics_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - quantum_net

  quantum_dashboard:
    image: grafana/grafana
    volumes:
      - ./docker/grafana/provisioning:/etc/grafana/provisioning
      - quantum_dashboard_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - quantum_metrics
    networks:
      - quantum_net

networks:
  quantum_net:
    driver: bridge

volumes:
  quantum_redis_data:
  quantum_db_data:
  quantum_metrics_data:
  quantum_dashboard_data:

---
# Directory: project_root/docker/quantumshield/Dockerfile
FROM python:3.11-slim

LABEL maintainer="QuantumShieldAI Team"
LABEL description="QuantumShieldAI - Advanced Quantum-Safe Security System"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY quantumshield/ quantumshield/
COPY alembic/ alembic/
COPY alembic.ini .

# Create necessary directories
RUN mkdir -p data/logs data/models

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run with uvicorn
CMD ["uvicorn", "quantumshield.main:app", "--host", "0.0.0.0", "--port", "8080"]

---
# Directory: project_root/quantumshield/main.py
from fastapi import FastAPI
from quantumshield.core.quantum_shield import QuantumShieldAI
from quantumshield.api.routes import router as api_router
from quantumshield.core.config import Settings
from quantumshield.core.logging import setup_logging
from quantumshield.db.session import engine
from quantumshield.db import models

app = FastAPI(
    title="QuantumShieldAI",
    description="Next-Generation Quantum-Safe Security System",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    setup_logging()
    models.Base.metadata.create_all(bind=engine)
    app.state.quantum_shield = QuantumShieldAI()
    await app.state.quantum_shield.start()

app.include_router(api_router)

---
# Directory: project_root/.env.example
ENVIRONMENT=production
LOG_LEVEL=INFO
POSTGRES_USER=quantumshield
POSTGRES_PASSWORD=quantum_secure_password
POSTGRES_DB=quantumshield_events
DATABASE_URL=postgresql://quantumshield:quantum_secure_password@quantum_db:5432/quantumshield_events
REDIS_URL=redis://quantum_redis:6379/0
SECRET_KEY=your-quantum-secure-key-here
