FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy config
COPY config/ config/

# Create non-root user
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from support_agent.mimo_integration.client import MiMoClient; print('ok')" || exit 1

EXPOSE 8000

CMD ["support-agent", "listen", "--channels", "email,chat,discord"]
