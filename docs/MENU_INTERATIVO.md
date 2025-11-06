# 🎨 Menu Interativo - Bot Telegram

## 📋 Visão Geral

O bot agora possui um sistema de menu interativo com botões, facilitando a navegação e uso das funcionalidades sem precisar digitar comandos.

## 🏠 Menu Principal

Ao digitar `/start` ou `/menu`, você verá 4 botões principais:

```
┌─────────────────────────┐
│  🔑 Credenciais         │
├─────────────────────────┤
│  🔍 Palavras-chave      │
├─────────────────────────┤
│  ⏰ Agendamento         │
├─────────────────────────┤
│  🚀 Buscas e Status     │
└─────────────────────────┘
```

## 🔑 Menu de Credenciais

**Opções disponíveis:**
- ➕ **Cadastrar FB** - Cadastrar login e senha do Facebook
- 👁️ **Ver Credenciais** - Visualizar credenciais cadastradas (mascaradas)
- ◀️ **Voltar** - Retornar ao menu principal

### Fluxo de Cadastro
1. Clique em "Cadastrar FB"
2. Digite seu email ou telefone
3. Digite sua senha
4. Credenciais são salvas com criptografia AES

## 🔍 Menu de Palavras-chave

**Opções disponíveis:**
- ➕ **Adicionar Palavra** - Adicionar nova palavra-chave para monitorar
- 📋 **Listar Palavras** - Ver todas as palavras ativas (organizadas por origem)
- 🗑️ **Remover Palavra** - Selecionar e remover palavra-chave
- ◀️ **Voltar** - Retornar ao menu principal

### Fluxo de Adição
1. Clique em "Adicionar Palavra"
2. Digite a palavra ou frase (ex: "iPhone 13")
3. Escolha a origem: OLX, Facebook ou Ambos
4. Escolha a prioridade: Alta (⭐⭐⭐), Média (⭐⭐) ou Baixa (⭐)

### Fluxo de Remoção
1. Clique em "Remover Palavra"
2. Selecione a palavra desejada da lista
3. Confirmação automática de remoção

## ⏰ Menu de Agendamento

**Opções disponíveis:**
- ⚙️ **Configurar Intervalo** - Escolher intervalo entre execuções (10min, 30min, 1h)
- ▶️ **Iniciar Scheduler** - Ativar execuções automáticas
- ⏸️ **Parar Scheduler** - Desativar execuções automáticas
- ◀️ **Voltar** - Retornar ao menu principal

**Status exibido:**
- 🟢 **Ativo** / 🔴 **Inativo**
- Intervalo configurado
- Próxima execução agendada

### Intervalos Disponíveis
- ⏱️ **10 minutos** - Execuções frequentes
- ⏱️ **30 minutos** - Execuções moderadas
- ⏱️ **1 hora (60 min)** - Execuções espaçadas

## 🚀 Menu de Buscas e Status

**Opções disponíveis:**
- 🔎 **Buscar Agora** - Executar busca manual imediata
- 📊 **Ver Status** - Visualizar status completo do sistema
- ◀️ **Voltar** - Retornar ao menu principal

### Busca Manual
1. Clique em "Buscar Agora"
2. Escolha a origem:
   - 🛒 **Buscar na OLX**
   - 📘 **Buscar no Facebook**
   - 🔍 **Buscar em Ambos**
3. Aguarde processamento (pode levar alguns minutos)
4. Veja resultado com novos anúncios encontrados

### Status do Sistema
Exibe informações detalhadas:

**⏰ Scheduler:**
- Status (Ativo/Inativo)
- Intervalo configurado
- Última execução
- Próxima execução
- Total de execuções
- Total de erros

**🔍 Palavras-Chave Ativas:**
- Quantidade por origem (OLX, Facebook, Ambos)
- Total de palavras

**🔑 Credenciais:**
- Status do Facebook (Configurado/Não configurado)

## 🎯 Navegação

### Navegação Hierárquica
- Todos os submenus possuem botão **◀️ Voltar**
- Retorna sempre ao menu anterior
- Menu principal acessível por `/start` ou `/menu` a qualquer momento

### Compatibilidade com Comandos
Todos os comandos de texto ainda funcionam:
- `/cadastrar_facebook` - Cadastrar credenciais
- `/adicionar_palavra` - Adicionar palavra-chave
- `/configurar_intervalo` - Configurar intervalo
- `/iniciar_scheduler` - Iniciar scheduler
- `/parar_scheduler` - Parar scheduler
- `/buscar_agora` - Busca manual
- `/status` - Ver status
- `/help` - Ver ajuda

## 💡 Vantagens do Menu Interativo

✅ **Visual** - Interface clara com emojis e organização
✅ **Intuitivo** - Não precisa decorar comandos
✅ **Mobile-friendly** - Fácil de usar no celular
✅ **Progressivo** - Vê apenas opções relevantes por vez
✅ **Navegável** - Sempre tem como voltar
✅ **Retrocompatível** - Comandos de texto continuam funcionando

## 🔄 Fluxo Completo de Uso

### Primeira Configuração
1. `/start` → Menu Principal
2. **🔑 Credenciais** → **➕ Cadastrar FB** → Digite email e senha
3. **🔍 Palavras-chave** → **➕ Adicionar Palavra** → Digite palavra → Escolha origem e prioridade
4. **⏰ Agendamento** → **⚙️ Configurar Intervalo** → Escolha 10, 30 ou 60 min
5. **⏰ Agendamento** → **▶️ Iniciar Scheduler** → Sistema ativo!

### Uso Diário
- **📊 Ver Status** - Verificar execuções e palavras ativas
- **🔎 Buscar Agora** - Executar busca manual quando quiser
- **📋 Listar Palavras** - Ver quais palavras estão ativas
- **⏸️ Parar Scheduler** - Desativar temporariamente

## 🛠️ Detalhes Técnicos

### Implementação
- **Framework:** python-telegram-bot v20.0+
- **Componentes:** InlineKeyboardButton, InlineKeyboardMarkup
- **Callbacks:** Padrão `menu_*` para navegação, `action_*` para ações
- **Estados:** ConversationHandler para fluxos com múltiplas etapas
- **Parse Mode:** HTML para formatação rica

### Estrutura de Callbacks
```
menu_credenciais → Abre submenu de credenciais
menu_palavras → Abre submenu de palavras
menu_agendamento → Abre submenu de agendamento
menu_buscas → Abre submenu de buscas
back_main_menu → Volta ao menu principal

action_cadastrar_fb → Inicia cadastro Facebook
action_ver_creds → Mostra credenciais
action_add_palavra → Inicia adição de palavra
action_list_palavras → Lista palavras ativas
action_remove_palavra → Lista palavras para remover
action_config_intervalo → Mostra opções de intervalo
action_start_scheduler → Inicia scheduler
action_stop_scheduler → Para scheduler
action_buscar_agora → Mostra opções de busca
action_ver_status → Mostra status completo

set_interval_{10|30|60} → Define intervalo específico
search_{olx|facebook|ambos} → Executa busca em origem específica
remove_kw_{id} → Remove palavra com ID específico
```

### Handlers Registrados
1. **Comandos básicos:** /start, /menu, /help, /status
2. **Navegação:** CallbackQueryHandler para menu_*
3. **Ações:** CallbackQueryHandler para action_*
4. **ConversationHandlers:** Para fluxos com entrada de texto
5. **Backward compatibility:** Comandos de texto tradicionais

---

**Desenvolvido para facilitar o uso do bot de scraping de anúncios! 🚀**
