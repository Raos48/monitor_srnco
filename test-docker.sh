#!/bin/bash
# ==========================================
# Script de Teste Local do Docker
# Sistema SIGA
# ==========================================

set -e

echo "=========================================="
echo "Sistema SIGA - Teste de Build Docker"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir com cores
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado!"
    exit 1
fi
print_success "Docker instalado"

# Verificar se arquivo .env existe
if [ ! -f .env ]; then
    print_info "Arquivo .env não encontrado. Criando a partir do .env.example..."
    cp .env.example .env
    print_info "IMPORTANTE: Edite o arquivo .env com suas configurações antes de continuar!"
    exit 0
fi
print_success "Arquivo .env encontrado"

# Build da imagem
print_info "Iniciando build da imagem Docker..."
docker build -t siga-web:latest -f Dockerfile .

if [ $? -eq 0 ]; then
    print_success "Build concluído com sucesso!"
else
    print_error "Erro no build da imagem"
    exit 1
fi

# Testar a imagem
print_info "Testando a imagem..."
docker run --rm siga-web:latest python --version
print_success "Imagem funcional!"

# Verificar tamanho da imagem
SIZE=$(docker images siga-web:latest --format "{{.Size}}")
print_info "Tamanho da imagem: $SIZE"

# Perguntar se deseja iniciar containers
read -p "Deseja iniciar os containers com docker-compose? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Iniciando containers com docker-compose..."
    docker-compose up -d

    print_success "Containers iniciados!"
    print_info "Aguardando serviços iniciarem (30s)..."
    sleep 30

    # Verificar status
    docker-compose ps

    # Testar health check
    print_info "Testando health check..."
    curl -f http://localhost:8000/api/health/ || print_error "Health check falhou"

    print_success "Deploy local concluído!"
    echo ""
    print_info "Acesse: http://localhost:8000"
    print_info "Logs: docker-compose logs -f"
    print_info "Parar: docker-compose down"
fi

echo "=========================================="
echo "Teste concluído!"
echo "=========================================="
