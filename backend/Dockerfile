FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --requirement /app/requirements.txt

COPY backend/alembic.ini /app/alembic.ini
COPY backend/alembic /app/alembic
COPY backend/app /app/app
COPY backend/scripts/run-migrations.sh /app/run-migrations.sh
COPY backend/scripts/create-initial-user.py /app/create-initial-user.py
COPY backend/scripts/validate-config.sh /app/validate-config.sh

RUN chmod 755 /app/run-migrations.sh /app/create-initial-user.py /app/validate-config.sh \
    && useradd --create-home --uid 10001 cloudtask
USER cloudtask
