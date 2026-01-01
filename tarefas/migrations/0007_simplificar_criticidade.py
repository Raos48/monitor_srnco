# Generated migration file for criticidade simplification

from django.db import migrations, models


def migrar_dados_criticidade(apps, schema_editor):
    """
    Migra os dados existentes de 5 níveis para 2 níveis.
    
    Estratégia:
    - CRÍTICA, ALTA, MÉDIA → CRÍTICA (prazos estourados ou próximos)
    - BAIXA, NENHUMA → REGULAR (dentro do prazo)
    """
    Tarefa = apps.get_model('tarefas', 'Tarefa')
    
    # Tarefas que se tornam CRÍTICAS
    tarefas_criticas = Tarefa.objects.filter(
        nivel_criticidade_calculado__in=['CRÍTICA', 'ALTA', 'MÉDIA']
    )
    tarefas_criticas.update(
        nivel_criticidade_calculado='CRÍTICA',
        pontuacao_criticidade=100,
        cor_criticidade_calculado='#dc3545'  # Vermelho
    )
    
    print(f"✅ {tarefas_criticas.count()} tarefas migradas para CRÍTICA")
    
    # Tarefas que se tornam REGULARES
    tarefas_regulares = Tarefa.objects.filter(
        nivel_criticidade_calculado__in=['BAIXA', 'NENHUMA']
    )
    tarefas_regulares.update(
        nivel_criticidade_calculado='REGULAR',
        pontuacao_criticidade=0,
        cor_criticidade_calculado='#28a745'  # Verde
    )
    
    print(f"✅ {tarefas_regulares.count()} tarefas migradas para REGULAR")


def reverter_migracao(apps, schema_editor):
    """
    Reversão da migração (se necessário).
    
    ATENÇÃO: Esta reversão é APROXIMADA pois perdemos informação
    ao simplificar de 5 para 2 níveis.
    """
    Tarefa = apps.get_model('tarefas', 'Tarefa')
    
    # Críticas permanecem críticas
    Tarefa.objects.filter(
        nivel_criticidade_calculado='CRÍTICA'
    ).update(
        pontuacao_criticidade=5
    )
    
    # Regulares viram NENHUMA
    Tarefa.objects.filter(
        nivel_criticidade_calculado='REGULAR'
    ).update(
        nivel_criticidade_calculado='NENHUMA',
        pontuacao_criticidade=0,
        cor_criticidade_calculado='#6c757d'  # Cinza
    )


class Migration(migrations.Migration):

    dependencies = [
        ('tarefas', '0006_tarefa_alerta_criticidade_calculado_and_more'),
    ]

    operations = [
        # 1. Primeiro alteramos as choices do campo
        migrations.AlterField(
            model_name='tarefa',
            name='nivel_criticidade_calculado',
            field=models.CharField(
                choices=[
                    ('CRÍTICA', 'Crítica'),
                    ('REGULAR', 'Regular')
                ],
                db_index=True,
                default='REGULAR',
                max_length=10,
                verbose_name='Nível de Criticidade (Calculado)'
            ),
        ),
        
        # 2. Depois migramos os dados
        migrations.RunPython(
            migrar_dados_criticidade,
            reverse_code=reverter_migracao
        ),
    ]