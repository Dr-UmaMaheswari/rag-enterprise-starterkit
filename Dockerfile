FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .

COPY src /app/src
COPY samples /app/samples

EXPOSE 8000
CMD ["uvicorn", "rag_starterkit.main:app", "--host", "0.0.0.0", "--port", "8000"]
