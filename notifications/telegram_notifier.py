"""
Notificador via Telegram
Envia notificações de anúncios para o Telegram
"""

import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Bot
from telegram.error import TelegramError
from loguru import logger

from notifications.base_notifier import BaseNotifier


class TelegramNotifier(BaseNotifier):
    """Notificador que envia mensagens via Telegram"""
    
    def __init__(self, token: str, chat_id: str, database_path: str = 'marketplace_anuncios.db'):
        """
        Inicializa o notificador Telegram
        
        Args:
            token: Token do bot do Telegram
            chat_id: ID do chat para enviar mensagens
            database_path: Caminho do banco de dados SQLite
        """
        if not token or not chat_id:
            raise ValueError("Token e chat_id são obrigatórios")
        
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self.database_path = database_path
        logger.info(f"TelegramNotifier inicializado - Chat ID: {chat_id}")
    
    async def send(self, message: str) -> bool:
        """
        Envia uma mensagem de texto simples
        
        Args:
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info("Mensagem enviada com sucesso")
            return True
        except TelegramError as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False
    
    async def send_anuncio(self, anuncio: Dict) -> bool:
        """
        Envia notificação formatada de um anúncio
        
        Args:
            anuncio: Dicionário com dados do anúncio
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            mensagem = self._formatar_anuncio(anuncio)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=mensagem,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            # Marca como enviado no banco de dados
            self._marcar_como_enviado(anuncio.get('url'))
            
            logger.info(f"Anúncio enviado: {anuncio.get('titulo', 'N/A')}")
            return True
            
        except TelegramError as e:
            logger.error(f"Erro ao enviar anúncio: {e}")
            return False
    
    async def send_anuncios_batch(self, anuncios: List[Dict], delay: float = 1.0) -> int:
        """
        Envia múltiplos anúncios com delay entre eles
        
        Args:
            anuncios: Lista de dicionários com dados dos anúncios
            delay: Tempo de espera entre envios (segundos)
            
        Returns:
            int: Quantidade de anúncios enviados com sucesso
        """
        enviados = 0
        
        for anuncio in anuncios:
            if await self.send_anuncio(anuncio):
                enviados += 1
            
            # Aguarda para não sobrecarregar a API do Telegram
            if delay > 0:
                await asyncio.sleep(delay)
        
        logger.info(f"{enviados}/{len(anuncios)} anúncios enviados com sucesso")
        return enviados
    
    async def send_resumo(self, total_facebook: int, total_olx: int, total_novos: int) -> bool:
        """
        Envia resumo diário de anúncios
        
        Args:
            total_facebook: Total de anúncios do Facebook
            total_olx: Total de anúncios da OLX
            total_novos: Total de novos anúncios hoje
            
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            hoje = datetime.now().strftime("%d/%m/%Y")
            
            mensagem = (
                f"📊 *Resumo de Anúncios - {hoje}*\n\n"
                f"🆕 Novos anúncios encontrados: *{total_novos}*\n\n"
                f"📦 Facebook Marketplace: {total_facebook}\n"
                f"🛍️ OLX: {total_olx}\n\n"
                f"💾 Total no banco: {total_facebook + total_olx}"
            )
            
            return await self.send(mensagem)
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo: {e}")
            return False
    
    def _formatar_anuncio(self, anuncio: Dict) -> str:
        """
        Formata um anúncio para envio
        
        Args:
            anuncio: Dicionário com dados do anúncio
            
        Returns:
            str: Mensagem formatada em Markdown
        """
        # Emoji baseado na origem
        emoji_origem = "📦" if anuncio.get('origem') == 'facebook' else "🛍️"
        nome_origem = "Facebook" if anuncio.get('origem') == 'facebook' else "OLX"
        
        # Monta a mensagem
        titulo = anuncio.get('titulo', 'N/A')
        preco = anuncio.get('preco', 'N/A')
        localizacao = anuncio.get('localizacao', '')
        url = anuncio.get('url', '')
        data_pub = anuncio.get('data_publicacao', '')
        categoria = anuncio.get('categoria', '')
        
        mensagem = f"{emoji_origem} *{titulo}*\n\n"
        mensagem += f"💰 Preço: *{preco}*\n"
        
        if localizacao:
            mensagem += f"📍 Local: {localizacao}\n"
        
        if categoria:
            mensagem += f"🏷️ Categoria: {categoria}\n"
        
        if data_pub:
            mensagem += f"📅 Publicado: {data_pub}\n"
        
        mensagem += f"🌐 Origem: {nome_origem}\n\n"
        mensagem += f"🔗 [Ver anúncio]({url})"
        
        return mensagem
    
    def _marcar_como_enviado(self, url: str) -> bool:
        """
        Marca um anúncio como enviado no banco de dados
        
        Args:
            url: URL do anúncio
            
        Returns:
            bool: True se marcado com sucesso
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE anuncios 
                SET enviado_telegram = 1,
                    data_envio_telegram = CURRENT_TIMESTAMP
                WHERE url = ?
            ''', (url,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Erro ao marcar anúncio como enviado: {e}")
            return False
    
    def get_anuncios_nao_enviados(self, origem: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Busca anúncios que ainda não foram enviados
        
        Args:
            origem: Filtrar por origem ('facebook', 'olx', None para todos)
            limit: Limite de resultados
            
        Returns:
            List[Dict]: Lista de anúncios não enviados
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM anuncios 
                WHERE enviado_telegram = 0
            '''
            
            params = []
            if origem:
                query += ' AND origem = ?'
                params.append(origem)
            
            query += ' ORDER BY data_coleta DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            anuncios = [dict(row) for row in rows]
            conn.close()
            
            logger.info(f"Encontrados {len(anuncios)} anúncios não enviados")
            return anuncios
            
        except Exception as e:
            logger.error(f"Erro ao buscar anúncios não enviados: {e}")
            return []
    
    async def enviar_pendentes(self, origem: Optional[str] = None, delay: float = 1.0) -> int:
        """
        Envia todos os anúncios pendentes
        
        Args:
            origem: Filtrar por origem ('facebook', 'olx', None para todos)
            delay: Tempo de espera entre envios (segundos)
            
        Returns:
            int: Quantidade de anúncios enviados
        """
        anuncios = self.get_anuncios_nao_enviados(origem=origem)
        
        if not anuncios:
            logger.info("Nenhum anúncio pendente para enviar")
            return 0
        
        logger.info(f"Enviando {len(anuncios)} anúncios pendentes...")
        return await self.send_anuncios_batch(anuncios, delay=delay)
