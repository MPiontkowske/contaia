from celery import Celery


def make_celery(app):
    """Cria e configura instância Celery integrada ao app Flask."""
    broker  = app.config.get("CELERY_BROKER_URL")
    backend = app.config.get("CELERY_RESULT_BACKEND") or broker

    celery = Celery(
        app.import_name,
        broker=broker,
        backend=backend,
    )
    celery.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        result_expires=3600,  # resultados expiram em 1h
        task_track_started=True,
    )

    # Faz as tasks rodarem dentro do app context do Flask
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Instância global — só usada quando CELERY_BROKER_URL está configurado
_celery_instance = None


def get_celery(app=None):
    global _celery_instance
    if _celery_instance is None and app is not None:
        _celery_instance = make_celery(app)
    return _celery_instance
