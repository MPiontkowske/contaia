import json
from datetime import datetime, timedelta
from .extensions import db


TOOL_LABELS = {
    "cobranca_lembrete1": "1º Lembrete",
    "cobranca_lembrete2": "2º Lembrete",
    "cobranca_parcelamento": "Proposta de Parcelamento",
    "cobranca_reajuste": "Reajuste de Honorários",
    "relatorio_mensal": "Relatório Mensal",
    "relatorio_dre": "Análise de DRE",
    "relatorio_comparativo": "Comparativo Mensal",
    "relatorio_anual": "Resumo Anual",
    "receita_intimacao": "Resposta a Intimação",
    "receita_defesa": "Defesa / Impugnação",
    "receita_comunicar_cliente": "Comunicar Cliente",
    "receita_parcelamento": "Parcelamento Fiscal",
}

TOOL_CATEGORY = {
    "cobranca_lembrete1": "cobranca",
    "cobranca_lembrete2": "cobranca",
    "cobranca_parcelamento": "cobranca",
    "cobranca_reajuste": "cobranca",
    "relatorio_mensal": "relatorio",
    "relatorio_dre": "relatorio",
    "relatorio_comparativo": "relatorio",
    "relatorio_anual": "relatorio",
    "receita_intimacao": "receita",
    "receita_defesa": "receita",
    "receita_comunicar_cliente": "receita",
    "receita_parcelamento": "receita",
}


class User(db.Model):
    __tablename__ = "user"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    plan          = db.Column(db.String(20), default="trial")  # trial | active | cancelled
    trial_ends    = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at           = db.Column(db.DateTime)
    trial_warned_at         = db.Column(db.DateTime)
    reset_token             = db.Column(db.String(64), index=True)
    reset_token_expires     = db.Column(db.DateTime)
    subscription_end        = db.Column(db.DateTime)   # quando a assinatura ativa expira
    subscription_warned_at  = db.Column(db.DateTime)   # D-7 email enviado
    is_admin                = db.Column(db.Boolean, default=False)

    # Perfil do contador — pré-preenchimento em formulários
    profile_nome      = db.Column(db.String(120))   # Nome do contador
    profile_escritorio = db.Column(db.String(120))  # Nome do escritório
    profile_cargo     = db.Column(db.String(80))    # Cargo / função

    generations = db.relationship("Generation", backref="user", lazy="dynamic",
                                  foreign_keys="Generation.user_id")
    templates   = db.relationship("Template", backref="user", lazy="dynamic",
                                  foreign_keys="Template.user_id")

    @property
    def first_name(self):
        return self.name.split()[0] if self.name else "Usuário"

    @property
    def has_access(self):
        if self.is_admin:
            return True
        if self.plan == "active":
            if self.subscription_end and self.subscription_end < datetime.utcnow():
                return False
            return True
        if self.plan == "trial" and self.trial_ends and self.trial_ends > datetime.utcnow():
            return True
        return False

    @property
    def trial_days_remaining(self):
        if self.plan != "trial" or not self.trial_ends:
            return None
        delta = self.trial_ends - datetime.utcnow()
        return max(0, delta.days)

    @property
    def subscription_days_remaining(self):
        if self.plan != "active" or not self.subscription_end:
            return None
        delta = self.subscription_end - datetime.utcnow()
        return max(0, delta.days)

    @property
    def plan_label(self):
        labels = {"trial": "Trial", "active": "Ativo", "cancelled": "Cancelado"}
        return labels.get(self.plan, self.plan)


class Generation(db.Model):
    __tablename__ = "generation"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    tool        = db.Column(db.String(60), nullable=False)
    titulo      = db.Column(db.String(150))
    campos_json = db.Column(db.Text)
    resultado   = db.Column(db.Text, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    feedback    = db.Column(db.Boolean)  # True=positivo, False=negativo, None=sem feedback
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def campos(self):
        if not self.campos_json:
            return {}
        try:
            return json.loads(self.campos_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @property
    def tool_label(self):
        return TOOL_LABELS.get(self.tool, self.tool)

    @property
    def category(self):
        return TOOL_CATEGORY.get(self.tool, "")

    @property
    def resultado_preview(self):
        if not self.resultado:
            return ""
        text = self.resultado.strip()
        return text[:180] + "…" if len(text) > 180 else text

    def to_dict(self):
        return {
            "id": self.id,
            "tool": self.tool,
            "tool_label": self.tool_label,
            "category": self.category,
            "titulo": self.titulo,
            "resultado": self.resultado,
            "resultado_preview": self.resultado_preview,
            "is_favorite": self.is_favorite,
            "feedback": self.feedback,
            "created_at": self.created_at.strftime("%d/%m/%Y %H:%M"),
        }


class Template(db.Model):
    __tablename__ = "template"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    tool        = db.Column(db.String(60), nullable=False, index=True)
    nome        = db.Column(db.String(120), nullable=False)
    campos_json = db.Column(db.Text, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def campos(self):
        try:
            return json.loads(self.campos_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        return {
            "id": self.id,
            "tool": self.tool,
            "nome": self.nome,
            "campos": self.campos,
        }
