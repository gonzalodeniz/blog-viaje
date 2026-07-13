FROM python:3.12-slim AS base

RUN groupadd --system bitacora && useradd --system --gid bitacora --create-home bitacora

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir .

USER bitacora
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
