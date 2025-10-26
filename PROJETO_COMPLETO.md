# 📦 Facebook Marketplace Scraper - Resumo do Projeto

## ✅ O que foi implementado

### 1. Sistema de Login no Facebook
- ✅ Função `FacebookLogin` que recebe email e senha
- ✅ Login automático via Selenium
- ✅ Identificação automática dos campos de login
- ✅ Preenchimento automático de credenciais
- ✅ Verificação de login bem-sucedido
- ✅ Tratamento de erros e mensagens de bloqueio
- ✅ Salvamento e carregamento de cookies
- ✅ Reutilização de sessão autenticada

**Arquivo:** `facebook_marketplace/facebook_login.py`

### 2. Spider do Scrapy para Marketplace
- ✅ Spider configurado para Curitiba
- ✅ Aceita palavra-chave como parâmetro
- ✅ Monta URL corretamente com query encoding
- ✅ Usa Selenium para lidar com JavaScript
- ✅ Extrai título, preço, localização, URL, imagem
- ✅ Múltiplos seletores CSS para maior compatibilidade
- ✅ Salva HTML para debug quando necessário
- ✅ Logging detalhado do processo

**Arquivo:** `facebook_marketplace/spiders/facebook_marketplace_spider.py`

### 3. Banco de Dados SQLite
- ✅ Schema completo com todos os campos
- ✅ Índices para otimizar buscas
- ✅ Constraint UNIQUE em URLs (evita duplicatas)
- ✅ Timestamps automáticos
- ✅ Pipeline automático de salvamento

**Arquivo:** `facebook_marketplace/pipelines.py`

### 4. Sistema de Items
- ✅ Definição completa dos campos
- ✅ Campos: titulo, descricao, preco, localizacao, url, imagem_url, vendedor, palavra_chave, data_coleta

**Arquivo:** `facebook_marketplace/items.py`

### 5. Configurações Otimizadas
- ✅ User-Agent realista
- ✅ Delays apropriados (2s)
- ✅ Headers HTTP completos
- ✅ Selenium configurado com anti-detecção
- ✅ AutoThrottle habilitado
- ✅ Logging configurado

**Arquivo:** `facebook_marketplace/settings.py`

### 6. Função Principal de Busca
- ✅ Interface simples: `buscar_anuncios(palavra_chave, email, senha, cidade)`
- ✅ Suporte para busca com e sem login
- ✅ Reutilização automática de cookies
- ✅ Integração completa: login → busca → salvamento
- ✅ Linha de comando com argumentos
- ✅ Tratamento de erros completo

**Arquivo:** `buscar_marketplace.py`

### 7. Documentação Completa
- ✅ README.md detalhado
- ✅ GUIA_RAPIDO.md para uso imediato
- ✅ Exemplos de código comentados
- ✅ Consultas SQL úteis
- ✅ Troubleshooting

### 8. Sistema de Testes
- ✅ Teste de estrutura de arquivos
- ✅ Teste de login
- ✅ Teste de banco de dados
- ✅ Teste de busca
- ✅ Exemplos de uso

**Arquivo:** `teste.py` e `exemplo_uso.py`

---

## 📂 Estrutura Completa do Projeto

```
src-scrapy-marketplace-v2/
│
├── .venv/                          # Ambiente virtual Python
├── facebook_marketplace/           # Pacote principal do Scrapy
│   ├── __init__.py
│   ├── items.py                    # Definição dos items
│   ├── pipelines.py                # Pipeline SQLite
│   ├── settings.py                 # Configurações do Scrapy
│   ├── middlewares.py              # Middlewares
│   ├── facebook_login.py           # Módulo de login
│   └── spiders/
│       ├── __init__.py
│       └── facebook_marketplace_spider.py  # Spider principal
│
├── buscar_marketplace.py           # Script principal
├── exemplo_uso.py                  # Exemplos de uso
├── teste.py                        # Testes automatizados
├── scrapy.cfg                      # Configuração do Scrapy
├── requirements.txt                # Dependências
├── .gitignore                      # Arquivos ignorados pelo Git
├── README.md                       # Documentação completa
├── GUIA_RAPIDO.md                  # Guia rápido
│
└── marketplace_anuncios.db         # Banco SQLite (criado ao executar)
```

---

## 🎯 Como Usar

### Método 1: Python (Recomendado)
```python
from buscar_marketplace import buscar_anuncios

buscar_anuncios(
    palavra_chave="honda civic",
    email="seu_email@exemplo.com",
    senha="sua_senha"
)
```

