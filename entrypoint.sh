#!/bin/bash

if [ "$1" = "api-service" ]; then
  # Reset last_run_at for all tasks to force rescheduling
  python manage.py shell -c '
from django_celery_beat.models import PeriodicTask, PeriodicTasks
PeriodicTask.objects.update(enabled=True, last_run_at=None)
PeriodicTasks.update_changed()
'
  exec gunicorn -b 0.0.0.0:8000 ptx_core_backend.wsgi:application --error-logfile - --workers 10 --worker-class gevent --worker-connections 1000 --access-logfile - ${@:2}
elif [ "$1" = "celery-worker" ]; then
  exec celery -A ptx_core_backend worker --loglevel=info ${@:2}
elif [ "$1" = "celery-beat" ]; then
  # Start Celery beat with a custom scheduler reset
  python manage.py shell -c '
from django_celery_beat.models import PeriodicTask, PeriodicTasks
PeriodicTask.objects.update(enabled=True, last_run_at=None)
PeriodicTasks.update_changed()
'
  exec celery -A ptx_core_backend beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler ${@:2}
else
  echo "Invalid command, please use one of: api-service, celery-worker, celery-beat"
  exit 1
fi
