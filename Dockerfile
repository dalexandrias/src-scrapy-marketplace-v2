# Dockerfile para Scraper de Anúncios (OLX + Facebook Marketplace)
# Otimizado para menor tamanho de imagem

# ========== STAGE 1: Builder ==========
FROM python:3.9-slim AS builder

WORKDIR /app

# Variáveis de ambiente para build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ========== STAGE 2: Runtime ==========
FROM python:3.9-slim

# Metadados
LABEL maintainer="Scraper Marketplace"
LABEL description="Scraper automatizado de anúncios com Telegram Bot"

WORKDIR /app

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH=/root/.local/bin:$PATH \
    TZ=America/Sao_Paulo

# Copiar dependências Python do builder
COPY --from=builder /root/.local /root/.local

# Instalar apenas dependências runtime necessárias e Playwright em uma camada
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && playwright install chromium \
    && playwright install-deps chromium \
    && apt-get purge -y --auto-remove wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache \
    && rm -rf /var/cache/apt/archives/*

# Copiar e configurar entrypoint ANTES de copiar o resto (para não ser sobrescrito)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && sed -i 's/\r$//' /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/logs /app/data /app/backups

# Copiar código da aplicação (última camada para melhor cache)
COPY . .

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('/app/data/marketplace_anuncios.db'); conn.close()" || exit 1

# Usar entrypoint para inicialização
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Comando padrão
CMD ["python", "main.py"]
