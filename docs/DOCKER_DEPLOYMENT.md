# 🐳 Guia de Deploy com Docker

Este documento descreve como fazer o deploy do **Scraper de Anúncios** usando Docker e Docker Compose.

## 📋 Pré-requisitos

- Docker 20.10+
- Docker Compose 1.29+
- Token do Bot do Telegram (obter via [@BotFather](https://t.me/BotFather))
- 2GB RAM mínimo
- 10GB espaço em disco

## 🚀 Quick Start

### 1️⃣ Clonar o Repositório

```bash
git clone <seu-repositorio>
cd src-scrapy-marketplace-v2
```

### 2️⃣ Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:

```bash
# OBRIGATÓRIO: Token do bot do Telegram
TELEGRAM_BOT_TOKEN=7873616074:AAG49dPdQqfTMJZtI7HqDu-8-a91TtfJSfA

# OPCIONAL: Configurações do scheduler
SCHEDULER_INTERVAL=30
SCHEDULER_ENABLED=false
```

### 3️⃣ Criar Diretórios Necessários

```bash
mkdir -p data logs backups
```

### 4️⃣ Executar Migrações do Banco

**⚠️ IMPORTANTE:** Execute as migrações ANTES de iniciar o container!

```bash
# No ambiente local (com Python instalado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.\.venv\Scripts\activate   # Windows

pip install -r requirements.txt
python -m migrations.001_initial_schema
python -m migrations.002_add_credentials_and_keywords
```

### 5️⃣ Build e Iniciar Container

```bash
# Build da imagem
docker-compose build

# Iniciar em modo daemon (background)
docker-compose up -d

# Ou iniciar em foreground (ver logs)
docker-compose up
```

## 📊 Gerenciar Container

### Ver Logs

```bash
# Logs em tempo real
docker-compose logs -f

# Últimas 100 linhas
docker-compose logs --tail=100

# Logs de um período específico
docker-compose logs --since 1h
```

### Status do Container

```bash
# Ver status
docker-compose ps

# Ver recursos usados
docker stats scraper-marketplace
```

### Parar/Reiniciar Container

```bash
# Parar
docker-compose stop

# Reiniciar
docker-compose restart

# Parar e remover
docker-compose down

# Parar, remover e limpar volumes
docker-compose down -v
```

## 🔧 Configuração Avançada

### Ajustar Recursos (RAM/CPU)

Edite `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # Máximo 2 CPUs
      memory: 2G       # Máximo 2GB RAM
    reservations:
      cpus: '1.0'      # Mínimo 1 CPU
      memory: 1G       # Mínimo 1GB RAM
```

### Configurar Backup Automático

O sistema faz backup automático antes de cada migração. Para backups periódicos, configure via bot do Telegram:

```
/backup - Fazer backup manual
```

### Persistência de Dados

Os seguintes diretórios são mapeados como volumes:

- `./data` → Banco de dados SQLite
- `./logs` → Logs da aplicação
- `./backups` → Backups do banco

**⚠️ NUNCA DELETE ESSES DIRETÓRIOS SEM BACKUP!**

## 🤖 Usar o Bot do Telegram

Após iniciar o container, abra o Telegram e:

1. Busque pelo nome do seu bot (@seu_bot)
2. Envie `/start` para iniciar
3. Use `/help` para ver todos os comandos

### Comandos Principais

```
/start - Iniciar bot
/help - Lista de comandos
/status - Ver status do sistema
/cadastrar_facebook - Cadastrar credenciais
/adicionar_palavra - Adicionar palavra-chave
/configurar_intervalo - Definir intervalo (10/30/60 min)
/iniciar_scheduler - Iniciar buscas automáticas
/buscar_agora - Busca manual
```

## 🔐 Segurança

### Credenciais do Facebook

- Senhas são criptografadas com **Fernet** (AES 128-bit)
- Chaves de criptografia armazenadas no banco
- Nunca compartilhe o arquivo `.env`

### Token do Telegram

- Mantenha o token em segredo
- Não comite o arquivo `.env` no Git
- Rotacione o token periodicamente

## 🐛 Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker-compose logs

# Verificar configuração
docker-compose config

# Rebuild completo
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Banco de dados corrompido

```bash
# Restaurar do backup
cd data
cp marketplace_anuncios.db marketplace_anuncios_corrupted.db
cp ../backups/marketplace_anuncios_backup_YYYYMMDD_HHMMSS.db marketplace_anuncios.db

# Reiniciar container
docker-compose restart
```

### Chrome/ChromeDriver não funciona

O Dockerfile já instala Chrome e ChromeDriver automaticamente. Se houver problemas:

```bash
# Rebuild da imagem
docker-compose build --no-cache
```

### Erro de memória

Aumente os recursos no `docker-compose.yml` ou adicione swap:

```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Aumentar para 4GB
```

## 📈 Monitoramento

### Health Check

O container possui health check automático. Verificar:

```bash
docker inspect scraper-marketplace | grep -A 10 Health
```

### Logs Estruturados

Logs são salvos em `./logs/` com rotação automática:

- `app.log` - Log principal
- `app.YYYY-MM-DD.log` - Logs arquivados

## 🔄 Atualização

Para atualizar o sistema:

```bash
# 1. Fazer backup
docker-compose exec scraper-marketplace python -c "from backup_manager import BackupManager; BackupManager().create_backup()"

# 2. Parar container
docker-compose down

# 3. Atualizar código
git pull

# 4. Rebuild
docker-compose build

# 5. Executar novas migrações (se houver)
# Ver migrations/ para novos arquivos

# 6. Reiniciar
docker-compose up -d
```

## 📞 Suporte

Em caso de problemas:

1. Verificar logs: `docker-compose logs -f`
2. Verificar health: `docker-compose ps`
3. Verificar recursos: `docker stats`
4. Consultar documentação do bot: [TELEGRAM_BOT_COMMANDS.md](TELEGRAM_BOT_COMMANDS.md)

## 📝 Notas Importantes

- ✅ Execute migrações ANTES do primeiro deploy
- ✅ Configure backup automático
- ✅ Mantenha o `.env` seguro
- ✅ Monitore uso de recursos
- ✅ Faça backups regulares
- ❌ Não exponha o token do Telegram
- ❌ Não delete volumes sem backup
- ❌ Não execute em produção sem SSL (se hospedar externamente)

---

**Última atualização:** 27/10/2025
