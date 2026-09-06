FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

RUN addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 -ingroup appuser appuser
WORKDIR /app

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY --chown=appuser:appuser . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

RUN chmod +x run.sh

USER appuser

ENV HOME=/app
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["./run.sh"]