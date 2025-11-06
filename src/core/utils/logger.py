"""
Módulo de logging centralizado usando Loguru.
Configura logs estruturados com rotação, retenção e formatação customizada.
"""

import sys
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from loguru import logger

from src.core.config import Config


class LoggerSetup:
    """Classe para configurar o sistema de logging do projeto"""
    
    _configured = False
    
    @classmethod
    def setup(cls, 
              level: Optional[str] = None,
              log_dir: Optional[str] = None,
              log_prefix: Optional[str] = None,
              rotation: Optional[str] = None,
              retention_days: Optional[int] = None,
              compression: Optional[str] = None,
              custom_format: Optional[str] = None) -> None:
        """
        Configura o logger com as configurações especificadas ou padrões do config.py
        
        Args:
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Diretório onde salvar os logs
            log_prefix: Prefixo do nome do arquivo de log
            rotation: Critério de rotação (ex: "00:00" para meia-noite, "12:00" para meio-dia, "10 MB" para tamanho)
            retention_days: Número de dias para manter logs antigos
            compression: Formato de compressão ("zip", "gz", "tar.gz")
            custom_format: Formato customizado para os logs
        """
        if cls._configured:
            logger.warning("Logger já foi configurado. Reconfigurando...")
            logger.remove()  # Remove handlers existentes
        
        # Usar configurações do config.py se não especificadas
        level = level or Config.logging.LEVEL
        log_dir = Path(log_dir) if log_dir else Config.logging.get_log_dir()
        log_prefix = log_prefix or Config.logging.FILE_PREFIX
        rotation = rotation or Config.logging.ROTATION
        retention_days = retention_days or Config.logging.RETENTION_DAYS
        compression = compression or Config.logging.COMPRESSION
        log_format = custom_format or Config.logging.get_format()
        
        # Criar diretório de logs se não existir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Construir caminho do arquivo com data no nome
        from datetime import datetime
        log_file = log_dir / Config.logging.FILE_FORMAT.format(
            prefix=log_prefix,
            time=datetime.now()
        )
        
        # Remover handler padrão do loguru
        logger.remove()
        
        # Adicionar handler para console (stdout) com cores
        logger.add(
            sys.stdout,
            format=log_format,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # Adicionar handler para arquivo com rotação diária
        logger.add(
            str(log_dir / f"{log_prefix}_{{time:YYYY-MM-DD}}.log"),
            format=log_format,
            level=level,
            rotation=rotation,  # Rotaciona à meia-noite ou conforme configurado
            retention=f"{retention_days} days",  # Mantém logs por X dias
            compression=compression,  # Comprime logs antigos
            backtrace=True,
            diagnose=True,
            encoding="utf-8",
            enqueue=True  # Thread-safe
        )
        
        cls._configured = True
        logger.info(f"Logger configurado - Nível: {level}, Diretório: {log_dir}")
        logger.info(f"Rotação: {rotation}, Retenção: {retention_days} dias, Compressão: {compression}")
    
    @classmethod
    def setup_for_scraper(cls, scraper_name: str) -> None:
        """
        Configura logger específico para um scraper com arquivo separado
        
        Args:
            scraper_name: Nome do scraper (ex: 'olx', 'facebook')
        """
        log_prefix = f"{scraper_name}_scraper"
        
        cls.setup(log_prefix=log_prefix)
        logger.info(f"Logger configurado para scraper: {scraper_name}")
    
    @classmethod
    def is_configured(cls) -> bool:
        """Verifica se o logger já foi configurado"""
        return cls._configured


def get_logger(name: Optional[str] = None):
    """
    Retorna uma instância do logger.
    Configura automaticamente se ainda não foi configurado.
    
    Args:
        name: Nome do logger (opcional, usado para contexto)
    
    Returns:
        Logger configurado
    """
    if not LoggerSetup.is_configured():
        LoggerSetup.setup()
    
    if name:
        return logger.bind(name=name)
    return logger


# Contextualizadores úteis
@contextmanager
def log_scraper_execution(scraper_name: str, palavra_chave: str):
    """
    Context manager para logar execução de scraper
    
    Exemplo:
        with log_scraper_execution('olx', 'motocicleta'):
            # código do scraper
    """
    logger.info(f"Iniciando scraper {scraper_name} - Palavra-chave: {palavra_chave}")
    try:
        yield
        logger.success(f"Scraper {scraper_name} executado com sucesso")
    except Exception as e:
        logger.error(f"Erro no scraper {scraper_name}: {str(e)}", exc_info=True)
        raise


@contextmanager
def log_notification_send(destino: str, tipo: str):
    """
    Context manager para logar envio de notificações
    
    Exemplo:
        with log_notification_send('telegram', 'anuncio'):
            # código de envio
    """
    logger.info(f"Enviando notificação {tipo} para {destino}")
    try:
        yield
        logger.success(f"Notificação {tipo} enviada para {destino}")
    except Exception as e:
        logger.error(f"Erro ao enviar notificação {tipo} para {destino}: {str(e)}", exc_info=True)
        raise


@contextmanager
def log_database_operation(operation: str, table: str):
    """
    Context manager para logar operações de banco de dados
    
    Exemplo:
        with log_database_operation('insert', 'anuncios'):
            # código de inserção
    """
    logger.debug(f"Operação de banco: {operation} em {table}")
    try:
        yield
        logger.debug(f"Operação {operation} em {table} concluída")
    except Exception as e:
        logger.error(f"Erro na operação {operation} em {table}: {str(e)}", exc_info=True)
        raise


# Funções auxiliares de logging
def log_item_scraped(origem: str, titulo: str, preco: str):
    """Loga item raspado"""
    logger.info(f"[{origem.upper()}] Item encontrado: {titulo} - {preco}")


def log_item_saved(origem: str, item_id: int, titulo: str):
    """Loga item salvo no banco"""
    logger.success(f"[{origem.upper()}] Item #{item_id} salvo: {titulo}")


def log_item_duplicate(origem: str, url: str):
    """Loga item duplicado"""
    logger.debug(f"[{origem.upper()}] Item duplicado ignorado: {url}")


def log_notification_sent(origem: str, titulo: str, chat_id: str):
    """Loga notificação enviada"""
    logger.success(f"[{origem.upper()}] Notificação enviada para {chat_id}: {titulo}")


def log_error(origem: str, mensagem: str, exception: Optional[Exception] = None):
    """Loga erro com contexto"""
    if exception:
        logger.error(f"[{origem.upper()}] {mensagem}: {str(exception)}", exc_info=True)
    else:
        logger.error(f"[{origem.upper()}] {mensagem}")


# Configuração automática na importação (pode ser desabilitado se necessário)
def auto_setup():
    """Configura o logger automaticamente se ainda não foi configurado"""
    if not LoggerSetup.is_configured():
        try:
            LoggerSetup.setup()
        except Exception as e:
            # Fallback para configuração básica
            logger.remove()
            logger.add(sys.stdout, level="INFO")
            logger.warning(f"Erro ao configurar logger com config.py: {e}")
            logger.warning("Usando configuração básica de logging")


# Executar configuração automática
auto_setup()


if __name__ == "__main__":
    # Teste de logging
    logger.debug("Mensagem de DEBUG")
    logger.info("Mensagem de INFO")
    logger.success("Mensagem de SUCCESS")
    logger.warning("Mensagem de WARNING")
    logger.error("Mensagem de ERROR")
    
    # Testar funções auxiliares
    log_item_scraped("olx", "Moto Honda CG 160", "R$ 8.500")
    log_item_saved("olx", 123, "Moto Honda CG 160")
    log_item_duplicate("facebook", "https://facebook.com/marketplace/item/123")
    log_notification_sent("telegram", "Novo anúncio encontrado", "1275893490")
    
    print("\n" + "="*50)
    print("Diretório de logs:", Config.logging.get_log_dir())
    print("Arquivo atual:", Config.logging.get_log_path().name)
    print("Retenção:", Config.logging.RETENTION_DAYS, "dias")
    print("Rotação:", Config.logging.ROTATION)
    print("Compressão:", Config.logging.COMPRESSION)
