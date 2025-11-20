#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para buscar anúncios na OLX usando Playwright
Usa navegador real (Chromium) para contornar anti-bot do Cloudflare

Uso:
    python olx_scraper.py "honda pcx"
    python olx_scraper.py "iphone 13" --estado sp
"""

import argparse
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus

# Adicionar o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.utils.logger import logger
import sqlite3


def get_db_connection():
    """Retorna conexão com banco de dados e garante que tabela existe"""
    # Usar o mesmo banco de dados do sistema principal
    db_path = Path(__file__).parent.parent.parent / 'data' / 'marketplace_anuncios.db'
    conn = sqlite3.connect(db_path)
    
    # A tabela já existe no sistema principal, não precisa criar
    return conn


def buscar_anuncios_olx_playwright(palavra_chave: str, estado: str = 'pr'):
    """
    Busca anúncios na OLX usando Playwright (navegador real)
    
    Args:
        palavra_chave: Termo para buscar
        estado: Estado (pr, sp, rj, etc)
    
    Returns:
        Lista de dicionários com anúncios encontrados
    """
    logger.info(f"Buscando '{palavra_chave}' na OLX (estado: {estado})")
    
    # Construir URL
    palavra_encoded = quote_plus(palavra_chave)
    url = Config.olx.get_search_url(palavra_chave=palavra_chave, estado=estado)
    
    logger.info(f"URL: {url}")
    
    anuncios = []
    
    with sync_playwright() as p:
        # Lançar navegador com otimizações para produção
        logger.info("Abrindo navegador Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',  # Evita problemas de memória compartilhada
                '--disable-gpu',             # Desabilita GPU (não precisa em headless)
                '--no-sandbox',              # Necessário em containers Docker
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
        )
        
        page = context.new_page()
        
        try:
            # Navegar para página de busca
            logger.info("Carregando página da OLX...")
            page.goto(url, wait_until='load', timeout=60000)
            
            # Aguardar JavaScript carregar
            page.wait_for_timeout(3000)
            
            # Pegar HTML completo
            html = page.content()
            
            logger.info(f"Página carregada ({len(html):,} bytes)")
            
            # Extrair __NEXT_DATA__
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', 
                            html, re.DOTALL)
            
            if not match:
                logger.error("Não encontrou __NEXT_DATA__ na página")
                return []
            
            logger.info("__NEXT_DATA__ encontrado, extraindo anúncios...")
            
            # Parse JSON
            try:
                next_data = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar JSON: {e}")
                return []
            
            # Extrair anúncios do JSON
            try:
                ads_data = next_data.get('props', {}).get('pageProps', {}).get('ads', [])
                logger.info(f"Total de anúncios encontrados: {len(ads_data)}")
                
                if not ads_data:
                    logger.warning("Nenhum anúncio no JSON")
                    return []
                
                # Processar cada anúncio
                for ad in ads_data:
                    try:
                        # Extrair dados básicos
                        titulo = ad.get('title', '').strip()
                        preco_raw = ad.get('price', '')
                        localizacao_raw = ad.get('location', '').strip()
                        
                        # Validar campos obrigatórios
                        if not titulo:
                            logger.debug("Anúncio sem título, ignorando")
                            continue
                        
                        # Processar e validar preço
                        preco = str(preco_raw).strip() if preco_raw else ''
                        if not preco or preco.lower() in ['', '0', 'r$ 0', 'não informado', 'n/a']:
                            logger.debug(f"Anúncio '{titulo[:40]}...' sem preço válido, ignorando")
                            continue
                        
                        # Processar e validar localização
                        localizacao = localizacao_raw if localizacao_raw else ''
                        if not localizacao or localizacao.lower() in ['', 'não informado', 'n/a']:
                            logger.debug(f"Anúncio '{titulo[:40]}...' sem localização válida, ignorando")
                            continue
                        
                        # Extrair URL da primeira imagem
                        imagem_url = ''
                        images_list = ad.get('images', [])
                        if images_list and isinstance(images_list, list) and len(images_list) > 0:
                            # Pegar a primeira imagem (original)
                            first_image = images_list[0]
                            if isinstance(first_image, dict):
                                imagem_url = first_image.get('original', '') or first_image.get('originalWebp', '')
                        
                        # Extrair dados do anúncio
                        anuncio = {
                            'id_anuncio': str(ad.get('listId', '')),
                            'titulo': titulo,
                            'preco': preco,
                            'localizacao': localizacao,
                            'data_publicacao': ad.get('date', ''),
                            'url': ad.get('url', '') or ad.get('friendlyUrl', ''),
                            'imagem_url': imagem_url,
                            'categoria': ad.get('category', ''),
                            'palavra_chave': palavra_chave,
                            'origem': 'olx',
                            'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        
                        anuncios.append(anuncio)
                        logger.debug(f"  ✓ {anuncio['titulo'][:60]}... - {anuncio['preco']}")
                        
                    except Exception as e:
                        logger.warning(f"Erro processando anúncio: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Erro extraindo anúncios do JSON: {e}")
                return []
            
        finally:
            browser.close()
    
    logger.info(f"Total processado: {len(anuncios)} anúncios")
    return anuncios


def salvar_anuncios_database(anuncios):
    """Salva anúncios no banco de dados"""
    if not anuncios:
        logger.warning("Nenhum anúncio para salvar")
        return 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    salvos = 0
    duplicados = 0
    
    for anuncio in anuncios:
        try:
            # Verificar se já existe (por URL, que é único)
            cursor.execute(
                "SELECT id FROM anuncios WHERE url = ? AND origem = 'olx'",
                (anuncio['url'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                duplicados += 1
                logger.debug(f"Anúncio duplicado (URL {anuncio['url']}): {anuncio['titulo'][:50]}")
                continue
            
            # Inserir novo anúncio (estrutura da tabela principal do sistema)
            cursor.execute("""
                INSERT INTO anuncios (
                    titulo, preco, localizacao, data_publicacao,
                    url, imagem_url, categoria, palavra_chave, origem, data_coleta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                anuncio['titulo'],
                anuncio['preco'],
                anuncio['localizacao'],
                anuncio['data_publicacao'],
                anuncio['url'],
                anuncio['imagem_url'],
                anuncio['categoria'],
                anuncio['palavra_chave'],
                anuncio['origem'],
                anuncio['data_coleta'],
            ))
            
            salvos += 1
            logger.debug(f"✓ Salvo: {anuncio['titulo'][:50]}")
            
        except Exception as e:
            logger.error(f"Erro salvando anúncio: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    logger.info(f"Salvos: {salvos} novos | Duplicados: {duplicados}")
    return salvos


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Busca anúncios na OLX usando Playwright (navegador real)'
    )
    parser.add_argument('palavra_chave', help='Palavra-chave para buscar')
    parser.add_argument('--estado', default='pr', help='Estado (default: pr)')
    
    args = parser.parse_args()
    
    try:
        # Buscar anúncios
        logger.info("="*60)
        logger.info(f"BUSCA OLX - '{args.palavra_chave}'")
        logger.info("="*60)
        
        anuncios = buscar_anuncios_olx_playwright(
            palavra_chave=args.palavra_chave,
            estado=args.estado
        )
        
        if not anuncios:
            logger.warning("❌ Nenhum anúncio encontrado")
            return 1
        
        # Salvar no banco
        salvos = salvar_anuncios_database(anuncios)
        
        # Extrair URLs dos anúncios
        urls = [anuncio.get('url') for anuncio in anuncios if anuncio.get('url')]
        
        # Imprimir resultado em JSON para o scheduler parsear
        import json
        resultado = {
            'encontrados': len(anuncios),
            'salvos': salvos,
            'duplicados': len(anuncios) - salvos,
            'palavra_chave': args.palavra_chave,
            'urls': urls
        }
        print(f"RESULT_JSON:{json.dumps(resultado)}")
        
        logger.info("="*60)
        logger.info(f"✅ CONCLUÍDO")
        logger.info(f"   Encontrados: {len(anuncios)}")
        logger.info(f"   Salvos: {salvos}")
        logger.info("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Erro na busca: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
