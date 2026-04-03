"""
Entry point para o worker Celery.

Uso (VPS):
    celery -A worker.celery worker --loglevel=info --concurrency=2
"""
from app import create_app
from app.celery_app import get_celery

flask_app = create_app()
app = get_celery(flask_app)
