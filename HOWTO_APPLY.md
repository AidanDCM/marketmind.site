# MarketMind Fix Pack - How to Apply

## 🎯 Quick Start (10 Steps)

This guide gets MarketMind running locally with the Fix Pack applied.

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- Port 8001 (API), 3000 (Console), 5432 (DB), 6379 (Redis) available

### Step 1: Setup Environment
```bash
# Copy the unified environment template
cp .env.example .env

# Edit .env with your preferred editor
# Key variables to check:
# - NEXT_PUBLIC_API_URL=http://localhost:8001
# - DB_URL=postgresql+psycopg2://postgres:postgres@db:5432/hive
# - SECRET_KEY=<generate-a-secure-key-for-production>
```

### Step 2: Use Dev Docker Compose
```bash
# The new docker-compose.dev.yml includes:
# - Auto-migrations (alembic upgrade head)
# - Dev-mode API with hot reload
# - All services with health checks
# - Console connected to API

# Start everything
docker compose -f docker-compose.dev.yml up --build -d

# Watch logs (optional)
docker compose -f docker-compose.dev.yml logs -f
```

### Step 3: Wait for Services
```bash
# Check all services are healthy
docker compose -f docker-compose.dev.yml ps

# Should see:
# - db: healthy
# - redis: healthy
# - migrate: exited (0)
# - api: healthy
# - worker: healthy
# - beat: healthy
# - console: healthy
```

### Step 4: Test API Health
```bash
# Basic health check
curl -i http://localhost:8001/health/ping
# Expected: HTTP/1.1 200 OK

# Full health summary
curl http://localhost:8001/health/summary | jq .
# Expected: JSON with service status

# Database connectivity
curl http://localhost:8001/health/data | jq .
# Expected: db.ok=true, redis.ok=true
```

### Step 5: Create Test User
```bash
# Register a test user
curl -X POST http://localhost:8001/auth/register \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=testpass123" \
  -F "first_name=Test" \
  -F "last_name=User"

# Expected: User created with ID
```

### Step 6: Get Auth Token
```bash
# Login to get JWT token
curl -X POST http://localhost:8001/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"

# Copy the access_token from response
# Example: {"access_token":"eyJ...","token_type":"bearer"}
```

### Step 7: Test Protected Endpoint
```bash
# Replace <TOKEN> with your actual token
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8001/auth/users/me

# Expected: Your user details
```

### Step 8: Open Console
```bash
# Open in browser
open http://localhost:3000

# Or manually navigate to:
# http://localhost:3000
```

The console should load and connect to the API at `http://localhost:8001`.

### Step 9: Test Worker
```bash
# Check worker is processing
docker compose -f docker-compose.dev.yml exec worker \
  celery -A apps.hive_worker.celery_app:app inspect active

# Check scheduled tasks
docker compose -f docker-compose.dev.yml exec worker \
  celery -A apps.hive_worker.celery_app:app inspect scheduled

# Verify beat is running
docker compose -f docker-compose.dev.yml logs beat | tail -20
```

### Step 10: Quick Sanity Routes
```bash
# Dashboard KPIs
curl http://localhost:8001/dash/kpis | jq .

# Pricing history
curl http://localhost:8001/pricing/history | jq .

# Profit log
curl http://localhost:8001/profit/log | jq .

# Ingestion status
curl http://localhost:8001/ingest/status | jq .
```

## 🔧 What the Fix Pack Fixed

### 1. Unified Environment Variable
- **Before**: Mix of `NEXT_PUBLIC_API`, `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_API_URL`
- **After**: Single `NEXT_PUBLIC_API_URL` everywhere
- **Files updated**: 
  - `apps/console/lib/api.ts`
  - `.env.example`
  - Docker Compose files

### 2. Dev Rate Limiting
- **Added**: `apps/hive_api/middleware/rate_limit.py`
- **Purpose**: Simple in-memory rate limiter for dev (protects `/auth/token`)
- **Fallback**: Only used when Redis/SlowAPI unavailable and not in production

### 3. Docker Compose Improvements
- **Fixed**: Port mapping (8001:8000 instead of 8001:8001)
- **Fixed**: Worker healthcheck syntax (`celery_app:app`)
- **Added**: Auto-migrations via `migrate` service
- **Added**: Complete `docker-compose.dev.yml` with all services

### 4. Auth Router
- **Status**: Already complete and working
- **Features**: `/auth/register`, `/auth/token`, `/auth/users/me`
- **Rate limiting**: Applied via SlowAPI (Redis) or fallback (memory)

## 🚀 Production Deployment

For production, use the existing production configs:

```bash
# Use production compose
docker compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

## 📝 Notes

### Still Truncated Files
Some files have ellipsis (`...`) in the repo. Most are documentation, but check:
- `apps/hive_api/routers/ingest.py` - Complete, no truncation found
- `apps/hive_api/routers/marketing.py` - Complete, no truncation found

### Environment Variables
The Fix Pack unified to `NEXT_PUBLIC_API_URL`. If you see old references to:
- `NEXT_PUBLIC_API`
- `NEXT_PUBLIC_API_BASE`

Replace them with `NEXT_PUBLIC_API_URL`.

### Database Migrations
The dev compose runs `alembic upgrade head` automatically. For manual migration:
```bash
docker compose -f docker-compose.dev.yml exec api \
  python -m alembic upgrade head
```

### Console API Connection
The console now reads `NEXT_PUBLIC_API_URL` and handles both relative and absolute URLs correctly.

## 🆘 Troubleshooting

### API Not Starting
```bash
# Check logs
docker compose -f docker-compose.dev.yml logs api

# Common issues:
# - Database not ready (wait and retry)
# - Port 8001 already in use
# - Missing environment variables
```

### Console Not Connecting to API
```bash
# Verify NEXT_PUBLIC_API_URL is set
docker compose -f docker-compose.dev.yml exec console \
  printenv | grep NEXT_PUBLIC_API_URL

# Should show: NEXT_PUBLIC_API_URL=http://localhost:8001
```

### Worker Not Processing
```bash
# Check Redis connection
docker compose -f docker-compose.dev.yml exec worker \
  redis-cli -h redis ping

# Check Celery status
docker compose -f docker-compose.dev.yml exec worker \
  celery -A apps.hive_worker.celery_app:app status
```

### Database Connection Issues
```bash
# Test direct connection
docker compose -f docker-compose.dev.yml exec db \
  psql -U postgres -d hive -c "SELECT 1;"

# Check migrations
docker compose -f docker-compose.dev.yml exec api \
  python -m alembic current
```

## ✅ Success Indicators

When everything is working:
1. All services show "healthy" in `docker compose ps`
2. API responds at http://localhost:8001/health/summary
3. Console loads at http://localhost:3000
4. Auth works (register, login, protected routes)
5. Worker processes tasks (check logs)
6. Beat schedules tasks (check logs)

## 🎉 You're Ready!

MarketMind is now running locally with:
- ✅ Unified environment variables
- ✅ Working authentication with rate limiting
- ✅ All services connected and healthy
- ✅ Console talking to API
- ✅ Workers processing tasks
- ✅ Database migrations applied

Next steps:
1. Configure external API credentials (Amazon, CJ, etc.) in `.env`
2. Run integration tests: `make verify-integrations`
3. Explore the console at http://localhost:3000
4. Check the API docs at http://localhost:8001/docs (dev only)
