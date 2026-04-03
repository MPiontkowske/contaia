"""
Tasks Celery para geração assíncrona de textos.

Só é importado/executado quando CELERY_BROKER_URL está configurado.
"""
import json
import logging
from .celery_app import get_celery

logger = logging.getLogger(__name__)


def _get_task():
    """Retorna a task registrada no Celery atual."""
    celery = get_celery()
    if celery is None:
        raise RuntimeError("Celery não inicializado.")

    @celery.task(bind=True, name="contaia.gerar_texto", max_retries=2,
                 default_retry_delay=5)
    def gerar_texto(self, user_id: int, tool: str, campos: dict,
                    user_api_key: str | None = None):
        """
        Executa a chamada Claude e persiste a Generation no banco.
        Retorna dict com resultado e id da generation.
        """
        from .extensions import db
        from .models import User, Generation
        from .services.ai import call_claude
        from .services.prompts import build_prompt, auto_title

        try:
            user = db.session.get(User, user_id)
            api_key = user_api_key or (user.anthropic_api_key if user else None)

            system_prompt, user_message, max_tokens, model = build_prompt(tool, campos)
            resultado = call_claude(system_prompt, user_message, max_tokens, model,
                                    user_api_key=api_key)

            titulo = auto_title(tool, campos)
            gen = Generation(
                user_id=user_id,
                tool=tool,
                titulo=titulo,
                campos_json=json.dumps(campos, ensure_ascii=False),
                resultado=resultado,
            )
            db.session.add(gen)
            db.session.commit()

            return {"resultado": resultado, "id": gen.id}

        except Exception as exc:
            logger.exception("Erro na task gerar_texto (tool=%s, user=%s)", tool, user_id)
            raise self.retry(exc=exc)

    return gerar_texto


# Cache da task para não recriar a cada chamada
_task_cache = None


def get_gerar_task():
    global _task_cache
    if _task_cache is None:
        _task_cache = _get_task()
    return _task_cache
