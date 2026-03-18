FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .
COPY . .
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" 

