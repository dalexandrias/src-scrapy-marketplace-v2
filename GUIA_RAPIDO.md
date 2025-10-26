# 🚀 Guia Rápido de Uso

## Início Rápido (5 minutos)

### 1. Busca Simples (Sem Login)

```python
from buscar_marketplace import buscar_anuncios

# Buscar anúncios de "honda civic" em Curitiba
buscar_anuncios(palavra_chave="honda civic")
```

**Linha de comando:**
```bash
python buscar_marketplace.py "honda civic"
```

---

### 2. Busca com Login (Recomendado)

```python
from buscar_marketplace import buscar_anuncios

buscar_anuncios(
    palavra_chave="honda civic",
    email="seu_email@exemplo.com",
    senha="sua_senha",
    cidade="curitiba"
)
```

**Linha de comando:**
```bash
python buscar_marketplace.py "honda civic" --email seu@email.com --senha sua_senha
```

---

### 3. Consultar Resultados

```python
import sqlite3

# Conectar ao banco
conn = sqlite3.connect('marketplace_anuncios.db')
cursor = conn.cursor()

# Buscar anúncios
cursor.execute("""
    SELECT titulo, preco, url 
    FROM anuncios 
    WHERE palavra_chave = 'honda civic'
    ORDER BY created_at DESC
""")

# Mostrar resultados
for titulo, preco, url in cursor.fetchall():
    print(f"{titulo} - {preco}")
    print(f"Link: {url}\n")

conn.close()
```

---

## 📋 Comandos Úteis

### Executar Busca
```bash
# Busca simples
python buscar_marketplace.py "produto desejado"

# Busca com login
python buscar_marketplace.py "produto" --email email@exemplo.com --senha senha123

# Busca em outra cidade
python buscar_marketplace.py "produto" --cidade "sao-paulo"

# Forçar novo login (não usar cookies)
python buscar_marketplace.py "produto" --email email@exemplo.com --senha senha123 --no-cookies
```

### Executar Testes
```bash
python teste.py
```

### Ver Exemplos
```bash
python exemplo_uso.py
```

---

## 📊 Estrutura do Banco de Dados

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
);
```

---

## 🔍 Consultas SQL Úteis

### Total de anúncios
```sql
SELECT COUNT(*) FROM anuncios;
```

### Anúncios por palavra-chave
```sql
SELECT palavra_chave, COUNT(*) as total
FROM anuncios
GROUP BY palavra_chave;
```

### Últimos 10 anúncios
```sql
SELECT titulo, preco, url, created_at
FROM anuncios
ORDER BY created_at DESC
LIMIT 10;
```

### Anúncios de uma busca específica
```sql
SELECT titulo, preco, localizacao, url
FROM anuncios
WHERE palavra_chave = 'honda civic'
ORDER BY created_at DESC;
```

### Anúncios por faixa de preço (exemplo)
```sql
SELECT titulo, preco, url
FROM anuncios
WHERE preco LIKE '%30.000%' OR preco LIKE '%40.000%'
ORDER BY created_at DESC;
```

---

## ⚠️ Troubleshooting

### Problema: "Scrapy não encontrado"
**Solução:** Ative o ambiente virtual
```bash
.venv\Scripts\activate
```

### Problema: "ChromeDriver não encontrado"
**Solução:** O ChromeDriver é instalado automaticamente. Certifique-se de ter o Google Chrome instalado.

### Problema: "Login falhou"
**Soluções:**
1. Verifique email e senha
2. Facebook pode pedir verificação de segurança (SMS/email)
3. Use cookies salvos após primeiro login bem-sucedido
4. Execute com `headless=False` para ver o que está acontecendo

### Problema: "Nenhum anúncio encontrado"
**Soluções:**
1. Verifique o arquivo `marketplace_debug.html` gerado
2. Facebook pode ter alterado a estrutura HTML
3. Pode precisar de login para ver anúncios
4. Tente outra palavra-chave

---

## 📁 Arquivos Importantes

- `buscar_marketplace.py` - Script principal de busca
- `facebook_marketplace/facebook_login.py` - Módulo de login
- `facebook_marketplace/spiders/facebook_marketplace_spider.py` - Spider do Scrapy
- `facebook_marketplace/pipelines.py` - Pipeline para salvar no SQLite
- `facebook_marketplace/settings.py` - Configurações do Scrapy
- `marketplace_anuncios.db` - Banco de dados SQLite (criado após primeira busca)
- `facebook_cookies.pkl` - Cookies salvos do Facebook

---

## 💡 Dicas

1. **Use cookies salvos:** Após primeiro login, os cookies são reutilizados automaticamente
2. **Respeite delays:** O sistema já tem delays configurados (2s entre requisições)
3. **Não abuse:** Evite fazer muitas requisições seguidas
4. **Use conta de teste:** Não use sua conta pessoal do Facebook
5. **Verifique logs:** Os logs mostram detalhes do processo
6. **Debug HTML:** O arquivo `marketplace_debug.html` ajuda a entender a estrutura

---

## 🎯 Exemplos de Busca

```python
# Carros
buscar_anuncios("honda civic")
buscar_anuncios("toyota corolla")

# Eletrônicos
buscar_anuncios("iphone 14")
buscar_anuncios("notebook dell")

# Imóveis
buscar_anuncios("apartamento")

# Múltiplas buscas
palavras = ["honda civic", "toyota corolla", "ford focus"]
for palavra in palavras:
    buscar_anuncios(palavra)
```

---

**Leia o README.md completo para mais informações!**
