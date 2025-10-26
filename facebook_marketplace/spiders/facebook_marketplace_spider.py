"""
Spider para coletar anúncios do Facebook Marketplace em Curitiba
"""

import scrapy
from urllib.parse import quote_plus
from datetime import datetime
from facebook_marketplace.items import MarketplaceAnuncioItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time


class FacebookMarketplaceSpider(scrapy.Spider):
    """Spider para coletar anúncios do Facebook Marketplace"""
    
    name = 'facebook_marketplace'
    allowed_domains = ['facebook.com']
    
    def __init__(self, palavra_chave='', cidade='curitiba', *args, **kwargs):
        """
        Inicializa o spider
        
        Args:
            palavra_chave (str): Palavra-chave para buscar no marketplace
            cidade (str): Cidade para filtrar os resultados (padrão: curitiba)
        """
        super(FacebookMarketplaceSpider, self).__init__(*args, **kwargs)
        self.palavra_chave = palavra_chave
        self.cidade = cidade.lower()
        self.base_url = f'https://www.facebook.com/marketplace/{self.cidade}'
        
        if self.palavra_chave:
            query_encoded = quote_plus(self.palavra_chave)
            self.start_urls = [f'{self.base_url}/search/?query={query_encoded}']
        else:
            self.start_urls = [self.base_url]
        
        self.logger.info(f"Spider inicializado para buscar: '{self.palavra_chave}' em {self.cidade}")
        self.logger.info(f"URL de busca: {self.start_urls[0]}")
        
        # Inicializa o driver do Selenium
        self.driver = None
    
    def _setup_driver(self):
        """Configura o driver do Chrome"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.logger.info("Driver do Chrome configurado")
    
    def start_requests(self):
        """Inicia as requisições"""
        # Não faz requisição HTTP do Scrapy, usa apenas Selenium
        # Por isso, retornamos uma Request com don't_filter=True
        # e processamos diretamente no parse
        for url in self.start_urls:
            # Precisamos fazer yield de Request, mas o parse vai usar Selenium
            # handle_httpstatus_list aceita qualquer status code
            yield scrapy.Request(
                url=url, 
                callback=self.parse,
                dont_filter=True,
                errback=self.errback_httpbin,
                meta={'handle_httpstatus_all': True}  # Aceita qualquer status HTTP
            )
    
    def errback_httpbin(self, failure):
        """Trata erros de requisição"""
        self.logger.error(repr(failure))
    
    def parse(self, response):
        """
        Faz o parsing da página de resultados do marketplace
        
        Args:
            response: Resposta da requisição
        """
        self.logger.info(f"Fazendo parse da página: {response.url}")
        self.logger.info(f"Status da resposta: {response.status}")
        
        # Configura e usa o driver do Selenium
        if not self.driver:
            self._setup_driver()
        
        try:
            # Acessa a URL com Selenium
            self.driver.get(response.url)
            self.logger.info("Página carregada com Selenium")
            
            # Aguarda a página carregar
            time.sleep(5)
            
            # Tenta rolar a página para carregar mais anúncios
            try:
                for i in range(3):  # Rola 3 vezes
                    self.logger.info(f"Rolando página ({i+1}/3)...")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
            except Exception as e:
                self.logger.warning(f"Erro ao rolar página: {e}")
            
            # Obtém o HTML da página
            html = self.driver.page_source
            
            # Salva o HTML para debug
            with open('marketplace_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.info("HTML salvo em marketplace_debug.html")
            
            # Usa Selenium direto para encontrar elementos (evita bug de typing no Python 3.9)
            from selenium.webdriver.common.by import By
            
            anuncios = []
            
            # Tenta diferentes seletores CSS
            seletores_css = [
                'div[data-testid="marketplace_feed_item"]',
                'a[href*="/marketplace/item/"]',
            ]
            
            for seletor in seletores_css:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    if elementos:
                        anuncios = elementos
                        self.logger.info(f"Encontrados {len(anuncios)} anúncios usando seletor: {seletor}")
                        break
                except Exception as e:
                    self.logger.warning(f"Erro ao usar seletor {seletor}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Erro ao usar Selenium: {e}")
            return []
        
        if not anuncios:
            self.logger.warning("Nenhum anúncio encontrado.")
            self.logger.warning(f"URL: {self.driver.current_url}")
        
        # Processa cada anúncio encontrado (agora são WebElements do Selenium)
        for anuncio in anuncios:
            try:
                item = self._extrair_dados_anuncio_selenium(anuncio)
                if item:
                    yield item
            except Exception as e:
                self.logger.error(f"Erro ao processar anúncio: {e}")
                continue
        
        # Log do total de anúncios processados
        self.logger.info(f"Total de anúncios processados: {len(anuncios)}")
    
    def closed(self, reason):
        """Fecha o driver quando o spider termina"""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
            self.logger.info("Driver do Chrome fechado")
    
    def _extrair_dados_anuncio_selenium(self, elemento):
        """
        Extrai os dados de um anúncio específico usando elemento do Selenium
        
        Args:
            elemento: WebElement do Selenium representando o anúncio
            
        Returns:
            MarketplaceAnuncioItem: Item com os dados do anúncio
        """
        try:
            from selenium.webdriver.common.by import By
            
            item = MarketplaceAnuncioItem()
            
            # Extrai URL - se for um link diretamente
            try:
                if elemento.tag_name == 'a':
                    url = elemento.get_attribute('href')
                else:
                    # Procura por um link dentro do elemento
                    link = elemento.find_element(By.CSS_SELECTOR, 'a[href*="/marketplace/item/"]')
                    url = link.get_attribute('href')
                
                if url:
                    # Limpa a URL (remove parâmetros desnecessários)
                    url = url.split('?')[0]
                    item['url'] = url
                else:
                    return None
            except:
                return None
            
            # Extrai título
            try:
                titulo = elemento.find_element(By.CSS_SELECTOR, 'span').text
                item['titulo'] = titulo.strip() if titulo else 'N/A'
            except:
                item['titulo'] = 'N/A'
            
            # Extrai preço
            try:
                # Procura por textos que contenham R$
                spans = elemento.find_elements(By.TAG_NAME, 'span')
                preco = 'N/A'
                for span in spans:
                    text = span.text
                    if 'R$' in text:
                        preco = text
                        break
                item['preco'] = preco
            except:
                item['preco'] = 'N/A'
            
            # Localização
            item['localizacao'] = self.cidade
            
            # URL da imagem
            try:
                img = elemento.find_element(By.TAG_NAME, 'img')
                item['imagem_url'] = img.get_attribute('src') or ''
            except:
                item['imagem_url'] = ''
            
            # Descrição e vendedor
            item['descricao'] = item['titulo']  # Por enquanto usa o título
            item['vendedor'] = 'N/A'
            
            # Metadados
            item['data_coleta'] = datetime.now().isoformat()
            item['palavra_chave'] = self.palavra_chave
            
            self.logger.debug(f"Anúncio extraído: {item['titulo']} - {item['preco']}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do anúncio: {e}")
            return None
    
    def _extrair_dados_anuncio(self, anuncio, selector):
        """
        Método antigo mantido para compatibilidade (não usado mais)
        
        Args:
            anuncio: Seletor do anúncio
            selector: Selector da página
            
        Returns:
            MarketplaceAnuncioItem: Item com os dados do anúncio
        """
        try:
            item = MarketplaceAnuncioItem()
            
            # Extrai URL
            url = anuncio.css('::attr(href)').get()
            if url:
                # Limpa a URL (remove parâmetros desnecessários)
                url = url.split('?')[0]
                if not url.startswith('http'):
                    url = f'https://www.facebook.com{url}'
                item['url'] = url
            else:
                return None
            
            # Extrai título
            titulo_seletores = [
                'span.x1lliihq.x6ikm8r.x10wlt62.x1n2onr6::text',
                'span::text',
                'div.x1lliihq::text',
            ]
            titulo = None
            for seletor in titulo_seletores:
                titulo = anuncio.css(seletor).get()
                if titulo:
                    break
            item['titulo'] = titulo.strip() if titulo else 'N/A'
            
            # Extrai preço
            preco_seletores = [
                'span.x193iq5w::text',
                'span[dir="auto"]::text',
            ]
            preco = None
            for seletor in preco_seletores:
                textos = anuncio.css(seletor).getall()
                for texto in textos:
                    if 'R$' in texto or texto.replace('.', '').replace(',', '').isdigit():
                        preco = texto
                        break
                if preco:
                    break
            item['preco'] = preco.strip() if preco else 'N/A'
            
            # Extrai localização
            localizacao = anuncio.css('span:contains("Curitiba")::text, span:contains("km")::text').get()
            item['localizacao'] = localizacao.strip() if localizacao else self.cidade
            
            # Extrai URL da imagem
            imagem_url = anuncio.css('img::attr(src)').get()
            item['imagem_url'] = imagem_url if imagem_url else ''
            
            # Descrição (normalmente precisa acessar a página do anúncio)
            item['descricao'] = item['titulo']  # Por enquanto usa o título
            
            # Vendedor (difícil de extrair sem acessar a página do anúncio)
            item['vendedor'] = 'N/A'
            
            # Metadados
            item['data_coleta'] = datetime.now().isoformat()
            item['palavra_chave'] = self.palavra_chave
            
            self.logger.debug(f"Anúncio extraído: {item['titulo']} - {item['preco']}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair dados do anúncio: {e}")
            return None
