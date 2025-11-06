# 🚀 Execução Paralela com Multithread

## Visão Geral

O sistema agora suporta **execução paralela** de buscas usando **ThreadPoolExecutor** do Python. Isso significa que múltiplas palavras-chave podem ser buscadas simultaneamente, acelerando significativamente o processo.

## Configuração

### Variável de Ambiente

Adicione ao seu arquivo `.env`:

```bash
# Número de threads para executar buscas em paralelo (1-10)
# Maior = mais rápido, mas consome mais recursos
# Recomendado: 3-5 para melhor performance
SCHEDULER_MAX_WORKERS=3
```

### Valores Recomendados

| Workers | Uso Recomendado | Características |
|---------|----------------|-----------------|
| **1** | Testes, recursos limitados | Execução sequencial (sem paralelismo) |
| **3** | **Recomendado** | Balanceamento ideal entre velocidade e recursos |
| **5** | Máquinas potentes | Maior velocidade, maior consumo de RAM/CPU |
| **10** | Servidores dedicados | Máxima velocidade possível |

## Como Funciona

### Antes (Sequencial)
```
Palavra 1 → [====] 30s
Palavra 2 →          [====] 30s  
Palavra 3 →                   [====] 30s
Total: 90 segundos
```

### Depois (Paralelo com 3 workers)
```
Palavra 1 → [====] 30s
Palavra 2 → [====] 30s
Palavra 3 → [====] 30s
Total: 30 segundos
```

## Ganho de Performance

### Exemplo Real: 9 Palavras-chave

| Workers | Tempo Estimado | Ganho |
|---------|----------------|-------|
| 1 worker | ~4.5 minutos | Baseline |
| 3 workers | ~**1.5 minutos** | **3x mais rápido** |
| 5 workers | ~**54 segundos** | **5x mais rápido** |

## Implementação Técnica

### ThreadPoolExecutor

O sistema usa `concurrent.futures.ThreadPoolExecutor` para:
- Submeter todas as tarefas de busca
- Executar até N tarefas simultaneamente (N = MAX_WORKERS)
- Processar resultados conforme completam
- Gerenciar recursos automaticamente

### Thread-Safe

Todos os métodos são **thread-safe**:
- ✅ Cada thread executa scraper independente (subprocess)
- ✅ Resultados consolidados após todas as threads
- ✅ Logs com identificação da palavra-chave
- ✅ Banco de dados SQLite com controle de concorrência

## Logs Melhorados

### Logs com Identificação

```
🔍 [honda pcx] Iniciando busca OLX...
🔍 [onix] Iniciando busca Facebook...
✅ [honda pcx] OLX: 15 encontrados, 3 novos
✅ [onix] Facebook: 20 encontrados, 5 novos
```

### Resumo de Execução

```
📝 9 palavras-chave encontradas - Usando 3 workers
📊 Resumo OLX: 8 sucessos, 1 erro
📊 Total: 120 encontrados, 15 novos
✅ Busca OLX finalizada em 87.3s (9 palavras com 3 workers)
```

## Recursos do Sistema

### Consumo por Worker

- **CPU**: ~10-15% por worker durante busca
- **RAM**: ~100-200MB por worker (Playwright + Chromium)
- **Rede**: Depende da quantidade de anúncios

### Recomendações de Hardware

| Configuração | Max Workers |
|--------------|-------------|
| 2GB RAM, 2 cores | 1-2 |
| 4GB RAM, 4 cores | 3-4 |
| 8GB+ RAM, 6+ cores | 5-10 |

## Monitoramento

### Via Logs

Acompanhe em tempo real:
```bash
tail -f logs/marketplace.log
```

### Via Bot do Telegram

O bot enviará:
- Notificação de início (com número de workers)
- Progresso individual de cada palavra
- Resumo final com estatísticas

## Ajuste Fino

### Otimizar para Velocidade
```bash
SCHEDULER_MAX_WORKERS=5  # Mais threads
```

### Otimizar para Recursos
```bash
SCHEDULER_MAX_WORKERS=2  # Menos threads
```

### Balanceamento
```bash
SCHEDULER_MAX_WORKERS=3  # Ideal (padrão)
```

## Troubleshooting

### Muitos Timeouts

**Problema**: Workers em excesso sobrecarregando o sistema

**Solução**: Reduzir MAX_WORKERS
```bash
SCHEDULER_MAX_WORKERS=2
```

### Muito Lento

**Problema**: Poucos workers, execução sequencial

**Solução**: Aumentar MAX_WORKERS
```bash
SCHEDULER_MAX_WORKERS=5
```

### Alto Consumo de RAM

**Problema**: Muitos navegadores Chromium abertos simultaneamente

**Solução**: 
1. Reduzir workers
2. Verificar se há processos fantasma do Chromium

```bash
# Windows
taskkill /F /IM chrome.exe

# Linux
pkill chromium
```

## Código

### Arquivos Modificados

1. **`.env.example`**
   - Adicionado `SCHEDULER_MAX_WORKERS=3`

2. **`src/core/config.py`**
   - Classe `SchedulerConfig` com validação (1-10 workers)

3. **`src/managers/scheduler_manager.py`**
   - Métodos `_execute_olx_scraper()` e `_execute_facebook_scraper()` thread-safe
   - Métodos `_run_olx_search()` e `_run_facebook_search()` com ThreadPoolExecutor
   - Logs melhorados com identificação de palavra

## Benefícios

✅ **Velocidade**: Até 10x mais rápido (com 10 workers)  
✅ **Eficiência**: Melhor uso de CPU multi-core  
✅ **Escalabilidade**: Configurável via `.env`  
✅ **Confiabilidade**: Thread-safe e com tratamento de erros  
✅ **Monitoramento**: Logs detalhados e resumo de execução  

## Comparação de Cenários

### Cenário 1: 3 Palavras-chave
- **Sequencial**: 90s (1 worker)
- **Paralelo**: 30s (3 workers) - **3x mais rápido**

### Cenário 2: 10 Palavras-chave
- **Sequencial**: 300s = 5min (1 worker)
- **Paralelo**: 60s = 1min (5 workers) - **5x mais rápido**

### Cenário 3: 20 Palavras-chave
- **Sequencial**: 600s = 10min (1 worker)
- **Paralelo**: 120s = 2min (10 workers) - **5x mais rápido**

---

**Versão**: 2.0.1  
**Data**: 31/10/2025  
**Feature**: Multithread com ThreadPoolExecutor
