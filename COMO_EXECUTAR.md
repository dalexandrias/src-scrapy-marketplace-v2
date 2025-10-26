# 🎯 COMO EXECUTAR - Primeira Vez

## Passo a Passo para Iniciantes

### 1️⃣ Certifique-se de que o ambiente virtual está ativo

```powershell
# Verifique se aparece (.venv) no início do prompt
# Se não aparecer, ative com:
.venv\Scripts\activate
```

### 2️⃣ Escolha UMA das opções abaixo:

---

## 🔥 OPÇÃO 1: Busca SEM Login (Mais Simples)

### Via Python:
```python
from buscar_marketplace import buscar_anuncios

# Buscar "honda civic" em Curitiba
buscar_anuncios(palavra_chave="honda civic")
```

### Via Linha de Comando:
```powershell
python buscar_marketplace.py "honda civic"
```

**Pronto!** Os anúncios serão salvos em `marketplace_anuncios.db`

---

## 🔐 OPÇÃO 2: Busca COM Login (Mais Completo)

### Via Python:
```python
from buscar_marketplace import buscar_anuncios

buscar_anuncios(
    palavra_chave="honda civic",
    email="SEU_EMAIL@exemplo.com",      # ⬅️ MUDE AQUI
    senha="SUA_SENHA",                   # ⬅️ MUDE AQUI
    cidade="curitiba"
)
```

### Via Linha de Comando:
```powershell
python buscar_marketplace.py "honda civic" --email SEU_EMAIL@exemplo.com --senha SUA_SENHA
```

**Importante:** 
- Use uma conta de teste, não sua conta pessoal
- Os cookies serão salvos para reutilização
- Da próxima vez não precisará fazer login novamente

---

## 📊 Ver os Resultados

### Opção 1: Via Python
```python
import sqlite3

conn = sqlite3.connect('marketplace_anuncios.db')
cursor = conn.cursor()

# Buscar todos os anúncios
cursor.execute("SELECT titulo, preco, url FROM anuncios")

for titulo, preco, url in cursor.fetchall():
    print(f"{titulo} - {preco}")
    print(f"{url}\n")

conn.close()
```

### Opção 2: Usar o Exemplo Pronto
```powershell
python exemplo_uso.py
```

### Opção 3: DB Browser for SQLite
1. Baixe: https://sqlitebrowser.org/
2. Abra o arquivo `marketplace_anuncios.db`
3. Veja os dados na tabela `anuncios`

---

## 🧪 Testar se Está Tudo OK

```powershell
python teste.py
```

Deve mostrar:
```
✓ Estrutura de Arquivos: PASSOU
```

---

## 📝 Exemplo Completo Passo a Passo

1. **Abrir terminal no VS Code** (Ctrl + ')

2. **Ativar ambiente virtual** (se não estiver ativo):
   ```powershell
   .venv\Scripts\activate
   ```

3. **Criar arquivo `minha_busca.py`**:
   ```python
   from buscar_marketplace import buscar_anuncios
   import sqlite3

   # Fazer a busca
   print("Buscando anúncios...")
   buscar_anuncios(palavra_chave="honda civic")

   # Ver resultados
   print("\nResultados:")
   conn = sqlite3.connect('marketplace_anuncios.db')
   cursor = conn.cursor()
   cursor.execute("SELECT titulo, preco FROM anuncios LIMIT 5")
   
   for titulo, preco in cursor.fetchall():
       print(f"- {titulo}: {preco}")
   
   conn.close()
   ```

4. **Executar**:
   ```powershell
   python minha_busca.py
   ```

---

## ❓ Problemas Comuns

### "ModuleNotFoundError: No module named 'scrapy'"
**Solução:** Ative o ambiente virtual
```powershell
.venv\Scripts\activate
```

### "scrapy: The term 'scrapy' is not recognized"
**Solução:** Use o Python do ambiente virtual
```powershell
python buscar_marketplace.py "honda civic"
```
Não use `scrapy` diretamente.

### "Nenhum anúncio encontrado"
**Soluções:**
1. Tente com login (email e senha)
2. Tente outra palavra-chave
3. Verifique `marketplace_debug.html` que foi gerado

### "Login falhou"
**Soluções:**
1. Verifique email e senha
2. Facebook pode pedir verificação (SMS/email)
3. Tente abrir o Facebook manualmente primeiro
4. Use uma conta de teste

---

## 🎬 Exemplo Rápido de 30 Segundos

```powershell
# 1. Ativar ambiente
.venv\Scripts\activate

# 2. Buscar
python buscar_marketplace.py "iphone"

# 3. Ver resultados (aguardar finalizar a busca antes)
python -c "import sqlite3; conn = sqlite3.connect('marketplace_anuncios.db'); cursor = conn.cursor(); cursor.execute('SELECT titulo, preco FROM anuncios LIMIT 10'); [print(f'{t} - {p}') for t, p in cursor.fetchall()]"
```

---

## 📚 Próximos Passos

1. ✅ Executar primeira busca
2. ✅ Ver resultados no banco
3. ✅ Testar com login
4. ✅ Fazer múltiplas buscas
5. ✅ Explorar `exemplo_uso.py`
6. ✅ Ler `README.md` completo

---

## 🆘 Precisa de Ajuda?

1. Veja os logs no terminal - eles mostram o que está acontecendo
2. Execute `python teste.py` para verificar o sistema
3. Confira `GUIA_RAPIDO.md` para comandos úteis
4. Leia `PROJETO_COMPLETO.md` para entender a arquitetura

---

**Boa sorte! 🚀**
