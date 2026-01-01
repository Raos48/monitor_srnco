# ==========================================
# Dockerfile Multi-Stage para Django em Produção
# Sistema SIGA - SRNCO
# ==========================================

# Estágio 1: Builder - Instala dependências
FROM python:3.11-slim as builder

# Define variáveis de ambiente para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instala dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# ==========================================
# Estágio 2: Runtime - Imagem final otimizada
FROM python:3.11-slim

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    DJANGO_SETTINGS_MODULE=config.settings

# Instala apenas as dependências de runtime necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 django && \
    mkdir -p /app /app/staticfiles /app/media && \
    chown -R django:django /app

# Define diretório de trabalho
WORKDIR /app

# Copia dependências Python instaladas do builder
COPY --from=builder --chown=django:django /root/.local /root/.local

# Copia o código da aplicação
COPY --chown=django:django . .

# Muda para usuário não-root
USER django

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput --clear

# Expõe a porta 8000
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Comando padrão: executa o servidor Gunicorn
CMD ["gunicorn", "config.wsgi:application", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--threads", "2", \
    "--worker-class", "gthread", \
    "--worker-tmp-dir", "/dev/shm", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info", \
    "--timeout", "120", \
    "--graceful-timeout", "30", \
    "--keep-alive", "5"]
