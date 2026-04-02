import logging
from flask import current_app, url_for
from flask_mail import Message
from ..extensions import mail

log = logging.getLogger(__name__)

_TRIAL_WARNING_HTML = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#09090f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090f;padding:40px 0">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111118;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:36px 32px;color:#e8e8e0">
        <!-- Logo -->
        <tr><td style="padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,.07)">
          <span style="font-size:1.4rem;font-weight:700;color:#e8e8e0">Conta<span style="color:#d4a843">IA</span></span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding-top:28px">
          <p style="margin:0 0 16px;font-size:1rem;font-weight:700;color:#e8e8e0">Olá, {nome}!</p>
          <p style="margin:0 0 16px;color:#888;font-size:.9rem;line-height:1.65">
            Seu período de trial expira em <strong style="color:#d4a843">2 dias</strong>.
            Não perca acesso às ferramentas que simplificam sua rotina contábil.
          </p>

          <!-- Features -->
          <table cellpadding="0" cellspacing="0" style="margin:20px 0;width:100%">
            {features}
          </table>

          <!-- CTA -->
          <table cellpadding="0" cellspacing="0" style="margin:28px 0 8px">
            <tr><td>
              <a href="{url_planos}" style="display:inline-block;background:#d4a843;color:#000;font-weight:700;font-size:.9rem;padding:12px 28px;border-radius:8px;text-decoration:none">
                Ver planos e assinar &rarr;
              </a>
            </td></tr>
          </table>

          <p style="margin:20px 0 0;color:#555;font-size:.75rem;line-height:1.6">
            Se não quiser mais receber notificações, simplesmente ignore este e-mail.<br>
            &copy; ContaIA &mdash; Copiloto para contadores
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

_FEATURE_ROW = """\
<tr>
  <td width="20" style="color:#22c55e;font-size:.85rem;padding:4px 8px 4px 0;vertical-align:top">&check;</td>
  <td style="color:#888;font-size:.85rem;padding:4px 0;line-height:1.5">{text}</td>
</tr>"""

_FEATURES = [
    "Cobranças sem constrangimento — lembretes, parcelamento e reajuste",
    "Relatórios gerenciais mensais em linguagem simples",
    "Comunicações com a Receita Federal",
    "Histórico completo e favoritos de todas as gerações",
]


_RESET_HTML = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#09090f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090f;padding:40px 0">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111118;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:36px 32px;color:#e8e8e0">
        <tr><td style="padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,.07)">
          <span style="font-size:1.4rem;font-weight:700;color:#e8e8e0">Conta<span style="color:#d4a843">IA</span></span>
        </td></tr>
        <tr><td style="padding-top:28px">
          <p style="margin:0 0 16px;font-size:1rem;font-weight:700;color:#e8e8e0">Olá, {nome}!</p>
          <p style="margin:0 0 20px;color:#888;font-size:.9rem;line-height:1.65">
            Recebemos uma solicitação para redefinir a senha da sua conta ContaIA.<br>
            Clique no botão abaixo para criar uma nova senha. O link expira em <strong style="color:#d4a843">2 horas</strong>.
          </p>
          <table cellpadding="0" cellspacing="0" style="margin:24px 0">
            <tr><td>
              <a href="{url}" style="display:inline-block;background:#d4a843;color:#000;font-weight:700;font-size:.9rem;padding:12px 28px;border-radius:8px;text-decoration:none">
                Redefinir minha senha &rarr;
              </a>
            </td></tr>
          </table>
          <p style="margin:0 0 8px;color:#555;font-size:.78rem;line-height:1.6">
            Se você não solicitou a redefinição, ignore este e-mail — sua senha permanece a mesma.
          </p>
          <p style="margin:16px 0 0;color:#555;font-size:.75rem">
            &copy; ContaIA &mdash; Copiloto para contadores
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


