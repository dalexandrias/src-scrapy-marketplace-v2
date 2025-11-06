# 🐳 Guia Docker - Scraper Marketplace

## 📋 Pré-requisitos

- Docker Engine 20.10+
- Docker Compose 2.0+
- Mínimo 2GB RAM disponível
- Mínimo 5GB espaço em disco

---

## 🚀 Quick Start

### 1️⃣ Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

**Edite o arquivo `.env`** e configure:

```bash
# OBRIGATÓRIO - Token do bot Telegram (@BotFather)
TELEGRAM_BOT_TOKEN=seu_token_aqui

# OBRIGATÓRIO - Seu chat ID (@userinfobot)
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Habilitar Telegram e Scheduler
TELEGRAM_ENABLED=true
SCHEDULER_ENABLED=true
```

### 2️⃣ Criar Diretórios Necessários

```bash
# Windows PowerShell
New-Item -ItemType Directory -Force -Path data, logs, backups

# Linux/Mac
mkdir -p data logs backups
```

### 3️⃣ Buildar a Imagem

```bash
docker-compose build
```

**Saída esperada:**
```
[+] Building 120.5s (12/12) FINISHED
 => [internal] load build definition
 => [internal] load .dockerignore
 => [1/8] FROM python:3.9-slim
 => [2/8] WORKDIR /app
 => [3/8] RUN apt-get update && apt-get install...
 => [4/8] COPY requirements.txt .
 => [5/8] RUN pip install --no-cache-dir -r requirements.txt
 => [6/8] RUN playwright install chromium
 => [7/8] COPY . .
 => exporting to image
 => => writing image sha256:...
```

### 4️⃣ Iniciar o Container

```bash
# Modo normal (anexado ao terminal)
docker-compose up

# Modo daemon (background)
docker-compose up -d
```

---

## 📊 Gerenciamento

### Ver Logs

```bash
# Ver logs em tempo real
docker-compose logs -f

# Ver últimas 100 linhas
docker-compose logs --tail=100

# Ver logs do bot
docker-compose logs -f scraper-marketplace
```

### Status do Container

```bash
# Ver status
docker-compose ps

# Ver uso de recursos
docker stats scraper-marketplace
```

### Parar e Reiniciar

```bash
# Parar o container
docker-compose stop

# Iniciar novamente
docker-compose start

# Reiniciar
docker-compose restart

# Parar e remover
docker-compose down
```

### Reconstruir Após Mudanças no Código

```bash
# Rebuild e restart
docker-compose up -d --build

# Forçar rebuild completo (sem cache)
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔍 Troubleshooting

### Container não inicia

**Verificar logs:**
```bash
docker-compose logs
```

**Causas comuns:**
1. ❌ Arquivo `.env` não existe
   - **Solução**: `Copy-Item .env.example .env`

2. ❌ `TELEGRAM_BOT_TOKEN` inválido
   - **Solução**: Verificar token com @BotFather

3. ❌ Permissões nos volumes
   - **Solução**: `chmod -R 755 data logs backups` (Linux/Mac)

### Health Check Falhando

```bash
# Verificar health status
docker inspect scraper-marketplace | grep -A 10 Health

# Testar manualmente
docker exec scraper-marketplace python -c "import sqlite3; conn = sqlite3.connect('/app/data/marketplace_anuncios.db'); conn.close()"
```

### Container usando muita RAM

**Ajustar limites no `docker-compose.yml`:**
```yaml
mem_limit: 1g          # Era 2g
mem_reservation: 512m  # Era 1g
```

### Playwright não funciona

**Verificar se Chromium foi instalado:**
```bash
docker exec scraper-marketplace playwright --version
docker exec scraper-marketplace ls /ms-playwright/chromium-*
```

**Reconstruir se necessário:**
```bash
docker-compose build --no-cache
```

---

## 📂 Estrutura de Volumes

```
.
├── data/                    # Banco de dados SQLite
│   └── marketplace_anuncios.db
│
├── logs/                    # Logs da aplicação
│   ├── marketplace_2025-11-04.log
│   └── marketplace_2025-11-03.log.zip
│
└── backups/                 # Backups automáticos
    └── marketplace_backup_20251104_120000.db
```

**Características:**
- ✅ Dados persistem mesmo após `docker-compose down`
- ✅ Logs acessíveis no host
- ✅ Backups automáticos salvos no host

---

## 🔧 Configurações Avançadas

### Executar Comandos no Container

```bash
# Acessar shell interativo
docker exec -it scraper-marketplace bash

# Executar comando único
docker exec scraper-marketplace python -c "print('Hello')"

# Ver anúncios no banco
docker exec scraper-marketplace python tests/test_deduplicacao.py
```

### Acessar Banco de Dados

```bash
# SQLite CLI
docker exec -it scraper-marketplace sqlite3 /app/data/marketplace_anuncios.db

