"""
Gerenciador de Limpeza de Anúncios
Remove anúncios que não aparecem mais nas buscas do marketplace
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.utils.logger import logger


class CleanupManager:
    """Gerenciador de limpeza de anúncios expirados/removidos"""
    
    def __init__(self):
        self.db_path = Config.database.get_connection_string()
    
    def mark_ads_as_seen(self, urls: List[str], origem: str) -> int:
        """
        Marca anúncios como vistos na última busca
        
        Args:
            urls: Lista de URLs dos anúncios encontrados na busca atual
            origem: Origem dos anúncios (facebook, olx)
        
        Returns:
            Número de anúncios marcados
        """
        if not urls:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Atualizar campo ultima_visualizacao para os anúncios encontrados
            placeholders = ','.join('?' * len(urls))
            cursor.execute(f"""
                UPDATE anuncios 
                SET ultima_visualizacao = CURRENT_TIMESTAMP
                WHERE url IN ({placeholders})
                AND origem = ?
            """, (*urls, origem))
            
            updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.debug(f"Marcados {updated} anúncios de {origem} como vistos")
            return updated
            
        except Exception as e:
            logger.error(f"Erro ao marcar anúncios como vistos: {e}")
            return 0
    
    def remove_expired_ads(self, origem: str = None, days_threshold: int = 7) -> Dict[str, int]:
        """
        Remove anúncios que não foram vistos nas últimas N buscas
        
        Args:
            origem: Filtrar por origem (facebook, olx) ou None para todas
            days_threshold: Número de dias sem ser visto para considerar expirado
        
        Returns:
            Dict com estatísticas da limpeza
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Primeiro, verificar quantos anúncios serão removidos
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            where_clause = "WHERE (ultima_visualizacao IS NULL OR ultima_visualizacao < ?)"
            params = [threshold_date.strftime("%Y-%m-%d %H:%M:%S")]
            
            if origem:
                where_clause += " AND origem = ?"
                params.append(origem)
            
            # Contar anúncios a serem removidos
            cursor.execute(f"""
                SELECT COUNT(*), origem
                FROM anuncios
                {where_clause}
                GROUP BY origem
            """, params)
            
            stats_before = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Buscar IDs e URLs dos anúncios que serão removidos (para log)
            cursor.execute(f"""
                SELECT id, url, titulo, origem
                FROM anuncios
                {where_clause}
                LIMIT 100
            """, params)
            
            removed_ads = cursor.fetchall()
            
            # Remover anúncios expirados
            cursor.execute(f"""
                DELETE FROM anuncios
                {where_clause}
            """, params)
            
            total_removed = cursor.rowcount
            conn.commit()
            
            # Log dos anúncios removidos
            if removed_ads:
                logger.info(f"🗑️ Removidos {total_removed} anúncios expirados (não vistos há {days_threshold} dias)")
                for ad_id, url, titulo, ad_origem in removed_ads[:10]:  # Mostrar apenas 10 primeiros
                    logger.debug(f"  [{ad_origem.upper()}] {titulo[:50]}... - {url}")
                
                if len(removed_ads) > 10:
                    logger.debug(f"  ... e mais {len(removed_ads) - 10} anúncios")
            
            conn.close()
            
            return {
                'total_removed': total_removed,
                'by_origin': stats_before,
                'days_threshold': days_threshold
            }
            
        except Exception as e:
            logger.error(f"Erro ao remover anúncios expirados: {e}")
            return {
                'total_removed': 0,
                'by_origin': {},
                'days_threshold': days_threshold,
                'error': str(e)
            }
    
    def cleanup_old_ads(self, keep_days: int = 30) -> Dict[str, int]:
        """
        Remove anúncios muito antigos (baseado em data_coleta)
        
        Args:
            keep_days: Manter apenas anúncios dos últimos N dias
        
        Returns:
            Dict com estatísticas da limpeza
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            threshold_date = datetime.now() - timedelta(days=keep_days)
            
            # Contar anúncios a serem removidos
            cursor.execute("""
                SELECT COUNT(*), origem
                FROM anuncios
                WHERE data_coleta < ?
                GROUP BY origem
            """, (threshold_date.strftime("%Y-%m-%d %H:%M:%S"),))
            
            stats_before = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Remover anúncios antigos
            cursor.execute("""
                DELETE FROM anuncios
                WHERE data_coleta < ?
            """, (threshold_date.strftime("%Y-%m-%d %H:%M:%S"),))
            
            total_removed = cursor.rowcount
            conn.commit()
            conn.close()
            
            if total_removed > 0:
                logger.info(f"🗑️ Removidos {total_removed} anúncios com mais de {keep_days} dias")
            
            return {
                'total_removed': total_removed,
                'by_origin': stats_before,
                'keep_days': keep_days
            }
            
        except Exception as e:
            logger.error(f"Erro ao remover anúncios antigos: {e}")
            return {
                'total_removed': 0,
                'by_origin': {},
                'keep_days': keep_days,
                'error': str(e)
            }
    
    def get_cleanup_stats(self) -> Dict:
        """
        Obtém estatísticas sobre anúncios que podem ser limpos
        
        Returns:
            Dict com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de anúncios
            cursor.execute("SELECT COUNT(*) FROM anuncios")
            total_ads = cursor.fetchone()[0]
            
            # Anúncios nunca vistos
            cursor.execute("SELECT COUNT(*) FROM anuncios WHERE ultima_visualizacao IS NULL")
            never_seen = cursor.fetchone()[0]
            
            # Anúncios não vistos há 7 dias
            threshold_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT COUNT(*) FROM anuncios 
                WHERE ultima_visualizacao < ? OR ultima_visualizacao IS NULL
            """, (threshold_7d,))
            not_seen_7d = cursor.fetchone()[0]
            
            # Anúncios não vistos há 30 dias
            threshold_30d = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                SELECT COUNT(*) FROM anuncios 
                WHERE ultima_visualizacao < ? OR ultima_visualizacao IS NULL
            """, (threshold_30d,))
            not_seen_30d = cursor.fetchone()[0]
            
            # Anúncios por origem
            cursor.execute("""
                SELECT origem, COUNT(*) 
                FROM anuncios 
                GROUP BY origem
            """)
            by_origin = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'total_ads': total_ads,
                'never_seen': never_seen,
                'not_seen_7_days': not_seen_7d,
                'not_seen_30_days': not_seen_30d,
                'by_origin': by_origin
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de limpeza: {e}")
            return {}
    
    def add_last_seen_column(self) -> bool:
        """
        Adiciona coluna ultima_visualizacao se não existir
        
        Returns:
            True se sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se coluna já existe
            cursor.execute("PRAGMA table_info(anuncios)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'ultima_visualizacao' not in columns:
                logger.info("Adicionando coluna 'ultima_visualizacao' à tabela anuncios...")
                cursor.execute("""
                    ALTER TABLE anuncios 
                    ADD COLUMN ultima_visualizacao TIMESTAMP
                """)
                
                # Criar índice para performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ultima_visualizacao 
                    ON anuncios(ultima_visualizacao)
                """)
                
                conn.commit()
                logger.success("✅ Coluna 'ultima_visualizacao' adicionada com sucesso")
            else:
                logger.debug("Coluna 'ultima_visualizacao' já existe")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar coluna ultima_visualizacao: {e}")
            return False
