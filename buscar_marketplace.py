"""
Módulo principal para buscar anúncios no Facebook Marketplace

Este módulo fornece uma interface simples para:
1. Fazer login no Facebook
2. Buscar anúncios no Marketplace de uma cidade específica
3. Salvar os resultados em um banco de dados SQLite

Exemplo de uso:
    from buscar_marketplace import buscar_anuncios
    
    # Buscar sem login (pode ter limitações)
    buscar_anuncios(palavra_chave="honda civic")
    
    # Buscar com login
    buscar_anuncios(
        palavra_chave="honda civic",
        email="seu_email@exemplo.com",
        senha="sua_senha",
        cidade="curitiba"
    )
"""

import logging
import sys
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer
from facebook_marketplace.facebook_login import FacebookLogin
from facebook_marketplace.spiders.facebook_marketplace_spider import FacebookMarketplaceSpider


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def buscar_anuncios(palavra_chave, email=None, senha=None, cidade='curitiba', usar_cookies_salvos=True):
    """
    Busca anúncios no Facebook Marketplace
    
    Args:
        palavra_chave (str): Palavra-chave para buscar (ex: "honda civic")
        email (str, optional): Email para login no Facebook
        senha (str, optional): Senha para login no Facebook
        cidade (str, optional): Cidade para filtrar os resultados (padrão: "curitiba")
        usar_cookies_salvos (bool, optional): Se True, tenta usar cookies salvos antes de fazer login
    
    Returns:
        bool: True se a busca foi executada com sucesso
        
    Exemplo:
        >>> buscar_anuncios("honda civic", email="seu@email.com", senha="senha123")
        True
    """
    try:
        logger.info("="*80)
        logger.info(f"Iniciando busca por: '{palavra_chave}' em {cidade}")
        logger.info("="*80)
        
        # Se email e senha foram fornecidos, faz login
        if email and senha:
            logger.info("Credenciais fornecidas. Fazendo login no Facebook...")
            
            fb_login = FacebookLogin(headless=True)
            login_sucesso = False
            
            # Tenta usar cookies salvos primeiro
            if usar_cookies_salvos:
                logger.info("Tentando usar cookies salvos...")
                if fb_login.carregar_cookies():
                    login_sucesso = True
                    logger.info("Login restaurado com sucesso usando cookies!")
            
            # Se não conseguiu com cookies, faz login normal
            if not login_sucesso:
                logger.info("Fazendo login com credenciais...")
                login_sucesso = fb_login.login(email, senha, save_cookies=True)
            
            if login_sucesso:
                logger.info("✓ Login realizado com sucesso!")
                logger.info("Cookies salvos para uso futuro")
            else:
                logger.error("✗ Falha no login. Continuando sem autenticação...")
                logger.warning("Nota: Algumas funcionalidades podem estar limitadas")
            
            # Fecha o navegador do login
            fb_login.close()
            logger.info("")
        
        else:
            logger.warning("Executando sem login (email/senha não fornecidos)")
            logger.warning("Alguns anúncios podem não estar acessíveis")
            logger.info("")
        
        # Configura e executa o spider
        logger.info("Iniciando spider do Scrapy...")
        
        configure_logging()
        runner = CrawlerRunner(get_project_settings())
        
        @defer.inlineCallbacks
        def crawl():
            yield runner.crawl(
                FacebookMarketplaceSpider,
                palavra_chave=palavra_chave,
                cidade=cidade
            )
            reactor.stop()
        
        crawl()
        reactor.run(installSignalHandlers=False)  # Desabilita signal handlers para evitar erro no Windows
        
        logger.info("="*80)
        logger.info("Busca concluída!")
        logger.info("Os anúncios foram salvos no banco de dados: marketplace_anuncios.db")
        logger.info("="*80)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("\n\nBusca interrompida pelo usuário")
        return False
        
    except Exception as e:
        logger.error(f"Erro durante a busca: {e}", exc_info=True)
        return False


def buscar_sem_login(palavra_chave, cidade='curitiba'):
    """
    Busca anúncios sem fazer login (modo simplificado)
    
    Args:
        palavra_chave (str): Palavra-chave para buscar
        cidade (str, optional): Cidade para filtrar os resultados (padrão: "curitiba")
    
    Returns:
        bool: True se a busca foi executada com sucesso
    """
    return buscar_anuncios(palavra_chave=palavra_chave, cidade=cidade)


if __name__ == '__main__':
    """
    Permite executar o script diretamente da linha de comando
    
    Exemplos:
        python buscar_marketplace.py "honda civic"
        python buscar_marketplace.py "iphone" --cidade "sao-paulo"
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Buscar anúncios no Facebook Marketplace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  
  Buscar sem login:
    python buscar_marketplace.py "honda civic"
  
  Buscar com login:
    python buscar_marketplace.py "honda civic" --email seu@email.com --senha sua_senha
  
  Buscar em outra cidade:
    python buscar_marketplace.py "iphone" --cidade "sao-paulo"
  
  Buscar sem usar cookies salvos:
    python buscar_marketplace.py "notebook" --email seu@email.com --senha sua_senha --no-cookies
        '''
    )
    
    parser.add_argument(
        'palavra_chave',
        type=str,
        help='Palavra-chave para buscar no Marketplace'
    )
    
    parser.add_argument(
        '--email',
        type=str,
        default=None,
        help='Email para login no Facebook (opcional)'
    )
    
    parser.add_argument(
        '--senha',
        type=str,
        default=None,
        help='Senha para login no Facebook (opcional)'
    )
    
    parser.add_argument(
        '--cidade',
        type=str,
        default='curitiba',
        help='Cidade para filtrar os resultados (padrão: curitiba)'
    )
    
    parser.add_argument(
        '--no-cookies',
        action='store_true',
        help='Não usar cookies salvos (sempre fazer login novo)'
    )
    
    args = parser.parse_args()
    
    # Validação
    if args.email and not args.senha:
        logger.error("Erro: Se fornecer --email, também deve fornecer --senha")
        sys.exit(1)
    
    if args.senha and not args.email:
        logger.error("Erro: Se fornecer --senha, também deve fornecer --email")
        sys.exit(1)
    
    # Executa a busca
    sucesso = buscar_anuncios(
        palavra_chave=args.palavra_chave,
        email=args.email,
        senha=args.senha,
        cidade=args.cidade,
        usar_cookies_salvos=not args.no_cookies
    )
    
    sys.exit(0 if sucesso else 1)
