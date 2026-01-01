# Guia de Deploy - Sistema SIGA

Este guia descreve como fazer o deploy da aplicação Django usando Docker no Easypanel ou qualquer outro provedor cloud.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Conta no Easypanel ou provedor cloud
- Banco de dados MySQL (pode ser externo ou usar o do docker-compose)

## 🚀 Deploy no Easypanel

### Opção 1: Deploy Direto com Dockerfile

1. **Criar novo serviço no Easypanel**
   - Type: App
   - Source: Git Repository ou Upload do código

2. **Configurar Build Settings**
   - Build Type: Dockerfile
   - Dockerfile Path: `./Dockerfile`

3. **Configurar Variáveis de Ambiente**

   Vá em Settings > Environment e adicione:

   ```
   SECRET_KEY=sua-chave-secreta-aqui
   DEBUG=False
   ALLOWED_HOSTS=seu-dominio.easypanel.app,seu-dominio.com

   # Banco de Dados (use o banco fornecido pelo Easypanel ou externo)
   DATABASE_URL=mysql://usuario:senha@host:3306/database

   # Email
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=seu-email@gmail.com
   EMAIL_HOST_PASSWORD=sua-senha-de-app

   # Azure AD (opcional)
   AZURE_AD_CLIENT_ID=seu-client-id
   AZURE_AD_CLIENT_SECRET=seu-secret
   AZURE_AD_TENANT_ID=seu-tenant-id
   SENDER_EMAIL=email@dominio.com

   # API
   API_ROBO_SECRET_HASH=hash-secreto-aleatorio
   ```

4. **Configurar Porta**
   - Port: 8000

5. **Deploy**
   - Clique em "Deploy"
   - Aguarde o build e deploy

### Opção 2: Deploy com Docker Compose

Se o Easypanel suportar docker-compose:

1. **Criar arquivo .env**
   ```bash
   cp .env.example .env
   # Edite o .env com suas credenciais
   ```

2. **Fazer deploy**
   ```bash
   docker-compose up -d
   ```

## 🔧 Configuração Adicional Necessária

### 1. Ajustar settings.py para Produção

Certifique-se de que o [config/settings.py](config/settings.py) tenha:

```python
import os
import dj_database_url

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False') == 'True'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ALLOWED_HOSTS
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 2. Criar Worker Separado (Importante!)

Para processar tarefas em background, crie um **segundo serviço** no Easypanel:

**Configurações do Worker:**
- Name: siga-worker
- Type: App
- Same Dockerfile
- Command Override: `python manage.py worker`
- Mesmas variáveis de ambiente do serviço principal

## 📊 Monitoramento e Logs

### Ver logs do container:
```bash
docker logs -f siga-web
docker logs -f siga-worker
```

### Health Check:
```
https://seu-dominio.com/api/health/
```

Deve retornar:
```json
{
  "status": "ok",
  "mensagem": "API do Sistema SIGA está funcionando"
}
```

## 🔒 Segurança em Produção

### Checklist de Segurança:

- [ ] `DEBUG=False` em produção
- [ ] `SECRET_KEY` forte e única
- [ ] HTTPS configurado (SSL/TLS)
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] Firewall configurado
- [ ] Backups automáticos do banco de dados
- [ ] Variáveis sensíveis em variáveis de ambiente (nunca no código)
- [ ] Atualizações de segurança regulares

## 🗄️ Banco de Dados

### Opção 1: Banco Gerenciado (Recomendado)

Use um banco MySQL gerenciado:
- AWS RDS
- DigitalOcean Managed Database
- Google Cloud SQL
- Azure Database for MySQL

### Opção 2: Banco no Docker Compose

Se usar o MySQL do docker-compose, configure volumes para persistência:
```yaml
volumes:
  mysql_data:
    driver: local
```

### Fazer backup do banco:
```bash
docker exec siga-db mysqldump -u monitor_user -p monitor_srnco2 > backup.sql
```

### Restaurar backup:
```bash
docker exec -i siga-db mysql -u monitor_user -p monitor_srnco2 < backup.sql
```

## 🔄 Atualizações

Para atualizar a aplicação:

```bash
# Pull das mudanças
git pull origin main

# Rebuild do container
docker-compose down
docker-compose up -d --build

# Executar migrações
docker-compose exec web python manage.py migrate
```

## 📈 Escalabilidade

### Aumentar workers do Gunicorn:

Edite o Dockerfile ou sobrescreva o comando:

```bash
gunicorn config.wsgi:application \
  --workers 8 \
  --threads 4 \
  --bind 0.0.0.0:8000
```

Fórmula recomendada: `workers = (2 x CPU cores) + 1`

## ❓ Troubleshooting

### Container não inicia:
```bash
docker logs siga-web
```

### Erro de conexão com banco:
- Verifique se `DATABASE_URL` está correto
- Verifique se o banco está acessível
- Teste conexão: `docker-compose exec web python manage.py dbshell`

### Arquivos estáticos não carregam:
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Worker não processa tarefas:
```bash
docker logs siga-worker
# Verifique se o worker está rodando
docker-compose ps
```

## 📞 Suporte

Para problemas ou dúvidas, consulte a documentação do Django ou entre em contato com a equipe de desenvolvimento.

---

**Sistema SIGA** - Sistema Integrado de Gestão e Acompanhamento
