# 🤖 Comandos do Bot do Telegram

Guia completo de todos os comandos disponíveis no bot do Scraper de Anúncios.

## 📚 Comandos Básicos

### `/start`
Inicia o bot e mostra mensagem de boas-vindas.

**Exemplo:**
```
/start
```

**Resposta:**
```
👋 Olá João!

Bem-vindo ao Scraper de Anúncios! 🤖

Eu posso ajudá-lo a:
• 🔑 Gerenciar credenciais do Facebook
• 🔍 Adicionar palavras-chave para busca
• ⏰ Configurar intervalo de buscas automáticas
• 📊 Visualizar status e estatísticas
• 🚀 Executar buscas manuais

Use /help para ver todos os comandos disponíveis.
```

### `/help`
Mostra lista completa de comandos disponíveis.

**Exemplo:**
```
/help
```

---

## 🔑 Gerenciamento de Credenciais

### `/cadastrar_facebook`
Cadastra credenciais do Facebook para login automático.

**Fluxo:**
1. Comando: `/cadastrar_facebook`
2. Bot pede o **email**
3. Você envia: `seuemail@gmail.com`
4. Bot pede a **senha**
5. Você envia: `sua_senha` (mensagem é deletada automaticamente)
6. Bot confirma o cadastro

**Segurança:**
- ✅ Senha é criptografada com Fernet (AES 128-bit)
- ✅ Mensagem com senha é deletada automaticamente
- ✅ Apenas o hash criptografado é armazenado

**Exemplo:**
```
Você: /cadastrar_facebook
Bot: Digite o email da sua conta Facebook:

Você: joao@gmail.com
Bot: ✅ Email: joao@gmail.com
     Agora digite a senha:

Você: minha_senha_secreta
Bot: ✅ Credenciais salvas com sucesso!
     🔒 A senha foi criptografada e armazenada de forma segura.
```

### `/ver_credenciais`
Lista credenciais cadastradas (com mascaramento).

**Exemplo:**
```
Você: /ver_credenciais

Bot: 🔑 Credenciais Cadastradas

FACEBOOK:
  • Usuário: joa***@gmail.com
  • Status: ✅ Ativa
```

### `/remover_credenciais`
Remove credenciais cadastradas (em breve).

---

## 🔍 Gerenciamento de Palavras-Chave

### `/adicionar_palavra`
Adiciona uma palavra-chave para busca automática.

**Fluxo:**
1. Comando: `/adicionar_palavra`
2. Bot pede a **palavra**
3. Você envia: `honda civic`
4. Bot mostra menu de **origem** (OLX, Facebook, Ambos)
5. Você escolhe a origem
6. Bot mostra menu de **prioridade** (Baixa, Média, Alta)
7. Você escolhe a prioridade
8. Bot confirma o cadastro

**Exemplo:**
```
Você: /adicionar_palavra
Bot: Digite a palavra ou termo de busca:

Você: honda civic
Bot: ✅ Palavra: honda civic
     Onde deseja buscar?
     [🛒 OLX] [📘 Facebook] [🔍 Ambos]

Você: [clica em "Ambos"]
Bot: ✅ Origem: AMBOS
     Escolha a prioridade:
     [⭐ Baixa] [⭐⭐ Média] [⭐⭐⭐ Alta]

Você: [clica em "Alta"]
Bot: ✅ Palavra-chave adicionada!
     🔍 Palavra: honda civic
     📍 Origem: AMBOS
     ⭐ Prioridade: Alta ⭐⭐⭐
```

### `/listar_palavras`
Lista todas as palavras-chave ativas.

**Exemplo:**
```
Você: /listar_palavras

Bot: 🔍 Palavras-Chave Ativas

🛒 OLX:
  • corolla ⭐⭐
  • ford focus ⭐

📘 Facebook:
  • civic type r ⭐⭐⭐

🔍 Ambos:
  • honda civic ⭐⭐⭐
  • toyota ⭐⭐

Total: 5 palavras
```

### `/remover_palavra <palavra>`
Remove uma palavra-chave específica.

**Exemplo:**
```
Você: /remover_palavra honda civic

Bot: ✅ Palavra honda civic removida!
```

---

## ⏰ Configuração de Agendamento

### `/configurar_intervalo`
Define o intervalo entre buscas automáticas.

**Opções:**
- ⚡ **10 minutos** - Buscas frequentes
- ⏱️ **30 minutos** - Buscas moderadas (padrão)
- ⏰ **1 hora** - Buscas espaçadas

**Exemplo:**
```
Você: /configurar_intervalo

Bot: ⏰ Configurar Intervalo de Buscas
     Escolha o intervalo entre as buscas automáticas:
     [⚡ 10 minutos] [⏱️ 30 minutos] [⏰ 1 hora]

Você: [clica em "30 minutos"]

Bot: ✅ Intervalo configurado!
     ⏰ Intervalo: 30 minutos
     ⚠️ Use /iniciar_scheduler para ativar as buscas automáticas.
```

