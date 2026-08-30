FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/models \
    CHROMA_PERSIST_DIR=/app/chroma_data

ARG EMBEDDING_MODEL
ARG MAX_TOKENS
ENV EMBEDDING_MODEL=$EMBEDDING_MODEL \
    MAX_TOKENS=$MAX_TOKENS

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model into the image
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['EMBEDDING_MODEL'])"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY knowledge/ ./knowledge/
COPY ingestion/ ./ingestion/
RUN python -m ingestion.build_index

COPY . .

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
