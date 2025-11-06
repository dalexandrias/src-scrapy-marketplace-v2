"""
Utilitário para gerenciamento de logs.
Fornece funções para limpar, listar e comprimir logs antigos.
"""

import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger

from src.core.config import Config


class LogManager:
    """Gerenciador de arquivos de log"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de logs
        
        Args:
            log_dir: Diretório de logs (usa Config se não especificado)
        """
        self.log_dir = log_dir or Config.logging.get_log_dir()
        self.log_prefix = Config.logging.FILE_PREFIX
        self.retention_days = Config.logging.RETENTION_DAYS
    
    def list_log_files(self, include_compressed: bool = True) -> List[Path]:
        """
        Lista todos os arquivos de log
        
        Args:
            include_compressed: Incluir arquivos comprimidos (.zip, .gz)
        
        Returns:
            Lista de caminhos dos arquivos de log
        """
        if not self.log_dir.exists():
            return []
        
        patterns = [f"{self.log_prefix}*.log"]
        if include_compressed:
            patterns.extend([f"{self.log_prefix}*.log.zip", f"{self.log_prefix}*.log.gz"])
        
        log_files = []
        for pattern in patterns:
            log_files.extend(self.log_dir.glob(pattern))
        
        return sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)
    
    def get_log_info(self) -> Dict:
        """
        Obtém informações sobre os logs
        
        Returns:
            Dicionário com estatísticas dos logs
        """
        log_files = self.list_log_files()
        
        total_size = sum(f.stat().st_size for f in log_files)
        total_files = len(log_files)
        
        compressed = [f for f in log_files if f.suffix in ['.zip', '.gz']]
        uncompressed = [f for f in log_files if f.suffix == '.log']
        
        oldest_file = min(log_files, key=lambda p: p.stat().st_mtime) if log_files else None
        newest_file = max(log_files, key=lambda p: p.stat().st_mtime) if log_files else None
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'compressed': len(compressed),
            'uncompressed': len(uncompressed),
            'oldest_file': oldest_file.name if oldest_file else None,
            'newest_file': newest_file.name if newest_file else None,
            'log_dir': str(self.log_dir),
            'retention_days': self.retention_days
        }
    
    def clean_old_logs(self, days: Optional[int] = None, dry_run: bool = False) -> List[Path]:
        """
        Remove logs mais antigos que X dias
        
        Args:
            days: Número de dias (usa Config se não especificado)
            dry_run: Se True, apenas lista arquivos sem deletar
        
        Returns:
            Lista de arquivos deletados (ou que seriam deletados em dry_run)
        """
        days = days or self.retention_days
        cutoff_date = datetime.now() - timedelta(days=days)
        
        log_files = self.list_log_files()
        to_delete = []
        
        for log_file in log_files:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                to_delete.append(log_file)
        
        if not dry_run:
            for log_file in to_delete:
                try:
                    log_file.unlink()
                    logger.info(f"Log deletado: {log_file.name}")
                except Exception as e:
                    logger.error(f"Erro ao deletar {log_file.name}: {e}")
        else:
            logger.info(f"[DRY RUN] {len(to_delete)} arquivos seriam deletados")
            for log_file in to_delete:
                logger.info(f"  - {log_file.name}")
        
        return to_delete
    
    def compress_old_logs(self, days: int = 7, dry_run: bool = False) -> List[Path]:
        """
        Comprime logs não comprimidos mais antigos que X dias
        
        Args:
            days: Logs com mais de X dias serão comprimidos
            dry_run: Se True, apenas lista arquivos sem comprimir
        
        Returns:
            Lista de arquivos comprimidos (ou que seriam comprimidos)
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = [f for f in self.list_log_files(include_compressed=False) if f.suffix == '.log']
        
        to_compress = []
        
        for log_file in log_files:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                to_compress.append(log_file)
        
        if not dry_run:
            for log_file in to_compress:
                try:
                    compressed_path = log_file.with_suffix('.log.gz')
                    
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    log_file.unlink()
                    logger.info(f"Log comprimido: {log_file.name} -> {compressed_path.name}")
                except Exception as e:
                    logger.error(f"Erro ao comprimir {log_file.name}: {e}")
        else:
            logger.info(f"[DRY RUN] {len(to_compress)} arquivos seriam comprimidos")
            for log_file in to_compress:
                logger.info(f"  - {log_file.name}")
        
        return to_compress
    
    def cleanup(self, dry_run: bool = False) -> Dict:
        """
        Executa limpeza completa: comprime logs antigos e remove muito antigos
        
        Args:
            dry_run: Se True, apenas simula sem fazer alterações
        
        Returns:
            Dicionário com resultados da limpeza
        """
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Iniciando limpeza de logs...")
        
        # Comprimir logs com mais de 7 dias
        compressed = self.compress_old_logs(days=7, dry_run=dry_run)
        
        # Deletar logs com mais de X dias (configurado)
        deleted = self.clean_old_logs(dry_run=dry_run)
        
        result = {
            'compressed': len(compressed),
            'deleted': len(deleted),
            'dry_run': dry_run
        }
        
        logger.success(f"{'[DRY RUN] ' if dry_run else ''}Limpeza concluída: "
                      f"{result['compressed']} comprimidos, {result['deleted']} deletados")
        
        return result
    
    def display_logs_summary(self) -> str:
        """
        Retorna um resumo dos logs em formato texto
        
        Returns:
            String formatada com resumo dos logs
        """
        info = self.get_log_info()
        
        lines = [
            "=" * 60,
            "RESUMO DOS LOGS",
            "=" * 60,
            f"Diretório: {info['log_dir']}",
            f"Retenção configurada: {info['retention_days']} dias",
            "",
            f"Total de arquivos: {info['total_files']}",
            f"Tamanho total: {info['total_size_mb']} MB",
            f"  - Não comprimidos: {info['uncompressed']}",
            f"  - Comprimidos: {info['compressed']}",
            "",
            f"Arquivo mais antigo: {info['oldest_file'] or 'N/A'}",
            f"Arquivo mais recente: {info['newest_file'] or 'N/A'}",
            "=" * 60,
        ]
        
        return "\n".join(lines)


def cleanup_logs(dry_run: bool = False) -> None:
    """
    Função auxiliar para executar limpeza de logs
    
    Args:
        dry_run: Se True, apenas simula sem fazer alterações
    """
    manager = LogManager()
    manager.cleanup(dry_run=dry_run)


if __name__ == "__main__":
    # Teste do gerenciador de logs
    manager = LogManager()
    
    print(manager.display_logs_summary())
    
    print("\nTestando limpeza (dry-run)...")
    result = manager.cleanup(dry_run=True)
    print(f"\nResultado: {result}")
