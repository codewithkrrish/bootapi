FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

COPY app ./app

# The database lives here; mount a volume on it in production.
VOLUME ["/app/data"]
ENV BOOTAPI_DATABASE_PATH=/app/data/bootapi.db

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
