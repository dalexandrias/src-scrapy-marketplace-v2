#!/usr/bin/env python
"""
Script para executar migrações do banco de dados

Uso:
    python scripts/migrate_database.py
    python scripts/migrate_database.py --check
    python scripts/migrate_database.py --migration 001
"""

import sys
from pathlib import Path
import argparse

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from migrations.migration_001_add_origem_fields import Migration001
from utils.logger import logger


MIGRATIONS = [
    Migration001,
]


def listar_migrations():
    """Lista todas as migrações disponíveis"""
    logger.info("="*60)
    logger.info("📋 MIGRAÇÕES DISPONÍVEIS")
    logger.info("="*60)
    
    for migration_class in MIGRATIONS:
        migration = migration_class()
        is_applied, message = migration.check_if_applied()
        
        status = "✅ Aplicada" if is_applied else "⏳ Pendente"
        
        logger.info(f"\n{migration.VERSION}: {migration.NAME}")
        logger.info(f"  Descrição: {migration.DESCRIPTION}")
        logger.info(f"  Status: {status}")
    
    logger.info("\n" + "="*60)


def executar_migration(version=None):
    """
    Executa uma migração específica ou todas pendentes
    
    Args:
        version: Versão específica da migração (ex: "001") ou None para todas
    """
    migrations_a_executar = []
    
    if version:
        # Buscar migração específica
        for migration_class in MIGRATIONS:
            if migration_class.VERSION == version:
                migrations_a_executar.append(migration_class)
                break
        
        if not migrations_a_executar:
            logger.error(f"❌ Migração {version} não encontrada")
            return False
    else:
        # Executar todas pendentes
        for migration_class in MIGRATIONS:
            migration = migration_class()
            is_applied, _ = migration.check_if_applied()
            
            if not is_applied:
                migrations_a_executar.append(migration_class)
    
    if not migrations_a_executar:
        logger.info("✅ Todas as migrações já foram aplicadas!")
        return True
    
    # Executar migrações
    logger.info(f"Executando {len(migrations_a_executar)} migração(ões)...\n")
    
    sucesso = True
    for migration_class in migrations_a_executar:
        migration = migration_class()
        logger.info(f"Executando {migration.VERSION}: {migration.NAME}")
        
        if not migration.up():
            logger.error(f"❌ Erro ao executar migração {migration.VERSION}")
            sucesso = False
            break
        
        logger.info("")
    
    return sucesso


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Gerencia migrações do banco de dados'
    )
    
    parser.add_argument(
        '--check', '-c',
        action='store_true',
        help='Verifica status das migrações sem executar'
    )
    
    parser.add_argument(
        '--migration', '-m',
        type=str,
        help='Executa uma migração específica (ex: 001)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.check:
            # Apenas listar status
            listar_migrations()
            return 0
        
        # Executar migrações
        logger.info("="*60)
        logger.info("🔄 EXECUTANDO MIGRAÇÕES")
        logger.info("="*60)
        logger.info("")
        
        sucesso = executar_migration(args.migration)
        
        if sucesso:
            logger.success("\n✅ Migrações concluídas com sucesso!")
            return 0
        else:
            logger.error("\n❌ Erro ao executar migrações")
            return 1
        
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
