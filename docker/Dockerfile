FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS build

# Compile bytecode and enable caching
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_COMPILE_BYTECODE=1 
ENV UV_LINK_MODE=copy

# Disable Python downloads as the system Python interpreter instead
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app/

COPY requirements.txt /app/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    uv venv && uv pip install -r requirements.txt
    
# Add project source code
COPY ./main.py /app

FROM python:3.14-slim-trixie

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/releasenote

# Copy the server from the builder
COPY --from=build /app /releasenote

RUN chmod +x /releasenote/main.py

ENV PATH="/releasenote/.venv/bin:$PATH"

ENTRYPOINT ["python3", "/releasenote/main.py"]