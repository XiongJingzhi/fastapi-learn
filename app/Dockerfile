FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

WORKDIR /app

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=app/uv.lock,target=uv.lock \
    --mount=type=bind,source=app/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

COPY ./app/scripts /app/scripts
COPY ./app/alembic.ini /app/alembic.ini
COPY ./app/app /app/app

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=app/uv.lock,target=uv.lock \
    --mount=type=bind,source=app/pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

CMD ["bash", "-c", "bash scripts/prestart.sh && fastapi run --workers 2 app/main.py --host 0.0.0.0 --port 8000"]
