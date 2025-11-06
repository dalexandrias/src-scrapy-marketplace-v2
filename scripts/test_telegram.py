#!/usr/bin/env python
"""
Script para testar a configuração do Telegram Bot

Uso:
    python scripts/test_telegram.py
    python scripts/test_telegram.py --mensagem "Teste customizado"
"""

import sys
from pathlib import Path
import argparse
import asyncio

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from config import Config
from utils.logger import logger


async def testar_bot(mensagem_custom=None):
    """
    Testa conexão com o bot do Telegram
    
    Args:
        mensagem_custom: Mensagem customizada para enviar
    """
    logger.info("="*60)
    logger.info("🤖 TESTE DO TELEGRAM BOT")
    logger.info("="*60)
    
    # Verificar configuração
    if not Config.telegram.is_configured():
        logger.error("❌ Telegram não está configurado corretamente")
        logger.info("Configure as seguintes variáveis no arquivo .env:")
        logger.info("  - TELEGRAM_BOT_TOKEN")
        logger.info("  - TELEGRAM_CHAT_ID")
        logger.info("  - TELEGRAM_ENABLED=true")
        return False
    
    logger.info(f"Bot Token: {Config.telegram.BOT_TOKEN[:10]}...")
    logger.info(f"Chat ID: {Config.telegram.CHAT_ID}")
    logger.info("")
    
    try:
        # Criar bot
        logger.info("Criando instância do bot...")
        bot = Bot(token=Config.telegram.BOT_TOKEN)
        
        # Obter informações do bot
        logger.info("Obtendo informações do bot...")
        bot_info = await bot.get_me()
        
        logger.success(f"✅ Bot conectado com sucesso!")
        logger.info(f"Nome do bot: @{bot_info.username}")
        logger.info(f"ID do bot: {bot_info.id}")
        logger.info("")
        
        # Enviar mensagem de teste
        mensagem = mensagem_custom or "🎉 *Teste de conexão*\n\nO bot está funcionando corretamente!"
        
        logger.info(f"Enviando mensagem de teste para chat {Config.telegram.CHAT_ID}...")
        await bot.send_message(
            chat_id=Config.telegram.CHAT_ID,
            text=mensagem,
            parse_mode='Markdown'
        )
        
        logger.success("✅ Mensagem enviada com sucesso!")
        logger.info("")
        logger.info("="*60)
        logger.info("✅ TESTE CONCLUÍDO COM SUCESSO!")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar bot: {e}", exc_info=True)
        logger.info("")
        logger.info("Possíveis causas:")
        logger.info("  1. Token do bot inválido")
        logger.info("  2. Chat ID incorreto")
        logger.info("  3. Bot não foi iniciado (@BotFather -> /start)")
        logger.info("  4. Problemas de conexão com a internet")
        logger.info("")
        logger.info("Como obter o Chat ID:")
        logger.info("  1. Envie uma mensagem para @userinfobot")
        logger.info("  2. O bot responderá com seu ID")
        
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Testa a configuração do Telegram Bot'
    )
    
    parser.add_argument(
        '--mensagem', '-m',
        type=str,
        help='Mensagem customizada para enviar'
    )
    
    args = parser.parse_args()
    
    # Executar teste
    sucesso = asyncio.run(testar_bot(args.mensagem))
    
    return 0 if sucesso else 1


if __name__ == '__main__':
    sys.exit(main())
