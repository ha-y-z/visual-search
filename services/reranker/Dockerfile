FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Standard PyPI torch wheels for linux bundle their own CUDA runtime, so no
# system CUDA toolkit is required to install them; this base image is used
# because torch.cuda.is_available() needs the NVIDIA driver's libcuda,
# which is injected at `docker run --gpus` time via the container toolkit.
# On a plain CPU host the same image runs fine with cuda.is_available()==False.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    HF_HOME=/root/.cache/huggingface \
    PATH=/app/.venv/bin:$PATH

RUN uv python install 3.13

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY README.md ./
COPY app ./app
RUN uv sync --no-dev

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=5 \
    CMD curl -fsS http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
