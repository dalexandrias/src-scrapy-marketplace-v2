# Sistema de Logs - Marketplace Scraper

Sistema avançado de logging com rotação automática, gestão de histórico e compressão de logs antigos.

## 📋 Características

- ✅ **Arquivos com Data**: Logs organizados por data (ex: `marketplace_2025-11-02.log`)
- ✅ **Rotação Automática**: Cria novo arquivo a cada dia ou quando atinge tamanho limite
- ✅ **Retenção Configurável**: Remove automaticamente logs mais antigos que X dias
- ✅ **Compressão**: Comprime logs antigos em formato ZIP/GZ para economizar espaço
- ✅ **Thread-Safe**: Suporta logging concorrente de múltiplas threads
- ✅ **Níveis Personalizáveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **Console + Arquivo**: Logs são exibidos no console E salvos em arquivo

## ⚙️ Configuração via `.env`

```bash
# Nível de log
LOG_LEVEL=INFO

# Diretório dos logs
LOG_DIR=logs

# Prefixo dos arquivos (será adicionado a data)
LOG_FILE_PREFIX=marketplace

# Quando rotacionar (criar novo arquivo)
# Tempo: "00:00", "12:00", "1 day", "1 week"
# Tamanho: "10 MB", "500 KB", "1 GB"
LOG_ROTATION=00:00

# Quantos dias manter os logs
LOG_RETENTION_DAYS=30

# Formato de compressão
LOG_COMPRESSION=zip

# Formato do nome do arquivo
LOG_FILE_FORMAT={prefix}_{time:YYYY-MM-DD}.log
```

## 📁 Estrutura de Logs

```
logs/
├── marketplace_2025-11-02.log          # Log de hoje (ativo)
├── marketplace_2025-11-01.log          # Log de ontem
├── marketplace_2025-10-31.log.zip      # Log comprimido
├── marketplace_2025-10-30.log.zip      # Log comprimido
└── ...
```

## 🔄 Rotação de Logs

### Por Tempo
Cria novo arquivo em horário específico:
- `00:00` - Meia-noite (padrão)
- `12:00` - Meio-dia
- `1 day` - A cada 24 horas
- `1 week` - Semanalmente

### Por Tamanho
Cria novo arquivo quando atinge tamanho:
- `10 MB` - 10 megabytes
- `500 KB` - 500 kilobytes
- `1 GB` - 1 gigabyte

## 🗑️ Gestão de Histórico

### Limpeza Automática
Na inicialização, o sistema:
1. Verifica logs com mais de 7 dias
2. Comprime logs não comprimidos
3. Remove logs mais antigos que `LOG_RETENTION_DAYS`

### Limpeza Manual

```python
from src.core.utils.log_manager import LogManager

manager = LogManager()

# Ver resumo dos logs
print(manager.display_logs_summary())

# Limpar logs antigos (dry-run)
manager.cleanup(dry_run=True)

# Limpar logs antigos (real)
manager.cleanup(dry_run=False)

# Comprimir logs com mais de 7 dias
manager.compress_old_logs(days=7)

# Deletar logs com mais de 30 dias
manager.clean_old_logs(days=30)
```

### Via Linha de Comando

```bash
# Ver resumo dos logs
python -c "from src.core.utils.log_manager import LogManager; print(LogManager().display_logs_summary())"

# Simular limpeza (não deleta nada)
python -c "from src.core.utils.log_manager import LogManager; LogManager().cleanup(dry_run=True)"

# Executar limpeza real
python -c "from src.core.utils.log_manager import LogManager; LogManager().cleanup(dry_run=False)"
```

## 📊 Informações dos Logs

```python
from src.core.utils.log_manager import LogManager

manager = LogManager()
info = manager.get_log_info()

print(f"Total de arquivos: {info['total_files']}")
print(f"Tamanho total: {info['total_size_mb']} MB")
print(f"Comprimidos: {info['compressed']}")
print(f"Não comprimidos: {info['uncompressed']}")
print(f"Arquivo mais antigo: {info['oldest_file']}")
print(f"Arquivo mais recente: {info['newest_file']}")
```

## 🎨 Formato dos Logs

