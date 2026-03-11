FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip build \
    && python -m build --wheel --outdir /dist


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system acunetix \
    && useradd --system --gid acunetix --create-home --home-dir /home/acunetix acunetix

COPY --from=builder /dist/*.whl /tmp/

RUN python -m pip install --no-cache-dir /tmp/*.whl \
    && rm -f /tmp/*.whl

USER acunetix

EXPOSE 3000

ENTRYPOINT ["acunetix-mcp-server"]
CMD ["serve"]
