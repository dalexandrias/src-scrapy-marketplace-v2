"""
Módulo de configuração centralizado para o projeto Marketplace Scraper.
Utiliza python-decouple para carregar variáveis de ambiente do arquivo .env
"""

import os
from pathlib import Path
from typing import List
from decouple import config, Csv


# Diretório base do projeto (raiz do projeto)
BASE_DIR = Path(__file__).parent.parent.parent


class TelegramConfig:
    """Configurações do Telegram"""
    
    BOT_TOKEN: str = config('TELEGRAM_BOT_TOKEN', default='')
    CHAT_ID: str = config('TELEGRAM_CHAT_ID', default='')
    ENABLED: bool = config('TELEGRAM_ENABLED', default=False, cast=bool)
    DELAY: float = config('TELEGRAM_DELAY', default=1.0, cast=float)
    
    @classmethod
    def is_configured(cls) -> bool:
        """Verifica se o Telegram está configurado corretamente"""
        return bool(cls.BOT_TOKEN and cls.CHAT_ID and cls.ENABLED)
    
    @classmethod
    def validate(cls) -> None:
        """Valida configurações do Telegram"""
        if cls.ENABLED:
            if not cls.BOT_TOKEN:
                raise ValueError("TELEGRAM_BOT_TOKEN não está configurado no .env")
            if not cls.CHAT_ID:
                raise ValueError("TELEGRAM_CHAT_ID não está configurado no .env")


