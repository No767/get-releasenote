FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS build

# Compile bytecode and enable caching
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy

# Disable Python downloads as the system Python interpreter instead
ENV UV_PYTHON_DOWNLOADS=0

# Do not install development dependencies
ENV UV_NO_DEV=1

# Do not install default groups
ENV UV_NO_DEFAULT_GROUPS=true


WORKDIR /app/

COPY pyproject.toml uv.lock /app/

# Install dependencies through lockfile
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project
    
# Add project source code
COPY ./src /app

# Install the rest (this allows for optimal caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

FROM python:3.14-slim-trixie

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/releasenote

# Copy the server from the builder
COPY --from=build /app /releasenote

ENV PATH="/releasenote/.venv/bin:$PATH"

ENTRYPOINT ["python3", "/releasenote/main.py"]