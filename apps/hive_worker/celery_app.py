import os

from celery import Celery
from celery.schedules import crontab
from kombu import Queue

# Optional observability imports
try:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
except ImportError:  # pragma: no cover
    sentry_sdk = None
    CeleryIntegration = None
    SqlalchemyIntegration = None

try:
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
except ImportError:  # pragma: no cover
    CeleryInstrumentor = None

try:
    from prometheus_client import Counter, Histogram, start_http_server
    # Worker metrics
    TASK_COUNTER = Counter('celery_tasks_total', 'Total number of Celery tasks', ['task_name', 'status'])
    TASK_DURATION = Histogram('celery_task_duration_seconds', 'Task execution time', ['task_name'])
except ImportError:  # pragma: no cover
    Counter = None
    Histogram = None
    start_http_server = None
    TASK_COUNTER = None
    TASK_DURATION = None

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_BACKEND_URL = CELERY_BROKER_URL

app = Celery("hive", broker=CELERY_BROKER_URL, backend=CELERY_BACKEND_URL)

# Production-ready Celery configuration
app.conf.update(
    # Task execution settings
    task_acks_late=True,  # Acknowledge tasks only after completion
    worker_prefetch_multiplier=1,  # Prevent worker overload
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    
    # Retry and error handling
    task_default_retry_delay=60,  # 1 minute default retry delay
    task_max_retries=3,  # Maximum retries per task
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
    
    # Worker lifecycle
    worker_max_tasks_per_child=1000,  # Recycle workers to prevent memory leaks
    worker_disable_rate_limits=False,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Serialization (security)
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Dead letter queue simulation via failed task tracking
    task_track_started=True,
    task_send_sent_event=True,
)

app.autodiscover_tasks(["apps.hive_worker.tasks"])  # ensure package path

# Initialize observability
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN and sentry_sdk:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            CeleryIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=os.getenv("APP_ENV", "development"),
    )

# OpenTelemetry instrumentation
if CeleryInstrumentor is not None:
    try:
        CeleryInstrumentor().instrument()
    except Exception:  # pragma: no cover
        pass

# Start Prometheus metrics server for worker
if start_http_server is not None:
    try:
        metrics_port = int(os.getenv("WORKER_METRICS_PORT", "9091"))
        start_http_server(metrics_port)
    except Exception:  # pragma: no cover
        pass
# Explicit imports to guarantee task registration
app.conf.imports = (
    "apps.hive_worker.tasks.ingest",
    "apps.hive_worker.tasks.compliance",
    "apps.hive_worker.tasks.lint",
    "apps.hive_worker.tasks.brains.pricing",
    "apps.hive_worker.tasks.brains.marketing",
    "apps.hive_worker.tasks.brains.analytics",
    "apps.hive_worker.tasks.brains.compliance",
    "apps.hive_worker.tasks.brains.expansion",
    # Phase 15 learning tasks
    "apps.hive_worker.tasks.learning",
)

# Phase 7: define dedicated queues per brain and route tasks explicitly
app.conf.task_default_queue = "default"
app.conf.task_queues = (
    # Core/default
    Queue("default"),
    # Brain-specific queues
    Queue("pricing"),
    Queue("marketing"),
    Queue("analytics"),
    Queue("compliance"),
    Queue("expansion"),
    # Phase 15 learning queue
    Queue("learning"),
    # Ingestion and support pipelines referenced by API
    Queue("q.catalog"),
    Queue("q.orders"),
    Queue("q.signals"),
    Queue("q.backfill"),
)

app.conf.task_routes = {
    # Pricing brain
    "apps.hive_worker.tasks.brains.pricing.price_decide": {"queue": "pricing"},
    # Marketing brain
    "apps.hive_worker.tasks.brains.marketing.generate_copy": {"queue": "marketing"},
    # Analytics brain
    "apps.hive_worker.tasks.brains.analytics.aggregate_kpis": {"queue": "analytics"},
    # Compliance brain
    "apps.hive_worker.tasks.brains.compliance.check_order": {"queue": "compliance"},
    # Expansion brain
    "apps.hive_worker.tasks.brains.expansion.score_market": {"queue": "expansion"},
    # Phase 15 learning tasks
    "apps.hive_worker.tasks.learning.train_model": {"queue": "learning"},
    "apps.hive_worker.tasks.learning.schedule_retrains": {"queue": "learning"},
    "apps.hive_worker.tasks.learning.promote_rollout_task": {"queue": "learning"},
    "apps.hive_worker.tasks.learning.detect_drift": {"queue": "learning"},
    "apps.hive_worker.tasks.learning.run_benchmark": {"queue": "learning"},
}

# Celery Beat schedule: run sample ingestion hourly at minute 5
app.conf.timezone = os.getenv("APP_TZ", "UTC")
app.conf.beat_schedule = {
    "hourly-sample-ingest": {
        "task": "apps.hive_worker.tasks.ingest.run_ingest",
        "schedule": crontab(minute=5),
    },
    # Phase 11: periodically reload/compile enabled compliance packs
    "compliance-reload-packs": {
        "task": "apps.hive_worker.tasks.compliance.reload_enabled_packs",
        "schedule": crontab(minute="*/15"),
    },
    # Phase 11: post-publish scanners
    "post-publish-scan": {
        "task": "apps.hive_worker.tasks.lint.scan_post_publish",
        "schedule": crontab(minute="*/10"),
    },
    # Phase 15: nightly learning retrains (03:00 UTC)
    "nightly-learning-retrain": {
        "task": "apps.hive_worker.tasks.learning.schedule_retrains",
        "schedule": crontab(minute=0, hour=3),
    },
}