class DatabaseConfig:
    """Configurações do banco de dados"""
    
    PATH: str = config('DATABASE_PATH', default='data/marketplace_anuncios.db')
    
    @classmethod
    def get_full_path(cls) -> Path:
        """Retorna o caminho completo do banco de dados"""
        db_path = Path(cls.PATH)
        if db_path.is_absolute():
            return db_path
        return BASE_DIR / db_path
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Retorna a string de conexão SQLite"""
        return str(cls.get_full_path())


class OlxConfig:
    """Configurações da OLX"""
    
    USER_AGENT: str = config(
        'OLX_USER_AGENT',
        default='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36'
    )
    REQUEST_DELAY: int = config('OLX_REQUEST_DELAY', default=2, cast=int)
    ESTADOS: List[str] = config('OLX_ESTADOS', default='SP,RJ,PR,MG', cast=Csv())
    CATEGORIA_PADRAO: str = config('OLX_CATEGORIA_PADRAO', default='carros')
    
    # Configurações do Scrapy para OLX
    CONCURRENT_REQUESTS: int = 4
    CONCURRENT_REQUESTS_PER_DOMAIN: int = 2
    DOWNLOAD_DELAY: int = REQUEST_DELAY
    AUTOTHROTTLE_ENABLED: bool = True
    AUTOTHROTTLE_START_DELAY: float = 1.0
    AUTOTHROTTLE_MAX_DELAY: float = 10.0
    AUTOTHROTTLE_TARGET_CONCURRENCY: float = 2.0
    
    @classmethod
    def get_base_url(cls, estado: str = 'pr') -> str:
        """Retorna a URL base da OLX"""
        return "https://www.olx.com.br"
    
    @classmethod
    def get_search_url(cls, palavra_chave: str, estado: str = 'pr', categoria: str = None) -> str:
        """
        Constrói URL de busca na OLX para região de Curitiba/PR
        
        Formato fixo da URL:
        https://www.olx.com.br/autos-e-pecas/carros-vans-e-utilitarios/estado-pr/regiao-de-curitiba-e-paranagua/grande-curitiba?q=parametroDeBusca&sf=1&f=p
        
        Parâmetros:
            - q: palavra de busca (URL encoded)
            - sf=1: ordenação (1 = mais recentes primeiro)
            - f=p: filtro de particular
        
        Args:
            palavra_chave: Termo de busca
            estado: Ignorado - sempre usa PR/Curitiba
            categoria: Ignorado - não usa categoria na URL
        
        Returns:
            URL formatada para busca na OLX Curitiba
        """
        from urllib.parse import quote_plus
        
        # URL encode da palavra-chave
        palavra_encoded = quote_plus(palavra_chave)
        
        # URL fixa para Curitiba/PR conforme solicitado
        base_url = cls.get_base_url()
        regiao = 'estado-pr/regiao-de-curitiba-e-paranagua/grande-curitiba'
        
        # Construir URL com todos os filtros
        # q: palavra de busca
        # sf=1: mais recentes primeiro
        # f=p: filtro de particular
        return f"{base_url}/{regiao}?q={palavra_encoded}&sf=1&f=p"


class FacebookConfig:
    """Configurações do Facebook Marketplace"""
    
    EMAIL: str = config('FACEBOOK_EMAIL', default='')
    PASSWORD: str = config('FACEBOOK_PASSWORD', default='')
    USE_COOKIES: bool = config('FACEBOOK_USE_COOKIES', default=True, cast=bool)
    CIDADE_PADRAO: str = config('FACEBOOK_CIDADE_PADRAO', default='curitiba')
    
    # Configurações do Scrapy para Facebook
    CONCURRENT_REQUESTS: int = 2
    DOWNLOAD_DELAY: int = 3
    AUTOTHROTTLE_ENABLED: bool = True
    AUTOTHROTTLE_START_DELAY: float = 2.0
    AUTOTHROTTLE_MAX_DELAY: float = 10.0
    
    @classmethod
    def has_credentials(cls) -> bool:
        """Verifica se há credenciais configuradas"""
        return bool(cls.EMAIL and cls.PASSWORD)
    
    @classmethod
    def get_base_url(cls) -> str:
        """Retorna a URL base do Facebook"""
        return "https://www.facebook.com"
    
    @classmethod
    def get_marketplace_url(cls, cidade: str = None) -> str:
        """Retorna a URL do Marketplace para uma cidade"""
        cidade_url = cidade or cls.CIDADE_PADRAO
        cidade_formatada = cidade_url.replace(' ', '-').lower()
        return f"{cls.get_base_url()}/marketplace/{cidade_formatada}"


class LoggingConfig:
    """Configurações de logging"""
    
    LEVEL: str = config('LOG_LEVEL', default='INFO')
    DIR: str = config('LOG_DIR', default='logs')
    FILE_PREFIX: str = config('LOG_FILE_PREFIX', default='marketplace')
    
    # Rotação: pode ser tempo ("00:00", "12:00") ou tamanho ("10 MB", "500 KB")
    ROTATION: str = config('LOG_ROTATION', default='00:00')  # Meia-noite por padrão
    
    # Retenção: quantos dias manter os logs (ex: "7 days", "30 days", "1 week")
    RETENTION_DAYS: int = config('LOG_RETENTION_DAYS', default=30, cast=int)
    
    # Compressão de logs antigos
    COMPRESSION: str = config('LOG_COMPRESSION', default='zip')
    
    # Formato do nome do arquivo com data
    FILE_FORMAT: str = config('LOG_FILE_FORMAT', default='{prefix}_{time:YYYY-MM-DD}.log')
    
    @classmethod
    def get_log_dir(cls) -> Path:
        """Retorna o diretório de logs"""
        log_dir = Path(cls.DIR)
        if log_dir.is_absolute():
            return log_dir
        return BASE_DIR / log_dir
    
    @classmethod
    def get_log_path(cls) -> Path:
        """Retorna o caminho completo do arquivo de log com data"""
        from datetime import datetime
        
        log_dir = cls.get_log_dir()
        
        # Substituir placeholders no formato
        # {prefix} -> LOG_FILE_PREFIX
        # {time:YYYY-MM-DD} -> data atual formatada
        filename = cls.FILE_FORMAT.replace('{prefix}', cls.FILE_PREFIX)
        
        # Substituir formato de data
        now = datetime.now()
        filename = filename.replace('{time:YYYY-MM-DD}', now.strftime('%Y-%m-%d'))
        
        return log_dir / filename
    
    @classmethod
    def get_retention(cls) -> str:
        """Retorna string de retenção formatada para Loguru"""
        return f"{cls.RETENTION_DAYS} days"
    
    @classmethod
    def get_format(cls) -> str:
        """Retorna o formato do log"""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )


class GeneralConfig:
    """Configurações gerais da aplicação"""
    
    AUTO_RUN: bool = config('AUTO_RUN', default=False, cast=bool)
    AUTO_RUN_INTERVAL: int = config('AUTO_RUN_INTERVAL', default=30, cast=int)
    
    # Constantes do projeto
    PROJECT_NAME: str = "Marketplace Scraper"
    PROJECT_VERSION: str = "2.0.0"
    
    # Origens suportadas
    ORIGEM_FACEBOOK: str = "facebook"
    ORIGEM_OLX: str = "olx"
    ORIGENS_VALIDAS: List[str] = [ORIGEM_FACEBOOK, ORIGEM_OLX]


class SchedulerConfig:
    """Configurações do agendador de tarefas"""
    
    INTERVAL: int = config('SCHEDULER_INTERVAL', default=30, cast=int)
    ENABLED: bool = config('SCHEDULER_ENABLED', default=False, cast=bool)
    TIMEZONE: str = config('SCHEDULER_TIMEZONE', default='America/Sao_Paulo')
    MAX_WORKERS: int = config('SCHEDULER_MAX_WORKERS', default=3, cast=int)
    
    @classmethod
    def get_max_workers(cls) -> int:
        """Retorna número de workers limitado entre 1 e 10"""
        return max(1, min(10, cls.MAX_WORKERS))


class Config:
    """Classe principal que agrupa todas as configurações"""
    
    telegram = TelegramConfig
    database = DatabaseConfig
    scheduler = SchedulerConfig
    olx = OlxConfig
    facebook = FacebookConfig
    logging = LoggingConfig
    general = GeneralConfig
    
    @classmethod
    def validate_all(cls) -> None:
        """Valida todas as configurações"""
        errors = []
        
        try:
            cls.telegram.validate()
        except ValueError as e:
            errors.append(f"Telegram: {str(e)}")
        
        # Validar banco de dados
        db_path = cls.database.get_full_path()
        if not db_path.parent.exists():
            errors.append(f"Diretório do banco de dados não existe: {db_path.parent}")
        
        # Validar arquivo de log
        log_path = cls.logging.get_log_path()
        if not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Não foi possível criar diretório de logs: {str(e)}")
        
        if errors:
            raise ValueError(f"Erros de configuração encontrados:\n" + "\n".join(f"- {e}" for e in errors))
    
    @classmethod
    def display_config(cls) -> str:
        """Retorna uma string com as configurações (sem dados sensíveis)"""
        lines = [
            f"=== {cls.general.PROJECT_NAME} v{cls.general.PROJECT_VERSION} ===",
            "",
            "Telegram:",
            f"  - Habilitado: {cls.telegram.ENABLED}",
            f"  - Configurado: {cls.telegram.is_configured()}",
            f"  - Delay: {cls.telegram.DELAY}s",
            "",
            "Scheduler:",
            f"  - Habilitado: {cls.scheduler.ENABLED}",
            f"  - Intervalo: {cls.scheduler.INTERVAL} minutos",
            f"  - Max Workers: {cls.scheduler.get_max_workers()}",
            f"  - Timezone: {cls.scheduler.TIMEZONE}",
            "",
            "Banco de Dados:",
            f"  - Caminho: {cls.database.get_full_path()}",
            "",
            "OLX:",
            f"  - Estados: {', '.join(cls.olx.ESTADOS)}",
            f"  - Categoria Padrão: {cls.olx.CATEGORIA_PADRAO}",
            f"  - Delay: {cls.olx.REQUEST_DELAY}s",
            "",
            "Facebook:",
            f"  - Cidade Padrão: {cls.facebook.CIDADE_PADRAO}",
            f"  - Usar Cookies: {cls.facebook.USE_COOKIES}",
            f"  - Credenciais Configuradas: {cls.facebook.has_credentials()}",
            "",
            "Logging:",
            f"  - Nível: {cls.logging.LEVEL}",
            f"  - Diretório: {cls.logging.get_log_dir()}",
            f"  - Arquivo Atual: {cls.logging.get_log_path().name}",
            f"  - Rotação: {cls.logging.ROTATION}",
            f"  - Retenção: {cls.logging.RETENTION_DAYS} dias",
            f"  - Compressão: {cls.logging.COMPRESSION}",
            "",
            "Geral:",
            f"  - Auto Run: {cls.general.AUTO_RUN}",
            f"  - Intervalo: {cls.general.AUTO_RUN_INTERVAL} minutos",
        ]
        
        return "\n".join(lines)


# Instância global de configuração
config_instance = Config()


if __name__ == "__main__":
    # Teste de configuração
    print(Config.display_config())
    print("\nValidando configurações...")
    try:
        Config.validate_all()
        print("✅ Todas as configurações estão válidas!")
    except ValueError as e:
        print(f"❌ Erros encontrados:\n{e}")
