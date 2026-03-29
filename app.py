from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import anthropic
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "contaia-secret-2026-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///contaia.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ─── MODELS ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    plan          = db.Column(db.String(20), default="trial")   # trial | active | cancelled
    trial_ends    = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin      = db.Column(db.Boolean, default=False)
    usages        = db.relationship("Usage", backref="user", lazy=True)

class Usage(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tool       = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        user = User.query.get(session["user_id"])
        if not user or not user.is_admin:
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

def current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None

def has_access(user):
    if user.is_admin:
        return True
    if user.plan == "active":
        return True
    if user.plan == "trial" and user.trial_ends > datetime.utcnow():
        return True
    return False

def call_claude(system_prompt, user_message):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "Erro: chave de API não configurada."
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return message.content[0].text

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data  = request.get_json()
        name  = data.get("name", "").strip()
        email = data.get("email", "").strip().lower()
        pwd   = data.get("password", "")
        if not name or not email or not pwd:
            return jsonify({"error": "Preencha todos os campos."}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "E-mail já cadastrado."}), 400
        user = User(name=name, email=email,
                    password_hash=generate_password_hash(pwd))
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return jsonify({"ok": True})
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data  = request.get_json()
        email = data.get("email", "").strip().lower()
        pwd   = data.get("password", "")
        user  = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, pwd):
            return jsonify({"error": "E-mail ou senha incorretos."}), 401
        session["user_id"] = user.id
        return jsonify({"ok": True, "admin": user.is_admin})
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    access = has_access(user)
    trial_days = None
    if user.plan == "trial":
        delta = user.trial_ends - datetime.utcnow()
        trial_days = max(0, delta.days)
    total_uses = Usage.query.filter_by(user_id=user.id).count()
    return render_template("dashboard.html", user=user, access=access,
                           trial_days=trial_days, total_uses=total_uses)

# ─── FERRAMENTAS ──────────────────────────────────────────────────────────────

@app.route("/ferramenta/cobranca")
@login_required
def tool_cobranca():
    user = current_user()
    if not has_access(user):
        return redirect(url_for("sem_acesso"))
    return render_template("tool_cobranca.html", user=user)

@app.route("/ferramenta/relatorio")
@login_required
def tool_relatorio():
    user = current_user()
    if not has_access(user):
        return redirect(url_for("sem_acesso"))
    return render_template("tool_relatorio.html", user=user)

@app.route("/ferramenta/receita")
@login_required
def tool_receita():
    user = current_user()
    if not has_access(user):
        return redirect(url_for("sem_acesso"))
    return render_template("tool_receita.html", user=user)

@app.route("/sem-acesso")
@login_required
def sem_acesso():
    return render_template("sem_acesso.html", user=current_user())

# ─── API IA ───────────────────────────────────────────────────────────────────

