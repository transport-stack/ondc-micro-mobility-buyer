from __future__ import absolute_import, unicode_literals
import os

# TODO: What will go here?
# set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.development')

try:
    from celery import Celery
except ImportError as exc:
    raise ImportError(
        "Please set up using the steps here: "
        "https://gitlab.com/chartrmobility/osrtc/osrtc-app/-/wikis/Redis-+-Celery-for-Background-Tasks"
    ) from exc

app = Celery("ptx_core_backend")

# Your additional Celery configuration
app.conf.update(
    broker_connection_retry=True,
    broker_connection_max_retries=None,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.

app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
