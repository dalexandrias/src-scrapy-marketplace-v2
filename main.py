"""
Script Principal - Entry Point do Container Docker
Inicializa todos os componentes do sistema de scraping automatizado
"""

import sys
import signal
import asyncio
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.utils.logger import logger
from src.core.utils.log_manager import LogManager
from src.core.config import Config
from src.bot.telegram_bot import TelegramBot
from src.managers.scheduler_manager import SchedulerManager
from src.managers.credentials_manager import CredentialsManager
from src.managers.keywords_manager import KeywordsManager


class ScraperApplication:
    """Aplicação principal do scraper automatizado"""
    
    def __init__(self):
        self.bot = None
        self.scheduler = None
        self.running = False
    
    def _run_migrations(self) -> bool:
        """
        Executa migrações necessárias no banco de dados existente
        
        Returns:
            True se migrações foram aplicadas com sucesso
        """
        import sqlite3
        
        db_path = Config.database.get_connection_string()
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Função auxiliar para verificar se coluna existe
            def column_exists(table: str, column: str) -> bool:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                return column in columns
            
            # Função auxiliar para verificar se tabela existe
            def table_exists(table: str) -> bool:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                return cursor.fetchone() is not None
            
            changes_made = False
            
            # 1. Verificar/adicionar colunas na tabela anuncios
            if table_exists('anuncios'):
                if not column_exists('anuncios', 'origem'):
                    logger.info("Adicionando coluna 'origem' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN origem TEXT DEFAULT 'facebook'")
                    changes_made = True
                
                if not column_exists('anuncios', 'categoria'):
                    logger.info("Adicionando coluna 'categoria' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN categoria TEXT")
                    changes_made = True
                
                if not column_exists('anuncios', 'data_publicacao'):
                    logger.info("Adicionando coluna 'data_publicacao' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN data_publicacao TEXT")
                    changes_made = True
                
                if not column_exists('anuncios', 'enviado_telegram'):
                    logger.info("Adicionando coluna 'enviado_telegram' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN enviado_telegram INTEGER DEFAULT 0")
                    changes_made = True
                
                if not column_exists('anuncios', 'data_envio_telegram'):
                    logger.info("Adicionando coluna 'data_envio_telegram' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN data_envio_telegram TEXT")
                    changes_made = True
                
                if not column_exists('anuncios', 'ultima_visualizacao'):
                    logger.info("Adicionando coluna 'ultima_visualizacao' à tabela anuncios...")
                    cursor.execute("ALTER TABLE anuncios ADD COLUMN ultima_visualizacao TIMESTAMP")
                    changes_made = True
            
            # 2. Criar tabela credentials se não existir
            if not table_exists('credentials'):
                logger.info("Criando tabela 'credentials'...")
                cursor.execute('''
                    CREATE TABLE credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service TEXT NOT NULL,
                        username TEXT NOT NULL,
                        encrypted_password TEXT NOT NULL,
                        encryption_key TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(service, username)
                    )
                ''')
                changes_made = True
            
            # 3. Criar tabela palavras_chave se não existir
            if not table_exists('palavras_chave'):
                logger.info("Criando tabela 'palavras_chave'...")
                cursor.execute('''
                    CREATE TABLE palavras_chave (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        palavra TEXT NOT NULL,
                        origem TEXT NOT NULL CHECK(origem IN ('facebook', 'olx', 'ambos')),
                        prioridade INTEGER DEFAULT 1,
                        ativo INTEGER DEFAULT 1,
                        total_encontrados INTEGER DEFAULT 0,
                        ultima_busca TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(palavra, origem)
                    )
                ''')
                changes_made = True
            
            # 4. Criar tabela scheduler_config se não existir
            if not table_exists('scheduler_config'):
                logger.info("Criando tabela 'scheduler_config'...")
                cursor.execute('''
                    CREATE TABLE scheduler_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        interval_minutes INTEGER NOT NULL DEFAULT 30,
                        enabled INTEGER DEFAULT 1,
                        last_run TIMESTAMP,
                        next_run TIMESTAMP,
                        total_runs INTEGER DEFAULT 0,
                        total_errors INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute("INSERT INTO scheduler_config (interval_minutes, enabled) VALUES (30, 0)")
                changes_made = True
            
            # 5. Criar tabela execution_logs se não existir
            if not table_exists('execution_logs'):
                logger.info("Criando tabela 'execution_logs'...")
                cursor.execute('''
                    CREATE TABLE execution_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT NOT NULL CHECK(tipo IN ('facebook', 'olx', 'manual', 'scheduled')),
                        palavra_chave TEXT,
                        status TEXT NOT NULL CHECK(status IN ('success', 'error', 'running')),
                        total_encontrados INTEGER DEFAULT 0,
                        total_novos INTEGER DEFAULT 0,
                        mensagem TEXT,
                        duracao_segundos REAL,
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        finished_at TIMESTAMP
                    )
                ''')
                changes_made = True
            
            # 6. Criar índices se não existirem
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_url ON anuncios(url)",
                "CREATE INDEX IF NOT EXISTS idx_palavra_chave ON anuncios(palavra_chave)",
                "CREATE INDEX IF NOT EXISTS idx_origem ON anuncios(origem)",
                "CREATE INDEX IF NOT EXISTS idx_enviado_telegram ON anuncios(enviado_telegram)",
                "CREATE INDEX IF NOT EXISTS idx_data_publicacao ON anuncios(data_publicacao)",
                "CREATE INDEX IF NOT EXISTS idx_ultima_visualizacao ON anuncios(ultima_visualizacao)",
                "CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service)",
                "CREATE INDEX IF NOT EXISTS idx_credentials_active ON credentials(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_palavras_ativo ON palavras_chave(ativo)",
                "CREATE INDEX IF NOT EXISTS idx_palavras_origem ON palavras_chave(origem)",
                "CREATE INDEX IF NOT EXISTS idx_palavras_prioridade ON palavras_chave(prioridade DESC)",
                "CREATE INDEX IF NOT EXISTS idx_logs_tipo ON execution_logs(tipo)",
                "CREATE INDEX IF NOT EXISTS idx_logs_status ON execution_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_logs_started_at ON execution_logs(started_at DESC)",
            ]
            
            for index_sql in indices:
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            if changes_made:
                logger.success("✅ Migrações aplicadas com sucesso")
            else:
                logger.debug("✓ Banco de dados já está atualizado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao executar migrações: {e}")
            return False
    
    def _initialize_database(self) -> bool:
        """
        Inicializa o banco de dados se não existir
        
        Returns:
            True se banco foi criado/já existe com sucesso
        """
        import sqlite3
        
        db_path = Config.database.get_connection_string()
        db_file = Path(db_path)
        
        # Criar diretório se não existir
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Verificar se banco já existe
        if db_file.exists():
            logger.debug(f"Banco de dados já existe: {db_path}")
            # Executar migrações para garantir que todas as tabelas/colunas existem
            self._run_migrations()
            return True
        
        logger.info(f"🔧 Criando banco de dados: {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Criar tabela principal de anúncios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anuncios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT,
                    descricao TEXT,
                    preco TEXT,
                    localizacao TEXT,
                    url TEXT UNIQUE,
                    imagem_url TEXT,
                    vendedor TEXT,
                    palavra_chave TEXT,
                    data_coleta TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    origem TEXT DEFAULT 'facebook',
                    categoria TEXT,
                    data_publicacao TEXT,
                    enviado_telegram INTEGER DEFAULT 0,
                    data_envio_telegram TEXT,
                    ultima_visualizacao TIMESTAMP
                )
            ''')
            
            # Criar tabela de credenciais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    encrypted_password TEXT NOT NULL,
                    encryption_key TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service, username)
                )
            ''')
            
            # Criar tabela de palavras-chave
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS palavras_chave (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    palavra TEXT NOT NULL,
                    origem TEXT NOT NULL CHECK(origem IN ('facebook', 'olx', 'ambos')),
                    prioridade INTEGER DEFAULT 1,
                    ativo INTEGER DEFAULT 1,
                    total_encontrados INTEGER DEFAULT 0,
                    ultima_busca TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(palavra, origem)
                )
            ''')
            
            # Criar tabela de configuração do scheduler
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduler_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interval_minutes INTEGER NOT NULL DEFAULT 30,
                    enabled INTEGER DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    total_runs INTEGER DEFAULT 0,
                    total_errors INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Inserir configuração padrão do scheduler
            cursor.execute('''
                INSERT INTO scheduler_config (interval_minutes, enabled)
                SELECT 30, 1
                WHERE NOT EXISTS (SELECT 1 FROM scheduler_config)
            ''')
            
            # Criar tabela de logs de execução
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL CHECK(tipo IN ('facebook', 'olx', 'manual', 'scheduled')),
                    palavra_chave TEXT,
                    status TEXT NOT NULL CHECK(status IN ('success', 'error', 'running')),
                    total_encontrados INTEGER DEFAULT 0,
                    total_novos INTEGER DEFAULT 0,
                    mensagem TEXT,
                    duracao_segundos REAL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP
                )
            ''')
            
            # Criar índices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON anuncios(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_palavra_chave ON anuncios(palavra_chave)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_origem ON anuncios(origem)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_enviado_telegram ON anuncios(enviado_telegram)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_publicacao ON anuncios(data_publicacao)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_credentials_active ON credentials(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_palavras_ativo ON palavras_chave(ativo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_palavras_origem ON palavras_chave(origem)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_palavras_prioridade ON palavras_chave(prioridade DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_tipo ON execution_logs(tipo)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_status ON execution_logs(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_started_at ON execution_logs(started_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ultima_visualizacao ON anuncios(ultima_visualizacao)')
            
            conn.commit()
            conn.close()
            
            logger.success(f"✅ Banco de dados criado com sucesso: {db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar banco de dados: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """
        Handler para sinais de interrupção (SIGTERM, SIGINT)
        Realiza graceful shutdown
        """
        logger.warning(f"Sinal {signum} recebido. Iniciando shutdown...")
        self.running = False
    
    def _check_dependencies(self) -> bool:
        """
        Verifica dependências necessárias para executar
        
        Returns:
            True se todas as dependências estão OK
        """
        logger.info("🔍 Verificando dependências...")
        
        # Verificar token do Telegram
        if not Config.telegram.BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN não configurado no .env")
            return False
        
        logger.success("✅ Token do Telegram configurado")
        
        # Inicializar banco de dados se não existir
        if not self._initialize_database():
            logger.error("❌ Falha ao inicializar banco de dados")
            return False
        
        logger.success(f"✅ Banco de dados pronto")
        
        return True
    
    def _show_startup_info(self):
        """Exibe informações de inicialização"""
        credentials_manager = CredentialsManager()
        keywords_manager = KeywordsManager()
        
        # Verificar credenciais
        creds = credentials_manager.list_credentials()
        facebook_creds = [c for c in creds if c['service'] == 'facebook' and c['is_active']]
        
        # Verificar palavras-chave
        keywords = keywords_manager.list_keywords(only_active=True)
        
        logger.info("=" * 70)
        logger.info("🤖 SCRAPER DE ANÚNCIOS - SISTEMA AUTOMATIZADO")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📊 STATUS DO SISTEMA:")
        logger.info(f"   🔑 Credenciais Facebook: {'✅ Configurado' if facebook_creds else '❌ Não configurado'}")
        logger.info(f"   🔍 Palavras-chave ativas: {len(keywords)}")
        logger.info(f"   ⏰ Scheduler: Pronto para iniciar")
        logger.info(f"   🤖 Bot Telegram: Pronto para iniciar")
        logger.info("")
        
        if facebook_creds:
            logger.info(f"   Facebook: {facebook_creds[0]['username'][:3]}***{facebook_creds[0]['username'][-4:]}")
        
        if keywords:
            logger.info("   Palavras-chave:")
            for kw in keywords[:5]:  # Mostrar apenas as 5 primeiras
                stars = "⭐" * kw['prioridade']
                logger.info(f"      • {kw['palavra']} ({kw['origem']}) {stars}")
            if len(keywords) > 5:
                logger.info(f"      ... e mais {len(keywords) - 5} palavras")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("")
    
    def _cleanup_old_logs(self):
        """Limpa logs antigos baseado na configuração de retenção"""
        try:
            log_manager = LogManager()
            
            # Obter informações dos logs
            info = log_manager.get_log_info()
            
            logger.info(f"📁 Logs: {info['total_files']} arquivos ({info['total_size_mb']} MB)")
            
            # Executar limpeza se houver mais de 10 arquivos
            if info['total_files'] > 10:
                logger.info("🧹 Executando limpeza de logs antigos...")
                result = log_manager.cleanup(dry_run=False)
                
                if result['compressed'] > 0 or result['deleted'] > 0:
                    logger.success(f"✅ Limpeza concluída: {result['compressed']} comprimidos, {result['deleted']} deletados")
            else:
                logger.debug("Limpeza de logs não necessária")
                
        except Exception as e:
            logger.warning(f"Erro ao limpar logs: {e}")
    
    async def run(self):
        """Executa a aplicação principal"""
        try:
            # Registrar handlers de sinais
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            logger.info("🚀 Iniciando aplicação...")
            
            # Limpar logs antigos na inicialização
            self._cleanup_old_logs()
            
            # Verificar dependências
            if not self._check_dependencies():
                logger.error("❌ Falha na verificação de dependências")
                return 1
            
            # Mostrar informações de inicialização
            self._show_startup_info()
            
            # Inicializar bot do Telegram
            logger.info("🤖 Inicializando Bot do Telegram...")
            self.bot = TelegramBot()
            
            # Iniciar bot em background
            self.running = True
            
            # Criar task para rodar o bot
            bot_task = asyncio.create_task(self.bot.run())
            
            logger.success("✅ Sistema iniciado com sucesso!")
            logger.info("")
            logger.info("💡 DICAS:")
            logger.info("   • Use /help no Telegram para ver todos os comandos")
            logger.info("   • Configure credenciais com /cadastrar_facebook")
            logger.info("   • Adicione palavras-chave com /adicionar_palavra")
            logger.info("   • Configure intervalo com /configurar_intervalo")
            logger.info("   • Inicie o scheduler com /iniciar_scheduler")
            logger.info("")
            logger.info("⏳ Aguardando comandos...")
            
            # Aguardar até ser interrompido
            while self.running:
                await asyncio.sleep(1)
            
            # Shutdown graceful
            logger.info("🛑 Iniciando shutdown graceful...")
            
            # Parar scheduler se estiver rodando
            if self.bot and self.bot.scheduler_manager.is_running():
                logger.info("Parando scheduler...")
                self.bot.scheduler_manager.stop()
            
            # Parar bot
            if self.bot:
                logger.info("Parando bot do Telegram...")
                await self.bot.stop()
            
            logger.success("✅ Shutdown concluído!")
            return 0
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️ Interrompido pelo usuário (Ctrl+C)")
            self.running = False
            
            # Cleanup
            if self.bot:
                await self.bot.stop()
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erro crítico na aplicação: {e}", exc_info=True)
            
            # Cleanup em caso de erro
            if self.bot:
                try:
                    await self.bot.stop()
                except:
                    pass
            
            return 1


def main():
    """Função principal"""
    app = ScraperApplication()
    
    try:
        exit_code = asyncio.run(app.run())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
