#!/usr/bin/env python
"""
Script para exportar anúncios do banco de dados para CSV ou JSON

Uso:
    python scripts/export_anuncios.py --formato csv
    python scripts/export_anuncios.py --formato json --origem olx
    python scripts/export_anuncios.py --formato csv --palavra-chave "honda cg"
    python scripts/export_anuncios.py --formato csv --output meus_anuncios.csv
"""

import sys
from pathlib import Path
import argparse
import sqlite3
import json
import csv
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from utils.logger import logger


def exportar_csv(dados, arquivo_saida):
    """
    Exporta dados para CSV
    
    Args:
        dados: Lista de dicionários com os dados
        arquivo_saida: Caminho do arquivo de saída
    """
    if not dados:
        logger.warning("Nenhum dado para exportar")
        return
    
    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        # Usar as chaves do primeiro registro como cabeçalho
        fieldnames = dados[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(dados)
    
    logger.success(f"✅ Dados exportados para: {arquivo_saida}")


def exportar_json(dados, arquivo_saida):
    """
    Exporta dados para JSON
    
    Args:
        dados: Lista de dicionários com os dados
        arquivo_saida: Caminho do arquivo de saída
    """
    if not dados:
        logger.warning("Nenhum dado para exportar")
        return
    
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    
    logger.success(f"✅ Dados exportados para: {arquivo_saida}")


def buscar_anuncios(origem=None, palavra_chave=None, limite=None):
    """
    Busca anúncios no banco de dados
    
    Args:
        origem: Filtrar por origem (facebook, olx)
        palavra_chave: Filtrar por palavra-chave
        limite: Limite de registros
    
    Returns:
        Lista de dicionários com os dados
    """
    db_path = Config.database.get_connection_string()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    cursor = conn.cursor()
    
    # Construir query
    query = "SELECT * FROM anuncios WHERE 1=1"
    params = []
    
    if origem:
        query += " AND origem = ?"
        params.append(origem)
    
    if palavra_chave:
        query += " AND palavra_chave LIKE ?"
        params.append(f"%{palavra_chave}%")
    
    query += " ORDER BY data_coleta DESC"
    
    if limite:
        query += f" LIMIT {limite}"
    
    # Executar query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Converter para lista de dicionários
    dados = [dict(row) for row in rows]
    
    conn.close()
    
    return dados


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Exporta anúncios do banco de dados para CSV ou JSON'
    )
    
    parser.add_argument(
        '--formato', '-f',
        type=str,
        choices=['csv', 'json'],
        default='csv',
        help='Formato de exportação (csv ou json). Padrão: csv'
    )
    
    parser.add_argument(
        '--origem', '-o',
        type=str,
        choices=['facebook', 'olx'],
        help='Filtrar por origem (facebook ou olx)'
    )
    
    parser.add_argument(
        '--palavra-chave', '-p',
        type=str,
        help='Filtrar por palavra-chave'
    )
    
    parser.add_argument(
        '--limite', '-l',
        type=int,
        help='Limite de registros a exportar'
    )
    
    parser.add_argument(
        '--output', '-out',
        type=str,
        help='Arquivo de saída (padrão: anuncios_YYYYMMDD_HHMMSS.csv/json)'
    )
    
    args = parser.parse_args()
    
    try:
        logger.info("="*60)
        logger.info("📊 EXPORTAÇÃO DE ANÚNCIOS")
        logger.info("="*60)
        
        # Buscar dados
        logger.info("Buscando anúncios no banco de dados...")
        dados = buscar_anuncios(
            origem=args.origem,
            palavra_chave=args.palavra_chave,
            limite=args.limite
        )
        
        if not dados:
            logger.warning("Nenhum anúncio encontrado com os filtros especificados")
            return 0
        
        logger.info(f"Total de anúncios encontrados: {len(dados)}")
        
        # Determinar arquivo de saída
        if args.output:
            arquivo_saida = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extensao = args.formato
            arquivo_saida = f"anuncios_{timestamp}.{extensao}"
        
        # Exportar
        logger.info(f"Exportando para {args.formato.upper()}...")
        
        if args.formato == 'csv':
            exportar_csv(dados, arquivo_saida)
        else:
            exportar_json(dados, arquivo_saida)
        
        # Resumo
        logger.info("")
        logger.info("="*60)
        logger.info("📋 RESUMO DA EXPORTAÇÃO")
        logger.info("="*60)
        logger.info(f"Registros exportados: {len(dados)}")
        logger.info(f"Formato: {args.formato.upper()}")
        logger.info(f"Arquivo: {arquivo_saida}")
        if args.origem:
            logger.info(f"Origem filtrada: {args.origem}")
        if args.palavra_chave:
            logger.info(f"Palavra-chave: {args.palavra_chave}")
        logger.info("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar anúncios: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
