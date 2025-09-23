FROM python:3.12-slim

# Create non-root user
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY infra/docker/requirements-worker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY packages /app/packages
COPY apps/hive_worker /app/apps/hive_worker

# Change ownership to app user
RUN chown -R app:app /app

# Add health check for beat scheduler
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "celery.*beat" || exit 1

# Switch to non-root user
USER app

# Run Beat scheduler only
CMD ["celery", "-A", "apps.hive_worker.celery_app.app", "beat", \
     "--loglevel=INFO", "--pidfile=/tmp/celerybeat.pid"]
