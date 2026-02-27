FROM python:3.11-slim@sha256:8ef21a26e7c342e978a68cf2d6b07627885930530064f572f432ea422a8c0907

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:edd1fd89f3e5b005814cc8f777610445d7b7e3ed05361f9ddfae67bebfe8456a /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]