# Rigor - FastAPI app container (deployable to Alibaba Function Compute / ECS)
FROM python:3.12-slim

WORKDIR /app

# System deps kept minimal; scipy & pymupdf ship manylinux wheels.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rigor/ ./rigor/
COPY web/ ./web/

# API key / endpoint are injected at runtime as env vars (never baked into image).
EXPOSE 8000
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
