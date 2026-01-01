# 🚀 Deploy Rápido no Easypanel - Sistema SIGA

## Passo a Passo Simplificado

### 1️⃣ Preparar o Projeto

Certifique-se de que os seguintes arquivos estão no seu repositório Git:
- ✅ `Dockerfile` (arquivo principal para produção)
- ✅ `Dockerfile.easypanel` (versão simplificada, opcional)
- ✅ `.dockerignore`
- ✅ `requirements.txt`
- ✅ `.env.example` (modelo de variáveis)

### 2️⃣ Criar Banco de Dados MySQL no Easypanel

1. No Easypanel, clique em **"+ Create"**
2. Selecione **"Database"** > **"MySQL"**
3. Configure:
   - **Name**: `siga-db`
   - **MySQL Version**: 8.0
   - **Root Password**: [senha segura]
   - **Database**: `monitor_srnco2`
   - **User**: `monitor_user`
   - **Password**: [senha segura]
4. Clique em **"Create"**
5. **Anote a DATABASE_URL** que será mostrada (formato: `mysql://user:pass@host:port/database`)

### 3️⃣ Criar Serviço Web (Aplicação Principal)

1. No Easypanel, clique em **"+ Create"**
2. Selecione **"App"** > **"From Git"**
3. Configure:

#### **General Settings:**
- **Name**: `siga-web`
- **Git Repository**: [URL do seu repositório]
- **Branch**: `main` (ou sua branch principal)

#### **Build Settings:**
- **Build Type**: `Dockerfile`
- **Dockerfile Path**: `./Dockerfile`
- **Build Context**: `.`

#### **Deployment:**
- **Port**: `8000`

#### **Environment Variables** (copie e cole):

```env
# Django Core
SECRET_KEY=gere-uma-chave-secreta-forte-aqui
DEBUG=False
ALLOWED_HOSTS=seu-app.easypanel.app,seu-dominio.com

# Database (use a URL fornecida pelo banco MySQL criado anteriormente)
DATABASE_URL=mysql://monitor_user:SUA_SENHA@siga-db:3306/monitor_srnco2

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app-do-gmail
DEFAULT_FROM_EMAIL=seu-email@gmail.com

# Azure AD (opcional - para email corporativo)
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_TENANT_ID=
SENDER_EMAIL=

# API
API_ROBO_SECRET_HASH=gere-um-hash-aleatorio-seguro
```

#### **Resources:**
- **CPU**: 0.5-1 core
- **Memory**: 512MB - 1GB
- **Storage**: 5GB (mínimo)

4. Clique em **"Deploy"**
5. Aguarde o build e deploy (pode levar 2-5 minutos)

### 4️⃣ Criar Worker (Processamento Background)

1. Clique em **"+ Create"** novamente
2. Selecione **"App"** > **"From Git"**
3. Configure:

#### **General Settings:**
- **Name**: `siga-worker`
- **Git Repository**: [mesmo repositório]
- **Branch**: `main`

#### **Build Settings:**
- **Build Type**: `Dockerfile`
- **Dockerfile Path**: `./Dockerfile`

#### **Command Override:**
```bash
python manage.py worker
```

#### **Environment Variables:**
- ✅ **Copie TODAS as mesmas variáveis do serviço `siga-web`**

#### **Resources:**
- **CPU**: 0.25-0.5 core
- **Memory**: 256MB - 512MB

4. Clique em **"Deploy"**

### 5️⃣ Executar Migrações Iniciais

Após o deploy bem-sucedido:

1. Acesse o console do serviço `siga-web`
2. Execute:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

3. (Opcional) Criar superusuário:
```bash
python manage.py createsuperuser
```

### 6️⃣ Configurar Domínio Personalizado (Opcional)

1. No serviço `siga-web`, vá em **"Domains"**
2. Adicione seu domínio
3. Configure DNS do seu domínio:
   - Adicione registro CNAME apontando para o domínio fornecido pelo Easypanel
4. Aguarde propagação DNS (pode levar até 48h)
5. Atualize a variável `ALLOWED_HOSTS` para incluir seu domínio

## ✅ Verificação do Deploy

Após o deploy, verifique:

### 1. Health Check
```
https://seu-app.easypanel.app/api/health/
```
Deve retornar:
```json
{
  "status": "ok",
  "mensagem": "API do Sistema SIGA está funcionando"
}
```

### 2. Admin
```
https://seu-app.easypanel.app/admin/
```

### 3. Logs
- Acesse os logs no Easypanel para verificar se há erros
- Verifique logs do `siga-web` e `siga-worker`

## 🔧 Troubleshooting

### ❌ Erro: "Database connection failed"
- Verifique se a `DATABASE_URL` está correta
- Confirme que o banco de dados está rodando
- Teste conexão no console do container

### ❌ Erro: "Static files not loading"
```bash
python manage.py collectstatic --noinput --clear
```

### ❌ Erro: "Worker não processa tarefas"
- Verifique logs do `siga-worker`
- Confirme que as variáveis de ambiente estão iguais ao `siga-web`

### ❌ Erro: "Bad Gateway (502)"
- Aguarde alguns minutos (container pode estar iniciando)
- Verifique se a porta 8000 está configurada corretamente
- Verifique logs para erros de inicialização

## 🔐 Gerando Chaves Secretas

### SECRET_KEY do Django:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Ou use um gerador online:
```
https://djecrety.ir/
```

### API_ROBO_SECRET_HASH:
```bash
openssl rand -hex 32
```

## 📊 Monitoramento

- **Logs em tempo real**: Easypanel > App > Logs
- **Métricas**: Easypanel > App > Metrics
- **Health Check**: Configure alertas no Easypanel

## 🔄 Atualizações

Para atualizar a aplicação:

1. Faça commit e push das mudanças no Git
2. No Easypanel, clique em **"Redeploy"** no serviço `siga-web`
3. Aguarde o novo build
4. Se houver migrações, execute-as no console:
```bash
python manage.py migrate
```

## 📞 Suporte

- **Documentação completa**: Ver [DEPLOY.md](DEPLOY.md)
- **Issues**: Reporte problemas no GitHub
- **Email**: Contate a equipe de desenvolvimento

---

**Sistema SIGA** - Deploy concluído! 🎉
