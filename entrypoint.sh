#!/bin/bash
# ==========================================
# Script de Entrypoint para Docker
# Sistema SIGA - SRNCO
# ==========================================

set -e

echo "================================================"
echo "Sistema SIGA - Iniciando..."
echo "================================================"

# Espera o banco de dados estar pronto
echo "[1/5] Aguardando banco de dados..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-3306}; do
  echo "Aguardando MySQL em ${DB_HOST:-db}:${DB_PORT:-3306}..."
  sleep 2
done
echo "✓ Banco de dados disponível!"

# Executa migrações
echo "[2/5] Executando migrações do banco de dados..."
python manage.py migrate --noinput

# Coleta arquivos estáticos
echo "[3/5] Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Cria superusuário se não existir (apenas em dev)
if [ "$DEBUG" = "True" ]; then
  echo "[4/5] Criando superusuário (modo DEBUG)..."
  python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuário criado: admin/admin123')
else:
    print('Superusuário já existe')
END
fi

# Inicia o servidor
echo "[5/5] Iniciando servidor Gunicorn..."
echo "================================================"
exec "$@"
