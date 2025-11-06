"""
Bot do Telegram para gerenciar buscas de anúncios
Comandos interativos para configurar credenciais, palavras-chave e agendamento
"""

import re
import asyncio
from datetime import datetime
from typing import Optional
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from src.core.config import Config
from src.core.utils.logger import logger
from src.managers.credentials_manager import CredentialsManager
from src.managers.keywords_manager import KeywordsManager
from src.managers.scheduler_manager import SchedulerManager


# Estados da conversa para cadastro de credenciais
ASK_EMAIL, ASK_PASSWORD = range(2)

# Estados da conversa para adicionar palavra-chave
ASK_PALAVRA, ASK_ORIGEM, ASK_PRIORIDADE = range(3)

# Estados da conversa para buscar palavra específica
ASK_BUSCA_PALAVRA, ASK_BUSCA_ORIGEM = range(2)


class TelegramBot:
    """Bot do Telegram para gerenciar o scraper"""
    
    def __init__(self):
        self.token = Config.telegram.BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado no .env")
        
        self.credentials_manager = CredentialsManager()
        self.keywords_manager = KeywordsManager()
        self.scheduler_manager = SchedulerManager(on_search_complete=self._on_search_complete)
        
        self.application = None
        self.chat_id = None  # Chat ID do usuário autorizado
    
    def _send_message_sync(self, **kwargs):
        """
        Envia mensagem do Telegram de forma síncrona (útil para threads)
        
        Args:
            **kwargs: Argumentos para send_message (chat_id, text, etc.)
        """
        import nest_asyncio
        nest_asyncio.apply()
        
        # Usar asyncio.run para criar e fechar loop automaticamente
        try:
            # asyncio.run cria um novo loop, executa e fecha de forma segura
            return asyncio.run(
                self.application.bot.send_message(**kwargs)
            )
        except RuntimeError as e:
            # Se der erro de loop fechado, tentar com loop manual
            logger.warning(f"Erro com asyncio.run, tentando com loop manual: {e}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.application.bot.send_message(**kwargs)
                )
                return result
            finally:
                try:
                    loop.close()
                except:
                    pass
    
    def _send_photo_sync(self, **kwargs):
        """
        Envia foto do Telegram de forma síncrona (útil para threads)
        
        Args:
            **kwargs: Argumentos para send_photo (chat_id, photo, caption, etc.)
        """
        import nest_asyncio
        nest_asyncio.apply()
        
        # Usar asyncio.run para criar e fechar loop automaticamente
        try:
            # asyncio.run cria um novo loop, executa e fecha de forma segura
            return asyncio.run(
                self.application.bot.send_photo(**kwargs)
            )
        except RuntimeError as e:
            # Se der erro de loop fechado, tentar com loop manual
            logger.warning(f"Erro com asyncio.run, tentando com loop manual: {e}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.application.bot.send_photo(**kwargs)
                )
                return result
            finally:
                try:
                    loop.close()
                except:
                    pass
    
    def _on_search_complete(self, tipo: str, total_palavras: int, 
                           total_encontrados: int, total_novos: int, duracao: float):
        """
        Callback chamado quando uma busca automática é concluída
        
        Args:
            tipo: Tipo de busca (olx, facebook)
            total_palavras: Total de palavras buscadas
            total_encontrados: Total de anúncios encontrados
            total_novos: Total de anúncios novos
            duracao: Duração em segundos
        """
        if not self.chat_id:
            logger.warning("Chat ID não configurado, notificação não enviada")
            return
        
        if not self.application:
            logger.warning("Application não inicializado, notificação não enviada")
            return
        
        emoji = "🛒" if tipo == "olx" else "📘"
        
        # Calcular duplicados
        total_duplicados = total_encontrados - total_novos
        
        # Mensagem de status
        if total_novos > 0:
            status = f"✨ {total_novos} novos"
        else:
            status = "ℹ️ Nenhum novo"
        
        mensagem = f"""
{emoji} <b>Busca {tipo.upper()} Concluída</b>

📊 <b>Estatísticas:</b>
• Palavras buscadas: {total_palavras}
• Anúncios encontrados: {total_encontrados}
• {status}
• Duplicados: {total_duplicados}
• Duração: {duracao:.1f}s

⏰ Próxima busca em {self.scheduler_manager.get_config()['interval_minutes']} minutos
"""
        
        logger.info(f"Enviando notificação para chat_id: {self.chat_id}")
        
        # Enviar mensagem de forma síncrona (seguro para threads)
        try:
            self._send_message_sync(
                chat_id=self.chat_id,
                text=mensagem,
                parse_mode='HTML'
            )
            logger.success("Notificação enviada com sucesso")
            
            # Enviar automaticamente os anúncios novos (sem menu)
            if total_novos > 0:
                logger.info(f"Enviando {total_novos} anúncios novos automaticamente...")
                self._send_found_ads(tipo, limit=None)  # None = enviar todos os novos
            else:
                logger.warning("Nenhum anúncio novo para enviar")
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")
    
    def _send_ads_menu(self, tipo: str, total: int):
        """Envia menu para escolher quantos anúncios exibir"""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            # Criar botões com opções
            keyboard = []
            
            # Sempre mostrar opção de 5
            keyboard.append([InlineKeyboardButton("📄 Ver 5 anúncios", callback_data=f"show_ads_{tipo}_5")])
            
            # Mostrar opção de 20 se houver pelo menos 20
            if total >= 20:
                keyboard.append([InlineKeyboardButton("📑 Ver 20 anúncios", callback_data=f"show_ads_{tipo}_20")])
            
            # Mostrar opção de 40 se houver pelo menos 40
            if total >= 40:
                keyboard.append([InlineKeyboardButton("📚 Ver 40 anúncios", callback_data=f"show_ads_{tipo}_40")])
            
            # Sempre mostrar opção "Todos"
            keyboard.append([InlineKeyboardButton(f"📦 Ver TODOS ({total} anúncios)", callback_data=f"show_ads_{tipo}_all")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            emoji = "🛒" if tipo == "olx" else "📘"
            mensagem = f"{emoji} <b>Anúncios Disponíveis</b>\n\nQuantos anúncios você deseja visualizar?"
            
            # Enviar de forma síncrona (seguro para threads)
            self._send_message_sync(
                chat_id=self.chat_id,
                text=mensagem,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            logger.success("Menu de anúncios enviado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao enviar menu de anúncios: {e}")
    
    def _send_found_ads(self, tipo: str, limit: int = None):
        """Envia detalhes dos anúncios mais recentes encontrados"""
        try:
            import sqlite3
            from pathlib import Path
            
            logger.info(f"_send_found_ads: Iniciando busca de anúncios (tipo={tipo}, limit={limit})")
            
            db_path = Path(__file__).parent.parent.parent / "data" / "marketplace_anuncios.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Buscar últimos anúncios (ordenados por data de scraping)
            # Filtrar apenas anúncios com preço E localização válidos E que ainda não foram enviados
            if limit is None:
                # Buscar todos
                cursor.execute("""
                    SELECT id, titulo, preco, localizacao, url, data_coleta, imagem_url
                    FROM anuncios
                    WHERE origem = ?
                    AND preco IS NOT NULL 
                    AND preco != '' 
                    AND preco != 'Não informado'
                    AND localizacao IS NOT NULL 
                    AND localizacao != '' 
                    AND localizacao != 'Não informado'
                    AND (enviado_telegram = 0 OR enviado_telegram IS NULL)
                    ORDER BY data_coleta DESC
                """, (tipo,))
            else:
                # Buscar com limite (pegar mais para compensar possíveis filtros)
                cursor.execute("""
                    SELECT id, titulo, preco, localizacao, url, data_coleta, imagem_url
                    FROM anuncios
                    WHERE origem = ?
                    AND preco IS NOT NULL 
                    AND preco != '' 
                    AND preco != 'Não informado'
                    AND localizacao IS NOT NULL 
                    AND localizacao != '' 
                    AND localizacao != 'Não informado'
                    AND (enviado_telegram = 0 OR enviado_telegram IS NULL)
                    ORDER BY data_coleta DESC
                    LIMIT ?
                """, (tipo, limit))
            
            anuncios_raw = cursor.fetchall()
            conn.close()
            
            # Filtrar anúncios válidos (validação adicional em Python)
            anuncios = []
            for ad in anuncios_raw:
                id_anuncio, titulo, preco, localizacao, url, data_coleta, imagem_url = ad
                
                # Validar se preço e localização são válidos
                preco_valido = preco and preco.strip() and preco.lower() not in ['não informado', 'n/a', '-']
                localizacao_valida = localizacao and localizacao.strip() and localizacao.lower() not in ['não informado', 'n/a', '-']
                
                if preco_valido and localizacao_valida:
                    anuncios.append(ad)
            
            logger.info(f"_send_found_ads: Encontrados {len(anuncios)} anúncios válidos no banco (de {len(anuncios_raw)} totais)")
            
            if not anuncios:
                logger.warning("_send_found_ads: Nenhum anúncio válido encontrado no banco de dados")
                # Enviar mensagem informando que não há anúncios válidos
                emoji = "🛒" if tipo == "olx" else "📘"
                self._send_message_sync(
                    chat_id=self.chat_id,
                    text=f"{emoji} <b>Nenhum anúncio completo encontrado</b>\n\n"
                         f"Os anúncios disponíveis não possuem preço ou localização válidos.",
                    parse_mode='HTML'
                )
                return
            
            # Dividir em chunks de 10 anúncios para evitar mensagens muito longas
            chunk_size = 10
            total_chunks = (len(anuncios) + chunk_size - 1) // chunk_size  # Arredondar para cima
            
            emoji = "🛒" if tipo == "olx" else "📘"
            
            # Lista para armazenar IDs dos anúncios enviados com sucesso
            anuncios_enviados_ids = []
            
            for chunk_num in range(total_chunks):
                start_idx = chunk_num * chunk_size
                end_idx = min(start_idx + chunk_size, len(anuncios))
                chunk = anuncios[start_idx:end_idx]
                
                # Enviar cada anúncio individualmente com imagem
                for i, ad in enumerate(chunk, start_idx + 1):
                    id_anuncio, titulo, preco, localizacao, url, data_coleta, imagem_url = ad
                    
                    # Escapar caracteres especiais do HTML no título e localização
                    from html import escape
                    titulo_escaped = escape(titulo)
                    preco_escaped = escape(preco)
                    localizacao_escaped = escape(localizacao)
                    
                    # Definir marcação do marketplace
                    marketplace_badge = "🟣 <b>OLX</b>" if tipo == "olx" else "🔵 <b>FACEBOOK</b>"
                    
                    # Montar mensagem com link clicável (URL não precisa de escape)
                    mensagem = f"{marketplace_badge} | {emoji} <b>{i}. {titulo_escaped}</b>\n\n"
                    mensagem += f"💰 <b>Preço:</b> {preco_escaped}\n"
                    mensagem += f"📍 <b>Local:</b> {localizacao_escaped}\n"
                    mensagem += f"🔗 <a href=\"{url}\">Ver anúncio completo</a>\n"
                    
                    enviado_com_sucesso = False
                    # Se tiver imagem, enviar com foto
                    if imagem_url and imagem_url.strip() and imagem_url.startswith('http'):
                        try:
                            self._send_photo_sync(
                                chat_id=self.chat_id,
                                photo=imagem_url,
                                caption=mensagem,
                                parse_mode='HTML'
                            )
                            enviado_com_sucesso = True
                        except Exception as e:
                            logger.warning(f"Erro ao enviar imagem {imagem_url}: {e}")
                            # Se falhar ao enviar imagem, enviar só texto
                            try:
                                self._send_message_sync(
                                    chat_id=self.chat_id,
                                    text=mensagem,
                                    parse_mode='HTML',
                                    disable_web_page_preview=False
                                )
                                enviado_com_sucesso = True
                            except Exception as e2:
                                logger.error(f"Erro ao enviar texto após falha de imagem: {e2}")
                    else:
                        # Sem imagem, enviar só texto
                        try:
                            self._send_message_sync(
                                chat_id=self.chat_id,
                                text=mensagem,
                                parse_mode='HTML',
                                disable_web_page_preview=False
                            )
                            enviado_com_sucesso = True
                        except Exception as e:
                            logger.error(f"Erro ao enviar mensagem: {e}")
                    
                    # Se enviado com sucesso, adicionar ID à lista
                    if enviado_com_sucesso:
                        anuncios_enviados_ids.append(id_anuncio)
            
            # Marcar anúncios como enviados no banco de dados
            if anuncios_enviados_ids:
                try:
                    db_path = Path(__file__).parent.parent.parent / "data" / "marketplace_anuncios.db"
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    from datetime import datetime
                    data_envio = datetime.now().isoformat()
                    
                    # Atualizar todos os anúncios enviados
                    placeholders = ','.join('?' * len(anuncios_enviados_ids))
                    cursor.execute(f"""
                        UPDATE anuncios 
                        SET enviado_telegram = 1, data_envio_telegram = ?
                        WHERE id IN ({placeholders})
                    """, [data_envio] + anuncios_enviados_ids)
                    
                    conn.commit()
                    conn.close()
                    
                    logger.success(f"Marcados {len(anuncios_enviados_ids)} anúncios como enviados no banco de dados")
                except Exception as e:
                    logger.error(f"Erro ao marcar anúncios como enviados: {e}")
            
            logger.success(f"Enviados {len(anuncios)} anúncios para o Telegram em {total_chunks} mensagem(ns)")
        except Exception as e:
            logger.error(f"Erro ao enviar anúncios: {e}", exc_info=True)
    
    async def _send_found_ads_by_palavra(self, chat_id: int, palavra: str, origem: str, limit: int = 20):
        """Envia anúncios encontrados para uma palavra específica"""
        try:
            import sqlite3
            from pathlib import Path
            
            logger.info(f"_send_found_ads_by_palavra: Buscando anúncios (palavra={palavra}, origem={origem}, limit={limit})")
            
            db_path = Path(__file__).parent.parent.parent / "data" / "marketplace_anuncios.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Montar query baseado na origem
            if origem == 'ambos':
                cursor.execute("""
                    SELECT id, titulo, preco, localizacao, url, data_coleta, imagem_url, origem
                    FROM anuncios
                    WHERE LOWER(palavra_chave) = LOWER(?)
                    AND preco IS NOT NULL 
                    AND preco != '' 
                    AND localizacao IS NOT NULL 
                    AND localizacao != ''
                    AND (enviado_telegram = 0 OR enviado_telegram IS NULL)
                    ORDER BY data_coleta DESC
                    LIMIT ?
                """, (palavra, limit))
            else:
                cursor.execute("""
                    SELECT id, titulo, preco, localizacao, url, data_coleta, imagem_url, origem
                    FROM anuncios
                    WHERE LOWER(palavra_chave) = LOWER(?)
                    AND origem = ?
                    AND preco IS NOT NULL 
                    AND preco != '' 
                    AND localizacao IS NOT NULL 
                    AND localizacao != ''
                    AND (enviado_telegram = 0 OR enviado_telegram IS NULL)
                    ORDER BY data_coleta DESC
                    LIMIT ?
                """, (palavra, origem, limit))
            
            anuncios = cursor.fetchall()
            conn.close()
            
            logger.info(f"_send_found_ads_by_palavra: Encontrados {len(anuncios)} anúncios para '{palavra}'")
            
            if not anuncios:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"📭 <b>Nenhum anúncio novo encontrado</b>\n\n"
                         f"A busca por '<code>{palavra}</code>' não retornou novos anúncios.\n"
                         f"Todos os anúncios disponíveis já foram enviados anteriormente.",
                    parse_mode='HTML'
                )
                return
            
            # Lista para armazenar IDs dos anúncios enviados com sucesso
            anuncios_enviados_ids = []
            
            # Enviar cada anúncio individualmente com imagem
            for i, ad in enumerate(anuncios, 1):
                id_anuncio, titulo, preco, localizacao, url, data_coleta, imagem_url, ad_origem = ad
                
                emoji = "🛒" if ad_origem == "olx" else "📘"
                
                # Montar mensagem com link clicável
                mensagem = f"{emoji} <b>{i}. {titulo}</b>\n\n"
                mensagem += f"💰 <b>Preço:</b> {preco}\n"
                mensagem += f"📍 <b>Local:</b> {localizacao}\n"
                mensagem += f"🔗 <a href='{url}'>Ver anúncio completo</a>\n"
                
                enviado_com_sucesso = False
                # Se tiver imagem, enviar com foto
                if imagem_url and imagem_url.strip() and imagem_url.startswith('http'):
                    try:
                        await self.application.bot.send_photo(
                            chat_id=chat_id,
                            photo=imagem_url,
                            caption=mensagem,
                            parse_mode='HTML'
                        )
                        enviado_com_sucesso = True
                    except Exception as e:
                        logger.warning(f"Erro ao enviar imagem {imagem_url}: {e}")
                        # Se falhar ao enviar imagem, enviar só texto com link clicável
                        try:
                            await self.application.bot.send_message(
                                chat_id=chat_id,
                                text=mensagem,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            )
                            enviado_com_sucesso = True
                        except Exception as e2:
                            logger.error(f"Erro ao enviar texto após falha de imagem: {e2}")
                else:
                    # Sem imagem, enviar só texto com link clicável
                    try:
                        await self.application.bot.send_message(
                            chat_id=chat_id,
                            text=mensagem,
                            parse_mode='HTML',
                            disable_web_page_preview=True
                        )
                        enviado_com_sucesso = True
                    except Exception as e:
                        logger.error(f"Erro ao enviar mensagem: {e}")
                
                # Se enviado com sucesso, adicionar ID à lista
                if enviado_com_sucesso:
                    anuncios_enviados_ids.append(id_anuncio)
                
                # Pequeno delay para não sobrecarregar
                await asyncio.sleep(0.5)
            
            # Marcar anúncios como enviados no banco de dados
            if anuncios_enviados_ids:
                try:
                    db_path = Path(__file__).parent.parent.parent / "data" / "marketplace_anuncios.db"
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    from datetime import datetime
                    data_envio = datetime.now().isoformat()
                    
                    # Atualizar todos os anúncios enviados
                    placeholders = ','.join('?' * len(anuncios_enviados_ids))
                    cursor.execute(f"""
                        UPDATE anuncios 
                        SET enviado_telegram = 1, data_envio_telegram = ?
                        WHERE id IN ({placeholders})
                    """, [data_envio] + anuncios_enviados_ids)
                    
                    conn.commit()
                    conn.close()
                    
                    logger.success(f"Marcados {len(anuncios_enviados_ids)} anúncios como enviados no banco de dados")
                except Exception as e:
                    logger.error(f"Erro ao marcar anúncios como enviados: {e}")
            
            logger.success(f"Enviados {len(anuncios)} anúncios de '{palavra}' para o Telegram")
        except Exception as e:
            logger.error(f"Erro ao enviar anúncios por palavra: {e}", exc_info=True)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler do comando /start - mostra menu principal"""
        user = update.effective_user
        self.chat_id = update.effective_chat.id
        
        welcome_message = f"""
👋 Olá <b>{user.first_name}</b>!

Bem-vindo ao <b>Scraper de Anúncios</b>! 🤖

Escolha uma opção abaixo para começar:
"""
        
        # Menu principal com botões
        keyboard = [
            [InlineKeyboardButton("🔑 Credenciais", callback_data='menu_credenciais')],
            [InlineKeyboardButton("🔍 Palavras-chave", callback_data='menu_palavras')],
            [InlineKeyboardButton("⏰ Agendamento", callback_data='menu_agendamento')],
            [InlineKeyboardButton("🚀 Buscas e Status", callback_data='menu_buscas')],
            [InlineKeyboardButton("🗑️ Limpeza", callback_data='menu_limpeza')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        logger.info(f"Usuário {user.first_name} iniciou o bot (Chat ID: {self.chat_id})")
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler do comando /menu - reabre menu principal"""
        keyboard = [
            [InlineKeyboardButton("🔑 Credenciais", callback_data='menu_credenciais')],
            [InlineKeyboardButton("🔍 Palavras-chave", callback_data='menu_palavras')],
            [InlineKeyboardButton("⏰ Agendamento", callback_data='menu_agendamento')],
            [InlineKeyboardButton("🚀 Buscas e Status", callback_data='menu_buscas')],
            [InlineKeyboardButton("🗑️ Limpeza", callback_data='menu_limpeza')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏠 <b>Menu Principal</b>\n\nEscolha uma opção:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def menu_credenciais_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra submenu de credenciais"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("➕ Cadastrar Facebook", callback_data='action_cadastrar_fb')],
            [InlineKeyboardButton("�️ Ver Credenciais", callback_data='action_ver_creds')],
            [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔑 <b>Gerenciar Credenciais</b>\n\nEscolha uma ação:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def menu_palavras_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra submenu de palavras-chave"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("➕ Adicionar Palavra", callback_data='action_add_palavra')],
            [InlineKeyboardButton("📋 Listar Palavras", callback_data='action_list_palavras')],
            [InlineKeyboardButton("🗑️ Remover Palavra", callback_data='action_remove_palavra')],
            [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔍 <b>Gerenciar Palavras-chave</b>\n\nEscolha uma ação:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def menu_agendamento_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra submenu de agendamento"""
        query = update.callback_query
        await query.answer()
        
        # Verificar status do scheduler
        is_running = self.scheduler_manager.is_running()
        status_emoji = "🟢" if is_running else "🔴"
        status_text = "Ativo" if is_running else "Inativo"
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Configurar Intervalo", callback_data='action_config_intervalo')],
            [InlineKeyboardButton(f"▶️ Iniciar Scheduler", callback_data='action_start_scheduler')],
            [InlineKeyboardButton(f"⏸️ Parar Scheduler", callback_data='action_stop_scheduler')],
            [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⏰ <b>Agendamento de Buscas</b>\n\n"
            f"Status: {status_emoji} <b>{status_text}</b>\n\n"
            f"Escolha uma ação:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def menu_buscas_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra submenu de buscas"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔎 Buscar Agora (Todas)", callback_data='action_buscar_agora')],
            [InlineKeyboardButton("🔍 Buscar Palavra Específica", callback_data='action_buscar_palavra')],
            [InlineKeyboardButton("📊 Ver Status", callback_data='action_ver_status')],
            [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🚀 <b>Buscas e Informações</b>\n\nEscolha uma ação:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def menu_limpeza_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra submenu de limpeza de anúncios"""
        query = update.callback_query
        await query.answer()
        
        from src.managers.cleanup_manager import CleanupManager
        cleanup_manager = CleanupManager()
        
        # Adicionar coluna se não existir
        cleanup_manager.add_last_seen_column()
        
        # Obter estatísticas
        stats = cleanup_manager.get_cleanup_stats()
        
        stats_message = f"""
🗑️ <b>Limpeza de Anúncios</b>

📊 <b>Estatísticas:</b>
• Total de anúncios: {stats.get('total_ads', 0)}
• Nunca vistos: {stats.get('never_seen', 0)}
• Não vistos há 7 dias: {stats.get('not_seen_7_days', 0)}
• Não vistos há 30 dias: {stats.get('not_seen_30_days', 0)}

<b>Por origem:</b>
"""
        
        for origem, count in stats.get('by_origin', {}).items():
            stats_message += f"• {origem.upper()}: {count}\n"
        
        stats_message += "\n<i>Escolha uma ação abaixo:</i>"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ Remover não vistos (7 dias)", callback_data='action_cleanup_7d')],
            [InlineKeyboardButton("🗑️ Remover não vistos (30 dias)", callback_data='action_cleanup_30d')],
            [InlineKeyboardButton("🧹 Remover anúncios antigos (30+ dias)", callback_data='action_cleanup_old')],
            [InlineKeyboardButton("📊 Ver Estatísticas", callback_data='action_cleanup_stats')],
            [InlineKeyboardButton("◀️ Voltar ao Menu", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def action_cleanup_7d_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove anúncios não vistos há 7 dias"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("🗑️ <b>Removendo anúncios expirados...</b>", parse_mode='HTML')
        
        from src.managers.cleanup_manager import CleanupManager
        cleanup_manager = CleanupManager()
        
        result = cleanup_manager.remove_expired_ads(days_threshold=7)
        
        message = f"""
✅ <b>Limpeza Concluída!</b>

🗑️ Anúncios removidos: {result['total_removed']}
⏱️ Critério: Não vistos há {result['days_threshold']} dias

<b>Por origem:</b>
"""
        
        for origem, count in result.get('by_origin', {}).items():
            message += f"• {origem.upper()}: {count}\n"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Voltar à Limpeza", callback_data='menu_limpeza')],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def action_cleanup_30d_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove anúncios não vistos há 30 dias"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("🗑️ <b>Removendo anúncios expirados...</b>", parse_mode='HTML')
        
        from src.managers.cleanup_manager import CleanupManager
        cleanup_manager = CleanupManager()
        
        result = cleanup_manager.remove_expired_ads(days_threshold=30)
        
        message = f"""
✅ <b>Limpeza Concluída!</b>

🗑️ Anúncios removidos: {result['total_removed']}
⏱️ Critério: Não vistos há {result['days_threshold']} dias

<b>Por origem:</b>
"""
        
        for origem, count in result.get('by_origin', {}).items():
            message += f"• {origem.upper()}: {count}\n"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Voltar à Limpeza", callback_data='menu_limpeza')],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def action_cleanup_old_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove anúncios com mais de 30 dias"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("🧹 <b>Removendo anúncios antigos...</b>", parse_mode='HTML')
        
        from src.managers.cleanup_manager import CleanupManager
        cleanup_manager = CleanupManager()
        
        result = cleanup_manager.cleanup_old_ads(keep_days=30)
        
        message = f"""
✅ <b>Limpeza Concluída!</b>

🗑️ Anúncios removidos: {result['total_removed']}
📅 Critério: Coletados há mais de {result['keep_days']} dias

<b>Por origem:</b>
"""
        
        for origem, count in result.get('by_origin', {}).items():
            message += f"• {origem.upper()}: {count}\n"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Voltar à Limpeza", callback_data='menu_limpeza')],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def action_cleanup_stats_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra estatísticas detalhadas de limpeza"""
        query = update.callback_query
        await query.answer()
        
        from src.managers.cleanup_manager import CleanupManager
        cleanup_manager = CleanupManager()
        
        stats = cleanup_manager.get_cleanup_stats()
        
        message = f"""
📊 <b>Estatísticas Detalhadas</b>

<b>Total de anúncios:</b> {stats.get('total_ads', 0)}

<b>Anúncios por status:</b>
• Nunca vistos: {stats.get('never_seen', 0)}
• Não vistos há 7 dias: {stats.get('not_seen_7_days', 0)}
• Não vistos há 30 dias: {stats.get('not_seen_30_days', 0)}

<b>Anúncios por origem:</b>
"""
        
        for origem, count in stats.get('by_origin', {}).items():
            message += f"• {origem.upper()}: {count}\n"
        
        keyboard = [
            [InlineKeyboardButton("◀️ Voltar à Limpeza", callback_data='menu_limpeza')],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data='back_main_menu')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    
    async def back_main_menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Volta ao menu principal"""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("🔑 Credenciais", callback_data='menu_credenciais')],
            [InlineKeyboardButton("🔍 Palavras-chave", callback_data='menu_palavras')],
            [InlineKeyboardButton("⏰ Agendamento", callback_data='menu_agendamento')],
            [InlineKeyboardButton("🚀 Buscas e Status", callback_data='menu_buscas')],
            [InlineKeyboardButton("🗑️ Limpeza", callback_data='menu_limpeza')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🏠 <b>Menu Principal</b>\n\nEscolha uma opção:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler do comando /help"""
        help_message = """
📚 <b>Comandos Disponíveis</b>

<b>🔑 Credenciais:</b>
/cadastrar_facebook - Cadastrar login do Facebook
/ver_credenciais - Ver credenciais cadastradas
/remover_credenciais - Remover credenciais

<b>🔍 Palavras-Chave:</b>
/adicionar_palavra - Adicionar palavra de busca
/listar_palavras - Ver palavras cadastradas
/remover_palavra - Remover palavra de busca

<b>⏰ Agendamento:</b>
/configurar_intervalo - Definir intervalo (10min/30min/1h)
/iniciar_scheduler - Iniciar buscas automáticas
/parar_scheduler - Parar buscas automáticas

<b>🚀 Buscas:</b>
/buscar_agora - Executar busca manual (todas)
/status - Ver status e estatísticas

<b>🛠️ Outros:</b>
/logs - Ver informações dos logs
/backup - Fazer backup do banco de dados
/relatorio - Gerar relatório completo
/help - Mostrar esta mensagem

<i>💡 Use /menu ou /start para acessar o menu interativo!</i>
"""
        
        await update.message.reply_text(help_message, parse_mode='HTML')
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler do comando /logs - mostra informações dos logs"""
        try:
            from src.core.utils.log_manager import LogManager
            
            manager = LogManager()
            info = manager.get_log_info()
            
            logs_message = f"""
📁 <b>Informações dos Logs</b>

<b>📂 Diretório:</b> <code>{info['log_dir']}</code>

<b>📊 Estatísticas:</b>
• Total de arquivos: {info['total_files']}
• Tamanho total: {info['total_size_mb']} MB
• Não comprimidos: {info['uncompressed']}
• Comprimidos: {info['compressed']}

<b>📅 Histórico:</b>
• Mais antigo: <code>{info['oldest_file'] or 'N/A'}</code>
• Mais recente: <code>{info['newest_file'] or 'N/A'}</code>

<b>⚙️ Configuração:</b>
• Retenção: {info['retention_days']} dias
• Rotação: Meia-noite (00:00)
• Compressão: ZIP

<i>💡 Logs são limpos automaticamente após {info['retention_days']} dias</i>
"""
            
            await update.message.reply_text(logs_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao obter informações de logs: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao obter informações de logs.",
                parse_mode='HTML'
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler do comando /status - mostra dashboard"""
        try:
            # Obter configuração do scheduler
            scheduler_config = self.scheduler_manager.get_config()
            
            # Obter palavras-chave
            keywords_olx = self.keywords_manager.list_keywords('olx', only_active=True)
            keywords_facebook = self.keywords_manager.list_keywords('facebook', only_active=True)
            keywords_ambos = self.keywords_manager.list_keywords('ambos', only_active=True)
            
            # Obter credenciais
            creds = self.credentials_manager.list_credentials()
            creds_facebook = [c for c in creds if c['service'] == 'facebook' and c['is_active']]
            
            # Status do scheduler
            scheduler_status = "🟢 Ativo" if scheduler_config['enabled'] else "🔴 Inativo"
            
            # Formatar última execução
            if scheduler_config['last_run']:
                last_run = datetime.fromisoformat(scheduler_config['last_run']).strftime('%d/%m/%Y %H:%M:%S')
            else:
                last_run = "Nunca executado"
            
            # Formatar próxima execução
            if scheduler_config['next_run']:
                next_run = datetime.fromisoformat(scheduler_config['next_run']).strftime('%d/%m/%Y %H:%M:%S')
            else:
                next_run = "Não agendado"
            
            status_message = f"""
📊 <b>Status do Sistema</b>

<b>⏰ Scheduler:</b>
• Status: {scheduler_status}
• Intervalo: {scheduler_config['interval_minutes']} minutos
• Última execução: {last_run}
• Próxima execução: {next_run}
• Total execuções: {scheduler_config['total_runs']}
• Total erros: {scheduler_config['total_errors']}

<b>🔍 Palavras-Chave Ativas:</b>
• OLX: {len(keywords_olx)}
• Facebook: {len(keywords_facebook)}
• Ambos: {len(keywords_ambos)}
• <b>Total: {len(keywords_olx) + len(keywords_facebook) + len(keywords_ambos)}</b>

<b>🔑 Credenciais:</b>
• Facebook: {'✅ Configurado' if creds_facebook else '❌ Não configurado'}

Use /relatorio para ver estatísticas detalhadas.
"""
            
            await update.message.reply_text(status_message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao gerar status: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao gerar status. Verifique os logs.",
                parse_mode='HTML'
            )
    
    async def cadastrar_facebook_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia conversa para cadastrar credenciais do Facebook"""
        await update.message.reply_text(
            "🔑 <b>Cadastrar Credenciais do Facebook</b>\n\n"
            "Digite o <b>email</b> da sua conta Facebook:\n\n"
            "Use /cancelar para cancelar.",
            parse_mode='HTML'
        )
        return ASK_EMAIL
    
    async def cadastrar_facebook_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe o email e pede a senha"""
        email = update.message.text.strip()
        
        # Validar formato de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            await update.message.reply_text(
                "❌ Email inválido. Digite um email válido:",
                parse_mode='HTML'
            )
            return ASK_EMAIL
        
        context.user_data['email'] = email
        
        await update.message.reply_text(
            f"✅ Email: <code>{email}</code>\n\n"
            "Agora digite a <b>senha</b>:\n\n"
            "⚠️ A senha será criptografada antes de ser salva.",
            parse_mode='HTML'
        )
        return ASK_PASSWORD
    
    async def cadastrar_facebook_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe a senha e salva as credenciais"""
        password = update.message.text.strip()
        email = context.user_data.get('email')
        
        # Deletar mensagem com a senha por segurança
        await update.message.delete()
        
        if not password:
            await update.message.reply_text(
                "❌ Senha vazia. Digite uma senha válida:",
                parse_mode='HTML'
            )
            return ASK_PASSWORD
        
        # Salvar credenciais
        success = self.credentials_manager.save_credentials('facebook', email, password)
        
        if success:
            await update.message.reply_text(
                "✅ <b>Credenciais salvas com sucesso!</b>\n\n"
                "🔒 A senha foi criptografada e armazenada de forma segura.",
                parse_mode='HTML'
            )
            logger.success(f"Credenciais Facebook cadastradas para {email}")
        else:
            await update.message.reply_text(
                "❌ Erro ao salvar credenciais. Tente novamente.",
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
    
    async def cancelar_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancela conversação em andamento"""
        await update.message.reply_text(
            "❌ Operação cancelada.",
            parse_mode='HTML'
        )
        return ConversationHandler.END
    
    async def configurar_intervalo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra opções de intervalo"""
        keyboard = [
            [InlineKeyboardButton("⚡ 10 minutos", callback_data='interval_10')],
            [InlineKeyboardButton("⏱️ 30 minutos", callback_data='interval_30')],
            [InlineKeyboardButton("⏰ 1 hora", callback_data='interval_60')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⏰ <b>Configurar Intervalo de Buscas</b>\n\n"
            "Escolha o intervalo entre as buscas automáticas:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def configurar_intervalo_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa escolha do intervalo"""
        query = update.callback_query
        await query.answer()
        
        interval_map = {
            'interval_10': 10,
            'interval_30': 30,
            'interval_60': 60
        }
        
        interval_minutes = interval_map.get(query.data)
        
        if not interval_minutes:
            await query.edit_message_text("❌ Opção inválida.")
            return
        
        success = self.scheduler_manager.set_interval(interval_minutes)
        
        if success:
            interval_text = f"{interval_minutes} minutos" if interval_minutes < 60 else "1 hora"
            await query.edit_message_text(
                f"✅ <b>Intervalo configurado!</b>\n\n"
                f"⏰ Intervalo: <b>{interval_text}</b>\n\n"
                f"{'🟢 O scheduler será reiniciado com o novo intervalo.' if self.scheduler_manager.is_running() else '⚠️ Use /iniciar_scheduler para ativar as buscas automáticas.'}",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao configurar intervalo. Tente novamente.",
                parse_mode='HTML'
            )
    
    async def iniciar_scheduler_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia o scheduler"""
        if self.scheduler_manager.is_running():
            await update.message.reply_text(
                "⚠️ O scheduler já está em execução!",
                parse_mode='HTML'
            )
            return
        
        success = self.scheduler_manager.start()
        
        if success:
            config = self.scheduler_manager.get_config()
            await update.message.reply_text(
                f"✅ <b>Scheduler iniciado!</b>\n\n"
                f"⏰ Intervalo: {config['interval_minutes']} minutos\n"
                f"📅 Próxima execução: {datetime.fromisoformat(config['next_run']).strftime('%d/%m/%Y %H:%M:%S')}",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao iniciar scheduler. Verifique as configurações.",
                parse_mode='HTML'
            )
    
    async def parar_scheduler_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Para o scheduler"""
        if not self.scheduler_manager.is_running():
            await update.message.reply_text(
                "⚠️ O scheduler já está parado!",
                parse_mode='HTML'
            )
            return
        
        success = self.scheduler_manager.stop()
        
        if success:
            await update.message.reply_text(
                "✅ <b>Scheduler parado!</b>\n\n"
                "Use /iniciar_scheduler para reativar.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                "❌ Erro ao parar scheduler.",
                parse_mode='HTML'
            )
    
    async def buscar_agora_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra opções para busca manual"""
        keyboard = [
            [InlineKeyboardButton("🛒 OLX", callback_data='search_olx')],
            [InlineKeyboardButton("📘 Facebook", callback_data='search_facebook')],
            [InlineKeyboardButton("🔍 Ambos", callback_data='search_ambos')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚀 <b>Busca Manual</b>\n\n"
            "Escolha onde deseja buscar:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def buscar_agora_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa busca manual"""
        query = update.callback_query
        await query.answer()
        
        tipo_map = {
            'search_olx': 'olx',
            'search_facebook': 'facebook',
            'search_ambos': 'ambos'
        }
        
        tipo = tipo_map.get(query.data)
        
        if not tipo:
            await query.edit_message_text("❌ Opção inválida.")
            return
        
        emoji = {"olx": "🛒", "facebook": "📘", "ambos": "🔍"}[tipo]
        
        await query.edit_message_text(
            f"{emoji} <b>Iniciando busca {tipo}...</b>\n\n"
            "⏳ Aguarde, isso pode levar alguns minutos.",
            parse_mode='HTML'
        )
        
        # Executar busca em background
        success = self.scheduler_manager.run_manual_search(tipo)
        
        if success:
            await query.edit_message_text(
                f"✅ <b>Busca {tipo} concluída!</b>\n\n"
                "Use /status para ver as estatísticas.",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "❌ Erro ao executar busca. Verifique os logs.",
                parse_mode='HTML'
            )
    
    async def adicionar_palavra_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia conversa para adicionar palavra-chave"""
        # Verificar limite
        limit_status = self.keywords_manager.get_keywords_limit_status()
        
        if limit_status['no_limite']:
            await update.message.reply_text(
                f"❌ <b>Limite de palavras-chave atingido!</b>\n\n"
                f"📊 Você já tem {limit_status['total_ativas']}/{limit_status['limite']} palavras ativas.\n\n"
                f"💡 <b>Soluções:</b>\n"
                f"• Remova palavras inativas com /remover_palavra\n"
                f"• Aumente SCHEDULER_MAX_WORKERS no arquivo .env\n\n"
                f"Use /listar_palavras para ver as palavras ativas.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            f"🔍 <b>Adicionar Palavra-Chave</b>\n\n"
            f"📊 Limite: {limit_status['total_ativas']}/{limit_status['limite']} palavras\n"
            f"💡 Você pode adicionar mais {limit_status['disponivel']} palavra(s)\n\n"
            f"Digite a palavra ou termo de busca:\n\n"
            f"Exemplo: honda civic\n\n"
            f"Use /cancelar para cancelar.",
            parse_mode='HTML'
        )
        return ASK_PALAVRA
    
    async def adicionar_palavra_texto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe a palavra e pede a origem"""
        palavra = update.message.text.strip()
        
        if not palavra:
            await update.message.reply_text(
                "❌ Palavra vazia. Digite uma palavra válida:",
                parse_mode='HTML'
            )
            return ASK_PALAVRA
        
        context.user_data['palavra'] = palavra
        
        keyboard = [
            [InlineKeyboardButton("🛒 OLX", callback_data='origem_olx')],
            [InlineKeyboardButton("📘 Facebook", callback_data='origem_facebook')],
            [InlineKeyboardButton("🔍 Ambos", callback_data='origem_ambos')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Palavra: <code>{palavra}</code>\n\n"
            "Onde deseja buscar?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ASK_ORIGEM
    
    async def adicionar_palavra_origem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe a origem e pede a prioridade"""
        query = update.callback_query
        await query.answer()
        
        origem_map = {
            'origem_olx': 'olx',
            'origem_facebook': 'facebook',
            'origem_ambos': 'ambos'
        }
        
        origem = origem_map.get(query.data)
        
        if not origem:
            await query.edit_message_text("❌ Opção inválida.")
            return ConversationHandler.END
        
        context.user_data['origem'] = origem
        
        keyboard = [
            [InlineKeyboardButton("⭐ Baixa", callback_data='prioridade_1')],
            [InlineKeyboardButton("⭐⭐ Média", callback_data='prioridade_2')],
            [InlineKeyboardButton("⭐⭐⭐ Alta", callback_data='prioridade_3')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Origem: <b>{origem.upper()}</b>\n\n"
            "Escolha a prioridade:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ASK_PRIORIDADE
    
    async def adicionar_palavra_prioridade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe a prioridade e salva a palavra-chave"""
        query = update.callback_query
        await query.answer()
        
        prioridade_map = {
            'prioridade_1': 1,
            'prioridade_2': 2,
            'prioridade_3': 3
        }
        
        prioridade = prioridade_map.get(query.data)
        
        if prioridade is None:
            await query.edit_message_text("❌ Opção inválida.")
            return ConversationHandler.END
        
        palavra = context.user_data.get('palavra')
        origem = context.user_data.get('origem')
        
        # Verificar limite antes de adicionar
        limit_status = self.keywords_manager.get_keywords_limit_status()
        
        # Adicionar palavra-chave
        success = self.keywords_manager.add_keyword(palavra, origem, prioridade)
        
        if success:
            prioridade_text = {1: "Baixa ⭐", 2: "Média ⭐⭐", 3: "Alta ⭐⭐⭐"}[prioridade]
            # Atualizar status após adicionar
            new_status = self.keywords_manager.get_keywords_limit_status()
            await query.edit_message_text(
                f"✅ <b>Palavra-chave adicionada!</b>\n\n"
                f"🔍 Palavra: <code>{palavra}</code>\n"
                f"📍 Origem: <b>{origem.upper()}</b>\n"
                f"⭐ Prioridade: {prioridade_text}\n\n"
                f"📊 Limite: {new_status['total_ativas']}/{new_status['limite']} palavras",
                parse_mode='HTML'
            )
        else:
            # Verificar se falhou por limite ou palavra duplicada
            if limit_status['no_limite']:
                await query.edit_message_text(
                    f"❌ <b>Limite de palavras-chave atingido!</b>\n\n"
                    f"📊 Limite atual: {limit_status['total_ativas']}/{limit_status['limite']} palavras\n\n"
                    f"💡 <b>Soluções:</b>\n"
                    f"• Remova palavras inativas com /remover_palavra\n"
                    f"• Aumente SCHEDULER_MAX_WORKERS no arquivo .env\n\n"
                    f"Configuração atual: MAX_WORKERS = {limit_status['limite']}",
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    f"❌ <b>Erro ao adicionar palavra-chave.</b>\n\n"
                    f"A palavra <code>{palavra}</code> pode já estar cadastrada.\n\n"
                    f"Use /listar_palavras para ver as palavras ativas.",
                    parse_mode='HTML'
                )
        
        return ConversationHandler.END
    
    async def listar_palavras_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lista todas as palavras-chave ativas"""
        try:
            keywords = self.keywords_manager.list_keywords(only_active=True)
            
            # Obter status do limite
            limit_status = self.keywords_manager.get_keywords_limit_status()
            
            if not keywords:
                await update.message.reply_text(
                    f"📭 <b>Nenhuma palavra-chave cadastrada</b>\n\n"
                    f"💡 Você pode adicionar até <b>{limit_status['limite']}</b> palavras-chave.\n"
                    f"Use /adicionar_palavra para adicionar.",
                    parse_mode='HTML'
                )
                return
            
            # Agrupar por origem
            olx_kw = [k for k in keywords if k['origem'] == 'olx']
            facebook_kw = [k for k in keywords if k['origem'] == 'facebook']
            ambos_kw = [k for k in keywords if k['origem'] == 'ambos']
            
            message = "🔍 <b>Palavras-Chave Ativas</b>\n\n"
            
            if olx_kw:
                message += "🛒 <b>OLX:</b>\n"
                for kw in olx_kw:
                    stars = "⭐" * kw['prioridade']
                    message += f"  • {kw['palavra']} {stars}\n"
                message += "\n"
            
            if facebook_kw:
                message += "📘 <b>Facebook:</b>\n"
                for kw in facebook_kw:
                    stars = "⭐" * kw['prioridade']
                    message += f"  • {kw['palavra']} {stars}\n"
                message += "\n"
            
            if ambos_kw:
                message += "🔍 <b>Ambos:</b>\n"
                for kw in ambos_kw:
                    stars = "⭐" * kw['prioridade']
                    message += f"  • {kw['palavra']} {stars}\n"
            
            # Adicionar informação de limite
            message += f"\n📊 <b>Limite:</b> {limit_status['total_ativas']}/{limit_status['limite']} palavras"
            
            if limit_status['disponivel'] > 0:
                message += f"\n💡 Você pode adicionar mais {limit_status['disponivel']} palavra(s)"
            else:
                message += f"\n⚠️ Limite atingido! Aumente SCHEDULER_MAX_WORKERS no .env"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao listar palavras: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao listar palavras-chave.",
                parse_mode='HTML'
            )
    
    async def remover_palavra_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove uma palavra-chave"""
        # Verificar se foi passada a palavra como argumento
        if context.args:
            palavra = ' '.join(context.args)
            success = self.keywords_manager.remove_keyword(palavra)
            
            if success:
                await update.message.reply_text(
                    f"✅ Palavra <code>{palavra}</code> removida!",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    f"❌ Palavra <code>{palavra}</code> não encontrada.",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                "❌ <b>Uso:</b> /remover_palavra honda civic\n\n"
                "Ou use /listar_palavras para ver as palavras cadastradas.",
                parse_mode='HTML'
            )
    
    async def action_buscar_palavra_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Iniciar busca de palavra específica via botão do menu"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🔎 <b>Buscar Palavra Específica</b>\n\n"
            "Digite a palavra ou termo que deseja buscar:\n\n"
            "Exemplo: honda civic 2020\n\n"
            "Use /cancelar para cancelar.",
            parse_mode='HTML'
        )
        return ASK_BUSCA_PALAVRA
    
    async def buscar_palavra_texto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recebe a palavra e pede a origem da busca"""
        palavra = update.message.text.strip()
        
        if not palavra:
            await update.message.reply_text(
                "❌ Palavra vazia. Digite uma palavra válida:",
                parse_mode='HTML'
            )
            return ASK_BUSCA_PALAVRA
        
        context.user_data['busca_palavra'] = palavra
        
        keyboard = [
            [InlineKeyboardButton("🛒 OLX", callback_data='busca_olx')],
            [InlineKeyboardButton("📘 Facebook", callback_data='busca_facebook')],
            [InlineKeyboardButton("🔍 Ambos", callback_data='busca_ambos')],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Palavra: <code>{palavra}</code>\n\n"
            "Onde deseja buscar?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ASK_BUSCA_ORIGEM
    
    async def buscar_palavra_executar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executa a busca da palavra específica"""
        query = update.callback_query
        await query.answer()
        
        origem_map = {
            'busca_olx': 'olx',
            'busca_facebook': 'facebook',
            'busca_ambos': 'ambos'
        }
        
        origem = origem_map.get(query.data)
        
        if origem is None:
            await query.edit_message_text("❌ Opção inválida.")
            return ConversationHandler.END
        
        palavra = context.user_data.get('busca_palavra')
        
        # Mostrar mensagem de processamento
        await query.edit_message_text(
            f"🔍 <b>Iniciando busca...</b>\n\n"
            f"📝 Palavra: <code>{palavra}</code>\n"
            f"📍 Origem: <b>{origem.upper()}</b>\n\n"
            f"⏳ Aguarde, isso pode levar alguns segundos...",
            parse_mode='HTML'
        )
        
        try:
            total_encontrados = 0
            total_salvos = 0
            mensagens = []
            
            # Executar busca no OLX
            if origem in ['olx', 'ambos']:
                mensagens.append("🛒 Buscando no OLX...")
                await query.edit_message_text(
                    f"🔍 <b>Buscando...</b>\n\n"
                    f"📝 Palavra: <code>{palavra}</code>\n\n"
                    + "\n".join(mensagens),
                    parse_mode='HTML'
                )
                
                resultado_olx = self.scheduler_manager._execute_olx_scraper(palavra)
                if resultado_olx['status'] == 'success':
                    total_encontrados += resultado_olx['encontrados']
                    total_salvos += resultado_olx['salvos']
                    mensagens[-1] = f"🛒 OLX: {resultado_olx['encontrados']} encontrados, {resultado_olx['salvos']} novos"
                else:
                    mensagens[-1] = f"🛒 OLX: ❌ Erro - {resultado_olx['erro']}"
            
            # Executar busca no Facebook
            if origem in ['facebook', 'ambos']:
                mensagens.append("📘 Buscando no Facebook...")
                await query.edit_message_text(
                    f"🔍 <b>Buscando...</b>\n\n"
                    f"📝 Palavra: <code>{palavra}</code>\n\n"
                    + "\n".join(mensagens),
                    parse_mode='HTML'
                )
                
                from src.managers.credentials_manager import CredentialsManager
                credentials_manager = CredentialsManager()
                fb_credentials = credentials_manager.get_credentials('facebook')
                
                resultado_fb = self.scheduler_manager._execute_facebook_scraper(palavra, fb_credentials)
                if resultado_fb['status'] == 'success':
                    total_encontrados += resultado_fb['encontrados']
                    total_salvos += resultado_fb['salvos']
                    mensagens[-1] = f"📘 Facebook: {resultado_fb['encontrados']} encontrados, {resultado_fb['salvos']} novos"
                else:
                    mensagens[-1] = f"📘 Facebook: ❌ Erro - {resultado_fb['erro']}"
            
            # Mensagem final
            resultado_msg = f"✅ <b>Busca Concluída!</b>\n\n"
            resultado_msg += f"📝 Palavra: <code>{palavra}</code>\n"
            resultado_msg += f"📍 Origem: <b>{origem.upper()}</b>\n\n"
            resultado_msg += "<b>Resultados:</b>\n" + "\n".join(mensagens)
            resultado_msg += f"\n\n<b>Total:</b> {total_encontrados} encontrados, {total_salvos} novos"
            
            await query.edit_message_text(resultado_msg, parse_mode='HTML')
            
            # Se encontrou anúncios, enviar automaticamente
            if total_encontrados > 0:
                # Aguardar 1 segundo para não sobrecarregar
                await asyncio.sleep(1)
                
                # Enviar anúncios encontrados
                await self._send_found_ads_by_palavra(
                    chat_id=query.message.chat_id,
                    palavra=palavra,
                    origem=origem,
                    limit=20
                )
            
        except Exception as e:
            logger.error(f"Erro ao executar busca: {e}", exc_info=True)
            await query.edit_message_text(
                f"❌ <b>Erro ao executar busca</b>\n\n"
                f"Erro: {str(e)[:200]}",
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
    
    async def ver_credenciais_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostra credenciais cadastradas (mascaradas) via comando de texto"""
        try:
            creds = self.credentials_manager.list_credentials()
            
            if not creds:
                await update.message.reply_text(
                    "📭 <b>Nenhuma credencial cadastrada</b>\n\n"
                    "Use /cadastrar_facebook para adicionar.",
                    parse_mode='HTML'
                )
                return
            
            message = "🔑 <b>Credenciais Cadastradas</b>\n\n"
            
            for cred in creds:
                status = "✅ Ativa" if cred['is_active'] else "❌ Inativa"
                username_masked = cred['username'][:3] + "***" + cred['username'][-4:] if len(cred['username']) > 7 else "***"
                
                message += f"<b>{cred['service'].upper()}:</b>\n"
                message += f"  • Usuário: <code>{username_masked}</code>\n"
                message += f"  • Status: {status}\n\n"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao listar credenciais: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Erro ao listar credenciais.",
                parse_mode='HTML'
            )
    
    async def action_ver_creds_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Ver credenciais via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            creds = self.credentials_manager.list_credentials()
            
            if not creds:
                message = "📭 <b>Nenhuma credencial cadastrada</b>\n\n"
            else:
                message = "🔑 <b>Credenciais Cadastradas</b>\n\n"
                
                for cred in creds:
                    status = "✅ Ativa" if cred['is_active'] else "❌ Inativa"
                    username_masked = cred['username'][:3] + "***" + cred['username'][-4:] if len(cred['username']) > 7 else "***"
                    
                    message += f"<b>{cred['service'].upper()}:</b>\n"
                    message += f"  • Usuário: <code>{username_masked}</code>\n"
                    message += f"  • Status: {status}\n\n"
            
            # Botão voltar
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_credenciais')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao listar credenciais: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Erro ao listar credenciais.",
                parse_mode='HTML'
            )
    
    async def action_list_palavras_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Listar palavras-chave via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            keywords = self.keywords_manager.list_keywords(only_active=True)
            
            if not keywords:
                message = "� <b>Nenhuma palavra-chave cadastrada</b>\n\n"
            else:
                # Agrupar por origem
                olx_kw = [k for k in keywords if k['origem'] == 'olx']
                facebook_kw = [k for k in keywords if k['origem'] == 'facebook']
                ambos_kw = [k for k in keywords if k['origem'] == 'ambos']
                
                message = "🔍 <b>Palavras-Chave Ativas</b>\n\n"
                
                if olx_kw:
                    message += "🛒 <b>OLX:</b>\n"
                    for kw in olx_kw:
                        stars = "⭐" * kw['prioridade']
                        message += f"  • {kw['palavra']} {stars}\n"
                    message += "\n"
                
                if facebook_kw:
                    message += "📘 <b>Facebook:</b>\n"
                    for kw in facebook_kw:
                        stars = "⭐" * kw['prioridade']
                        message += f"  • {kw['palavra']} {stars}\n"
                    message += "\n"
                
                if ambos_kw:
                    message += "🔍 <b>Ambos:</b>\n"
                    for kw in ambos_kw:
                        stars = "⭐" * kw['prioridade']
                        message += f"  • {kw['palavra']} {stars}\n"
                
                message += f"\n<b>Total:</b> {len(keywords)} palavras"
            
            # Botão voltar
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_palavras')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao listar palavras: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Erro ao listar palavras-chave.",
                parse_mode='HTML'
            )
    
    async def action_ver_status_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Ver status via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Obter configuração do scheduler
            scheduler_config = self.scheduler_manager.get_config()
            
            # Obter palavras-chave
            keywords_olx = self.keywords_manager.list_keywords('olx', only_active=True)
            keywords_facebook = self.keywords_manager.list_keywords('facebook', only_active=True)
            keywords_ambos = self.keywords_manager.list_keywords('ambos', only_active=True)
            
            # Obter credenciais
            creds = self.credentials_manager.list_credentials()
            creds_facebook = [c for c in creds if c['service'] == 'facebook' and c['is_active']]
            
            # Status do scheduler
            scheduler_status = "🟢 Ativo" if scheduler_config['enabled'] else "🔴 Inativo"
            
            # Formatar última execução
            if scheduler_config['last_run']:
                last_run = datetime.fromisoformat(scheduler_config['last_run']).strftime('%d/%m/%Y %H:%M:%S')
            else:
                last_run = "Nunca executado"
            
            # Formatar próxima execução
            if scheduler_config['next_run']:
                next_run = datetime.fromisoformat(scheduler_config['next_run']).strftime('%d/%m/%Y %H:%M:%S')
            else:
                next_run = "Não agendado"
            
            status_message = f"""
📊 <b>Status do Sistema</b>

<b>⏰ Scheduler:</b>
• Status: {scheduler_status}
• Intervalo: {scheduler_config['interval_minutes']} minutos
• Última execução: {last_run}
• Próxima execução: {next_run}
• Total execuções: {scheduler_config['total_runs']}
• Total erros: {scheduler_config['total_errors']}

<b>🔍 Palavras-Chave Ativas:</b>
• OLX: {len(keywords_olx)}
• Facebook: {len(keywords_facebook)}
• Ambos: {len(keywords_ambos)}
• <b>Total: {len(keywords_olx) + len(keywords_facebook) + len(keywords_ambos)}</b>

<b>🔑 Credenciais:</b>
• Facebook: {'✅ Configurado' if creds_facebook else '❌ Não configurado'}
"""
            
            # Botão voltar
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_buscas')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(status_message, reply_markup=reply_markup, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Erro ao gerar status: {e}", exc_info=True)
            await query.edit_message_text(
                "❌ Erro ao gerar status. Verifique os logs.",
                parse_mode='HTML'
            )
    
    async def action_cadastrar_fb_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Iniciar cadastro de credenciais Facebook via botão"""
        query = update.callback_query
        await query.answer()
        
        # Redirecionar para o início do ConversationHandler
        await query.edit_message_text(
            "🔑 <b>Cadastrar Credenciais do Facebook</b>\n\n"
            "Por favor, envie seu <b>email ou telefone</b> do Facebook:",
            parse_mode='HTML'
        )
        
        return ASK_EMAIL
    
    async def action_add_palavra_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Iniciar adição de palavra-chave via botão"""
        query = update.callback_query
        await query.answer()
        
        # Redirecionar para o início do ConversationHandler
        await query.edit_message_text(
            "🔍 <b>Adicionar Palavra-Chave</b>\n\n"
            "Digite a palavra ou frase que deseja monitorar:\n\n"
            "<i>Exemplo: iPhone 13, Notebook Dell, etc.</i>",
            parse_mode='HTML'
        )
        
        return ASK_PALAVRA
    
    async def action_remove_palavra_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Iniciar remoção de palavra-chave via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Listar apenas palavras ATIVAS para remoção
            keywords = self.keywords_manager.list_keywords(only_active=True)
            
            if not keywords:
                keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_palavras')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    "📭 <b>Nenhuma palavra-chave ativa</b>\n\n"
                    "Use 'Adicionar Palavra' primeiro.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return ConversationHandler.END
            
            # Criar botões com as palavras ativas
            keyboard = []
            for kw in keywords:
                callback_data = f"remove_kw_{kw['id']}"
                # Mostrar origem e total de resultados
                label = f"🔹 {kw['palavra']} ({kw['origem']}) - {kw['total_encontrados']} resultados"
                keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
            
            keyboard.append([InlineKeyboardButton("◀️ Cancelar", callback_data='menu_palavras')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🗑️ <b>Remover Palavra-Chave</b>\n\n"
                "Selecione a palavra que deseja remover:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Erro ao listar palavras para remoção: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao carregar palavras-chave.")
            return ConversationHandler.END
    
    async def remove_keyword_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para confirmar remoção de palavra-chave"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extrair ID da palavra do callback_data
            keyword_id = int(query.data.replace('remove_kw_', ''))
            
            # Obter palavra antes de remover (buscar apenas entre ativas)
            keywords = self.keywords_manager.list_keywords(only_active=True)
            keyword = next((k for k in keywords if k['id'] == keyword_id), None)
            
            if not keyword:
                keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_palavras')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ <b>Palavra-chave não encontrada</b>\n\n"
                    "A palavra pode já ter sido removida.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return
            
            # Remover (o método recebe a palavra, não o ID)
            success = self.keywords_manager.remove_keyword(keyword['palavra'])
            
            if success:
                keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_palavras')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ <b>Palavra-chave removida!</b>\n\n"
                    f"Palavra: <code>{keyword['palavra']}</code>\n"
                    f"Origem: {keyword['origem']}",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text("❌ Erro ao remover palavra-chave.")
                
        except Exception as e:
            logger.error(f"Erro ao remover palavra: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao processar remoção.")
    
    async def action_config_intervalo_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Configurar intervalo do scheduler via botão"""
        query = update.callback_query
        await query.answer()
        
        # Mostrar opções de intervalo
        keyboard = [
            [InlineKeyboardButton("⏱️ 1 minuto", callback_data='set_interval_1')],
            [InlineKeyboardButton("⏱️ 3 minutos", callback_data='set_interval_3')],
            [InlineKeyboardButton("⏱️ 5 minutos", callback_data='set_interval_5')],
            [InlineKeyboardButton("⏱️ 10 minutos", callback_data='set_interval_10')],
            [InlineKeyboardButton("⏱️ 30 minutos", callback_data='set_interval_30')],
            [InlineKeyboardButton("⏱️ 1 hora (60 min)", callback_data='set_interval_60')],
            [InlineKeyboardButton("◀️ Voltar", callback_data='menu_agendamento')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ <b>Configurar Intervalo</b>\n\n"
            "Escolha o intervalo entre as execuções automáticas:\n\n"
            "<i>⚠️ Intervalos curtos (1-5 min) podem consumir mais recursos.</i>",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def set_interval_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para definir intervalo do scheduler"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extrair intervalo do callback_data
            interval = int(query.data.replace('set_interval_', ''))
            
            # Configurar intervalo
            self.scheduler_manager.set_interval(interval)
            
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_agendamento')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ <b>Intervalo configurado!</b>\n\n"
                f"Intervalo: {interval} minutos\n\n"
                f"<i>Use 'Iniciar Scheduler' para ativar as execuções automáticas.</i>",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao configurar intervalo: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao configurar intervalo.")
    
    async def action_start_scheduler_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Iniciar scheduler via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            success = self.scheduler_manager.start()
            
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_agendamento')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if success:
                config = self.scheduler_manager.get_config()
                await query.edit_message_text(
                    f"✅ <b>Scheduler iniciado!</b>\n\n"
                    f"Intervalo: {config['interval_minutes']} minutos\n"
                    f"Próxima execução: {datetime.fromisoformat(config['next_run']).strftime('%d/%m/%Y %H:%M:%S') if config['next_run'] else 'Em breve'}\n\n"
                    f"<i>As buscas serão executadas automaticamente.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    "❌ <b>Erro ao iniciar scheduler!</b>\n\n"
                    f"<i>Verifique se já não está em execução.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Erro ao iniciar scheduler: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao iniciar scheduler.")
    
    async def action_stop_scheduler_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Parar scheduler via botão"""
        query = update.callback_query
        await query.answer()
        
        try:
            success = self.scheduler_manager.stop()
            
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_agendamento')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if success:
                await query.edit_message_text(
                    "⏸️ <b>Scheduler parado!</b>\n\n"
                    "<i>As execuções automáticas foram desativadas.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    "❌ <b>Erro ao parar scheduler!</b>\n\n"
                    "<i>Verifique se já não está parado.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Erro ao parar scheduler: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao parar scheduler.")
    
    async def action_buscar_agora_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ação: Executar busca manual via botão"""
        query = update.callback_query
        await query.answer()
        
        # Mostrar opções de origem
        keyboard = [
            [InlineKeyboardButton("🛒 Buscar na OLX", callback_data='search_olx')],
            [InlineKeyboardButton("📘 Buscar no Facebook", callback_data='search_facebook')],
            [InlineKeyboardButton("🔍 Buscar em Ambos", callback_data='search_ambos')],
            [InlineKeyboardButton("◀️ Voltar", callback_data='menu_buscas')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔎 <b>Buscar Agora</b>\n\n"
            "Escolha onde deseja executar a busca:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def search_now_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback para executar busca manual"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Extrair origem do callback_data
            origem = query.data.replace('search_', '')
            
            # Mensagem de processamento
            await query.edit_message_text(
                f"⏳ <b>Iniciando busca...</b>\n\n"
                f"Origem: {origem.upper()}\n\n"
                f"<i>Aguarde, isso pode levar alguns minutos...</i>",
                parse_mode='HTML'
            )
            
            # Executar busca manual
            from datetime import datetime
            start_time = datetime.now()
            success = self.scheduler_manager.run_manual_search(tipo=origem)
            duration = (datetime.now() - start_time).total_seconds()
            
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_buscas')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if success:
                await query.edit_message_text(
                    f"✅ <b>Busca concluída!</b>\n\n"
                    f"Origem: {origem.upper()}\n"
                    f"Duração: {duration:.1f}s\n\n"
                    f"<i>Verifique os logs para mais detalhes sobre os anúncios encontrados.</i>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await query.edit_message_text(
                    f"❌ <b>Erro na busca</b>\n\n"
                    f"Verifique os logs para mais detalhes.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Erro ao executar busca manual: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("◀️ Voltar", callback_data='menu_buscas')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Erro ao executar busca.",
                reply_markup=reply_markup
            )
    
    async def show_ads_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback quando usuário escolhe quantos anúncios ver"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback_data: "show_ads_olx_5" → ["show", "ads", "olx", "5"]
            parts = query.data.split('_')
            tipo = parts[2]  # "olx" ou "facebook"
            limit_str = parts[3]  # "5", "20", "40", ou "all"
            
            # Editar mensagem para mostrar loading
            await query.edit_message_text(
                f"🔄 <b>Carregando anúncios...</b>",
                parse_mode='HTML'
            )
            
            # Determinar limite
            if limit_str == 'all':
                limit = None  # Buscar todos
                emoji = "📦"
                texto_limit = "TODOS"
            else:
                limit = int(limit_str)
                if limit == 5:
                    emoji = "📄"
                elif limit == 20:
                    emoji = "📑"
                else:
                    emoji = "📚"
                texto_limit = str(limit)
            
            # Enviar anúncios
            self._send_found_ads(tipo, limit)
            
            # Confirmar
            await query.edit_message_text(
                f"✅ <b>Enviando {texto_limit} anúncios!</b> {emoji}",
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar seleção de anúncios: {e}", exc_info=True)
            await query.edit_message_text("❌ Erro ao carregar anúncios.")
    
    def build_application(self):
        """Constrói a aplicação do bot com todos os handlers"""
        self.application = Application.builder().token(self.token).build()
        
        # Handlers de comandos simples
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(CommandHandler("iniciar_scheduler", self.iniciar_scheduler_command))
        self.application.add_handler(CommandHandler("parar_scheduler", self.parar_scheduler_command))
        self.application.add_handler(CommandHandler("listar_palavras", self.listar_palavras_command))
        self.application.add_handler(CommandHandler("remover_palavra", self.remover_palavra_command))
        self.application.add_handler(CommandHandler("ver_credenciais", self.ver_credenciais_command))
        
        # Handler para menu
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        
        # IMPORTANTE: ConversationHandlers DEVEM vir ANTES dos CallbackQueryHandlers genéricos
        # para evitar conflitos de pattern matching
        
        # ConversationHandler para cadastrar Facebook (com entry points via menu e comando)
        conv_handler_facebook = ConversationHandler(
            entry_points=[
                CommandHandler("cadastrar_facebook", self.cadastrar_facebook_start),
                CallbackQueryHandler(self.action_cadastrar_fb_callback, pattern='^action_cadastrar_fb$')
            ],
            states={
                ASK_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.cadastrar_facebook_email)],
                ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.cadastrar_facebook_password)],
            },
            fallbacks=[CommandHandler("cancelar", self.cancelar_command)],
        )
        self.application.add_handler(conv_handler_facebook)
        
        # ConversationHandler para adicionar palavra-chave (com entry points via menu e comando)
        conv_handler_palavra = ConversationHandler(
            entry_points=[
                CommandHandler("adicionar_palavra", self.adicionar_palavra_start),
                CallbackQueryHandler(self.action_add_palavra_callback, pattern='^action_add_palavra$')
            ],
            states={
                ASK_PALAVRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.adicionar_palavra_texto)],
                ASK_ORIGEM: [CallbackQueryHandler(self.adicionar_palavra_origem, pattern='^origem_')],
                ASK_PRIORIDADE: [CallbackQueryHandler(self.adicionar_palavra_prioridade, pattern='^prioridade_')],
            },
            fallbacks=[CommandHandler("cancelar", self.cancelar_command)],
        )
        self.application.add_handler(conv_handler_palavra)
        
        # ConversationHandler para buscar palavra específica
        conv_handler_busca = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.action_buscar_palavra_callback, pattern='^action_buscar_palavra$')
            ],
            states={
                ASK_BUSCA_PALAVRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.buscar_palavra_texto)],
                ASK_BUSCA_ORIGEM: [CallbackQueryHandler(self.buscar_palavra_executar, pattern='^busca_')],
            },
            fallbacks=[CommandHandler("cancelar", self.cancelar_command)],
            per_message=False,
        )
        self.application.add_handler(conv_handler_busca)
        
        # Handlers para navegação de menus
        self.application.add_handler(CallbackQueryHandler(self.menu_credenciais_callback, pattern='^menu_credenciais$'))
        self.application.add_handler(CallbackQueryHandler(self.menu_palavras_callback, pattern='^menu_palavras$'))
        self.application.add_handler(CallbackQueryHandler(self.menu_agendamento_callback, pattern='^menu_agendamento$'))
        self.application.add_handler(CallbackQueryHandler(self.menu_buscas_callback, pattern='^menu_buscas$'))
        self.application.add_handler(CallbackQueryHandler(self.menu_limpeza_callback, pattern='^menu_limpeza$'))
        self.application.add_handler(CallbackQueryHandler(self.back_main_menu_callback, pattern='^back_main_menu$'))
        
        # Handlers para ações de credenciais
        self.application.add_handler(CallbackQueryHandler(self.action_ver_creds_callback, pattern='^action_ver_creds$'))
        
        # Handlers para ações de palavras-chave
        self.application.add_handler(CallbackQueryHandler(self.action_list_palavras_callback, pattern='^action_list_palavras$'))
        self.application.add_handler(CallbackQueryHandler(self.action_remove_palavra_callback, pattern='^action_remove_palavra$'))
        self.application.add_handler(CallbackQueryHandler(self.remove_keyword_callback, pattern='^remove_kw_'))
        
        # Handlers para ações de limpeza
        self.application.add_handler(CallbackQueryHandler(self.action_cleanup_7d_callback, pattern='^action_cleanup_7d$'))
        self.application.add_handler(CallbackQueryHandler(self.action_cleanup_30d_callback, pattern='^action_cleanup_30d$'))
        self.application.add_handler(CallbackQueryHandler(self.action_cleanup_old_callback, pattern='^action_cleanup_old$'))
        self.application.add_handler(CallbackQueryHandler(self.action_cleanup_stats_callback, pattern='^action_cleanup_stats$'))
        
        # Handlers para ações de agendamento
        self.application.add_handler(CallbackQueryHandler(self.action_config_intervalo_callback, pattern='^action_config_intervalo$'))
        self.application.add_handler(CallbackQueryHandler(self.set_interval_callback, pattern='^set_interval_'))
        self.application.add_handler(CallbackQueryHandler(self.action_start_scheduler_callback, pattern='^action_start_scheduler$'))
        self.application.add_handler(CallbackQueryHandler(self.action_stop_scheduler_callback, pattern='^action_stop_scheduler$'))
        
        # Handlers para ações de busca
        self.application.add_handler(CallbackQueryHandler(self.action_buscar_agora_callback, pattern='^action_buscar_agora$'))
        self.application.add_handler(CallbackQueryHandler(self.action_ver_status_callback, pattern='^action_ver_status$'))
        self.application.add_handler(CallbackQueryHandler(self.search_now_callback, pattern='^search_'))
        
        # Handler para menu de seleção de anúncios
        self.application.add_handler(CallbackQueryHandler(self.show_ads_callback, pattern='^show_ads_(olx|facebook)_(5|20|40|all)$'))
        
        # Handler para configurar intervalo (backward compatibility)
        self.application.add_handler(CommandHandler("configurar_intervalo", self.configurar_intervalo_command))
        self.application.add_handler(CallbackQueryHandler(self.configurar_intervalo_callback, pattern='^interval_'))
        
        # Handler para busca manual (backward compatibility)
        self.application.add_handler(CommandHandler("buscar_agora", self.buscar_agora_command))
        self.application.add_handler(CallbackQueryHandler(self.buscar_agora_callback, pattern='^buscar_'))
        
        logger.success("Bot configurado com sucesso!")
    
    async def run(self):
        """Inicia o bot"""
        self.build_application()
        
        logger.info("🤖 Iniciando Bot do Telegram...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        logger.success("✅ Bot iniciado e aguardando comandos!")
        
        # Manter rodando
        await asyncio.Event().wait()
    
    async def stop(self):
        """Para o bot"""
        if self.application:
            logger.info("Parando bot do Telegram...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.success("Bot parado!")


if __name__ == "__main__":
    # Executar bot
    print("=" * 60)
    print("TELEGRAM BOT - SCRAPER DE ANÚNCIOS")
    print("=" * 60)
    
    bot = TelegramBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompido pelo usuário")
        asyncio.run(bot.stop())
    except Exception as e:
        logger.error(f"Erro crítico: {e}", exc_info=True)
