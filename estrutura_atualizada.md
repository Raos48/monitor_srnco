monitor_srnco/
│
├── .gitignore
├── Comandos.md
├── manage.py
├── convert_encoding.py
├── models_gerados.py
│
├── config/                          # Configurações principais do Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                            # App principal
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
│
├── tarefas/                         # App de gestão de tarefas
│   ├── __init__.py
│   ├── admin.py
│   ├── analisador.py
│   ├── apps.py
│   ├── models.py
│   ├── parametros.py
│   ├── parametros_admin.py
│   ├── tarefas_properties_criticidade.py
│   ├── urls.py
│   ├── views.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       ├── diagnostico_kpis.py
│   │       └── testar_analisador.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   ├── 0002_initial.py
│   │   ├── 0003_alter_tarefa_numero_protocolo_tarefa.py
│   │   ├── 0004_tarefa_data_inicio_ultima_exigencia_and_more.py
│   │   ├── 0005_parametrosanalise_historicoalteracaoprazos.py
│   │   └── 0006_tarefa_alerta_criticidade_calculado_and_more.py
│   └── tests/
│       └── test_analisador.py
│
├── importar_csv/                    # App para importação de dados CSV
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   ├── 0002_initial.py
│   │   ├── 0003_initial.py
│   │   └── 0004_historicotarefa_data_inicio_ultima_exigencia_and_more.py
│   └── templates/
│       └── importar_csv/
│           └── importar.html
│
├── usuarios/                        # App de gestão de usuários
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── importar_emails.py
│   └── migrations/
│       ├── __init__.py
│       ├── 0001_initial.py
│       └── 0002_alter_customuser_email.py
│
├── templates/                       # Templates HTML
│   ├── base.html
│   ├── base_OLD_BACKUP.html
│   ├── base_new.html
│   ├── teste_visual.html
│   ├── components/
│   │   ├── footer.html
│   │   ├── logout.html
│   │   ├── navbar_top.html
│   │   └── sidebar.html
│   ├── dashboards/
│   │   ├── dashboard_admin.html
│   │   ├── dashboard_coordenador.html
│   │   ├── dashboard_coordenador_OLD.html
│   │   ├── dashboard_servidor.html
│   │   └── dashboard_servidor_OLD.html
│   ├── registration/
│   │   └── login.html
│   └── tarefas/
│       ├── detalhe_servidor.html
│       ├── detalhe_tarefa.html
│       ├── lista_servidores.html
│       └── lista_tarefas.html
│
└── static/                          # Arquivos estáticos (CSS, JS, imagens)
    └── css/
        ├── global.css
        └── style.css