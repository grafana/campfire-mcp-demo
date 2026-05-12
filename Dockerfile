FROM python:3.11-slim@sha256:8ef21a26e7c342e978a68cf2d6b07627885930530064f572f432ea422a8c0907

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:1025398289b62de8269e70c45b91ffa37c373f38118d7da036fb8bb8efc85d97 /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]