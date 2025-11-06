"""
Migração 001: Adicionar campos de origem e notificação ao banco de dados

Esta migração adiciona os seguintes campos à tabela 'anuncios':
- origem: Identifica a origem do anúncio (facebook, olx)
- categoria: Categoria do anúncio
- enviado_telegram: Flag indicando se notificação foi enviada
- data_envio_telegram: Data/hora do envio da notificação
- data_publicacao: Data de publicação do anúncio

Também atualiza registros existentes para marcar origem='facebook'
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Tuple

from src.core.config import Config
from src.core.utils.logger import logger


class Migration001:
    """Migração para adicionar suporte a múltiplas origens e notificações"""
    
    VERSION = "001"
    NAME = "add_origem_fields"
    DESCRIPTION = "Adiciona campos de origem e notificação"
    
    def __init__(self, db_path: str = None):
        """
        Inicializa a migração
        
        Args:
            db_path: Caminho do banco de dados (opcional, usa config.py se não especificado)
        """
        self.db_path = db_path or Config.database.get_connection_string()
        self.backup_path = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Cria conexão com o banco de dados"""
        return sqlite3.connect(self.db_path)
    
    def _create_backup(self) -> str:
        """
        Cria backup do banco de dados antes da migração
        
        Returns:
            Caminho do arquivo de backup
        """
        db_file = Path(self.db_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = db_file.parent / f"{db_file.stem}_backup_{timestamp}{db_file.suffix}"
        
        logger.info(f"Criando backup do banco: {backup_file}")
        
        # Copiar banco de dados
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        self.backup_path = str(backup_file)
        logger.success(f"Backup criado: {backup_file}")
        return str(backup_file)
    
    def _check_column_exists(self, conn: sqlite3.Connection, table: str, column: str) -> bool:
        """
        Verifica se uma coluna existe na tabela
        
        Args:
            conn: Conexão com o banco
            table: Nome da tabela
            column: Nome da coluna
        
        Returns:
            True se a coluna existe, False caso contrário
        """
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
    
    def check_if_applied(self) -> Tuple[bool, str]:
        """
        Verifica se a migração já foi aplicada
        
        Returns:
            Tupla (is_applied, message)
        """
        try:
            conn = self._get_connection()
            
            # Verificar se a coluna 'origem' já existe
            if self._check_column_exists(conn, 'anuncios', 'origem'):
                conn.close()
                return True, "Migração já foi aplicada (coluna 'origem' existe)"
            
            conn.close()
            return False, "Migração ainda não foi aplicada"
            
        except sqlite3.Error as e:
            return False, f"Erro ao verificar migração: {str(e)}"
    
    def up(self) -> bool:
        """
        Aplica a migração (UP)
        
        Returns:
            True se sucesso, False se falha
        """
        logger.info(f"Iniciando migração {self.VERSION}: {self.NAME}")
        
        # Verificar se já foi aplicada
        is_applied, message = self.check_if_applied()
        if is_applied:
            logger.warning(message)
            return True
        
        try:
            # Criar backup
            self._create_backup()
            
            # Conectar ao banco
            conn = self._get_connection()
            cursor = conn.cursor()
            
            logger.info("Adicionando novas colunas...")
            
            # Adicionar coluna 'origem'
            if not self._check_column_exists(conn, 'anuncios', 'origem'):
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN origem TEXT DEFAULT 'facebook'
                """)
                logger.success("✅ Coluna 'origem' adicionada")
            
            # Adicionar coluna 'categoria'
            if not self._check_column_exists(conn, 'anuncios', 'categoria'):
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN categoria TEXT
                """)
                logger.success("✅ Coluna 'categoria' adicionada")
            
            # Adicionar coluna 'enviado_telegram'
            if not self._check_column_exists(conn, 'anuncios', 'enviado_telegram'):
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN enviado_telegram INTEGER DEFAULT 0
                """)
                logger.success("✅ Coluna 'enviado_telegram' adicionada")
            
            # Adicionar coluna 'data_envio_telegram'
            if not self._check_column_exists(conn, 'anuncios', 'data_envio_telegram'):
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN data_envio_telegram TEXT
                """)
                logger.success("✅ Coluna 'data_envio_telegram' adicionada")
            
            # Adicionar coluna 'data_publicacao'
            if not self._check_column_exists(conn, 'anuncios', 'data_publicacao'):
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN data_publicacao TEXT
                """)
                logger.success("✅ Coluna 'data_publicacao' adicionada")
            
            # Atualizar registros existentes com origem='facebook'
            logger.info("Atualizando registros existentes...")
            cursor.execute("""
                UPDATE anuncios 
                SET origem = 'facebook' 
                WHERE origem IS NULL OR origem = ''
            """)
            rows_updated = cursor.rowcount
            logger.success(f"✅ {rows_updated} registros atualizados com origem='facebook'")
            
            # Criar índices para melhorar performance
            logger.info("Criando índices...")
            
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_origem ON anuncios(origem)")
                logger.success("✅ Índice 'idx_origem' criado")
            except sqlite3.Error as e:
                logger.warning(f"Índice 'idx_origem' já existe ou erro: {e}")
            
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_enviado_telegram ON anuncios(enviado_telegram)")
                logger.success("✅ Índice 'idx_enviado_telegram' criado")
            except sqlite3.Error as e:
                logger.warning(f"Índice 'idx_enviado_telegram' já existe ou erro: {e}")
            
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_publicacao ON anuncios(data_publicacao)")
                logger.success("✅ Índice 'idx_data_publicacao' criado")
            except sqlite3.Error as e:
                logger.warning(f"Índice 'idx_data_publicacao' já existe ou erro: {e}")
            
            # Commit e fechar
            conn.commit()
            conn.close()
            
            logger.success(f"Migração {self.VERSION} aplicada com sucesso!")
            logger.info(f"Backup salvo em: {self.backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar migração: {str(e)}", exc_info=True)
            logger.error("A migração falhou. Você pode restaurar o backup se necessário.")
            if self.backup_path:
                logger.info(f"Arquivo de backup: {self.backup_path}")
            return False
    
    def down(self) -> bool:
        """
        Reverte a migração (DOWN)
        
        ATENÇÃO: SQLite não suporta DROP COLUMN facilmente.
        Esta operação requer recriar a tabela sem as colunas.
        Use o backup para reverter se necessário.
        
        Returns:
            False (não implementado)
        """
        logger.warning("Reversão de migração não implementada para SQLite")
        logger.info("Para reverter, restaure o backup do banco de dados")
        if self.backup_path:
            logger.info(f"Arquivo de backup: {self.backup_path}")
        return False


def run_migration(db_path: str = None) -> bool:
    """
    Executa a migração
    
    Args:
        db_path: Caminho do banco de dados (opcional)
    
    Returns:
        True se sucesso, False se falha
    """
    migration = Migration001(db_path)
    return migration.up()


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print(f"Migração {Migration001.VERSION}: {Migration001.NAME}")
    print(f"Descrição: {Migration001.DESCRIPTION}")
    print("="*60)
    print()
    
    # Verificar se já foi aplicada
    migration = Migration001()
    is_applied, message = migration.check_if_applied()
    
    print(f"Status: {message}")
    print()
    
    if is_applied:
        print("A migração já foi aplicada. Nada a fazer.")
        sys.exit(0)
    
    # Confirmar antes de aplicar
    response = input("Deseja aplicar esta migração? (s/N): ").strip().lower()
    
    if response in ['s', 'sim', 'y', 'yes']:
        print()
        success = migration.up()
        
        if success:
            print()
            print("="*60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            sys.exit(0)
        else:
            print()
            print("="*60)
            print("❌ MIGRAÇÃO FALHOU!")
            print("="*60)
            sys.exit(1)
    else:
        print("Migração cancelada pelo usuário.")
        sys.exit(0)
