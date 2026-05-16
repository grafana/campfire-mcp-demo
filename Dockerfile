FROM python:3.13-slim@sha256:dc1546eefcbe8caaa1f004f16ab76b204b5e1dbd58ff81b899f21cd40541232f

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:29bd45092ea8902c0bbb7f0a338f0494a382b1f4b18355df5be270ade679ff1d /uv /bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py .

EXPOSE 8000

CMD ["uv", "run", "python", "app.py"]