# ✅ Checklist de Deploy - Sistema SIGA

Use este checklist para garantir que todos os passos foram executados corretamente antes e depois do deploy.

## 📋 Pré-Deploy

### Código e Configurações

- [ ] Código commitado no Git
- [ ] Branch de produção atualizada (`main` ou `production`)
- [ ] Arquivo `.env` configurado (não commitar no Git!)
- [ ] `SECRET_KEY` única e segura gerada
- [ ] `DEBUG=False` em produção
- [ ] `ALLOWED_HOSTS` configurado com domínios corretos
- [ ] `DATABASE_URL` ou credenciais do banco configuradas
- [ ] Configurações de email testadas
- [ ] API_ROBO_SECRET_HASH gerado

### Arquivos Essenciais

- [ ] `Dockerfile` criado
- [ ] `.dockerignore` criado
- [ ] `requirements.txt` atualizado com todas as dependências
- [ ] `docker-compose.yml` configurado (se aplicável)
- [ ] `nginx.conf` configurado (se usar Nginx)

### Banco de Dados

- [ ] Banco de dados MySQL criado
- [ ] Usuário do banco criado com permissões adequadas
- [ ] Backup do banco local realizado (se migrar dados)
- [ ] Teste de conexão com banco realizado

### Testes Locais

- [ ] Aplicação testada localmente
- [ ] Worker testado e funcionando
- [ ] Importação CSV testada
- [ ] API testada com hash de autenticação
- [ ] Build do Docker testado localmente
- [ ] `docker-compose up` testado (se aplicável)

## 🚀 Durante o Deploy

### Easypanel - Serviço Web

- [ ] Serviço `siga-web` criado
- [ ] Repositório Git conectado
- [ ] Branch correta selecionada
- [ ] Dockerfile path configurado
- [ ] Porta 8000 configurada
- [ ] Variáveis de ambiente adicionadas:
  - [ ] `SECRET_KEY`
  - [ ] `DEBUG=False`
  - [ ] `ALLOWED_HOSTS`
  - [ ] `DATABASE_URL`
  - [ ] `EMAIL_HOST`
  - [ ] `EMAIL_PORT`
  - [ ] `EMAIL_USE_TLS`
  - [ ] `EMAIL_HOST_USER`
  - [ ] `EMAIL_HOST_PASSWORD`
  - [ ] `API_ROBO_SECRET_HASH`
  - [ ] Variáveis Azure AD (se aplicável)
- [ ] Build iniciado
- [ ] Build concluído sem erros
- [ ] Container iniciou com sucesso

### Easypanel - Worker

- [ ] Serviço `siga-worker` criado
- [ ] Mesmo repositório Git conectado
- [ ] Command override: `python manage.py worker`
- [ ] Mesmas variáveis de ambiente do `siga-web`
- [ ] Build concluído
- [ ] Worker em execução

### Banco de Dados

- [ ] Migrações executadas:
  ```bash
  python manage.py migrate
  ```
- [ ] Arquivos estáticos coletados:
  ```bash
  python manage.py collectstatic --noinput
  ```
- [ ] Dados iniciais populados (se necessário):
  ```bash
  python manage.py popular_filas_iniciais
  python manage.py setup_justificativas
  ```

### Superusuário

- [ ] Superusuário criado:
  ```bash
  python manage.py createsuperuser
  ```
- [ ] Login no admin testado

## ✅ Pós-Deploy

### Verificações Básicas

- [ ] Health check funcionando: `/api/health/`
- [ ] Página de login carregando
- [ ] Login funcionando
- [ ] Dashboard carregando
- [ ] Arquivos estáticos carregando (CSS, JS, imagens)
- [ ] Admin Django acessível: `/admin/`

### Funcionalidades Principais

- [ ] Lista de tarefas carregando
- [ ] Detalhes de tarefa funcionando
- [ ] Dashboard de coordenador funcionando
- [ ] Sistema de justificativas operacional
- [ ] Sistema de solicitações funcionando
- [ ] Importação CSV testada
- [ ] Worker processando tarefas

### API

- [ ] Endpoint `/api/health/` respondendo
- [ ] Autenticação da API funcionando
- [ ] Endpoints principais testados:
  - [ ] `GET /api/tarefas/`
  - [ ] `POST /api/tarefas/criar/`
  - [ ] `GET /api/servidor/<cpf>/`

### Performance e Logs

- [ ] Tempo de resposta aceitável (< 2s)
- [ ] Logs sem erros críticos
- [ ] Worker logs sem erros
- [ ] Memória e CPU em níveis normais

### Segurança

- [ ] HTTPS ativado (se domínio próprio)
- [ ] Certificado SSL válido
- [ ] Headers de segurança corretos
- [ ] CSRF protection ativo
- [ ] Variáveis sensíveis não expostas
- [ ] Firewall configurado

### Backup e Monitoramento

- [ ] Backup automático do banco configurado
- [ ] Monitoramento de uptime configurado
- [ ] Alertas de erro configurados
- [ ] Logs sendo salvos/armazenados

### Domínio e DNS (se aplicável)

- [ ] Domínio personalizado configurado
- [ ] DNS apontando corretamente
- [ ] SSL/TLS configurado para domínio
- [ ] Redirecionamento HTTP → HTTPS ativo
- [ ] `ALLOWED_HOSTS` atualizado com novo domínio

## 📊 Métricas de Sucesso

- [ ] Uptime > 99%
- [ ] Tempo de resposta < 2s
- [ ] 0 erros críticos nos logs
- [ ] Worker processando tarefas em < 5min
- [ ] Importação CSV funcionando

## 🔄 Rollback (Se necessário)

### Em caso de problemas:

1. [ ] Logs coletados e analisados
2. [ ] Erro identificado
3. [ ] Decisão: Fix ou Rollback?

### Se Rollback:

- [ ] Reverter para versão anterior no Git
- [ ] Fazer redeploy da versão estável
- [ ] Restaurar backup do banco (se necessário)
- [ ] Verificar que sistema voltou ao normal
- [ ] Documentar problema para correção

## 📝 Documentação Pós-Deploy

- [ ] URLs de produção documentadas
- [ ] Credenciais salvas em local seguro (password manager)
- [ ] Equipe notificada do deploy
- [ ] Changelog atualizado
- [ ] Documentação de API atualizada (se houve mudanças)

## 🎯 Próximos Passos

- [ ] Monitorar logs por 24h
- [ ] Coletar feedback dos usuários
- [ ] Otimizações identificadas documentadas
- [ ] Planejar próximas features

---

## ✨ Deploy Concluído!

Data do Deploy: _______________
Responsável: _______________
Versão: _______________

**Sistema SIGA** está em produção! 🚀
