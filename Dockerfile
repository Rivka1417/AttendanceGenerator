
# syntax=docker/dockerfile:1

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
    tesseract-ocr \
    tesseract-ocr-heb \
    tesseract-ocr-eng \
    poppler-utils \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .


RUN --mount=type=secret,id=netfree_ca \
    cat /etc/ssl/certs/ca-certificates.crt /run/secrets/netfree_ca \
    > /tmp/combined-ca.pem \
    && PIP_CERT=/tmp/combined-ca.pem \
       python -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt \
    && rm -f /tmp/combined-ca.pem

COPY . .

RUN mkdir -p /app/input /app/output

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "app.py"]
