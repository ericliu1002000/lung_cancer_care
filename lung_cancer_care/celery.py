import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lung_cancer_care.settings")

app = Celery("lung_cancer_care")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
