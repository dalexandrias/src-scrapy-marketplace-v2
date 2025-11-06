# 🚫 Sistema de Deduplicação de Anúncios

## 📋 Visão Geral

O sistema agora possui **verificação automática** para não enviar anúncios duplicados no Telegram. Apenas **anúncios novos** (que ainda não foram enviados) serão enviados para você.

---

## ✅ Como Funciona

### 1️⃣ **Campos no Banco de Dados**

Cada anúncio na tabela `anuncios` possui os campos:

- `enviado_telegram` (INTEGER): 
  - `0` = Anúncio **não enviado** (padrão)
  - `1` = Anúncio **já enviado**

- `data_envio_telegram` (TEXT):
  - Data/hora em que o anúncio foi enviado pela primeira vez

### 2️⃣ **Filtragem Automática**

Quando você solicita anúncios via Telegram:

✅ **ANTES de enviar**: 
- Sistema busca apenas anúncios com `enviado_telegram = 0 OR NULL`

✅ **DEPOIS de enviar**:
- Sistema marca `enviado_telegram = 1`
- Registra `data_envio_telegram` com timestamp

### 3️⃣ **Onde se Aplica**

O sistema de deduplicação funciona em:

1. **Menu Principal** → "Ver 5/10/20 anúncios OLX"
2. **Menu Principal** → "Ver 5/10/20 anúncios Facebook"
3. **Buscar Palavra Específica** → Todos os resultados
4. **Buscas Automáticas** (scheduler) → Notificações

---

## 🔍 Testando o Sistema

### Verificar Status dos Anúncios

Execute o script de teste:

```bash
python test_envio_duplicado.py
```

**Resultado esperado:**
```
📊 Total de anúncios no banco: 389
✅ Anúncios já enviados: 0
📭 Anúncios não enviados: 389

📈 Estatísticas por origem:
  - OLX: 210 novos anúncios
  - FACEBOOK: 179 novos anúncios
```

### Resetar Status (Para Testes)

Se quiser **resetar** todos os anúncios como "não enviados" (útil para testes):

1. Edite `test_envio_duplicado.py`
2. Descomente as linhas 42-45:
   ```python
   print("\n⚠️  RESETANDO status de envio para testes...")
   cursor.execute("UPDATE anuncios SET enviado_telegram = 0, data_envio_telegram = NULL")
   conn.commit()
   print("✅ Status resetado!")
   ```
3. Execute: `python test_envio_duplicado.py`

---

## 📊 Exemplo de Uso

### Primeira Solicitação
Você: `/buscar_agora` → Ver 5 anúncios OLX

**Bot envia:**
- ✅ Anúncio 1
- ✅ Anúncio 2
- ✅ Anúncio 3
- ✅ Anúncio 4
- ✅ Anúncio 5

**Banco marca:** 5 anúncios com `enviado_telegram = 1`

---

### Segunda Solicitação (mesmo dia)
Você: `/buscar_agora` → Ver 5 anúncios OLX

**Bot verifica:**
- ❌ Anúncio 1 (já enviado)
- ❌ Anúncio 2 (já enviado)
- ❌ Anúncio 3 (já enviado)
- ❌ Anúncio 4 (já enviado)
- ❌ Anúncio 5 (já enviado)
- ✅ Anúncio 6 (NOVO!)
- ✅ Anúncio 7 (NOVO!)
- ... e assim por diante

**Bot envia APENAS:**
- ✅ Anúncio 6
- ✅ Anúncio 7
- ✅ Anúncio 8
- ✅ Anúncio 9
- ✅ Anúncio 10

---

### Quando Não Há Novos Anúncios

Se todos os anúncios já foram enviados:

```
📭 Nenhum anúncio novo encontrado

A busca por 'honda pcx' não retornou novos anúncios.
Todos os anúncios disponíveis já foram enviados anteriormente.
```

---

## 🔧 Detalhes Técnicos

### Modificações Aplicadas

#### 1. `src/bot/telegram_bot.py` - Função `_send_found_ads()`

**Query SQL modificada:**
```sql
SELECT id, titulo, preco, localizacao, url, data_coleta, imagem_url
FROM anuncios
WHERE origem = ?
  AND (enviado_telegram = 0 OR enviado_telegram IS NULL)  -- 🆕 NOVO FILTRO
ORDER BY data_coleta DESC
LIMIT ?
```

**Após envio:**
```python
# Marcar anúncios como enviados
UPDATE anuncios 
SET enviado_telegram = 1, data_envio_telegram = ?
WHERE id IN (?, ?, ?, ...)
```

#### 2. `src/bot/telegram_bot.py` - Função `_send_found_ads_by_palavra()`

**Mesmas modificações** aplicadas para buscas por palavra-chave.

---

## 🎯 Vantagens

✅ **Sem Duplicatas**: Você nunca verá o mesmo anúncio duas vezes  
✅ **Economia de Tempo**: Veja apenas anúncios novos  
✅ **Controle Preciso**: Saiba exatamente quais anúncios já foram visualizados  
✅ **Rastreabilidade**: Data/hora de quando cada anúncio foi enviado  

---

## 🗄️ Estrutura do Banco de Dados

```sql
CREATE TABLE anuncios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    preco TEXT,
    localizacao TEXT,
    url TEXT UNIQUE,
    imagem_url TEXT,
    palavra_chave TEXT,
    origem TEXT,  -- 'olx' ou 'facebook'
    data_coleta TIMESTAMP,
    
    -- 🆕 CAMPOS DE RASTREAMENTO
    enviado_telegram INTEGER DEFAULT 0,
    data_envio_telegram TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 Próximos Passos

1. **Testar o bot** com comandos `/buscar_agora`
2. **Verificar** que anúncios duplicados não são enviados
3. **Monitorar logs** para confirmar marcação de envio
4. **Aguardar scraping** para verificar se novos anúncios são enviados corretamente

---

## ⚠️ Observações Importantes

- ⚡ O sistema marca anúncios como enviados **apenas se o envio for bem-sucedido**
- 🔄 Se houver erro no envio (conexão, Telegram API, etc.), o anúncio **não é marcado**
- 📝 Logs registram todas as operações para auditoria
- 🗑️ Anúncios marcados como enviados **permanecem no banco** (não são deletados)

---

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs em `logs/marketplace_YYYY-MM-DD.log`
2. Execute `test_envio_duplicado.py` para diagnóstico
3. Verifique se há erros de conexão com o banco de dados

---

**✅ Sistema de Deduplicação Ativo!**
