#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Scraper do Facebook Marketplace usando Playwright
Similar ao olx_scraper.py mas para Facebook
"""

import argparse
import json
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.utils.logger import logger
from src.core.config import Config

# Configurações
config = Config()


def get_db_connection():
    """Retorna conexão com o banco de dados principal"""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'marketplace_anuncios.db'
    conn = sqlite3.connect(db_path)
    return conn


def buscar_facebook_marketplace(palavra_chave, email=None, senha=None, cidade='curitiba'):
    """
    Busca anúncios no Facebook Marketplace usando Playwright
    
    Args:
        palavra_chave: Termo para buscar
        email: Email para login (opcional)
        senha: Senha para login (opcional)
        cidade: Cidade para buscar (padrão: curitiba)
    
    Returns:
        list: Lista de anúncios encontrados
    """
    anuncios = []
    
    logger.info(f"Iniciando busca no Facebook Marketplace: '{palavra_chave}' em {cidade}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu'
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Carregar cookies se existirem
        cookies_file = Path(__file__).parent.parent.parent / 'data' / 'facebook_cookies.json'
        if cookies_file.exists():
            try:
                with open(cookies_file, 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logger.info("Cookies do Facebook carregados")
            except Exception as e:
                logger.warning(f"Erro ao carregar cookies: {e}")
        
        page = context.new_page()
        
        # Fazer login se credenciais forem fornecidas e não houver cookies válidos
        if email and senha and not cookies_file.exists():
            logger.info("Fazendo login no Facebook...")
            try:
                page.goto('https://www.facebook.com/', wait_until='load', timeout=60000)
                page.wait_for_timeout(2000)
                
                # Preencher email
                page.fill('input[name="email"]', email)
                page.wait_for_timeout(500)
                
                # Preencher senha
                page.fill('input[name="pass"]', senha)
                page.wait_for_timeout(500)
                
                # Clicar em login
                page.click('button[name="login"]')
                page.wait_for_timeout(5000)
                
                # Salvar cookies
                cookies = context.cookies()
                with open(cookies_file, 'w') as f:
                    json.dump(cookies, f)
                logger.info("Login realizado e cookies salvos")
                
            except Exception as e:
                logger.error(f"Erro no login: {e}")
                logger.warning("Continuando sem login...")
        
        # Montar URL de busca
        cidade_slug = cidade.lower().replace(' ', '-')
        url = f'https://www.facebook.com/marketplace/{cidade_slug}/search/?query={palavra_chave}'
        
        logger.info(f"Acessando: {url}")
        
        try:
            page.goto(url, wait_until='load', timeout=60000)
            page.wait_for_timeout(5000)  # Aguardar carregamento inicial
            
            # Rolar a página para carregar mais anúncios
            for i in range(3):
                logger.info(f"Rolando página ({i+1}/3)...")
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(2000)
            
            # Buscar todos os links de anúncios
            logger.info("Extraindo anúncios...")
            
            # Tentar diferentes seletores que o Facebook pode usar
            selectors = [
                'a[href*="/marketplace/item/"]',
                'div[role="article"] a',
                'a[href*="marketplace"]'
            ]
            
            links = []
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Encontrados {len(elements)} elementos com seletor: {selector}")
                        links = elements
                        break
                except:
                    continue
            
            if not links:
                logger.warning("Nenhum anúncio encontrado na página")
                return []
            
            logger.info(f"Processando {len(links)} links...")
            
            # Extrair dados de cada anúncio
            urls_processadas = set()
            
            for link in links[:20]:  # Limitar a 20 anúncios
                try:
                    href = link.get_attribute('href')
                    if not href or '/marketplace/item/' not in href:
                        continue
                    
                    # Limpar URL
                    url_anuncio = "https://www.facebook.com" + href.split('?')[0]
                    if url_anuncio in urls_processadas:
                        continue
                    urls_processadas.add(url_anuncio)
                    
                    # Extrair título (texto do link ou elemento pai)
                    titulo = link.inner_text().strip()
                    if not titulo or len(titulo) < 3:
                        # Tentar pegar de span dentro do link
                        span = link.query_selector('span')
                        if span:
                            titulo = span.inner_text().strip()
                    
                    if not titulo:
                        logger.debug(f"Anúncio sem título, pulando: {url_anuncio}")
                        continue
                    
                    # Tentar extrair preço (buscar na estrutura pai)
                    preco = 'N/A'
                    try:
                        # Buscar elemento pai que contém o preço
                        parent = link.evaluate_handle('el => el.closest("div[role=\'article\']") || el.parentElement')
                        parent_element = parent.as_element()
                        if parent_element:
                            # Procurar por texto com R$
                            text_content = parent_element.inner_text()
                            lines = text_content.split('\n')
                            for line in lines:
                                if 'R$' in line and len(line) < 50:
                                    preco = line.strip()
                                    break
                    except:
                        pass
                    
                    # Validar se preço é válido
                    if not preco or preco in ['N/A', '', '0', 'R$ 0']:
                        logger.debug(f"Anúncio '{titulo[:40]}...' sem preço válido, ignorando")
                        continue
                    
                    # Tentar extrair imagem
                    imagem_url = ''
                    try:
                        img = link.query_selector('img')
                        if img:
                            imagem_url = img.get_attribute('src') or ''
                    except:
                        pass
                    
                    # Criar anúncio
                    anuncio = {
                        'titulo': titulo[:255],  # Limitar tamanho
                        'preco': preco,
                        'localizacao': cidade,
                        'url': url_anuncio,
                        'imagem_url': imagem_url,
                        'categoria': 'marketplace',
                        'palavra_chave': palavra_chave,
                        'origem': 'facebook',
                        'data_coleta': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'data_publicacao': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    anuncios.append(anuncio)
                    logger.debug(f"✓ {titulo[:60]}... - {preco}")
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar anúncio: {e}")
                    continue
            
        except PlaywrightTimeout:
            logger.error("Timeout ao carregar página do Facebook")
        except Exception as e:
            logger.error(f"Erro durante scraping: {e}", exc_info=True)
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
            # Verificar se já existe (por URL)
            cursor.execute(
                "SELECT id FROM anuncios WHERE url = ? AND origem = 'facebook'",
                (anuncio['url'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                duplicados += 1
                logger.debug(f"Anúncio duplicado: {anuncio['titulo'][:50]}")
                continue
            
            # Inserir novo anúncio
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
        description='Busca anúncios no Facebook Marketplace usando Playwright'
    )
    parser.add_argument('palavra_chave', help='Palavra-chave para buscar')
    parser.add_argument('--email', default=None, help='Email para login (opcional)')
    parser.add_argument('--senha', default=None, help='Senha para login (opcional)')
    parser.add_argument('--cidade', default='curitiba', help='Cidade (default: curitiba)')
    
    args = parser.parse_args()
    
    try:
        # Buscar anúncios
        logger.info("="*60)
        logger.info(f"BUSCA FACEBOOK - '{args.palavra_chave}'")
        logger.info("="*60)
        
        anuncios = buscar_facebook_marketplace(
            palavra_chave=args.palavra_chave,
            email=args.email,
            senha=args.senha,
            cidade=args.cidade
        )
        
        # Salvar no banco
        salvos = salvar_anuncios_database(anuncios)
        
        # Extrair URLs dos anúncios
        urls = [anuncio.get('url') for anuncio in anuncios if anuncio.get('url')]
        
        # Resultado em JSON para o scheduler parsear
        resultado = {
            'encontrados': len(anuncios),
            'salvos': salvos,
            'duplicados': len(anuncios) - salvos,
            'urls': urls
        }
        
        logger.info("="*60)
        logger.info(f"RESULTADO: {len(anuncios)} encontrados | {salvos} salvos")
        logger.info("="*60)
        
        # Output JSON para o scheduler
        print(f"RESULT_JSON:{json.dumps(resultado)}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Busca cancelada pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"Erro durante execução: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
