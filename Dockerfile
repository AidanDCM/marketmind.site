# Backend API image for MarketMind Autopilot.
# Build:  docker build -t marketmind-api .
# Run:    docker run -p 8000:8000 -v marketmind-data:/data marketmind-api
FROM python:3.12-slim

WORKDIR /app

# Dependency/install layer (cached unless these change).
COPY pyproject.toml README.md ./
COPY marketmind ./marketmind
COPY dashboard ./dashboard

RUN pip install --no-cache-dir .

# SQLite lives on a mounted volume so data survives container restarts.
# The app creates the parent dir + schema on startup.
ENV MARKETMIND_DATABASE_URL=sqlite:////data/marketmind.db
VOLUME ["/data"]

EXPOSE 8000

# Set MARKETMIND_API_TOKEN at runtime to require bearer-token auth.
CMD ["uvicorn", "marketmind.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
