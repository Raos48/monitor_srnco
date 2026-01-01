"""
SCRIPT DE APLICAÇÃO AUTOMÁTICA DAS MUDANÇAS
============================================

Este script aplica automaticamente todas as alterações necessárias
no arquivo tarefas/models.py para o sistema simplificado de criticidade.

ATENÇÃO: Execute este script ANTES de rodar a migration!

USO:
    python aplicar_refatoracao_models.py
"""

import os
import re
from pathlib import Path


def criar_backup(arquivo):
    """Cria backup do arquivo original"""
    backup = f"{arquivo}.backup_5_niveis"
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    print(f"✅ Backup criado: {backup}")


def aplicar_mudancas():
    """Aplica todas as mudanças no models.py"""
    
    arquivo = Path('tarefas/models.py')
    
    if not arquivo.exists():
        print("❌ Arquivo tarefas/models.py não encontrado!")
        print("Execute este script a partir da raiz do projeto Django.")
        return False
    
    print("🔧 Iniciando refatoração do models.py...")
    
    # Criar backup
    criar_backup(str(arquivo))
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # MUDANÇA 1: Simplificar choices do nivel_criticidade_calculado
    print("📝 Aplicando mudança 1: Simplificando choices...")
    conteudo = re.sub(
        r"nivel_criticidade_calculado = models\.CharField\(\s*max_length=10,\s*choices=\[\s*\('CRÍTICA', 'Crítica'\),\s*\('ALTA', 'Alta'\),\s*\('MÉDIA', 'Média'\),\s*\('BAIXA', 'Baixa'\),\s*\('NENHUMA', 'Nenhuma'\),\s*\],\s*default='NENHUMA',",
        "nivel_criticidade_calculado = models.CharField(\n        max_length=10,\n        choices=[\n            ('CRÍTICA', 'Crítica'),\n            ('REGULAR', 'Regular'),\n        ],\n        default='REGULAR',",
        conteudo,
        flags=re.DOTALL
    )
    
    # MUDANÇA 2: Atualizar tem_criticidade
    print("📝 Aplicando mudança 2: Atualizando tem_criticidade...")
    conteudo = re.sub(
        r"@property\s+def tem_criticidade\(self\):\s+\"\"\"Verifica se a tarefa possui criticidade\"\"\"\s+return self\.nivel_criticidade != 'NENHUMA'",
        "@property\n    def tem_criticidade(self):\n        \"\"\"Verifica se a tarefa está crítica (prazo estourado)\"\"\"\n        return self.nivel_criticidade_calculado == 'CRÍTICA'",
        conteudo
    )
    
    # MUDANÇA 3: Simplificar cor_criticidade
    print("📝 Aplicando mudança 3: Simplificando cor_criticidade...")
    conteudo = re.sub(
        r"@property\s+def cor_criticidade\(self\):\s+\"\"\"Retorna a cor hexadecimal do nível de criticidade\"\"\"\s+cores = \{\s+'CRÍTICA': '#dc3545',\s+'ALTA': '#fd7e14',\s+'MÉDIA': '#ffc107',\s+'BAIXA': '#28a745',\s+'NENHUMA': '#6c757d'\s+\}\s+return cores\.get\(self\.nivel_criticidade, '#6c757d'\)",
        "@property\n    def cor_criticidade(self):\n        \"\"\"Retorna a cor hexadecimal do nível de criticidade\"\"\"\n        cores = {\n            'CRÍTICA': '#dc3545',  # Vermelho\n            'REGULAR': '#28a745',   # Verde\n        }\n        return cores.get(self.nivel_criticidade_calculado, '#28a745')",
        conteudo
    )
    
    # MUDANÇA 4: Simplificar emoji_criticidade
    print("📝 Aplicando mudança 4: Simplificando emoji_criticidade...")
    conteudo = re.sub(
        r"@property\s+def emoji_criticidade\(self\):\s+\"\"\"Retorna emoji representando o nível de criticidade\"\"\"\s+emojis = \{\s+'CRÍTICA': '🔴',\s+'ALTA': '🟠',\s+'MÉDIA': '🟡',\s+'BAIXA': '🟢',\s+'NENHUMA': '⚪'\s+\}\s+return emojis\.get\(self\.nivel_criticidade, '⚪'\)",
        "@property\n    def emoji_criticidade(self):\n        \"\"\"Retorna emoji representando o nível de criticidade\"\"\"\n        emojis = {\n            'CRÍTICA': '⛔',\n            'REGULAR': '✅',\n        }\n        return emojis.get(self.nivel_criticidade_calculado, '✅')",
        conteudo
    )
    
    # MUDANÇA 5: Simplificar badge_html_criticidade
    print("📝 Aplicando mudança 5: Simplificando badge_html_criticidade...")
    conteudo = re.sub(
        r"badges_class = \{\s+'CRÍTICA': 'bg-danger',\s+'ALTA': 'bg-warning text-dark',\s+'MÉDIA': 'bg-info text-dark',\s+'BAIXA': 'bg-success',\s+'NENHUMA': 'bg-secondary'\s+\}\s+css_class = badges_class\.get\(self\.nivel_criticidade, 'bg-secondary'\)\s+emoji = self\.emoji_criticidade\s+nivel = self\.nivel_criticidade",
        "badges = {\n            'CRÍTICA': 'bg-danger',\n            'REGULAR': 'bg-success',\n        }\n        css_class = badges.get(self.nivel_criticidade_calculado, 'bg-success')\n        emoji = self.emoji_criticidade\n        nivel = self.nivel_criticidade_calculado",
        conteudo
    )
    
    # MUDANÇA 6: Simplificar estatisticas_criticidade
    print("📝 Aplicando mudança 6: Simplificando estatisticas_criticidade...")
    
    # Encontrar e substituir o método completo
    padrao_stats = r"(@classmethod\s+def estatisticas_criticidade\(cls, queryset=None\):.*?)(return estatisticas)"
    
    novo_metodo_stats = r"""\1        # Versão SIMPLIFICADA
        from django.db.models import Count, Q
        
        if queryset is None:
            queryset = cls.objects.all()
        
        # Consulta SQL simplificada
        stats = queryset.aggregate(
            total=Count('numero_protocolo_tarefa'),
            criticas=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='CRÍTICA')),
            regulares=Count('numero_protocolo_tarefa', filter=Q(nivel_criticidade_calculado='REGULAR'))
        )
        
        estatisticas = {
            'total': stats['total'],
            'criticas': stats['criticas'],
            'regulares': stats['regulares'],
        }
        
        # Calcular percentuais
        if estatisticas['total'] > 0:
            estatisticas['percentual_criticas'] = round(
                (stats['criticas'] / stats['total']) * 100, 1
            )
            estatisticas['percentual_regulares'] = round(
                (stats['regulares'] / stats['total']) * 100, 1
            )
        
        \2"""
    
    conteudo = re.sub(padrao_stats, novo_metodo_stats, conteudo, flags=re.DOTALL)
    
    # Salvar arquivo modificado
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print("✅ Todas as mudanças aplicadas com sucesso!")
    print(f"✅ Arquivo atualizado: {arquivo}")
    print(f"📦 Backup salvo: {arquivo}.backup_5_niveis")
    
    return True


def main():
    print("=" * 70)
    print("REFATORAÇÃO AUTOMÁTICA: SISTEMA DE CRITICIDADE SIMPLIFICADO")
    print("=" * 70)
    print()
    print("Este script vai:")
    print("  1. Criar backup do models.py atual")
    print("  2. Aplicar mudanças para sistema binário (CRÍTICA/REGULAR)")
    print("  3. Atualizar todos os métodos relacionados")
    print()
    
    resposta = input("Deseja continuar? (s/n): ").strip().lower()
    
    if resposta != 's':
        print("❌ Operação cancelada.")
        return
    
    print()
    
    if aplicar_mudancas():
        print()
        print("=" * 70)
        print("✅ REFATORAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        print()
        print("PRÓXIMOS PASSOS:")
        print("  1. Revisar as mudanças no arquivo tarefas/models.py")
        print("  2. Substituir tarefas/analisador.py pelo analisador_refatorado.py")
        print("  3. Executar: python manage.py makemigrations")
        print("  4. Executar: python manage.py migrate")
        print("  5. Recalcular criticidade de todas as tarefas")
        print()
    else:
        print()
        print("❌ Erro durante a refatoração!")
        print("Verifique se você está na raiz do projeto Django.")


if __name__ == '__main__':
    main()