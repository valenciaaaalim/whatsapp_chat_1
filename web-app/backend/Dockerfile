FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy GLiNER service module
COPY gliner_service.py .

# Copy seed script
COPY seed_data.py .

# Create assets directory if needed
RUN mkdir -p app/assets

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV GLINER_MODEL_NAME=knowledgator/gliner-pii-base-v1.0

# Pre-download GLiNER model and tokenizer so first request doesn't block
RUN python - <<'PY'\nimport os\nfrom gliner import GLiNER\nfrom transformers import AutoTokenizer\nmodel_name = os.environ.get(\"GLINER_MODEL_NAME\", \"knowledgator/gliner-pii-base-v1.0\")\nGLiNER.from_pretrained(model_name)\nAutoTokenizer.from_pretrained(model_name)\nprint(\"Pre-downloaded GLiNER model:\", model_name)\nPY

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
