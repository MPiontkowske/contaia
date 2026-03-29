# DEPLOY — ContaIA · VPS Ubuntu (Hostinger)

Tempo estimado: 20–30 minutos.

---

## 1. Conectar na VPS

```bash
ssh root@SEU_IP
```

---

## 2. Preparar o servidor

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx git

# Usuário dedicado e diretório de logs
useradd -m -s /bin/bash contaia
mkdir -p /var/log/contaia
chown contaia:contaia /var/log/contaia
```

---

## 3. Enviar os arquivos

Via SFTP (FileZilla): `sftp://SEU_IP` → usuário `root` → envie a pasta `contaia` para `/opt/`.

Ou via SCP no terminal local:
```bash
scp -r ./contaia root@SEU_IP:/opt/
```

---

## 4. Instalar dependências

```bash
cd /opt/contaia
chown -R contaia:contaia /opt/contaia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

---

## 5. Configurar variáveis de ambiente

```bash
# Gerar SECRET_KEY segura
python3 -c "import secrets; print(secrets.token_hex(32))"

# Criar o arquivo .env (NÃO commite este arquivo)
nano /opt/contaia/.env
```

Conteúdo do `.env` (substitua os valores):

```
FLASK_ENV=production
SECRET_KEY=cole-aqui-a-chave-gerada-acima
ANTHROPIC_API_KEY=sk-ant-...
ADMIN_EMAIL=seu@email.com
ADMIN_PASSWORD=senha-forte-aqui
```

```bash
chmod 600 /opt/contaia/.env
chown contaia:contaia /opt/contaia/.env
```

---

## 6. Ativar o serviço systemd

```bash
cp /opt/contaia/contaia.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable contaia
systemctl start contaia

# Verificar — deve mostrar "active (running)"
systemctl status contaia
```

O banco de dados e a conta admin são criados automaticamente na primeira inicialização.

---

## 7. Configurar Nginx

```bash
nano /etc/nginx/sites-available/contaia
```

Cole e salve:

```nginx
server {
    listen 80;
    server_name SEU_IP;  # substitua pelo domínio quando tiver

    client_max_body_size 1M;

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/contaia /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
```

---

## 8. Testar

Abra `http://SEU_IP` no navegador. Faça login com o e-mail e senha admin configurados.

---

## 9. Domínio + HTTPS (quando tiver domínio)

```bash
# 1. Aponte o DNS: registro A → SEU_IP
# 2. Edite o Nginx: troque SEU_IP pelo domínio
# 3. Instale SSL gratuito:
apt install -y certbot python3-certbot-nginx
certbot --nginx -d seudominio.com.br
```

HTTPS ativado. Renovação automática via cron.

---

## 10. Comandos úteis

```bash
# Logs em tempo real
journalctl -u contaia -f
tail -f /var/log/contaia/error.log

# Reiniciar após atualizar código
cd /opt/contaia && source venv/bin/activate && pip install -r requirements.txt
systemctl restart contaia

# Contar usuários
cd /opt/contaia && source venv/bin/activate
python3 -c "
from wsgi import app
from app.models import User, Generation
from app.extensions import db
with app.app_context():
    print(f'Usuários: {User.query.count()}')
    print(f'Gerações: {Generation.query.count()}')
    print(f'Ativos: {User.query.filter_by(plan=\"active\").count()}')
"

# Backup do banco
cp /opt/contaia/instance/contaia.db /opt/contaia/backups/contaia_$(date +%Y%m%d).db
```

---

## Checklist de produção

- [ ] `SECRET_KEY` definida e forte (nunca o valor padrão)
- [ ] `ANTHROPIC_API_KEY` válida
- [ ] `ADMIN_PASSWORD` forte e única
- [ ] Arquivo `.env` com permissão 600
- [ ] Nginx rodando como reverse proxy
- [ ] HTTPS ativo (após ter domínio)
- [ ] Serviço systemd em `enabled` (inicia com o servidor)
- [ ] Logs acessíveis em `/var/log/contaia/`
- [ ] Backup manual do `contaia.db` agendado
