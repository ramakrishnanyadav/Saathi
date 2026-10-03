FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY api /app/api
COPY docs /app/docs

ENV PYTHONPATH=/app/api
ENV SAATH_DB_PATH=/app/saath.db
ENV OLLAMA_BASE_URL=http://ollama:11434

EXPOSE 8000

CMD ["uvicorn", "saath.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
