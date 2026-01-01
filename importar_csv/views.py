import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.contrib.auth.models import Group
from .forms import CSVImportForm
from .models import RegistroImportacao, HistoricoTarefa
from tarefas.models import Tarefa
from usuarios.models import CustomUser, EmailServidor


class CoordenadorRequiredMixin(UserPassesTestMixin):
    """Garante que apenas Coordenadores acessem a página"""
    def test_func(self):
        return self.request.user.groups.filter(name='Coordenador').exists()


class ImportarCSVView(LoginRequiredMixin, CoordenadorRequiredMixin, View):
    template_name = 'importar_csv/importar.html'
    form_class = CSVImportForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        ultimas_importacoes = RegistroImportacao.objects.order_by('-data_importacao')[:5]
        return render(request, self.template_name, {
            'form': form,
            'ultimas_importacoes': ultimas_importacoes
        })

    def post(self, request, *args, **kwargs):
        """
        Método POST ASSÍNCRONO - Agenda a importação em segundo plano.
        O processamento real é feito pela tarefa processar_importacao_async.
        """
        import os
        from django.conf import settings
        from django.utils.text import get_valid_filename
        import uuid
        from .tasks import processar_importacao_async

        form = self.form_class(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, 'Formulário inválido')
            return redirect('importar_csv:importar_csv')

        arquivo_csv = request.FILES['arquivo_csv']

        if not arquivo_csv.name.endswith('.csv'):
            messages.error(request, 'Este não é um arquivo CSV válido.')
            return redirect('importar_csv:importar_csv')

        # Criar diretório de uploads se não existir
        upload_dir = os.path.join(settings.BASE_DIR, 'media', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Salvar arquivo temporariamente com nome único
        nome_seguro = get_valid_filename(arquivo_csv.name)
        nome_unico = f"{uuid.uuid4()}_{nome_seguro}"
        caminho_completo = os.path.join(upload_dir, nome_unico)

        # Gravar arquivo no disco
        with open(caminho_completo, 'wb+') as destination:
            for chunk in arquivo_csv.chunks():
                destination.write(chunk)

        # Criar registro de importação com status PENDING
        registro = RegistroImportacao.objects.create(
            usuario=request.user,
            nome_arquivo=arquivo_csv.name,
            caminho_arquivo=caminho_completo,
            status='PENDING'
        )

        # Agendar tarefa em segundo plano
        processar_importacao_async(registro.id)

        messages.success(
            request,
            f'✅ Importação agendada com sucesso! '
            f'O arquivo "{arquivo_csv.name}" está sendo processado em segundo plano. '
            f'Você pode acompanhar o progresso na lista de importações abaixo.'
        )

        return redirect('importar_csv:importar_csv')

    def post_sincrono(self, request, *args, **kwargs):
        """
        MÉTODO LEGADO - Processamento síncrono (BACKUP)
        Mantido para referência. Use post() para modo assíncrono.
        """
        form = self.form_class(request.POST, request.FILES)

        # Verifica se é uma requisição AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not form.is_valid():
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'Formulário inválido'
                }, status=400)
            return render(request, self.template_name, {'form': form})

        arquivo_csv = request.FILES['arquivo_csv']

        if not arquivo_csv.name.endswith('.csv'):
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': 'Este não é um arquivo CSV válido.'
                }, status=400)
            messages.error(request, 'Este não é um arquivo CSV válido.')
            return redirect('importar_csv:importar_csv')

        # Cria o registro de importação
        registro_importacao = RegistroImportacao.objects.create(
            usuario=request.user,
            nome_arquivo=arquivo_csv.name
        )

        BATCH_SIZE = 2000
        total_criados = 0
        total_atualizados = 0
        usuarios_criados = 0

        try:
            # Lê o arquivo CSV
            data_set = arquivo_csv.read().decode('latin-1')
            io_string = io.StringIO(data_set)
            reader = csv.reader(io_string, delimiter=',')
            header = next(reader)

            lote_dados_csv = {}
            total_rows = 0

            for i, row in enumerate(reader, 1):
                total_rows += 1
                
                # Remove aspas dos valores
                row = [campo.strip('"').strip() for campo in row]
                
                protocolo = row[0].strip()
                
                # Validação: verifica se o protocolo não está vazio
                if not protocolo:
                    continue
                
                lote_dados_csv[protocolo] = row

                # Processa em lotes
                if i % BATCH_SIZE == 0:
                    print(f"Processando lote de {len(lote_dados_csv)} registros únicos (linhas {i-BATCH_SIZE+1} a {i})...")
                    criados, atualizados, users_criados = self.processar_lote(
                        lote_dados_csv, 
                        registro_importacao
                    )
                    total_criados += criados
                    total_atualizados += atualizados
                    usuarios_criados += users_criados
                    print(f"Lote processado: {criados} tarefas criadas, {atualizados} atualizadas, {users_criados} usuários criados.")
                    lote_dados_csv = {}

            # Processa o último lote
            if lote_dados_csv:
                print(f"Processando lote final de {len(lote_dados_csv)} registros únicos...")
                criados, atualizados, users_criados = self.processar_lote(
                    lote_dados_csv, 
                    registro_importacao
                )
                total_criados += criados
                total_atualizados += atualizados
                usuarios_criados += users_criados
                print(f"Lote final processado: {criados} tarefas criadas, {atualizados} atualizadas, {users_criados} usuários criados.")

            # Atualiza o registro de importação
            registro_importacao.registros_criados = total_criados
            registro_importacao.registros_atualizados = total_atualizados
            registro_importacao.usuarios_criados = usuarios_criados
            registro_importacao.save()

            # Mensagem de sucesso com informação de usuários criados
            msg = (
                f"Importação concluída com sucesso! "
                f"{total_criados} tarefas criadas e {total_atualizados} atualizadas "
                f"de um total de {total_rows} linhas processadas."
            )
            if usuarios_criados > 0:
                msg += f" 👤 {usuarios_criados} novo(s) usuário(s) criado(s) automaticamente."

            messages.success(request, msg)

            # Se for AJAX, retorna JSON
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'total': total_rows,
                    'criadas': total_criados,
                    'atualizadas': total_atualizados,
                    'erros': 0,
                    'usuarios_criados': usuarios_criados,
                    'message': msg
                })

        except Exception as e:
            registro_importacao.delete()

            print(f"\n--- ERRO CRÍTICO NA IMPORTAÇÃO ---")
            print(f"Exceção: {type(e).__name__}")
            print(f"Mensagem: {e}")
            import traceback
            print(f"Traceback:\n{traceback.format_exc()}")
            print(f"A importação foi interrompida e todas as alterações foram revertidas.")
            print(f"---------------------------------\n")

            error_msg = f"Ocorreu um erro crítico durante a importação: {e}. A operação foi interrompida."
            messages.error(request, error_msg)

            # Se for AJAX, retorna JSON com erro
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': str(e),
                    'message': error_msg
                }, status=500)

        return redirect('importar_csv:importar_csv')

    def criar_usuario_automatico(self, siape, cpf, nome_completo, codigo_gex, nome_gex):
        """
        Cria um novo usuário automaticamente baseado nos dados da tarefa.
        ATUALIZADO: Cria usuário MESMO SEM e-mail cadastrado.
        
        Args:
            siape: SIAPE do servidor
            cpf: CPF do servidor
            nome_completo: Nome completo do servidor
            codigo_gex: Código da GEX
            nome_gex: Nome da GEX
            
        Returns:
            CustomUser: O usuário criado (sempre retorna, nunca None)
        """
        # Tenta buscar o e-mail na tabela EmailServidor
        email = None
        try:
            email_obj = EmailServidor.objects.get(siape=siape)
            email = email_obj.email
            print(f"  📧 E-mail encontrado para SIAPE {siape}: {email}")
        except EmailServidor.DoesNotExist:
            print(f"  ⚠️ SIAPE {siape}: E-mail não encontrado - criando usuário SEM e-mail")
        
        # Define senha padrão
        senha_padrao = "inss2025"
        
        try:
            # Cria o usuário (COM ou SEM e-mail)
            usuario = CustomUser.objects.create_user(
                siape=siape,
                nome_completo=nome_completo,
                email=email,  # Pode ser None - será gerado temporário
                cpf=cpf,
                password=senha_padrao,
                gex=nome_gex or f"GEX {codigo_gex}",
                lotacao=nome_gex or f"GEX {codigo_gex}",
                is_active=True
            )
            
            # Adiciona ao grupo "Servidor"
            grupo_servidor, _ = Group.objects.get_or_create(name='Servidor')
            usuario.groups.add(grupo_servidor)
            
            if email:
                print(f"  ✅ Usuário criado: {nome_completo} (SIAPE: {siape} | CPF: {cpf}) | E-mail: {email} | GEX: {nome_gex}")
            else:
                print(f"  ✅ Usuário criado SEM E-MAIL: {nome_completo} (SIAPE: {siape} | CPF: {cpf}) | GEX: {nome_gex}")
            
            return usuario
            
        except Exception as e:
            print(f"  ❌ ERRO ao criar usuário para SIAPE {siape}: {e}")
            return None

    def parse_date_ddmmyyyy(self, date_str):
        """Converte string de data do formato DDMMYYYY para date object"""
        if not date_str or date_str == '0':
            return None
        try:
            return datetime.strptime(date_str, '%d%m%Y').date()
        except ValueError:
            return None

    def parse_datetime(self, datetime_str):
        """
        Converte string de datetime para datetime object com timezone.
        Formato esperado: 20251021032919281414 (YYYYMMDDHHMMSSffffff)
        """
        if not datetime_str or datetime_str == '0':
            return None
        try:
            from django.utils import timezone
            # Formato: YYYYMMDDHHMMSSffffff
            dt_naive = datetime.strptime(datetime_str, '%Y%m%d%H%M%S%f')
            # Converte para datetime com timezone (horário de Brasília)
            dt_aware = timezone.make_aware(dt_naive, timezone.get_current_timezone())
            return dt_aware
        except ValueError:
            return None

    def safe_int(self, value, default=0):
        """Converte valor para int de forma segura"""
        if not value or value == '':
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def processar_lote(self, lote_dados_csv, registro_importacao):
        """
        Processa um lote de dados do CSV.
        Cria usuários automaticamente quando necessário (COM ou SEM e-mail).
        Importa TODOS os campos do CSV, incluindo os 3 NOVOS CAMPOS.
        
        MAPEAMENTO DE COLUNAS DO CSV (22 campos - índices 0 a 21):
        0  = Protocolo
        1  = Subtarefas pendentes
        2  = Código unidade
        3  = Nome serviço
        4  = Status
        5  = Descrição cumprimento
        6  = SIAPE
        7  = CPF
        8  = Nome responsável
        9  = Código GEX
        10 = Nome GEX
        11 = Data distribuição
        12 = Data última atualização
        13 = Data do prazo ← NOVO
        14 = Data início última exigência ← NOVO
        15 = Data fim última exigência
        16 = Indicador tarefa reaberta ← NOVO
        17 = Tempo última exigência
        18 = Tempo em pendência
        19 = Tempo em exigência
        20 = Tempo até última distribuição
        21 = Data processamento
        """
        
        with transaction.atomic():
            protocolos_lote = list(lote_dados_csv.keys())
            usuarios_criados_lote = 0

            # ETAPA 1: Identifica SIAPEs únicos no lote e cria usuários se necessário
            siapes_no_lote = {}
            for protocolo, row in lote_dados_csv.items():
                siape = row[6].strip() if len(row) > 6 and row[6] else None
                if siape and siape not in siapes_no_lote:
                    cpf = row[7].strip() if len(row) > 7 and row[7] else None
                    nome = row[8].strip() if len(row) > 8 and row[8] else f"Servidor {siape}"
                    codigo_gex = row[9].strip() if len(row) > 9 and row[9] else None
                    nome_gex = row[10].strip() if len(row) > 10 and row[10] else None
                    siapes_no_lote[siape] = {
                        'cpf': cpf,
                        'nome': nome,
                        'codigo_gex': codigo_gex,
                        'nome_gex': nome_gex
                    }
            
            # Verifica quais SIAPEs já têm usuário
            siapes_existentes = set(
                CustomUser.objects.filter(
                    siape__in=siapes_no_lote.keys()
                ).values_list('siape', flat=True)
            )
            
            # Cria usuários para os SIAPEs novos (COM OU SEM E-MAIL)
            for siape, dados in siapes_no_lote.items():
                if siape not in siapes_existentes:
                    try:
                        usuario_criado = self.criar_usuario_automatico(
                            siape=siape,
                            cpf=dados['cpf'],
                            nome_completo=dados['nome'],
                            codigo_gex=dados['codigo_gex'],
                            nome_gex=dados['nome_gex']
                        )
                        if usuario_criado:  # Sempre cria, mesmo sem e-mail
                            usuarios_criados_lote += 1
                    except Exception as e:
                        print(f"  ⚠️ Erro ao criar usuário para SIAPE {siape}: {e}")
                else:
                    # Atualiza o CPF e GEX do usuário existente se necessário
                    try:
                        usuario = CustomUser.objects.get(siape=siape)
                        atualizado = False
                        
                        if not usuario.cpf and dados['cpf']:
                            usuario.cpf = dados['cpf']
                            atualizado = True
                        
                        if not usuario.gex and dados['nome_gex']:
                            usuario.gex = dados['nome_gex']
                            usuario.lotacao = dados['nome_gex']
                            atualizado = True
                        
                        if atualizado:
                            usuario.save()
                            print(f"  🔄 Usuário atualizado: {usuario.nome_completo} (SIAPE: {siape})")
                    except Exception as e:
                        print(f"  ⚠️ Erro ao atualizar usuário SIAPE {siape}: {e}")

            # ETAPA 2: Conta quantos já existem (para estatísticas)
            protocolos_existentes = set(
                Tarefa.objects.filter(
                    numero_protocolo_tarefa__in=protocolos_lote
                ).values_list('numero_protocolo_tarefa', flat=True)
            )
            
            qtd_ja_existiam = len(protocolos_existentes)
            qtd_novos = len(protocolos_lote) - qtd_ja_existiam

            # ETAPA 3: Prepara todos os objetos para inserção (COM TODOS OS CAMPOS + 3 NOVOS)
            tarefas_para_inserir = []
            
            for protocolo, row in lote_dados_csv.items():
                try:
                    # Mantém como string (não converte para int)
                    protocolo_str = protocolo
                    siape = row[6].strip() if len(row) > 6 and row[6] else None
                    
                    dados_tarefa = {
                        'numero_protocolo_tarefa': protocolo_str,
                        'indicador_subtarefas_pendentes': self.safe_int(row[1]),
                        'codigo_unidade_tarefa': self.safe_int(row[2]),
                        'nome_servico': row[3] if len(row) > 3 else '',
                        'status_tarefa': row[4] if len(row) > 4 else '',
                        'descricao_cumprimento_exigencia_tarefa': row[5] if len(row) > 5 else '',
                        
                        # FK para CustomUser (pelo SIAPE)
                        'siape_responsavel_id': siape,
                        
                        # CPF do responsável
                        'cpf_responsavel': row[7].strip() if len(row) > 7 and row[7] else None,
                        
                        # Demais campos
                        'nome_profissional_responsavel': row[8].strip() if len(row) > 8 and row[8] else None,
                        'codigo_gex_responsavel': row[9].strip() if len(row) > 9 and row[9] else None,
                        'nome_gex_responsavel': row[10].strip() if len(row) > 10 and row[10] else None,
                        
                        # Datas (incluindo os 2 novos campos)
                        'data_distribuicao_tarefa': self.parse_date_ddmmyyyy(row[11]) if len(row) > 11 else None,
                        'data_ultima_atualizacao': self.parse_date_ddmmyyyy(row[12]) if len(row) > 12 else None,
                        'data_prazo': self.parse_date_ddmmyyyy(row[13]) if len(row) > 13 else None,  # ← NOVO índice 13
                        'data_inicio_ultima_exigencia': self.parse_date_ddmmyyyy(row[14]) if len(row) > 14 else None,  # ← NOVO índice 14
                        'data_fim_ultima_exigencia': self.parse_date_ddmmyyyy(row[15]) if len(row) > 15 else None,
                        
                        # Indicador de tarefa reaberta (novo)
                        'indicador_tarefa_reaberta': self.safe_int(row[16]) if len(row) > 16 else 0,  # ← NOVO índice 16
                        
                        # Tempos
                        'tempo_ultima_exigencia_em_dias': self.safe_int(row[17]) if len(row) > 17 else None,
                        'tempo_em_pendencia_em_dias': self.safe_int(row[18]),
                        'tempo_em_exigencia_em_dias': self.safe_int(row[19]),
                        'tempo_ate_ultima_distribuicao_tarefa_em_dias': self.safe_int(row[20]),
                        
                        # Data de processamento
                        'data_processamento_tarefa': self.parse_datetime(row[21]) if len(row) > 21 else None,
                    }
                    
                    tarefas_para_inserir.append(Tarefa(**dados_tarefa))
                    
                except (ValueError, IndexError) as e:
                    print(f"\n--- ERRO DE PARSING NA LINHA ---")
                    print(f"Protocolo: {protocolo}")
                    print(f"Dados da linha: {row}")
                    print(f"Erro: {e}")
                    print(f"--------------------------------\n")
                    raise ValueError(f"Formato de dados inválido na linha do protocolo {protocolo}")

            # ETAPA 4: Tenta criar TODOS, ignorando os que já existem
            if tarefas_para_inserir:
                Tarefa.objects.bulk_create(
                    tarefas_para_inserir, 
                    ignore_conflicts=True
                )
                if qtd_novos > 0:
                    print(f"  → {qtd_novos} tarefas novas criadas")

            # ETAPA 5: Busca TODOS os registros do lote (novos + existentes)
            protocolos_lote_str = protocolos_lote
            
            todas_tarefas_do_lote = {
                t.numero_protocolo_tarefa: t
                for t in Tarefa.objects.filter(numero_protocolo_tarefa__in=protocolos_lote_str)
            }

            # ETAPA 6: Atualiza TODOS os registros com os dados do CSV (incluindo os 3 novos campos)
            tarefas_para_atualizar = []
            protocolos_nao_encontrados = []
            
            for protocolo, row in lote_dados_csv.items():
                if protocolo not in todas_tarefas_do_lote:
                    protocolos_nao_encontrados.append(protocolo)
                    print(f"  ⚠️ AVISO: Protocolo '{protocolo}' não foi inserido")
                    continue
                    
                tarefa = todas_tarefas_do_lote[protocolo]
                siape = row[6].strip() if len(row) > 6 and row[6] else None
                
                # Atualiza TODOS os campos (incluindo os 3 novos)
                tarefa.indicador_subtarefas_pendentes = self.safe_int(row[1])
                tarefa.codigo_unidade_tarefa = self.safe_int(row[2])
                tarefa.nome_servico = row[3] if len(row) > 3 else ''
                tarefa.status_tarefa = row[4] if len(row) > 4 else ''
                tarefa.descricao_cumprimento_exigencia_tarefa = row[5] if len(row) > 5 else ''
                tarefa.siape_responsavel_id = siape
                tarefa.cpf_responsavel = row[7].strip() if len(row) > 7 and row[7] else None
                tarefa.nome_profissional_responsavel = row[8].strip() if len(row) > 8 and row[8] else None
                tarefa.codigo_gex_responsavel = row[9].strip() if len(row) > 9 and row[9] else None
                tarefa.nome_gex_responsavel = row[10].strip() if len(row) > 10 and row[10] else None
                tarefa.data_distribuicao_tarefa = self.parse_date_ddmmyyyy(row[11]) if len(row) > 11 else None
                tarefa.data_ultima_atualizacao = self.parse_date_ddmmyyyy(row[12]) if len(row) > 12 else None
                tarefa.data_prazo = self.parse_date_ddmmyyyy(row[13]) if len(row) > 13 else None  # ← NOVO
                tarefa.data_inicio_ultima_exigencia = self.parse_date_ddmmyyyy(row[14]) if len(row) > 14 else None  # ← NOVO
                tarefa.data_fim_ultima_exigencia = self.parse_date_ddmmyyyy(row[15]) if len(row) > 15 else None
                tarefa.indicador_tarefa_reaberta = self.safe_int(row[16]) if len(row) > 16 else 0  # ← NOVO
                tarefa.tempo_ultima_exigencia_em_dias = self.safe_int(row[17]) if len(row) > 17 else None
                tarefa.tempo_em_pendencia_em_dias = self.safe_int(row[18])
                tarefa.tempo_em_exigencia_em_dias = self.safe_int(row[19])
                tarefa.tempo_ate_ultima_distribuicao_tarefa_em_dias = self.safe_int(row[20])
                tarefa.data_processamento_tarefa = self.parse_datetime(row[21]) if len(row) > 21 else None
                
                tarefas_para_atualizar.append(tarefa)

            # Atualiza em massa COM TODOS OS CAMPOS (incluindo os 3 novos)
            if tarefas_para_atualizar:
                Tarefa.objects.bulk_update(
                    tarefas_para_atualizar,
                    fields=[
                        'indicador_subtarefas_pendentes',
                        'codigo_unidade_tarefa',
                        'nome_servico',
                        'status_tarefa',
                        'descricao_cumprimento_exigencia_tarefa',
                        'siape_responsavel',
                        'cpf_responsavel',
                        'nome_profissional_responsavel',
                        'codigo_gex_responsavel',
                        'nome_gex_responsavel',
                        'data_distribuicao_tarefa',
                        'data_ultima_atualizacao',
                        'data_prazo',  # ← NOVO
                        'data_inicio_ultima_exigencia',  # ← NOVO
                        'data_fim_ultima_exigencia',
                        'indicador_tarefa_reaberta',  # ← NOVO
                        'tempo_ultima_exigencia_em_dias',
                        'tempo_em_pendencia_em_dias',
                        'tempo_em_exigencia_em_dias',
                        'tempo_ate_ultima_distribuicao_tarefa_em_dias',
                        'data_processamento_tarefa',
                    ]
                )
                print(f"  → {len(tarefas_para_atualizar)} tarefas atualizadas")
                
                
            # ============================================
            # OTIMIZADO: CALCULAR CRITICIDADE E TIPO FILA COM BULK_UPDATE
            # ============================================
            print(f"  → Calculando criticidade e tipo de fila para {len(tarefas_para_atualizar)} tarefas...")

            tarefas_para_atualizar_criticidade = []
            for tarefa in tarefas_para_atualizar:
                try:
                    # Calcula criticidade SEM salvar (novo método otimizado)
                    campos_calculados = tarefa.calcular_criticidade()

                    # Atribui os valores aos campos da tarefa
                    for campo, valor in campos_calculados.items():
                        setattr(tarefa, campo, valor)

                    # Calcula tipo de fila
                    tarefa.tipo_fila = tarefa.classificar_fila()

                    tarefas_para_atualizar_criticidade.append(tarefa)
                except Exception as e:
                    print(f"  ⚠️ Erro ao calcular criticidade da tarefa {tarefa.numero_protocolo_tarefa}: {e}")

            # BULK UPDATE dos campos de criticidade + tipo_fila (UMA ÚNICA QUERY!)
            if tarefas_para_atualizar_criticidade:
                Tarefa.objects.bulk_update(
                    tarefas_para_atualizar_criticidade,
                    fields=[
                        'nivel_criticidade_calculado',
                        'regra_aplicada_calculado',
                        'alerta_criticidade_calculado',
                        'descricao_criticidade_calculado',
                        'dias_pendente_criticidade_calculado',
                        'prazo_limite_criticidade_calculado',
                        'pontuacao_criticidade',
                        'cor_criticidade_calculado',
                        'data_calculo_criticidade',
                        'tipo_fila'  # NOVO CAMPO
                    ]
                )

                # Estatísticas
                criticas_count = sum(1 for t in tarefas_para_atualizar_criticidade if t.nivel_criticidade_calculado == 'CRÍTICA')
                regulares_count = sum(1 for t in tarefas_para_atualizar_criticidade if t.nivel_criticidade_calculado == 'REGULAR')
                print(f"  → {len(tarefas_para_atualizar_criticidade)} tarefas com criticidade atualizada")
                print(f"  → Resumo: {criticas_count} críticas, {regulares_count} regulares")

                
                
                
                

            # ETAPA 6.5: Garantir que todas as tarefas presentes no CSV estejam marcadas como ativas
            if tarefas_para_atualizar:
                # Marca como ativa todas as tarefas que estão no CSV
                Tarefa.objects.filter(
                    numero_protocolo_tarefa__in=protocolos_lote_str
                ).update(ativa=True)
                print(f"  → {len(protocolos_lote_str)} tarefas marcadas como ativas (presentes no CSV)")

            # ETAPA 7: Cria os registros de histórico (COM TODOS OS CAMPOS + 3 NOVOS)
            tarefas_processadas = Tarefa.objects.filter(
                numero_protocolo_tarefa__in=protocolos_lote_str
            )
            
            historicos_para_criar = [
                HistoricoTarefa(
                    tarefa_original=tarefa_obj,
                    registro_importacao=registro_importacao,
                    status_tarefa=tarefa_obj.status_tarefa,
                    descricao_cumprimento_exigencia_tarefa=tarefa_obj.descricao_cumprimento_exigencia_tarefa,
                    siape_responsavel=tarefa_obj.siape_responsavel.siape if tarefa_obj.siape_responsavel else None,
                    cpf_responsavel=tarefa_obj.cpf_responsavel,
                    nome_profissional_responsavel=tarefa_obj.nome_profissional_responsavel,
                    codigo_gex_responsavel=tarefa_obj.codigo_gex_responsavel,
                    nome_gex_responsavel=tarefa_obj.nome_gex_responsavel,
                    data_distribuicao_tarefa=tarefa_obj.data_distribuicao_tarefa,
                    data_ultima_atualizacao=tarefa_obj.data_ultima_atualizacao,
                    data_prazo=tarefa_obj.data_prazo,  # ← NOVO
                    data_inicio_ultima_exigencia=tarefa_obj.data_inicio_ultima_exigencia,  # ← NOVO
                    data_fim_ultima_exigencia=tarefa_obj.data_fim_ultima_exigencia,
                    indicador_tarefa_reaberta=tarefa_obj.indicador_tarefa_reaberta,  # ← NOVO
                    data_processamento_tarefa=tarefa_obj.data_processamento_tarefa,
                    tempo_ultima_exigencia_em_dias=tarefa_obj.tempo_ultima_exigencia_em_dias,
                    tempo_em_pendencia_em_dias=tarefa_obj.tempo_em_pendencia_em_dias,
                    tempo_em_exigencia_em_dias=tarefa_obj.tempo_em_exigencia_em_dias,
                    tempo_ate_ultima_distribuicao_tarefa_em_dias=tarefa_obj.tempo_ate_ultima_distribuicao_tarefa_em_dias,
                ) 
                for tarefa_obj in tarefas_processadas
            ]
            
            if historicos_para_criar:
                HistoricoTarefa.objects.bulk_create(historicos_para_criar)
                print(f"  → {len(historicos_para_criar)} registros de histórico criados")
            
            # Log final sobre protocolos não inseridos
            if protocolos_nao_encontrados:
                print(f"  ⚠️ TOTAL: {len(protocolos_nao_encontrados)} protocolos não foram inseridos no banco")

            return qtd_novos, qtd_ja_existiam, usuarios_criados_lote


