"""
Migração 002: Adiciona tabelas para credenciais, palavras-chave e configuração do scheduler

Adiciona:
- Tabela credentials: Armazena credenciais criptografadas (Facebook, OLX)
- Tabela palavras_chave: Gerencia palavras de busca
- Tabela scheduler_config: Configuração do agendamento
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import Config
from src.core.utils.logger import logger


class Migration002:
    """Migração 002: Credenciais, Palavras-chave e Scheduler"""
    
    VERSION = "002"
    NAME = "add_credentials_and_keywords"
    DESCRIPTION = "Adiciona tabelas para credenciais, palavras-chave e scheduler"
    
    def __init__(self):
        self.db_path = Config.database.get_connection_string()
        self.migrations_table = "migrations"
    
    def check_if_applied(self) -> tuple[bool, str]:
        """Verifica se a migração já foi aplicada"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de migrações se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            # Verificar se esta migração já foi aplicada
            cursor.execute(f"""
                SELECT applied_at FROM {self.migrations_table}
                WHERE version = ?
            """, (self.VERSION,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return True, f"Migração aplicada em {result[0]}"
            else:
                return False, "Migração ainda não foi aplicada"
                
        except Exception as e:
            return False, f"Erro ao verificar: {str(e)}"
    
    def _create_backup(self) -> str:
        """Cria backup do banco antes da migração"""
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(self.db_path).parent / f"marketplace_anuncios_backup_{timestamp}.db"
        
        logger.info(f"Criando backup do banco: {backup_path}")
        shutil.copy2(self.db_path, backup_path)
        logger.success(f"Backup criado: {backup_path}")
        
        return str(backup_path)
    
    def up(self) -> bool:
        """Executa a migração"""
        try:
            logger.info(f"Iniciando migração {self.VERSION}: {self.NAME}")
            
            # Criar backup
            backup_path = self._create_backup()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Criar tabela de credenciais
            logger.info("Criando tabela 'credentials'...")
            cursor.execute("""
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
            """)
            logger.success("✅ Tabela 'credentials' criada")
            
            # Índices para credentials
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_credentials_service 
                ON credentials(service)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_credentials_active 
                ON credentials(is_active)
            """)
            
            # 2. Criar tabela de palavras-chave
            logger.info("Criando tabela 'palavras_chave'...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS palavras_chave (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    palavra TEXT NOT NULL,
                    origem TEXT NOT NULL CHECK(origem IN ('facebook', 'olx', 'ambos')),
                    ativo INTEGER DEFAULT 1,
                    prioridade INTEGER DEFAULT 0,
                    total_encontrados INTEGER DEFAULT 0,
                    ultima_busca TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(palavra, origem)
                )
            """)
            logger.success("✅ Tabela 'palavras_chave' criada")
            
            # Índices para palavras_chave
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_palavras_ativo 
                ON palavras_chave(ativo)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_palavras_origem 
                ON palavras_chave(origem)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_palavras_prioridade 
                ON palavras_chave(prioridade DESC)
            """)
            
            # 3. Criar tabela de configuração do scheduler
            logger.info("Criando tabela 'scheduler_config'...")
            cursor.execute("""
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
            """)
            logger.success("✅ Tabela 'scheduler_config' criada")
            
            # Inserir configuração padrão do scheduler
            cursor.execute("""
                INSERT INTO scheduler_config (interval_minutes, enabled)
                SELECT 30, 1
                WHERE NOT EXISTS (SELECT 1 FROM scheduler_config)
            """)
            
            # 4. Criar tabela de logs de execução
            logger.info("Criando tabela 'execution_logs'...")
            cursor.execute("""
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
            """)
            logger.success("✅ Tabela 'execution_logs' criada")
            
            # Índices para execution_logs
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_tipo 
                ON execution_logs(tipo)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_status 
                ON execution_logs(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_started 
                ON execution_logs(started_at DESC)
            """)
            
            # Registrar migração
            cursor.execute(f"""
                INSERT INTO {self.migrations_table} (version, name, applied_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (self.VERSION, self.NAME))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Migração {self.VERSION} aplicada com sucesso!")
            logger.info(f"Backup salvo em: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao executar migração {self.VERSION}: {e}", exc_info=True)
            return False
    
    def down(self) -> bool:
        """Reverte a migração (se necessário)"""
        try:
            logger.warning(f"Revertendo migração {self.VERSION}...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Drop tabelas na ordem inversa
            cursor.execute("DROP TABLE IF EXISTS execution_logs")
            cursor.execute("DROP TABLE IF EXISTS scheduler_config")
            cursor.execute("DROP TABLE IF EXISTS palavras_chave")
            cursor.execute("DROP TABLE IF EXISTS credentials")
            
            # Remover registro da migração
            cursor.execute(f"""
                DELETE FROM {self.migrations_table}
                WHERE version = ?
            """, (self.VERSION,))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Migração {self.VERSION} revertida com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao reverter migração: {e}", exc_info=True)
            return False


if __name__ == "__main__":
    migration = Migration002()
    
    # Verificar status
    is_applied, message = migration.check_if_applied()
    
    print("=" * 60)
    print(f"Migração {migration.VERSION}: {migration.NAME}")
    print(f"Descrição: {migration.DESCRIPTION}")
    print("=" * 60)
    print(f"\nStatus: {message}")
    
    if is_applied:
        print("\n⚠️  Migração já foi aplicada anteriormente")
        sys.exit(0)
    
    # Confirmar execução
    resposta = input("\nDeseja aplicar esta migração? (s/N): ").strip().lower()
    
    if resposta == 's':
        if migration.up():
            print("\n" + "=" * 60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ ERRO AO EXECUTAR MIGRAÇÃO")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\n⚠️  Migração cancelada pelo usuário")
        sys.exit(0)
