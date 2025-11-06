"""
Utilitário para coletar cookies do Cloudflare usando Playwright
Simula navegador real para passar pelo anti-bot da OLX
"""

from playwright.sync_api import sync_playwright
import time
from typing import Dict

def coletar_cookies_olx() -> Dict[str, str]:
    """
    Abre navegador real, visita OLX e coleta cookies do Cloudflare
    
    Returns:
        Dict com cookies no formato {nome: valor}
    """
    print("🌐 Iniciando navegador para coletar cookies...")
    
    with sync_playwright() as p:
        # Lançar navegador (headless=False para ver o que está acontecendo)
        browser = p.chromium.launch(headless=True)  # headless=True para produção
        
        # Criar contexto com User-Agent real
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
        )
        
        # Criar página
        page = context.new_page()
        
        try:
            # Visitar homepage da OLX
            print("   Visitando https://www.olx.com.br ...")
            page.goto('https://www.olx.com.br', wait_until='load', timeout=60000)
            
            # Aguardar alguns segundos para Cloudflare processar
            print("   Aguardando Cloudflare processar...")
            time.sleep(5)
            
            # Verificar se página carregou
            title = page.title()
            print(f"   Título da página: {title}")
            
            # Coletar cookies
            cookies = context.cookies()
            
            # Converter para formato dict
            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            print(f"   ✅ {len(cookies_dict)} cookies coletados:")
            for name in cookies_dict:
                print(f"      🍪 {name}")
            
            return cookies_dict
            
        finally:
            browser.close()


def testar_cookies():
    """Testa se os cookies coletados funcionam com requests"""
    import requests
    
    # Coletar cookies
    cookies = coletar_cookies_olx()
    
    # Testar com requests
    print("\n🔍 Testando cookies com requests...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9',
    }
    
    response = requests.get(
        'https://www.olx.com.br/estado-pr/regiao-de-curitiba-e-paranagua/grande-curitiba?q=pcx&sf=1&f=p',
        headers=headers,
        cookies=cookies,
        timeout=15
    )
    
    print(f"   Status: {response.status_code}")
    print(f"   Tamanho: {len(response.text):,} bytes")
    print(f"   Tem __NEXT_DATA__: {'__NEXT_DATA__' in response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCESSO! Cookies funcionaram")
        return True
    else:
        print(f"\n❌ FALHOU - HTTP {response.status_code}")
        return False


if __name__ == '__main__':
    testar_cookies()
