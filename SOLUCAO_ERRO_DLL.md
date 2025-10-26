# 🔧 Solução de Problemas - Python 3.9 + Windows

## ❌ Problemas Encontrados

### Erro 1: ImportError DLL
```
ImportError: DLL load failed while importing _rust: 
Não foi possível encontrar o procedimento especificado.
```

### Erro 2: AttributeError com Twisted Reactor
```
AttributeError: 'AsyncioSelectorReactor' object has no attribute '_handleSignals'
AttributeError: 'SelectReactor' object has no attribute '_handleSignals'
```

### Erro 3: SeleniumMiddleware Desabilitado
```
WARNING: Disabled SeleniumMiddleware: SELENIUM_DRIVER_NAME and 
SELENIUM_DRIVER_EXECUTABLE_PATH must be set
```

## 🔍 Causas

**Erro 1:** Incompatibilidade entre:
- Python 3.9
- Versões mais recentes do `cryptography` (43.x)
- Versões mais recentes do `scrapy` (2.11+)
- Windows

As versões mais recentes do `cryptography` usam bindings Rust que não são totalmente compatíveis com Python 3.9 no Windows.

**Erro 2:** Twisted reactor com signal handlers incompatível com Windows + Python 3.9

**Erro 3:** `which('chromedriver')` retorna `None` no Windows

## ✅ Soluções Aplicadas

### 1. Downgrade do cryptography e pyOpenSSL

```bash
pip uninstall -y cryptography pyopenssl
pip install cryptography==41.0.7 pyOpenSSL==23.3.0
```

### 2. Downgrade do Scrapy

```bash
pip uninstall -y scrapy
pip install scrapy==2.8.0
```

### 3. Correção do TWISTED_REACTOR

**Arquivo:** `facebook_marketplace/settings.py`

Comentado a linha:
```python
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
```

### 4. Alteração de CrawlerProcess para CrawlerRunner

**Arquivo:** `buscar_marketplace.py`

Substituído `CrawlerProcess` por `CrawlerRunner` com `reactor.run(installSignalHandlers=False)`

```python
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor, defer

# ...

configure_logging()
runner = CrawlerRunner(get_project_settings())

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(
        FacebookMarketplaceSpider,
        palavra_chave=palavra_chave,
        cidade=cidade
    )
    reactor.stop()

crawl()
reactor.run(installSignalHandlers=False)  # Desabilita signal handlers para evitar erro no Windows
```

### 5. Configuração Automática do ChromeDriver

**Arquivo:** `facebook_marketplace/settings.py`

Substituído `which('chromedriver')` por `ChromeDriverManager().install()`:

```python
from webdriver_manager.chrome import ChromeDriverManager

chrome_driver_path = ChromeDriverManager().install()

SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = chrome_driver_path
```

## 📋 Versões Compatíveis (Python 3.9 + Windows)

```
scrapy==2.8.0
cryptography==41.0.7
pyOpenSSL==23.3.0
selenium>=4.15.0
webdriver-manager>=4.0.1
scrapy-selenium>=0.0.7
```

## ✨ Resultado

Agora o script funciona perfeitamente:

```bash
python buscar_marketplace.py "honda civic" --email seu@email.com --senha sua_senha
```

## 🎯 Alternativas Futuras

Se quiser usar versões mais recentes:

### Opção 1: Atualizar Python
```bash
# Usar Python 3.10 ou 3.11
python --version  # Deve ser 3.10+
```

### Opção 2: Usar WSL (Windows Subsystem for Linux)
As versões mais recentes funcionam melhor no Linux.

### Opção 3: Usar Docker
Criar um container com ambiente controlado.

## 📝 Observações

- O `requirements.txt` foi atualizado com as versões corretas
- ChromeDriver é baixado automaticamente na primeira execução
- Os cookies do Facebook são salvos em `facebook_cookies.pkl`
- O banco de dados é criado em `marketplace_anuncios.db`

## 🔄 Se Reinstalar o Ambiente

```bash
# Deletar ambiente virtual
Remove-Item -Recurse -Force .venv

# Criar novo ambiente
python -m venv .venv
.venv\Scripts\activate

# Instalar dependências corretas
pip install -r requirements.txt
```

---

**Problema resolvido! ✅**