### `/iniciar_scheduler`
Inicia as buscas automáticas com o intervalo configurado.

**Exemplo:**
```
Você: /iniciar_scheduler

Bot: ✅ Scheduler iniciado!
     ⏰ Intervalo: 30 minutos
     📅 Próxima execução: 27/10/2025 15:30:00
```

### `/parar_scheduler`
Para as buscas automáticas.

**Exemplo:**
```
Você: /parar_scheduler

Bot: ✅ Scheduler parado!
     Use /iniciar_scheduler para reativar.
```

---

## 🚀 Execução de Buscas

### `/buscar_agora`
Executa uma busca manual imediata.

**Fluxo:**
1. Comando: `/buscar_agora`
2. Bot mostra menu: OLX, Facebook, Ambos
3. Você escolhe
4. Bot executa a busca
5. Bot envia resultado

**Exemplo:**
```
Você: /buscar_agora

Bot: 🚀 Busca Manual
     Escolha onde deseja buscar:
     [🛒 OLX] [📘 Facebook] [🔍 Ambos]

Você: [clica em "Ambos"]

Bot: 🔍 Iniciando busca ambos...
     ⏳ Aguarde, isso pode levar alguns minutos.

Bot (após conclusão):
     ✅ Busca ambos concluída!
     Use /status para ver as estatísticas.
```

---

## 📊 Monitoramento e Status

### `/status`
Exibe dashboard com status completo do sistema.

**Exemplo:**
```
Você: /status

Bot: 📊 Status do Sistema

⏰ Scheduler:
• Status: 🟢 Ativo
• Intervalo: 30 minutos
• Última execução: 27/10/2025 15:00:00
• Próxima execução: 27/10/2025 15:30:00
• Total execuções: 42
• Total erros: 2

🔍 Palavras-Chave Ativas:
• OLX: 5
• Facebook: 3
• Ambos: 8
• Total: 16

🔑 Credenciais:
• Facebook: ✅ Configurado

Use /relatorio para ver estatísticas detalhadas.
```

### `/relatorio`
Gera relatório completo com estatísticas detalhadas (em breve).

### `/backup`
Faz backup manual do banco de dados (em breve).

---

## 🛠️ Comandos Auxiliares

### `/cancelar`
Cancela uma operação em andamento (cadastro de credenciais, adicionar palavra, etc).

**Exemplo:**
```
Você: /adicionar_palavra
Bot: Digite a palavra ou termo de busca:

Você: /cancelar
Bot: ❌ Operação cancelada.
```

---

## 📱 Notificações Automáticas

O bot envia notificações automáticas quando:

### ✅ Busca Concluída

```
🛒 Busca OLX Concluída

📊 Estatísticas:
• Palavras buscadas: 5
• Anúncios encontrados: 23
• Novos anúncios: 7
• Duração: 45.3s

⏰ Próxima busca em 30 minutos
```

### ❌ Erro na Busca

```
❌ Erro na Busca Facebook

Erro: Timeout ao carregar página
Palavra: honda civic

Use /status para verificar o sistema.
```

---

## 💡 Dicas de Uso

### ✅ Boas Práticas

1. **Configure credenciais primeiro:**
   ```
   /cadastrar_facebook
   ```

2. **Adicione palavras-chave com prioridades:**
   - Alta (⭐⭐⭐): Termos mais importantes
   - Média (⭐⭐): Termos secundários
   - Baixa (⭐): Termos opcionais

3. **Configure intervalo adequado:**
   - 10 min: Se precisa de atualizações rápidas
   - 30 min: Balanceado (recomendado)
   - 1 hora: Para economizar recursos

4. **Monitore regularmente:**
   ```
   /status
   ```

### ❌ Evite

- ❌ Adicionar palavras muito genéricas
- ❌ Usar intervalos muito curtos (sobrecarga)
- ❌ Remover credenciais enquanto scheduler ativo
- ❌ Executar múltiplas buscas manuais simultâneas

---

## 🔐 Segurança

### Credenciais

- ✅ Senhas criptografadas com Fernet
- ✅ Mensagens com senha deletadas automaticamente
- ✅ Chaves únicas por credencial
- ✅ Visualização mascarada

### Bot

- ✅ Apenas você pode usar o bot
- ✅ Token mantido em segredo
- ✅ Logs não contêm senhas
- ✅ Comunicação criptografada (HTTPS)

---

## ❓ FAQ

**P: Como sei se o scheduler está rodando?**  
R: Use `/status` e verifique se aparece "🟢 Ativo"

**P: Posso ter múltiplas palavras-chave?**  
R: Sim! Adicione quantas quiser com `/adicionar_palavra`

**P: Como mudar a senha do Facebook?**  
R: Use `/cadastrar_facebook` novamente (substitui a anterior)

**P: O bot funciona offline?**  
R: Não, precisa estar conectado à internet

**P: Quantas buscas simultâneas posso fazer?**  
R: Recomendamos 1 por vez para não sobrecarregar

---

**Última atualização:** 27/10/2025  
**Versão do Bot:** 1.0.0
