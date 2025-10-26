"""
Script de teste para o sistema de scraping do Facebook Marketplace

Execute este script para testar o sistema completo:
- Teste de login
- Teste de busca sem login
- Teste de banco de dados
"""

import sys
import logging
from facebook_marketplace.facebook_login import FacebookLogin

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def teste_login():
    """
    Teste do módulo de login
    
    IMPORTANTE: Substitua EMAIL e SENHA com credenciais reais para testar
    """
    logger.info("="*80)
    logger.info("TESTE 1: Módulo de Login no Facebook")
    logger.info("="*80)
    
    # CONFIGURE AQUI SUAS CREDENCIAIS PARA TESTE
    EMAIL = "seu_email@exemplo.com"
    SENHA = "sua_senha"
    
    if EMAIL == "seu_email@exemplo.com":
        logger.warning("⚠️  AVISO: Configure EMAIL e SENHA no arquivo teste.py antes de testar login")
        logger.info("Pulando teste de login...\n")
        return False
    
    try:
        logger.info(f"Tentando fazer login com: {EMAIL}")
        
        # Inicializa o login (headless=False para ver o navegador)
        fb_login = FacebookLogin(headless=False)
        
        # Tenta fazer login
        sucesso = fb_login.login(EMAIL, SENHA, save_cookies=True)
        
        if sucesso:
            logger.info("✓ Login realizado com sucesso!")
            logger.info("✓ Cookies salvos para reutilização")
            
            # Testa obter cookies
            cookies = fb_login.get_cookies_dict()
            logger.info(f"Total de cookies: {len(cookies)}")
            
            fb_login.close()
            return True
        else:
            logger.error("✗ Falha no login")
            fb_login.close()
            return False
            
    except Exception as e:
        logger.error(f"✗ Erro durante teste de login: {e}")
        return False


def teste_busca_simples():
    """Teste de busca simples sem login"""
    logger.info("="*80)
    logger.info("TESTE 2: Busca Simples (Sem Login)")
    logger.info("="*80)
    
    try:
        from buscar_marketplace import buscar_anuncios
        
        logger.info("Buscando 'honda civic' em Curitiba...")
        
        sucesso = buscar_anuncios(
            palavra_chave="honda civic",
            cidade="curitiba"
        )
        
        if sucesso:
            logger.info("✓ Busca executada!")
            return True
        else:
            logger.error("✗ Falha na busca")
            return False
            
    except Exception as e:
        logger.error(f"✗ Erro durante teste de busca: {e}")
        return False


def teste_banco_dados():
    """Teste de leitura do banco de dados"""
    logger.info("="*80)
    logger.info("TESTE 3: Banco de Dados SQLite")
    logger.info("="*80)
    
    try:
        import sqlite3
        
        conn = sqlite3.connect('marketplace_anuncios.db')
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='anuncios'
        """)
        
        if cursor.fetchone():
            logger.info("✓ Tabela 'anuncios' encontrada")
            
            # Conta registros
            cursor.execute("SELECT COUNT(*) FROM anuncios")
            total = cursor.fetchone()[0]
            logger.info(f"✓ Total de anúncios no banco: {total}")
            
            if total > 0:
                # Mostra alguns exemplos
                cursor.execute("""
                    SELECT titulo, preco, url 
                    FROM anuncios 
                    LIMIT 5
                """)
                
                logger.info("\nExemplos de anúncios:")
                for i, (titulo, preco, url) in enumerate(cursor.fetchall(), 1):
                    logger.info(f"  {i}. {titulo} - {preco}")
                    logger.info(f"     {url}")
            
            conn.close()
            return True
        else:
            logger.warning("⚠️  Tabela 'anuncios' não encontrada")
            logger.info("Execute uma busca primeiro para criar o banco")
            conn.close()
            return False
            
    except sqlite3.OperationalError as e:
        logger.warning(f"⚠️  Banco de dados não encontrado: {e}")
        logger.info("Execute uma busca primeiro para criar o banco")
        return False
    except Exception as e:
        logger.error(f"✗ Erro ao testar banco: {e}")
        return False


def teste_estrutura_arquivos():
    """Verifica se todos os arquivos necessários existem"""
    logger.info("="*80)
    logger.info("TESTE 4: Estrutura de Arquivos")
    logger.info("="*80)
    
    import os
    
    arquivos_necessarios = [
        'scrapy.cfg',
        'buscar_marketplace.py',
        'exemplo_uso.py',
        'README.md',
        'requirements.txt',
        'facebook_marketplace/__init__.py',
        'facebook_marketplace/items.py',
        'facebook_marketplace/pipelines.py',
        'facebook_marketplace/settings.py',
        'facebook_marketplace/middlewares.py',
        'facebook_marketplace/facebook_login.py',
        'facebook_marketplace/spiders/__init__.py',
        'facebook_marketplace/spiders/facebook_marketplace_spider.py',
    ]
    
    todos_ok = True
    
    for arquivo in arquivos_necessarios:
        if os.path.exists(arquivo):
            logger.info(f"✓ {arquivo}")
        else:
            logger.error(f"✗ {arquivo} - NÃO ENCONTRADO")
            todos_ok = False
    
    if todos_ok:
        logger.info("\n✓ Todos os arquivos necessários estão presentes!")
        return True
    else:
        logger.error("\n✗ Alguns arquivos estão faltando")
        return False


def executar_todos_testes():
    """Executa todos os testes"""
    logger.info("\n")
    logger.info("╔" + "="*78 + "╗")
    logger.info("║" + " "*20 + "TESTES DO SISTEMA" + " "*41 + "║")
    logger.info("╚" + "="*78 + "╝")
    logger.info("\n")
    
    resultados = {}
    
    # Teste 1: Estrutura de arquivos
    resultados['Estrutura de Arquivos'] = teste_estrutura_arquivos()
    logger.info("\n")
    
    # Teste 2: Login (comentado por padrão - requer credenciais)
    # resultados['Login no Facebook'] = teste_login()
    # logger.info("\n")
    
    # Teste 3: Busca simples (comentado - demora)
    # resultados['Busca Simples'] = teste_busca_simples()
    # logger.info("\n")
    
    # Teste 4: Banco de dados
    resultados['Banco de Dados'] = teste_banco_dados()
    logger.info("\n")
    
    # Resumo
    logger.info("="*80)
    logger.info("RESUMO DOS TESTES")
    logger.info("="*80)
    
    for teste, sucesso in resultados.items():
        status = "✓ PASSOU" if sucesso else "✗ FALHOU"
        logger.info(f"{teste}: {status}")
    
    total_passou = sum(1 for s in resultados.values() if s)
    total_testes = len(resultados)
    
    logger.info("="*80)
    logger.info(f"Total: {total_passou}/{total_testes} testes passaram")
    logger.info("="*80)
    
    return total_passou == total_testes


if __name__ == '__main__':
    """
    Execute este arquivo para rodar os testes:
    
    python teste.py
    """
    
    sucesso = executar_todos_testes()
    
    if sucesso:
        logger.info("\n🎉 Todos os testes passaram!")
        sys.exit(0)
    else:
        logger.info("\n⚠️  Alguns testes falharam")
        sys.exit(1)
