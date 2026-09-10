FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/models \
    CHROMA_PERSIST_DIR=/app/chroma_data

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

ARG EMBEDDING_MODEL
ENV EMBEDDING_MODEL=$EMBEDDING_MODEL
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['EMBEDDING_MODEL'])"

ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COPY knowledge/ ./knowledge/
COPY ingestion/ ./ingestion/

ARG MAX_TOKENS
ENV MAX_TOKENS=$MAX_TOKENS

RUN python -m ingestion.build_index

COPY . .

CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
