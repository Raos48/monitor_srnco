# 📊 Sistema SIGA - Sistema Integrado de Gestão e Acompanhamento

Sistema web desenvolvido em Django para gestão e monitoramento de tarefas e filas de trabalho do SRNCO/INSS.

## 🚀 Características

- ✅ **Gestão de Tarefas**: Controle completo de tarefas com níveis de criticidade
- ✅ **Filas de Trabalho**: Organização por diferentes tipos de filas
- ✅ **Dashboard Coordenador**: Visão completa de KPIs e métricas
- ✅ **Sistema de Justificativas**: Análise e aprovação de justificativas
- ✅ **Solicitações de Ajuda**: Sistema de suporte entre servidores
- ✅ **Worker Assíncrono**: Processamento de tarefas em background
- ✅ **Importação CSV**: Upload e processamento de dados em lote
- ✅ **API REST**: Integração com robôs e sistemas externos
- ✅ **Notificações por Email**: Alertas automáticos (SMTP/Azure AD)

## 🛠️ Tecnologias

- **Backend**: Django 5.2.7
- **Database**: MySQL 8.0
- **Frontend**: Bootstrap 5.3, Chart.js
- **API**: Django REST Framework
- **Task Queue**: Django Background Tasks
- **Deploy**: Docker, Gunicorn, Nginx

## 📁 Estrutura do Projeto

```
monitor_srnco/
├── config/              # Configurações do Django
├── core/                # App principal
├── usuarios/            # Gestão de usuários
├── tarefas/             # App de tarefas e filas
│   ├── api/            # Endpoints da API
│   ├── management/     # Commands customizados
│   ├── services/       # Lógica de negócio
│   └── filas.py        # Sistema de filas
├── importar_csv/        # Importação de dados
├── templates/           # Templates HTML
├── static/              # Arquivos estáticos
├── Dockerfile           # Container de produção
├── docker-compose.yml   # Orquestração local
└── requirements.txt     # Dependências Python
```

## 🏁 Início Rápido

### Desenvolvimento Local

1. **Clone o repositório**
```bash
git clone <seu-repositorio>
cd monitor_srnco
```

2. **Crie ambiente virtual**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. **Instale dependências**
```bash
pip install -r requirements.txt
```

4. **Configure variáveis de ambiente**
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

5. **Execute migrações**
```bash
python manage.py migrate
```

6. **Crie superusuário**
```bash
python manage.py createsuperuser
```

7. **Inicie o servidor**
```bash
python manage.py runserver
```

8. **Inicie o worker** (em outro terminal)
```bash
python manage.py worker
```

Acesse: `http://localhost:8000`

### Deploy com Docker

```bash
# Build e iniciar containers
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar containers
docker-compose down
```

## 🚢 Deploy em Produção

### Easypanel (Recomendado)

Consulte o guia detalhado: **[EASYPANEL_DEPLOY.md](EASYPANEL_DEPLOY.md)**

Resumo:
1. Criar banco de dados MySQL
2. Criar serviço `siga-web`
3. Criar serviço `siga-worker`
4. Configurar variáveis de ambiente
5. Deploy!

### Docker (Genérico)

Consulte: **[DEPLOY.md](DEPLOY.md)**

## 📚 Documentação da API

### Health Check
```
GET /api/health/
```

### Listar Tarefas
```
GET /api/tarefas/
Authorization: X-API-Hash: <hash-secreto>
```

### Criar Tarefa
```
POST /api/tarefas/criar/
Authorization: X-API-Hash: <hash-secreto>
Content-Type: application/json

{
  "numero_processo": "12345678901",
  "servidor_cpf": "12345678901",
  // ... outros campos
}
```

Documentação completa: **[DOCUMENTACAO_API_ROBO.md](DOCUMENTACAO_API_ROBO.md)**

## 🔐 Segurança

- ✅ HTTPS obrigatório em produção
- ✅ SECRET_KEY única e segura
- ✅ CSRF protection ativado
- ✅ XSS protection
- ✅ SQL Injection protection (ORM)
- ✅ Autenticação hash para API
- ✅ Variáveis sensíveis em ambiente

## 👥 Perfis de Usuário

### Coordenador
- Acesso total ao dashboard
- Visualização de todas as filas
- Aprovação de justificativas
- Relatórios gerenciais

### Servidor
- Visualização de tarefas atribuídas
- Submissão de justificativas
- Solicitação de ajuda

### Equipe Volante
- Atendimento de solicitações
- Suporte a servidores

## 🔧 Comandos Úteis

### Gestão de Dados
```bash
# Popular filas iniciais
python manage.py popular_filas_iniciais

# Recalcular tarefas
python manage.py recalcular_tarefas

# Arquivar tarefas antigas
python manage.py arquivar_tarefas_antigas

# Diagnosticar KPIs
python manage.py diagnostico_kpis
```

### Worker
```bash
# Iniciar worker
python manage.py worker

# Worker com duração específica (segundos)
python manage.py worker --duration 3600
```

## 📊 Métricas e KPIs

O sistema calcula automaticamente:

- **Tarefas em atraso**: Por servidor e fila
- **Índice de criticidade**: Priorização inteligente
- **Tempo médio de execução**: Por tipo de tarefa
- **Taxa de conclusão**: Performance dos servidores
- **Distribuição de cargas**: Balanceamento de trabalho

## 🔄 Atualizações

```bash
# Pull das mudanças
git pull origin main

# Atualizar dependências
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Coletar estáticos
python manage.py collectstatic --noinput
```

## 🐛 Troubleshooting

### Erro de conexão com MySQL
```bash
# Verificar status do MySQL
systemctl status mysql

# Testar conexão
python manage.py dbshell
```

### Worker não processa tarefas
```bash
# Verificar tarefas pendentes
python manage.py

 shell
>>> from background_task.models import Task
>>> Task.objects.all()
```

### Arquivos estáticos não carregam
```bash
python manage.py collectstatic --clear --noinput
```

## 📝 Licença

Projeto desenvolvido para uso interno do INSS/SRNCO.

## 👨‍💻 Desenvolvimento

### Requisitos
- Python 3.11+
- MySQL 8.0+
- Node.js (opcional, para assets)

### Contribuir
1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: Reporte bugs no GitHub
- **Email**: Contate a equipe de desenvolvimento
- **Documentação**: Consulte os arquivos `.md` no projeto

---

**Sistema SIGA** - Desenvolvido com ❤️ para o SRNCO/INSS
