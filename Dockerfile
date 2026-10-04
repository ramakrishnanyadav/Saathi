# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: Final Runtime Image
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code & built frontend static dist
COPY api /app/api
COPY docs /app/docs
COPY --from=frontend-builder /app/web/dist /app/web/dist

ENV PYTHONPATH=/app/api
ENV SAATH_DB_PATH=:memory:
ENV SAATH_DEMO=1
ENV SAATH_FORECASTER=heuristic

EXPOSE 8000

CMD ["sh", "-c", "PYTHONPATH=api uvicorn saath.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
