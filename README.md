# Facebook Marketplace Scraper

Sistema de scraping para coletar anúncios do Facebook Marketplace com autenticação e armazenamento em SQLite.

## 📋 Características

- ✅ Login automático no Facebook com salvamento de cookies
- ✅ Busca de anúncios por palavra-chave
- ✅ Filtro por cidade (Curitiba por padrão)
- ✅ Armazenamento automático em banco SQLite
- ✅ Extração de: título, preço, localização, URL, imagem
- ✅ Tratamento de erros e logging detalhado
- ✅ Uso de Selenium para lidar com JavaScript

## 🚀 Instalação

### Pré-requisitos

- Python 3.9+
- Google Chrome instalado
- ChromeDriver (instalado automaticamente)

### Instalar dependências

```bash
# Ativar ambiente virtual (se ainda não ativou)
.venv\Scripts\activate

# As dependências já foram instaladas:
# - scrapy
# - selenium
# - webdriver-manager
# - scrapy-selenium
```

## 📖 Como Usar

### Método 1: Via Módulo Python

```python
from buscar_marketplace import buscar_anuncios

# Buscar sem login (limitado)
buscar_anuncios(palavra_chave="honda civic")

# Buscar com login (recomendado)
buscar_anuncios(
    palavra_chave="honda civic",
    email="seu_email@exemplo.com",
    senha="sua_senha",
    cidade="curitiba"
)
```

### Método 2: Via Linha de Comando

```bash
# Buscar sem login
python buscar_marketplace.py "honda civic"

# Buscar com login
python buscar_marketplace.py "honda civic" --email seu@email.com --senha sua_senha

# Buscar em outra cidade
python buscar_marketplace.py "iphone" --cidade "sao-paulo"

# Forçar novo login (não usar cookies salvos)
python buscar_marketplace.py "notebook" --email seu@email.com --senha sua_senha --no-cookies
```

### Método 3: Via Scrapy Diretamente

```bash
# Sem login
scrapy crawl facebook_marketplace -a palavra_chave="honda civic"

# Com cidade específica
scrapy crawl facebook_marketplace -a palavra_chave="iphone" -a cidade="sao-paulo"
```

## 📊 Banco de Dados

Os anúncios são salvos automaticamente em `marketplace_anuncios.db` (SQLite).

### Estrutura da Tabela

```sql
CREATE TABLE anuncios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    descricao TEXT,
    preco TEXT,
    localizacao TEXT,
    url TEXT UNIQUE,
    imagem_url TEXT,
    vendedor TEXT,
    palavra_chave TEXT,
    data_coleta TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Consultar Dados

```python
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('marketplace_anuncios.db')
cursor = conn.cursor()

# Buscar todos os anúncios
cursor.execute("SELECT * FROM anuncios")
anuncios = cursor.fetchall()

# Buscar por palavra-chave
cursor.execute("SELECT titulo, preco, url FROM anuncios WHERE palavra_chave = ?", ("honda civic",))
resultados = cursor.fetchall()

for titulo, preco, url in resultados:
    print(f"{titulo} - {preco}")
    print(f"Link: {url}\n")

conn.close()
```

## 🔧 Configurações

As configurações principais estão em `facebook_marketplace/settings.py`:

- **USER_AGENT**: Agente de usuário para evitar bloqueios
- **DOWNLOAD_DELAY**: Delay entre requisições (2 segundos)
- **CONCURRENT_REQUESTS**: Requisições simultâneas (4)
- **SELENIUM_DRIVER_ARGUMENTS**: Configurações do Chrome

## 📁 Estrutura do Projeto

```
src-scrapy-marketplace-v2/
├── facebook_marketplace/
│   ├── __init__.py
│   ├── items.py              # Definição dos items (dados coletados)
│   ├── pipelines.py          # Pipeline SQLite
│   ├── settings.py           # Configurações do Scrapy
│   ├── middlewares.py        # Middlewares personalizados
│   ├── facebook_login.py     # Módulo de login no Facebook
│   └── spiders/
│       ├── __init__.py
│       └── facebook_marketplace_spider.py  # Spider principal
├── buscar_marketplace.py     # Script principal
├── scrapy.cfg               # Configuração do projeto Scrapy
└── README.md                # Este arquivo
```

## ⚠️ Avisos Importantes

### Proteções do Facebook

O Facebook possui proteções anti-bot sofisticadas:

1. **Captcha**: Pode solicitar verificação humana
2. **Verificação de Segurança**: Pode pedir código SMS/email
3. **Limite de Requisições**: Pode bloquear temporariamente
4. **Cookies**: São salvos para reutilização e evitar logins frequentes

### Recomendações

- ✅ Use delays apropriados (configurado em 2s)
- ✅ Não faça muitas requisições seguidas
- ✅ Reutilize cookies salvos
- ✅ Execute em modo headless para performance
- ⚠️ Use conta de teste, não sua conta principal
- ⚠️ Respeite os Termos de Serviço do Facebook

### Limitações

- O Facebook pode alterar a estrutura HTML a qualquer momento
- Anúncios muito novos podem não aparecer
- Algumas informações requerem acesso à página individual do anúncio
- Login pode falhar se houver verificações de segurança

## 🐛 Debug

Se encontrar problemas:

1. **Verificar logs**: Os logs mostram o que está acontecendo
2. **Arquivo HTML**: É salvo como `marketplace_debug.html` para análise
3. **Modo não-headless**: Altere `headless=False` para ver o navegador

```python
# Em facebook_login.py, linha 17
fb_login = FacebookLogin(headless=False)  # Ver o navegador
```

## 📝 Exemplo Completo

```python
"""
Exemplo de uso completo do sistema
"""

from buscar_marketplace import buscar_anuncios
import sqlite3

# 1. Buscar anúncios
print("Buscando anúncios...")
sucesso = buscar_anuncios(
    palavra_chave="honda civic",
    email="seu_email@exemplo.com",  # Opcional
    senha="sua_senha",               # Opcional
    cidade="curitiba"
)

if sucesso:
    print("✓ Busca concluída!")
    
    # 2. Consultar resultados
    print("\nResultados salvos no banco de dados:")
    
    conn = sqlite3.connect('marketplace_anuncios.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT titulo, preco, localizacao, url 
        FROM anuncios 
        WHERE palavra_chave = 'honda civic'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    for titulo, preco, localizacao, url in cursor.fetchall():
        print(f"\n{titulo}")
        print(f"Preço: {preco}")
        print(f"Local: {localizacao}")
        print(f"Link: {url}")
    
    conn.close()
else:
    print("✗ Erro na busca")
```

## 🤝 Contribuindo

Sinta-se à vontade para melhorar o código:

1. Adicionar mais campos extraídos
2. Melhorar os seletores CSS/XPath
3. Adicionar suporte para outras cidades
4. Implementar paginação
5. Adicionar exportação para CSV/JSON

## 📄 Licença

Este projeto é para fins educacionais. Use com responsabilidade e respeite os Termos de Serviço do Facebook.
