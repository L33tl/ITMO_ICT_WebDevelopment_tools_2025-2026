import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "hackathon_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["celery_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    broker_connection_retry_on_startup=True,
)

celery_app.conf.task_routes = {
    "celery_tasks.parse_url_task": {"queue": "parsing"},
    "celery_tasks.health_check_task": {"queue": "default"},
    "celery_tasks.batch_parse_task": {"queue": "parsing"},
}

celery_app.conf.beat_schedule = {
    "health-check-every-2-min": {
        "task": "health_check_task",
        "schedule": 120.0,  # 2 minutes in seconds
        "args": (),
        "options": {
            "queue": "default",
            "priority": 0,
        },
    },
    "daily-batch-parse": {
        "task": "batch_parse_task",
        "schedule": crontab(hour=3, minute=0),  # 3:00 AM daily
        "args": ([
            "https://example.com",
            "https://httpbin.org",
            "https://jsonplaceholder.typicode.com",
        ],),
        "options": {
            "queue": "parsing",
            "priority": 5,
        },
    },
    "test-parse-every-10-min": {
        "task": "parse_url_task",
        "schedule": 600.0,  # 10 minutes in seconds
        "args": ("https://httpbin.org/html",),
        "options": {
            "queue": "parsing",
            "priority": 1,
        },
    },
    "weekly-health-report": {
        "task": "health_check_task",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),  # Monday 9:00 AM
        "args": (),
        "options": {
            "queue": "reports",
            "priority": 2,
        },
    },
    "hourly-test-task": {
        "task": "parse_url_task",
        "schedule": crontab(minute=0),  # Every hour at minute 0
        "args": ("https://httpbin.org/get",),
        "options": {
            "queue": "parsing",
            "priority": 3,
        },
    },
}
