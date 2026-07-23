FROM python:3.12-slim AS builder

# gcc + libvips-dev: solo hacen falta para compilar el binding cffi de
# pyvips al instalar (ADR-001); no viajan a la imagen final.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libvips-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS base

# libvips42: solo la librería en tiempo de ejecución (RF-R1-14/15).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libvips42 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system bitacora && useradd --system --gid bitacora --create-home bitacora

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN mkdir -p /app/media && chown bitacora:bitacora /app/media

USER bitacora
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
