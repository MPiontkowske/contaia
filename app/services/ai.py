import os
import logging
from typing import Optional
import anthropic

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _get_client(user_api_key: Optional[str] = None) -> anthropic.Anthropic:
    """Retorna cliente Anthropic. Se user_api_key fornecida, cria cliente dedicado."""
    if user_api_key:
        return anthropic.Anthropic(api_key=user_api_key)
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY não configurado no servidor.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def call_claude(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 1024,
    model: str = "claude-sonnet-4-6",
    user_api_key: Optional[str] = None,
) -> str:
    try:
        client = _get_client(user_api_key)
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    except anthropic.AuthenticationError:
        logger.error("Anthropic: erro de autenticação — chave inválida")
        raise RuntimeError("Chave de API inválida. Contate o suporte.")

    except anthropic.RateLimitError:
        logger.warning("Anthropic: rate limit atingido")
        raise RuntimeError(
            "Limite de requisições atingido. Aguarde alguns instantes e tente novamente."
        )

    except anthropic.APIConnectionError as e:
        logger.error(f"Anthropic: erro de conexão — {e}")
        raise RuntimeError(
            "Erro de conexão com o serviço de IA. Verifique sua internet e tente novamente."
        )

    except anthropic.APIStatusError as e:
        logger.error(f"Anthropic: status {e.status_code} — {e.message}")
        raise RuntimeError("O serviço de IA retornou um erro. Tente novamente em instantes.")

    except Exception as e:
        logger.exception(f"Erro inesperado na chamada Claude: {e}")
        raise RuntimeError("Erro ao processar sua solicitação. Tente novamente.")