```
2025-11-02 21:15:30 | INFO     | main:run:125 | 🚀 Iniciando aplicação...
2025-11-02 21:15:30 | SUCCESS  | logger:setup:72 | Logger configurado
2025-11-02 21:15:31 | WARNING  | bot:send:145 | Rate limit atingido
2025-11-02 21:15:32 | ERROR    | scraper:parse:89 | Erro ao fazer parsing
```

Formato:
- **Verde**: Data/Hora
- **Colorido por nível**: Level (INFO, WARNING, ERROR, etc.)
- **Ciano**: Módulo:Função:Linha
- **Colorido por nível**: Mensagem

## 🔧 Uso no Código

### Importação Básica
```python
from src.core.utils.logger import logger

logger.debug("Mensagem de debug")
logger.info("Informação")
logger.success("Operação bem-sucedida")
logger.warning("Aviso")
logger.error("Erro")
logger.critical("Erro crítico")
```

### Logs com Contexto
```python
from src.core.utils.logger import (
    log_item_scraped,
    log_item_saved,
    log_notification_sent
)

# Logar item raspado
log_item_scraped("olx", "Moto Honda", "R$ 5.000")

# Logar item salvo
log_item_saved("facebook", 123, "Carro Civic")

# Logar notificação
log_notification_sent("telegram", "Novo anúncio", "chat_id")
```

### Context Managers
```python
from src.core.utils.logger import (
    log_scraper_execution,
    log_database_operation
)

# Logar execução de scraper
with log_scraper_execution('olx', 'motocicleta'):
    # código do scraper
    pass

# Logar operação de banco
with log_database_operation('insert', 'anuncios'):
    # código de inserção
    pass
```

## 📈 Boas Práticas

1. **Use níveis apropriados**:
   - `DEBUG`: Informações detalhadas para diagnóstico
   - `INFO`: Eventos importantes do fluxo normal
   - `SUCCESS`: Operações concluídas com sucesso
   - `WARNING`: Situações inesperadas mas recuperáveis
   - `ERROR`: Erros que impedem operação específica
   - `CRITICAL`: Erros que podem parar o sistema

2. **Configure retenção adequada**:
   - Desenvolvimento: 7-15 dias
   - Produção: 30-90 dias
   - Auditoria: 180-365 dias

3. **Monitore espaço em disco**:
   ```bash
   du -sh logs/
   ```

4. **Rotação por tempo vs tamanho**:
   - **Tempo**: Melhor para análise diária/semanal
   - **Tamanho**: Melhor para sistemas com volume variável

## 🐛 Troubleshooting

### Logs não estão sendo criados
- Verifique permissões do diretório `logs/`
- Confirme que `LOG_DIR` existe ou pode ser criado
- Verifique variáveis no `.env`

### Logs não estão sendo deletados
- Confirme `LOG_RETENTION_DAYS` no `.env`
- Execute limpeza manual: `manager.cleanup()`
- Verifique logs de erro na inicialização

### Logs muito grandes
- Reduza `LOG_RETENTION_DAYS`
- Use rotação por tamanho menor (ex: `5 MB`)
- Aumente nível para `WARNING` ou `ERROR`
- Execute compressão manual: `manager.compress_old_logs(days=1)`

### Logs comprimidos não podem ser lidos
- Use ferramentas de descompressão:
  ```bash
  # ZIP
  unzip marketplace_2025-11-01.log.zip
  
  # GZ
  gunzip marketplace_2025-11-01.log.gz
  ```

## 📝 Exemplos de Configuração

### Desenvolvimento (alta verbosidade)
```bash
LOG_LEVEL=DEBUG
LOG_ROTATION=10 MB
LOG_RETENTION_DAYS=7
```

### Produção (balanceado)
```bash
LOG_LEVEL=INFO
LOG_ROTATION=00:00
LOG_RETENTION_DAYS=30
```

### Servidor (conservador)
```bash
LOG_LEVEL=WARNING
LOG_ROTATION=00:00
LOG_RETENTION_DAYS=90
LOG_COMPRESSION=gz
```

## 🔐 Segurança

- Logs podem conter dados sensíveis
- Configure `.gitignore` para ignorar `logs/`
- Use permissões restritivas no diretório
- Considere criptografia para logs muito antigos

## 📚 Referências

- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
