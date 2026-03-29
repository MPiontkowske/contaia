# ContaIA

Copiloto de inteligência artificial para escritórios contábeis brasileiros.

Gera cobranças, relatórios gerenciais e comunicações fiscais com qualidade profissional — sem depender de prompts manuais.

---

## Funcionalidades

| Ferramenta | O que gera |
|---|---|
| **Cobranças** | 1º lembrete cordial, 2º lembrete firme, proposta de parcelamento, comunicado de reajuste |
| **Relatórios** | Relatório mensal executivo, análise de DRE, comparativo mensal, resumo anual |
| **Receita Federal** | Resposta a intimação, impugnação administrativa, aviso ao cliente, carta de parcelamento fiscal |

Todos os textos ficam salvos no histórico por usuário, com suporte a favoritos.

---

## Stack

- **Backend:** Flask 3 + SQLAlchemy (SQLite por padrão, compatível com PostgreSQL)
- **IA:** Anthropic Claude (Haiku para e-mails, Sonnet para relatórios, Opus para documentos fiscais complexos)
- **Auth:** Sessão Flask com Werkzeug PBKDF2
- **Rate limiting:** Flask-Limiter (in-memory)
- **Frontend:** HTML/CSS/JS vanilla — sem dependências externas
- **Deploy:** Gunicorn + Nginx + systemd

---

## Estrutura do projeto

```
contaia/
├── wsgi.py                  # Entry point (Gunicorn)
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Dev / Prod configs
│   ├── extensions.py        # db, limiter
│   ├── models.py            # User, Generation
│   ├── decorators.py        # login_required, admin_required, access_required
│   ├── services/
│   │   ├── ai.py            # Cliente Anthropic + call_claude
│   │   └── prompts.py       # Todos os prompts centralizados
│   ├── routes/
│   │   ├── auth.py          # /login /register /logout
│   │   ├── main.py          # /dashboard /historico
│   │   ├── tools.py         # /ferramenta/*
│   │   ├── api.py           # /api/gerar /api/favoritar /api/deletar
│   │   └── admin.py         # /admin/
│   └── templates/           # Jinja2 templates
├── requirements.txt
├── .env.example
├── contaia.service          # systemd unit
└── DEPLOY.md
```

---

## Rodar localmente

**Pré-requisitos:** Python 3.11+

```bash
# 1. Clone e entre no diretório
cd contaia

# 2. Crie o ambiente virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com sua ANTHROPIC_API_KEY e demais valores

# 5. Inicie em modo desenvolvimento
set FLASK_ENV=development      # Windows
export FLASK_ENV=development   # Linux/Mac

python wsgi.py
```

Acesse: `http://localhost:5000`

A conta admin e o banco de dados são criados automaticamente na primeira inicialização.

---

## Modelos e planos

| Status | Acesso |
|---|---|
| `trial` | 7 dias a partir do cadastro |
| `active` | Acesso ilimitado (ativado pelo admin) |
| `cancelled` | Sem acesso |

A gestão de planos é feita pelo painel `/admin/`. Integração com gateway de pagamento é prevista para Fase 2.

---

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | Sim | Chave de sessão Flask — gere com `secrets.token_hex(32)` |
| `ANTHROPIC_API_KEY` | Sim | Chave da API Anthropic |
| `ADMIN_EMAIL` | Sim | E-mail da conta administrador |
| `ADMIN_PASSWORD` | Sim | Senha da conta administrador |
| `FLASK_ENV` | Não | `development` ou `production` (padrão: `production`) |
| `DATABASE_URL` | Não | URL do banco (padrão: `sqlite:///contaia.db`) |

---

## Deploy

Veja [DEPLOY.md](DEPLOY.md) para o guia completo de instalação em VPS Ubuntu (Hostinger).

---

## Segurança

- Senhas com hash PBKDF2 (Werkzeug)
- Sessões assinadas com `SECRET_KEY` obrigatória em produção
- Rate limiting: 40 gerações/hora por usuário, 15 logins/minuto por IP
- Headers de segurança: `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`
- Inputs truncados a 2.000 caracteres antes de chegarem ao prompt
- Erros da API Anthropic logados no servidor, nunca expostos ao cliente

---

## Avisos importantes

Os textos gerados pela IA para fins fiscais (intimações, defesas, parcelamentos) são **rascunhos de apoio** e devem ser revisados por contador ou advogado tributarista habilitado antes do uso. A ContaIA não substitui análise profissional.