class StatusImportacaoAPIView(LoginRequiredMixin, CoordenadorRequiredMixin, View):
    """
    API REST para verificar status de uma importação em tempo real.
    Retorna JSON com progresso, estatísticas e status atual.
    """

    def get(self, request, registro_id):
        from django.http import JsonResponse

        try:
            registro = RegistroImportacao.objects.get(id=registro_id, usuario=request.user)

            # Calcular tempo decorrido
            tempo_decorrido = None
            if registro.data_inicio_processamento:
                from django.utils import timezone
                if registro.status == 'PROCESSING':
                    delta = timezone.now() - registro.data_inicio_processamento
                    tempo_decorrido = delta.total_seconds()
                elif registro.data_fim_processamento:
                    tempo_decorrido = registro.duracao_processamento()

            return JsonResponse({
                'success': True,
                'status': registro.status,
                'status_display': registro.get_status_display(),
                'progresso': float(registro.progresso_percentual),
                'total_linhas': registro.total_linhas,
                'linhas_processadas': registro.linhas_processadas,
                'criados': registro.registros_criados,
                'atualizados': registro.registros_atualizados,
                'usuarios_criados': registro.usuarios_criados,
                'mensagem_erro': registro.mensagem_erro,
                'tempo_decorrido': tempo_decorrido,
                'nome_arquivo': registro.nome_arquivo,
            })

        except RegistroImportacao.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Registro de importação não encontrado'
            }, status=404)