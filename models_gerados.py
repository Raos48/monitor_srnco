# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('UsuariosAppCustomuser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Tarefas(models.Model):
    numero_protocolo_tarefa = models.BigIntegerField(primary_key=True)
    indicador_subtarefas_pendentes = models.IntegerField()
    codigo_unidade_tarefa = models.IntegerField()
    nome_servico = models.CharField(max_length=255)
    status_tarefa = models.CharField(max_length=100)
    descricao_cumprimento_exigencia_tarefa = models.TextField(blank=True, null=True)
    data_distribuicao_tarefa = models.DateField(blank=True, null=True)
    data_ultima_atualizacao = models.DateField(blank=True, null=True)
    data_fim_ultima_exigencia = models.DateField(blank=True, null=True)
    tempo_ultima_exigencia_em_dias = models.IntegerField(blank=True, null=True)
    tempo_em_pendencia_em_dias = models.IntegerField()
    tempo_em_exigencia_em_dias = models.IntegerField()
    tempo_ate_ultima_distribuicao_tarefa_em_dias = models.IntegerField()
    codigo_gex_responsavel = models.CharField(max_length=10, blank=True, null=True)
    data_processamento_tarefa = models.DateTimeField(blank=True, null=True)
    nome_gex_responsavel = models.CharField(max_length=255, blank=True, null=True)
    nome_profissional_responsavel = models.CharField(max_length=255, blank=True, null=True)
    siape_responsavel = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tarefas'


class TarefasAppNotificacaoemail(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=20)
    assunto = models.CharField(max_length=255)
    mensagem = models.TextField()
    enviado_em = models.DateTimeField()
    sucesso = models.BooleanField()
    erro = models.TextField(blank=True, null=True)
    destinatario = models.ForeignKey('UsuariosAppCustomuser', models.DO_NOTHING)
    remetente = models.ForeignKey('UsuariosAppCustomuser', models.DO_NOTHING, related_name='tarefasappnotificacaoemail_remetente_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tarefas_app_notificacaoemail'


class UsuariosAppCustomuser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    nome_completo = models.CharField(max_length=255)
    siape = models.CharField(unique=True, max_length=7)
    cpf = models.CharField(unique=True, max_length=14, blank=True, null=True)
    lotacao = models.CharField(max_length=255)
    gex = models.CharField(max_length=255)
    email = models.CharField(unique=True, max_length=254)
    bloqueado = models.BooleanField()
    bloqueado_por = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    data_bloqueio = models.DateTimeField(blank=True, null=True)
    motivo_bloqueio = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios_app_customuser'


class UsuariosAppCustomuserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(UsuariosAppCustomuser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuarios_app_customuser_groups'
        unique_together = (('customuser', 'group'),)


class UsuariosAppCustomuserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(UsuariosAppCustomuser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuarios_app_customuser_user_permissions'
        unique_together = (('customuser', 'permission'),)
