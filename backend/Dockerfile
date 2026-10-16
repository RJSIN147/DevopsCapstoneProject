# ---- build stage: install deps into a venv so the runtime image stays small ----
FROM python:3.12-slim AS build
WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt \
    # pip carries its own vendored copies of urllib3/msgpack/setuptools that Trivy flags,
    # and nothing needs pip once the deps are in, so take it out of the venv
    && pip uninstall -y pip

# ---- runtime stage ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# base image pip is never used at runtime, drop it so it doesn't show up in scans
RUN pip uninstall -y pip \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin clinic

COPY --from=build /opt/venv /opt/venv
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

# migrations first, then the API. exec so uvicorn gets SIGTERM directly from k8s
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
