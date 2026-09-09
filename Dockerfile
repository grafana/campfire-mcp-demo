FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:eb2843a1e56fd9e30c7276ce1a52cba86e64c7b385f5e3279a0e08e02dd058fc /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]