_WELCOME_HTML = """\
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#09090f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090f;padding:40px 0">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" style="background:#111118;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:36px 32px;color:#e8e8e0">
        <tr><td style="padding-bottom:24px;border-bottom:1px solid rgba(255,255,255,.07)">
          <span style="font-size:1.4rem;font-weight:700;color:#e8e8e0">Conta<span style="color:#d4a843">IA</span></span>
        </td></tr>
        <tr><td style="padding-top:28px">
          <p style="margin:0 0 8px;font-size:1.1rem;font-weight:700;color:#e8e8e0">Bem-vindo, {nome}!</p>
          <p style="margin:0 0 20px;color:#888;font-size:.9rem;line-height:1.65">
            Sua conta ContaIA está pronta. Você tem <strong style="color:#d4a843">7 dias gratuitos</strong>
            para explorar todas as ferramentas.
          </p>
          <table cellpadding="0" cellspacing="0" style="margin:0 0 24px;width:100%">
            {features}
          </table>
          <table cellpadding="0" cellspacing="0" style="margin:0 0 24px">
            <tr><td>
              <a href="{url_dashboard}" style="display:inline-block;background:#d4a843;color:#000;font-weight:700;font-size:.9rem;padding:12px 28px;border-radius:8px;text-decoration:none">
                Acessar minha conta &rarr;
              </a>
            </td></tr>
          </table>
          <p style="margin:0;color:#555;font-size:.75rem;line-height:1.6">
            Dúvidas? Responda este e-mail — estamos aqui para ajudar.<br>
            &copy; ContaIA &mdash; Copiloto para contadores
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

_WELCOME_FEATURES = [
    "Cobranças sem constrangimento — lembretes e parcelamento",
    "Relatórios gerenciais mensais em linguagem simples",
    "Comunicações com a Receita Federal",
    "Histórico, favoritos e templates reutilizáveis",
]


def send_welcome(user) -> bool:
    """Envia e-mail de boas-vindas após cadastro."""
    if not current_app.config.get("MAIL_USERNAME"):
        log.debug("MAIL_USERNAME não configurado — e-mail de boas-vindas ignorado")
        return False
    try:
        features_html = "".join(_FEATURE_ROW.format(text=f) for f in _WELCOME_FEATURES)
        html_body = _WELCOME_HTML.format(
            nome=user.first_name,
            url_dashboard=url_for("main.dashboard", _external=True),
            features=features_html,
        )
        msg = Message(
            subject="Bem-vindo ao ContaIA — seu trial de 7 dias começa agora",
            recipients=[user.email],
            html=html_body,
        )
        mail.send(msg)
        log.info("E-mail de boas-vindas enviado para %s", user.email)
        return True
    except Exception as exc:
        log.error("Erro ao enviar boas-vindas para %s: %s", user.email, exc)
        return False


def send_password_reset(user, token: str) -> bool:
    """Envia e-mail com link para redefinição de senha. Retorna True se enviou."""
    if not current_app.config.get("MAIL_USERNAME"):
        log.debug("MAIL_USERNAME não configurado — e-mail de reset ignorado")
        return False
    try:
        reset_url = url_for("auth.redefinir_senha", token=token, _external=True)
        html_body = _RESET_HTML.format(nome=user.first_name, url=reset_url)
        msg = Message(
            subject="Redefinição de senha — ContaIA",
            recipients=[user.email],
            html=html_body,
        )
        mail.send(msg)
        log.info("E-mail de reset enviado para %s", user.email)
        return True
    except Exception as exc:
        log.error("Erro ao enviar e-mail de reset para %s: %s", user.email, exc)
        return False


def send_trial_expiry_warning(user) -> bool:
    """Envia e-mail D-2 avisando que o trial expira em breve.

    Retorna True se o envio foi bem-sucedido, False caso contrário.
    Silencia erros para não quebrar o fluxo de login.
    """
    if not current_app.config.get("MAIL_USERNAME"):
        log.debug("MAIL_USERNAME não configurado — e-mail D-2 ignorado")
        return False

    try:
        url_planos = url_for("main.planos", _external=True)
        features_html = "".join(_FEATURE_ROW.format(text=f) for f in _FEATURES)
        html_body = _TRIAL_WARNING_HTML.format(
            nome=user.first_name,
            url_planos=url_planos,
            features=features_html,
        )
        msg = Message(
            subject="Seu trial do ContaIA expira em 2 dias",
            recipients=[user.email],
            html=html_body,
        )
        mail.send(msg)
        log.info("E-mail D-2 enviado para %s", user.email)
        return True
    except Exception as exc:
        log.error("Erro ao enviar e-mail D-2 para %s: %s", user.email, exc)
        return False
