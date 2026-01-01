from django.apps import AppConfig


class TarefasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tarefas'
    verbose_name = 'Tarefas e Filas'

    def ready(self):
        """Importa os admins quando o app estiver pronto"""
        import tarefas.admin  # noqa
        import tarefas.admin_acoes  # noqa