# Contar anúncios
docker exec scraper-marketplace sqlite3 /app/data/marketplace_anuncios.db "SELECT COUNT(*) FROM anuncios"
```

### Backup Manual

```bash
# Copiar banco para host
docker cp scraper-marketplace:/app/data/marketplace_anuncios.db ./backup_manual.db

# Restaurar banco
docker cp ./backup_manual.db scraper-marketplace:/app/data/marketplace_anuncios.db
```

---

## ⚙️ Configuração do docker-compose.yml

### Recursos (CPU/RAM)

```yaml
# Limitar a 2 CPUs e 2GB RAM
mem_limit: 2g
mem_reservation: 1g
cpus: 2.0
```

**Recomendações:**
- **Desenvolvimento**: 1 CPU, 1GB RAM
- **Produção (poucas palavras)**: 2 CPUs, 2GB RAM
- **Produção (muitas palavras)**: 4 CPUs, 4GB RAM

### Shared Memory (shm_size)

```yaml
shm_size: '2gb'
```

**Necessário para Playwright/Chromium!**
- Mínimo: 512mb
- Recomendado: 2gb
- Se ocorrer erros "out of memory", aumente para 4gb

### Logging

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # Tamanho máximo por arquivo
    max-file: "3"     # Manter 3 arquivos (30MB total)
```

**Alternativos:**
- `max-size: "5m"` para economizar espaço
- `max-file: "5"` para histórico maior

---

## 🌐 Rede e Portas

### Expor Porta (Se Necessário)

```yaml
ports:
  - "8080:8080"  # API/Dashboard futuro
```

### Usar Rede do Host

```yaml
network_mode: "host"  # Para acessar serviços locais
```

**⚠️ Atenção**: Não recomendado em produção!

---

## 📈 Monitoramento

### Docker Stats

```bash
# Monitorar em tempo real
docker stats scraper-marketplace

# Saída:
# CONTAINER            CPU %    MEM USAGE / LIMIT     MEM %
# scraper-marketplace  15.2%    450MiB / 2GiB         22.5%
```

### Health Check

```bash
# Ver status
docker inspect scraper-marketplace --format='{{.State.Health.Status}}'

# Ver histórico
docker inspect scraper-marketplace --format='{{json .State.Health}}' | jq
```

**Estados possíveis:**
- `healthy` ✅ - Funcionando
- `unhealthy` ❌ - Com problemas
- `starting` ⏳ - Inicializando

---

## 🔄 Atualização

### Atualizar Código

```bash
# 1. Parar container
docker-compose down

# 2. Atualizar código (git pull, etc)
git pull origin main

# 3. Rebuild e restart
docker-compose up -d --build
```

### Atualizar Dependências

**Se mudou `requirements.txt`:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

---

## 🗑️ Limpeza

### Remover Container e Volumes

```bash
# Apenas container
docker-compose down

# Container + volumes nomeados (não remove ./data, ./logs)
docker-compose down -v

# Container + imagem
docker-compose down --rmi all
```

### Limpeza Geral do Docker

```bash
# Remover containers parados
docker container prune

# Remover imagens não usadas
docker image prune -a

# Remover tudo (CUIDADO!)
docker system prune -a --volumes
```

---

## 📋 Checklist de Produção

Antes de colocar em produção:

- [ ] ✅ `.env` configurado corretamente
- [ ] ✅ `TELEGRAM_BOT_TOKEN` válido
- [ ] ✅ `TELEGRAM_CHAT_ID` correto
- [ ] ✅ `SCHEDULER_ENABLED=true`
- [ ] ✅ Palavras-chave cadastradas no banco
- [ ] ✅ Volumes `./data`, `./logs`, `./backups` existem
- [ ] ✅ Health check retorna `healthy`
- [ ] ✅ Logs não apresentam erros
- [ ] ✅ Teste manual de busca funciona
- [ ] ✅ Notificações Telegram funcionam
- [ ] ✅ Recursos (RAM/CPU) adequados

---

## 🆘 Suporte

### Logs Detalhados

```bash
# Logs com timestamp
docker-compose logs -f --timestamps

# Logs desde data específica
docker-compose logs --since 2025-11-04T10:00:00
```

### Entrar no Container

```bash
# Bash
docker exec -it scraper-marketplace bash

# Python REPL
docker exec -it scraper-marketplace python
```

### Verificar Configuração

```bash
# Ver variáveis de ambiente
docker exec scraper-marketplace env | grep TELEGRAM

# Ver versão do Python
docker exec scraper-marketplace python --version

# Ver pacotes instalados
docker exec scraper-marketplace pip list
```

---

**✅ Docker configurado e pronto para uso!**

Para mais informações, consulte:
- [Documentação Docker](https://docs.docker.com/)
- [Documentação Docker Compose](https://docs.docker.com/compose/)
- [Playwright Docker](https://playwright.dev/python/docs/docker)
