FROM python:3.12-slim

SHELL ["sh", "-exc"]

# COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    PIP_ROOT_USER_ACTION=ignore

#    UV_PROJECT_ENVIRONMENT=/app

COPY . .

RUN <<EOT
  pip install --no-cache-dir uv
  uv venv
  # uv python pin 3.12
  uv sync --no-dev --no-install-project
EOT

EXPOSE 8787

CMD uv run python -m deeplx_pool.fastapi_app