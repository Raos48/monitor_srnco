"""
Script para recalcular criticidades de todas as tarefas
Execute: python recalcular_agora.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tarefas.models import Tarefa
from tarefas.analisador import obter_analisador
from django.utils import timezone

print("=" * 80)
print("RECALCULANDO CRITICIDADES DE TODAS AS TAREFAS")
print("=" * 80)

analisador = obter_analisador()
tarefas = Tarefa.objects.all()
total = tarefas.count()

print(f"\nTotal de tarefas: {total}")
print("\nIniciando recálculo...")

atualizadas = 0
erros = 0

for i, tarefa in enumerate(tarefas, 1):
    try:
        # Atualizar flags de justificativa
        if hasattr(tarefa, 'atualizar_flags_justificativa'):
            tarefa.atualizar_flags_justificativa()

        # Analisar criticidade
        resultado = analisador.analisar_tarefa(tarefa)

        # Atualizar campos
        tarefa.nivel_criticidade_calculado = resultado['nivel']
        tarefa.regra_aplicada_calculado = resultado['regra']
        tarefa.alerta_criticidade_calculado = resultado['alerta']
        tarefa.descricao_criticidade_calculado = resultado['descricao']
        tarefa.dias_pendente_criticidade_calculado = resultado['dias_pendente']
        tarefa.prazo_limite_criticidade_calculado = resultado['prazo_limite']
        tarefa.cor_criticidade_calculado = resultado['cor']

        # Calcular pontuação
        ordem_severidade = {
            'CRÍTICA': 5,
            'JUSTIFICADA': 4,
            'EXCLUÍDA': 3,
            'REGULAR': 2,
        }
        tarefa.pontuacao_criticidade = ordem_severidade.get(resultado['nivel'], 0)
        tarefa.data_calculo_criticidade = timezone.now()

        # Salvar
        tarefa.save(update_fields=[
            'nivel_criticidade_calculado',
            'regra_aplicada_calculado',
            'alerta_criticidade_calculado',
            'descricao_criticidade_calculado',
            'dias_pendente_criticidade_calculado',
            'prazo_limite_criticidade_calculado',
            'pontuacao_criticidade',
            'cor_criticidade_calculado',
            'data_calculo_criticidade',
            'tem_justificativa_ativa',
            'tem_solicitacao_ajuda',
            'servico_excluido_criticidade',
        ])

        atualizadas += 1

        # Mostrar progresso a cada 100 tarefas
        if i % 100 == 0:
            print(f"  Processadas: {i}/{total} ({(i/total*100):.1f}%)")

    except Exception as e:
        erros += 1
        print(f"  ❌ Erro na tarefa {tarefa.numero_protocolo_tarefa}: {e}")

print("\n" + "=" * 80)
print("RECÁLCULO CONCLUÍDO!")
print("=" * 80)
print(f"\n✅ Tarefas atualizadas: {atualizadas}")
if erros > 0:
    print(f"❌ Erros: {erros}")

# Mostrar estatísticas
from collections import Counter
print("\n" + "=" * 80)
print("DISTRIBUIÇÃO DAS REGRAS APLICADAS:")
print("=" * 80)

regras = Tarefa.objects.values_list('regra_aplicada_calculado', flat=True)
contagem = Counter(regras)

for regra, count in sorted(contagem.items(), key=lambda x: x[1], reverse=True):
    from tarefas.analisador import obter_nome_regra_amigavel
    nome_amigavel = obter_nome_regra_amigavel(regra) if regra else "Sem Regra"
    percentual = (count / total * 100)
    print(f"  {nome_amigavel:50s} : {count:6d} ({percentual:5.1f}%)")

print("\n" + "=" * 80)
print("Estatísticas de Criticidade:")
print("=" * 80)

stats = Tarefa.estatisticas_criticidade()
print(f"\n  Total: {stats.get('total', 0)}")
print(f"  Críticas: {stats.get('criticas', 0)} ({stats.get('percentual_criticas', 0):.1f}%)")
print(f"  Regulares: {stats.get('regulares', 0)} ({stats.get('percentual_regulares', 0):.1f}%)")

print("\n✅ Pronto! Atualize a página do navegador para ver as mudanças.\n")
