# Multi-stage / Lightweight Python + OpenJDK runtime for Istanbul Transit Core
FROM python:3.11-slim

# Install OpenJDK 17 and curl for OTP runtime and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set permissions for Hugging Face non-root user (UID 1000)
RUN useradd -m -u 1000 user && \
    chown -R user:user /app && \
    chmod +x /app/bin/*.sh /app/*.sh

USER user

EXPOSE 7860 8000 8080

ENTRYPOINT ["/app/bin/entrypoint.sh"]
