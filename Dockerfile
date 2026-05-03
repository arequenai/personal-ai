FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY server ./server

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "server.main"]