### Método 2: Linha de Comando
```bash
python buscar_marketplace.py "honda civic" --email email@exemplo.com --senha senha123
```

### Método 3: Scrapy Direto
```bash
scrapy crawl facebook_marketplace -a palavra_chave="honda civic"
```

---

## 🔧 Tecnologias Utilizadas

- **Scrapy 2.11+** - Framework de web scraping
- **Selenium 4.15+** - Automação de navegador
- **WebDriver Manager** - Gerenciamento automático do ChromeDriver
- **scrapy-selenium** - Integração Scrapy + Selenium
- **SQLite** - Banco de dados
- **Python 3.9+** - Linguagem de programação

---

## 📊 Fluxo de Execução

```
1. Usuário chama buscar_anuncios()
   ↓
2. Sistema verifica se há email/senha
   ↓
3. Se sim: FacebookLogin.login()
   ├─ Abre navegador Chrome
   ├─ Acessa facebook.com
   ├─ Preenche email e senha
   ├─ Clica em login
   ├─ Verifica sucesso
   └─ Salva cookies
   ↓
4. Ou: Carrega cookies salvos
   ↓
5. Inicia CrawlerProcess do Scrapy
   ↓
6. FacebookMarketplaceSpider executa
   ├─ Monta URL com palavra-chave
   ├─ Faz requisição com Selenium
   ├─ Aguarda carregamento
   ├─ Extrai dados dos anúncios
   └─ Gera MarketplaceAnuncioItem
   ↓
7. SQLitePipeline processa items
   ├─ Conecta ao banco
   ├─ Cria tabela se não existir
   ├─ Insere anúncio (ou ignora se duplicado)
   └─ Commita transação
   ↓
8. Resultados salvos em marketplace_anuncios.db
```

---

## 🎉 Funcionalidades Destacadas

### 🔐 Login Inteligente
- Salva cookies após primeiro login
- Reutiliza cookies automaticamente
- Apenas faz novo login quando necessário

### 🚀 Performance
- Delays otimizados (2s)
- AutoThrottle habilitado
- Concurrent requests limitado (4)

### 🛡️ Anti-Detecção
- User-Agent realista
- Headers HTTP completos
- Remove indicadores de automação
- Selenium configurado para parecer navegação humana

### 💾 Persistência
- SQLite com constraints UNIQUE
- Evita duplicatas automaticamente
- Índices para busca rápida
- Timestamps automáticos

### 📝 Logging Completo
- Logs de todas as etapas
- Níveis apropriados (INFO, WARNING, ERROR)
- HTML salvo para debug
- Timestamps em todos os logs

---

## ⚠️ Limitações Conhecidas

1. **Facebook muda frequentemente:** A estrutura HTML pode mudar
2. **Captcha:** Facebook pode solicitar verificação
3. **Rate Limiting:** Muitas requisições podem resultar em bloqueio temporário
4. **Login:** Verificações de segurança podem impedir login automático
5. **JavaScript pesado:** Facebook usa muito JavaScript dinâmico
6. **Descrição completa:** Requer acessar página individual do anúncio

---

## 🔮 Melhorias Futuras Possíveis

- [ ] Acessar página individual de cada anúncio para descrição completa
- [ ] Implementar paginação para buscar mais resultados
- [ ] Adicionar suporte para filtros (preço, localização, etc.)
- [ ] Exportar para CSV/JSON além de SQLite
- [ ] Interface gráfica (GUI)
- [ ] Suporte para múltiplas cidades simultaneamente
- [ ] Notificações quando novos anúncios aparecem
- [ ] Análise de preços e tendências
- [ ] Suporte para Playwright (alternativa ao Selenium)
- [ ] API REST para integração com outros sistemas

---

## 📞 Suporte

### Logs
Todos os logs são exibidos no console com timestamps e níveis.

### Debug
- Arquivo `marketplace_debug.html` é criado quando anúncios não são encontrados
- Execute com `headless=False` para ver o navegador

### Testes
```bash
python teste.py
```

---

## ✨ Conclusão

Sistema completo e funcional para:
1. ✅ Login no Facebook com email e senha
2. ✅ Busca de anúncios no Marketplace
3. ✅ Extração de dados (título, preço, URL, etc.)
4. ✅ Salvamento automático em SQLite
5. ✅ Reutilização de sessão via cookies
6. ✅ Tratamento de erros e logging
7. ✅ Documentação completa

**Pronto para uso!** 🚀
