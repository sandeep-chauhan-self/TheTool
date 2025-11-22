# ---- Builder Stage ----
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install python dependencies
COPY requirements-prod.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements-prod.txt


# ---- Final Stage ----
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (optional cleanup)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy installed dependencies from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Create necessary directories *as root*
RUN mkdir -p /app/data/cache /app/data/reports /app/logs

# Create non-root user + give ownership
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user only AFTER all setup is done
USER appuser

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app", "--workers=2", "--timeout=120"]

