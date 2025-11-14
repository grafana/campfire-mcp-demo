FROM python:3.14-slim@sha256:9813eecff3a08a6ac88aea5b43663c82a931fd9557f6aceaa847f0d8ce738978

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:f6e3549ed287fee0ddde2460a2a74a2d74366f84b04aaa34c1f19fec40da8652 /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]