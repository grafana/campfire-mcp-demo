FROM python:3.11-slim@sha256:fa9b525a0be0c5ae5e6f2209f4be6fdc5a15a36fed0222144d98ac0d08f876d4

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]