@app.route("/api/gerar", methods=["POST"])
@login_required
def api_gerar():
    user = current_user()
    if not has_access(user):
        return jsonify({"error": "Acesso encerrado. Assine para continuar."}), 403

    data       = request.get_json()
    tool       = data.get("tool")
    campos     = data.get("campos", {})

    system_map = {
        "cobranca_lembrete1": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija textos profissionais, cordiais e eficazes. Retorne apenas o texto do e-mail, "
            "sem explicações adicionais."
        ),
        "cobranca_lembrete2": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija textos profissionais e firmes, mas sempre respeitosos. "
            "Retorne apenas o texto do e-mail, sem explicações adicionais."
        ),
        "cobranca_parcelamento": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija uma proposta de parcelamento que preserve o relacionamento com o cliente. "
            "Retorne apenas o texto do e-mail, sem explicações adicionais."
        ),
        "cobranca_reajuste": (
            "Você é um especialista em comunicação para escritórios contábeis brasileiros. "
            "Redija uma comunicação de reajuste que valorize os serviços e minimize cancelamentos. "
            "Retorne apenas o texto do e-mail, sem explicações adicionais."
        ),
        "relatorio_mensal": (
            "Você é um contador consultor especializado em traduzir números para empresários brasileiros leigos. "
            "Redija relatórios claros, sem jargão técnico, que gerem valor percebido. "
            "Retorne apenas o relatório formatado, sem explicações adicionais."
        ),
        "relatorio_dre": (
            "Você é um contador consultor especializado em explicar DRE para donos de negócio sem formação financeira. "
            "Use linguagem simples e exemplos do cotidiano. "
            "Retorne apenas a análise, sem explicações adicionais."
        ),
        "relatorio_comparativo": (
            "Você é um assistente contábil brasileiro especializado em análises comparativas mensais. "
            "Retorne apenas o texto do comparativo, sem explicações adicionais."
        ),
        "relatorio_anual": (
            "Você é um consultor contábil especializado em apresentações executivas anuais para clientes. "
            "Retorne apenas o resumo formatado, sem explicações adicionais."
        ),
        "receita_intimacao": (
            "Você é um especialista em comunicação fiscal e tributária brasileira. "
            "Redija respostas formais à Receita Federal com linguagem técnica e respeitosa. "
            "Retorne apenas o texto da resposta formal, sem explicações adicionais."
        ),
        "receita_defesa": (
            "Você é um especialista em defesa fiscal para contadores brasileiros. "
            "Redija impugnações administrativas técnicas e objetivas. "
            "Retorne apenas o texto da impugnação, sem explicações adicionais."
        ),
        "receita_comunicar_cliente": (
            "Você é um assistente de comunicação contábil. "
            "Redija e-mails que informam clientes sobre notificações fiscais sem gerar pânico, "
            "demonstrando controle e profissionalismo. "
            "Retorne apenas o texto do e-mail, sem explicações adicionais."
        ),
        "receita_parcelamento": (
            "Você é um especialista em comunicação tributária brasileira. "
            "Redija cartas formais de solicitação de parcelamento fiscal demonstrando boa-fé. "
            "Retorne apenas o texto da carta formal, sem explicações adicionais."
        ),
    }

    user_map = {
        "cobranca_lembrete1": (
            f"Redija um primeiro e-mail de lembrete de honorários em atraso.\n"
            f"Cliente: {campos.get('cliente')}\n"
            f"Empresa: {campos.get('empresa')}\n"
            f"Valor: R$ {campos.get('valor')}\n"
            f"Vencimento: {campos.get('vencimento')}\n"
            f"Contador: {campos.get('contador')}\n"
            f"Escritório: {campos.get('escritorio')}\n"
            f"Tom: cordial, sem constrangimento. Máximo 5 linhas."
        ),
        "cobranca_lembrete2": (
            f"Redija um segundo e-mail de cobrança de honorários.\n"
            f"Cliente: {campos.get('cliente')}\n"
            f"Valor: R$ {campos.get('valor')}\n"
            f"Dias em atraso: {campos.get('dias')}\n"
            f"Contador: {campos.get('contador')}\n"
            f"Tom: firme mas respeitoso. Mencione que a continuidade dos serviços pode ser afetada. Máximo 6 linhas."
        ),
        "cobranca_parcelamento": (
            f"Redija um e-mail propondo parcelamento de honorários atrasados.\n"
            f"Cliente: {campos.get('cliente')}\n"
            f"Valor total: R$ {campos.get('valor')}\n"
            f"Meses em atraso: {campos.get('meses')}\n"
            f"Parcelas propostas: {campos.get('parcelas')}\n"
            f"Contador: {campos.get('contador')}\n"
            f"Tom: parceiro, não credor. Máximo 8 linhas."
        ),
        "cobranca_reajuste": (
            f"Redija um e-mail comunicando reajuste de honorários.\n"
            f"Cliente: {campos.get('cliente')}\n"
            f"Valor atual: R$ {campos.get('valor_atual')}\n"
            f"Percentual de reajuste: {campos.get('percentual')}%\n"
            f"Data de vigência: {campos.get('data_vigencia')}\n"
            f"Contador: {campos.get('contador')}\n"
            f"Justifique de forma valorizada. Máximo 8 linhas."
        ),
        "relatorio_mensal": (
            f"Redija um relatório gerencial mensal em linguagem simples.\n"
            f"Empresa: {campos.get('empresa')}\n"
            f"Mês/Ano: {campos.get('mes_ano')}\n"
            f"Faturamento: R$ {campos.get('faturamento')}\n"
            f"Despesas: R$ {campos.get('despesas')}\n"
            f"Lucro líquido: R$ {campos.get('lucro')}\n"
            f"Observações: {campos.get('observacoes', 'Nenhuma')}\n"
            f"Estruture em: Resumo Executivo, Destaques do Mês (3 pontos), Atenção Para (1 alerta)."
        ),
        "relatorio_dre": (
            f"Explique o DRE abaixo para o dono da empresa em linguagem simples.\n"
            f"Empresa: {campos.get('empresa')}\n"
            f"Período: {campos.get('periodo')}\n"
            f"DRE: {campos.get('dre')}\n"
            f"Destaque: o que foi bem, o que preocupa, uma recomendação prática. Máximo 10 linhas."
        ),
        "relatorio_comparativo": (
            f"Redija um comparativo entre dois meses para o cliente.\n"
            f"Empresa: {campos.get('empresa')}\n"
            f"Mês anterior: {campos.get('mes_anterior')}\n"
            f"Mês atual: {campos.get('mes_atual')}\n"
            f"Tom: claro, sem alarmismo. Máximo 8 linhas."
        ),
        "relatorio_anual": (
            f"Redija um resumo anual executivo para apresentação ao cliente.\n"
            f"Empresa: {campos.get('empresa')}\n"
            f"Ano: {campos.get('ano')}\n"
            f"Dados anuais: {campos.get('dados')}\n"
            f"Estruture em: Performance Geral, 3 Conquistas, 2 Pontos de Atenção para o próximo ano."
        ),
        "receita_intimacao": (
            f"Redija uma resposta formal à intimação da Receita Federal.\n"
            f"Contribuinte: {campos.get('contribuinte')} / CNPJ: {campos.get('cnpj')}\n"
            f"Intimação: {campos.get('intimacao')}\n"
            f"Informações para resposta: {campos.get('informacoes')}\n"
            f"Estruture: identificação, referência à intimação, esclarecimentos, conclusão."
        ),
        "receita_defesa": (
            f"Redija uma impugnação administrativa ao auto de infração.\n"
            f"Contribuinte: {campos.get('contribuinte')} / CNPJ: {campos.get('cnpj')}\n"
            f"Auto de infração: {campos.get('auto')}\n"
            f"Argumentos de defesa: {campos.get('argumentos')}\n"
            f"Estruture: qualificação, tempestividade, mérito, pedido."
        ),
        "receita_comunicar_cliente": (
            f"Redija um e-mail comunicando uma notificação fiscal ao cliente.\n"
            f"Cliente: {campos.get('cliente')}\n"
            f"Assunto da notificação: {campos.get('assunto')}\n"
            f"Gravidade: {campos.get('gravidade')}\n"
            f"Contador: {campos.get('contador')}\n"
            f"Tom: tranquilizador, profissional. Máximo 8 linhas."
        ),
        "receita_parcelamento": (
            f"Redija uma carta formal de solicitação de parcelamento fiscal.\n"
            f"Contribuinte: {campos.get('contribuinte')} / CNPJ: {campos.get('cnpj')}\n"
            f"Débito: R$ {campos.get('debito')} — {campos.get('tributo')}\n"
            f"Parcelas: {campos.get('parcelas')}\n"
            f"Tom: formal, colaborativo, boa-fé."
        ),
    }

    if tool not in system_map:
        return jsonify({"error": "Ferramenta inválida."}), 400

    try:
        resultado = call_claude(system_map[tool], user_map[tool])
        db.session.add(Usage(user_id=user.id, tool=tool))
        db.session.commit()
        return jsonify({"resultado": resultado})
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar: {str(e)}"}), 500

# ─── ADMIN ────────────────────────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin():
    users      = User.query.order_by(User.created_at.desc()).all()
    total_uses = Usage.query.count()
    active     = User.query.filter_by(plan="active").count()
    trial      = User.query.filter_by(plan="trial").count()
    return render_template("admin.html", users=users,
                           total_uses=total_uses, active=active, trial=trial)

@app.route("/admin/toggle-plan/<int:user_id>", methods=["POST"])
@admin_required
def toggle_plan(user_id):
    user = User.query.get_or_404(user_id)
    user.plan = "active" if user.plan != "active" else "cancelled"
    db.session.commit()
    return jsonify({"ok": True, "plan": user.plan})

# ─── INIT ─────────────────────────────────────────────────────────────────────

def create_admin():
    with app.app_context():
        db.create_all()
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@contaia.com.br")
        admin_pwd   = os.environ.get("ADMIN_PASSWORD", "admin123")
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                name="Administrador",
                email=admin_email,
                password_hash=generate_password_hash(admin_pwd),
                plan="active",
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin criado: {admin_email}")

if __name__ == "__main__":
    create_admin()
    app.run(debug=False, host="0.0.0.0", port=5000)
