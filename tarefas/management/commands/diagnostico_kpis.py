"""
SCRIPT DE DIAGNÓSTICO - Dashboard Zerado
Execute este script no Django shell para identificar o problema

Uso:
python manage.py shell < diagnostico_kpis.py
"""

print("="*70)
print("DIAGNÓSTICO DO SISTEMA DE CRITICIDADE")
print("="*70)
print()

# ============================================
# TESTE 1: Verificar se existem tarefas
# ============================================
print("📋 TESTE 1: Verificando tarefas no banco...")
from tarefas.models import Tarefa

total_tarefas = Tarefa.objects.count()
print(f"   Total de tarefas no banco: {total_tarefas}")

if total_tarefas == 0:
    print("   ❌ PROBLEMA: Não há tarefas no banco de dados!")
    print("   SOLUÇÃO: Importe tarefas via CSV antes de continuar.")
    exit()
else:
    print(f"   ✅ OK: {total_tarefas} tarefas encontradas")
print()

# ============================================
# TESTE 2: Verificar properties instaladas
# ============================================
print("📋 TESTE 2: Verificando properties de criticidade...")
tarefa = Tarefa.objects.first()

try:
    nivel = tarefa.nivel_criticidade
    print(f"   ✅ Property 'nivel_criticidade' funcionando: {nivel}")
except AttributeError as e:
    print(f"   ❌ PROBLEMA: Property 'nivel_criticidade' não encontrada!")
    print(f"   ERRO: {e}")
    print("   SOLUÇÃO: Instale a ETAPA 3 (Properties no modelo Tarefa)")
    exit()

try:
    regra = tarefa.regra_aplicada
    print(f"   ✅ Property 'regra_aplicada' funcionando: {regra}")
except AttributeError as e:
    print(f"   ❌ PROBLEMA: Property 'regra_aplicada' não encontrada!")
    print(f"   SOLUÇÃO: Instale a ETAPA 3 (Properties no modelo Tarefa)")
    exit()

try:
    alerta = tarefa.alerta_criticidade
    print(f"   ✅ Property 'alerta_criticidade' funcionando: {alerta[:50]}...")
except AttributeError as e:
    print(f"   ❌ PROBLEMA: Property 'alerta_criticidade' não encontrada!")
    exit()

print()

# ============================================
# TESTE 3: Verificar analisador
# ============================================
print("📋 TESTE 3: Verificando analisador de criticidade...")
try:
    from tarefas.analisador import obter_analisador
    analisador = obter_analisador()
    print(f"   ✅ Analisador criado com sucesso")
    print(f"   Data referência: {analisador.data_referencia}")
    
    resultado = analisador.analisar_tarefa(tarefa)
    print(f"   ✅ Análise funcionando:")
    print(f"      - Regra: {resultado['regra']}")
    print(f"      - Severidade: {resultado['severidade']}")
except Exception as e:
    print(f"   ❌ PROBLEMA: Erro ao usar analisador!")
    print(f"   ERRO: {e}")
    exit()

print()

# ============================================
# TESTE 4: Verificar método estatísticas
# ============================================
print("📋 TESTE 4: Testando método estatisticas_criticidade...")
try:
    stats = Tarefa.estatisticas_criticidade()
    print(f"   ✅ Método funcionando!")
    print(f"   Resultados:")
    print(f"      - Total: {stats['total']}")
    print(f"      - Críticas: {stats['CRÍTICA']}")
    print(f"      - Altas: {stats['ALTA']}")
    print(f"      - Médias: {stats['MÉDIA']}")
    print(f"      - Baixas: {stats['BAIXA']}")
    print(f"      - Normais: {stats['NENHUMA']}")
except Exception as e:
    print(f"   ❌ PROBLEMA: Erro no método estatisticas_criticidade!")
    print(f"   ERRO: {e}")
    exit()

print()

# ============================================
# TESTE 5: Simular view do coordenador
# ============================================
print("📋 TESTE 5: Simulando dashboard do coordenador...")
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    # Buscar todas as tarefas
    tarefas = Tarefa.objects.select_related('siape_responsavel').all()
    print(f"   ✅ Tarefas carregadas: {tarefas.count()}")
    
    # Calcular estatísticas
    stats = Tarefa.estatisticas_criticidade(tarefas)
    print(f"   ✅ Estatísticas calculadas:")
    print(f"      - Total: {stats['total']}")
    print(f"      - Críticas: {stats['CRÍTICA']} ({stats.get('percentual_CRÍTICA', 0)}%)")
    print(f"      - Altas: {stats['ALTA']} ({stats.get('percentual_ALTA', 0)}%)")
    print(f"      - Médias: {stats['MÉDIA']} ({stats.get('percentual_MÉDIA', 0)}%)")
    print(f"      - Com criticidade: {stats['com_criticidade']}")
    
    # Filtrar prioritárias
    prioritarias = [t for t in tarefas if t.nivel_criticidade in ['CRÍTICA', 'ALTA']]
    print(f"   ✅ Tarefas prioritárias: {len(prioritarias)}")
    
    if len(prioritarias) > 0:
        print(f"   Exemplo de tarefa prioritária:")
        t = prioritarias[0]
        print(f"      - Protocolo: {t.numero_protocolo_tarefa}")
        print(f"      - Nível: {t.nivel_criticidade}")
        print(f"      - Regra: {t.regra_aplicada}")
        print(f"      - Alerta: {t.alerta_criticidade[:60]}...")
    
except Exception as e:
    print(f"   ❌ PROBLEMA na simulação da view!")
    print(f"   ERRO: {e}")
    import traceback
    traceback.print_exc()
    exit()

print()

# ============================================
# RESULTADO FINAL
# ============================================
print("="*70)
print("✅ DIAGNÓSTICO COMPLETO!")
print("="*70)
print()
print("Todos os componentes estão funcionando corretamente.")
print()
print("Se o dashboard ainda mostra zeros, o problema está na VIEW.")
print("Verifique se você atualizou corretamente o arquivo views.py")
print()
print("KPIs esperados no dashboard:")
print(f"   - Total: {stats['total']}")
print(f"   - 🔴 Críticas: {stats['CRÍTICA']}")
print(f"   - 🟠 Altas: {stats['ALTA']}")
print(f"   - 🟡 Médias: {stats['MÉDIA']}")
print(f"   - 🟢 Baixas: {stats['BAIXA']}")
print(f"   - ⚪ Normais: {stats['NENHUMA']}")
print()