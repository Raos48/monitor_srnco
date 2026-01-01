"""
Tarefas ass�ncronas para processamento de importa��o de CSV.
Utiliza django-background-tasks para executar em segundo plano.
"""
from background_task import background
from django.utils import timezone
import csv
import io
import traceback
import os
from .models import RegistroImportacao


@background(schedule=0)
def processar_importacao_async(registro_id):
    """
    Tarefa ass�ncrona para processar importa��o de CSV.

    Esta fun��o � executada em segundo plano pelo worker do django-background-tasks.
    Processa o arquivo CSV em lotes e atualiza o progresso em tempo real.

    Args:
        registro_id: ID do RegistroImportacao a ser processado
    """
    from .views import ImportarCSVView

    try:
        # Buscar o registro de importa��o
        registro = RegistroImportacao.objects.get(id=registro_id)

        # Marcar como processando
        registro.status = 'PROCESSING'
        registro.data_inicio_processamento = timezone.now()
        registro.save(update_fields=['status', 'data_inicio_processamento'])

        print(f"\n{'='*80}")
        print(f"INICIANDO IMPORTA��O ASS�NCRONA")
        print(f"Registro ID: {registro_id}")
        print(f"Arquivo: {registro.nome_arquivo}")
        print(f"{'='*80}\n")

        # Ler arquivo CSV salvo temporariamente
        if not os.path.exists(registro.caminho_arquivo):
            raise FileNotFoundError(f"Arquivo n�o encontrado: {registro.caminho_arquivo}")

        with open(registro.caminho_arquivo, 'r', encoding='latin-1') as arquivo:
            data_set = arquivo.read()
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string, delimiter=',')
            next(reader)  # Pular cabeçalho

            # Contar total de linhas primeiro
            linhas = list(reader)
            registro.total_linhas = len(linhas)
            registro.save(update_fields=['total_linhas'])

            print(f"Total de linhas a processar: {len(linhas)}")

            # Processar em lotes
            view = ImportarCSVView()
            BATCH_SIZE = 2000
            total_criados = 0
            total_atualizados = 0
            usuarios_criados = 0

            # Coletar todos os protocolos presentes no CSV para comparação posterior
            todos_protocolos_csv = set()

            lote_dados_csv = {}

            for i, row in enumerate(linhas, 1):
                # Remove aspas dos valores
                row = [campo.strip('"').strip() for campo in row]
                protocolo = row[0].strip()

                # Valida��o: verifica se o protocolo n�o est� vazio
                if not protocolo:
                    continue

                # Adicionar protocolo ao conjunto de protocolos presentes no CSV
                todos_protocolos_csv.add(protocolo)

                lote_dados_csv[protocolo] = row

                # Processar lote
                if i % BATCH_SIZE == 0:
                    print(f"\nProcessando lote de {len(lote_dados_csv)} registros �nicos (linhas {i-BATCH_SIZE+1} a {i})...")

                    criados, atualizados, users_criados = view.processar_lote(
                        lote_dados_csv,
                        registro
                    )

                    total_criados += criados
                    total_atualizados += atualizados
                    usuarios_criados += users_criados

                    print(f"Lote processado: {criados} tarefas criadas, {atualizados} atualizadas, {users_criados} usu�rios criados.")

                    # Atualizar progresso
                    registro.linhas_processadas = i
                    registro.calcular_progresso()
                    registro.registros_criados = total_criados
                    registro.registros_atualizados = total_atualizados
                    registro.usuarios_criados = usuarios_criados
                    registro.save(update_fields=[
                        'linhas_processadas',
                        'progresso_percentual',
                        'registros_criados',
                        'registros_atualizados',
                        'usuarios_criados'
                    ])

                    print(f"Progresso: {registro.progresso_percentual:.1f}%")

                    lote_dados_csv = {}

            # Processar lote final (se houver sobra)
            if lote_dados_csv:
                print(f"\nProcessando lote final de {len(lote_dados_csv)} registros �nicos...")

                criados, atualizados, users_criados = view.processar_lote(
                    lote_dados_csv,
                    registro
                )

                total_criados += criados
                total_atualizados += atualizados
                usuarios_criados += users_criados

                print(f"Lote final processado: {criados} tarefas criadas, {atualizados} atualizadas, {users_criados} usu�rios criados.")

            # ETAPA FINAL: Arquivar tarefas ausentes do CSV (marcar como inativas)
            print(f"\n{'='*80}")
            print(f"ETAPA DE ARQUIVAMENTO - Verificando tarefas ausentes no CSV")
            print(f"{'='*80}")

            from tarefas.models import Tarefa

            # Contar quantas tarefas estão ativas no banco antes do arquivamento
            total_ativas_antes = Tarefa.objects.filter(ativa=True).count()
            print(f"\nTarefas ativas no banco antes do arquivamento: {total_ativas_antes}")
            print(f"Protocolos únicos no CSV importado: {len(todos_protocolos_csv)}")

            # Buscar todas as tarefas que estão marcadas como ativas mas NÃO estão no CSV atual
            tarefas_para_arquivar = Tarefa.objects.filter(
                ativa=True
            ).exclude(
                numero_protocolo_tarefa__in=todos_protocolos_csv
            )

            qtd_arquivadas = tarefas_para_arquivar.count()

            if qtd_arquivadas > 0:
                # Marcar como inativas (arquivadas)
                tarefas_para_arquivar.update(ativa=False)
                print(f"\n✓ {qtd_arquivadas} tarefas foram arquivadas (marcadas como inativas)")
                print(f"  Motivo: Não constam no arquivo CSV importado")
            else:
                print(f"\n✓ Nenhuma tarefa precisou ser arquivada")
                print(f"  Todas as tarefas ativas no banco constam no CSV importado")

            # Confirmar totais finais
            total_ativas_depois = Tarefa.objects.filter(ativa=True).count()
            total_arquivadas_total = Tarefa.objects.filter(ativa=False).count()

            print(f"\nResumo final do banco de dados:")
            print(f"  • Tarefas ativas: {total_ativas_depois}")
            print(f"  • Tarefas arquivadas: {total_arquivadas_total}")
            print(f"  • Total no banco: {total_ativas_depois + total_arquivadas_total}")
            print(f"{'='*80}\n")

            # Finalizar com sucesso
            registro.status = 'COMPLETED'
            registro.registros_criados = total_criados
            registro.registros_atualizados = total_atualizados
            registro.usuarios_criados = usuarios_criados
            registro.data_fim_processamento = timezone.now()
            registro.linhas_processadas = registro.total_linhas
            registro.progresso_percentual = 100
            registro.save()

            # Arquivo CSV mantido no disco para auditoria
            # Pode ser removido manualmente através do Django Admin se necessário
            if os.path.exists(registro.caminho_arquivo):
                tamanho_mb = os.path.getsize(registro.caminho_arquivo) / (1024 * 1024)
                print(f"\n📁 Arquivo CSV mantido no disco para auditoria:")
                print(f"   Caminho: {registro.caminho_arquivo}")
                print(f"   Tamanho: {tamanho_mb:.2f} MB")
                print(f"   💡 Você pode deletar este arquivo manualmente pelo Django Admin quando necessário.")

            print(f"\n{'='*80}")
            print(f"IMPORTA��O CONCLU�DA COM SUCESSO!")
            print(f"Tarefas criadas: {total_criados}")
            print(f"Tarefas atualizadas: {total_atualizados}")
            print(f"Usu�rios criados: {usuarios_criados}")
            print(f"Dura��o: {registro.duracao_processamento():.2f} segundos")
            print(f"{'='*80}\n")

    except RegistroImportacao.DoesNotExist:
        print(f"\nL ERRO: Registro de importa��o {registro_id} n�o encontrado!")

    except Exception as e:
        # Capturar erro e salvar no registro
        error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"

        print(f"\n{'='*80}")
        print(f"L ERRO NA IMPORTA��O ASS�NCRONA")
        print(f"Registro ID: {registro_id}")
        print(f"Erro: {error_msg}")
        print(f"{'='*80}\n")

        try:
            registro.status = 'FAILED'
            registro.mensagem_erro = error_msg
            registro.data_fim_processamento = timezone.now()
            registro.save(update_fields=['status', 'mensagem_erro', 'data_fim_processamento'])

            # Arquivo mantido no disco mesmo em caso de erro para análise
            if registro.caminho_arquivo and os.path.exists(registro.caminho_arquivo):
                print(f"\n📁 Arquivo CSV mantido para análise do erro: {registro.caminho_arquivo}")
        except:
            pass
