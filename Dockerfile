FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/models

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

ARG EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
ENV EMBEDDING_MODEL=${EMBEDDING_MODEL}
RUN python -c "import os; from sentence_transformers import SentenceTransformer; \
    SentenceTransformer(os.environ['EMBEDDING_MODEL'])"

COPY knowledge/ ./knowledge/
# COPY ingestion/ ./ingestion/
# RUN python -m ingestion.build_index

COPY . .

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
