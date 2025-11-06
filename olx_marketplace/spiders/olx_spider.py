"""
Spider para coletar anúncios da OLX
Extrai dados do JSON __NEXT_DATA__ das páginas da OLX
"""

import scrapy
import json
import re
from datetime import datetime
from urllib.parse import urljoin

from olx_marketplace.items import OlxAnuncioItem
from config import Config


class OlxSpider(scrapy.Spider):
    """Spider para extrair anúncios da OLX"""
    
    name = 'olx'
    allowed_domains = ['olx.com.br']
    
    # Configurações do spider
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        },
        'DOWNLOAD_DELAY': Config.olx.DOWNLOAD_DELAY,
        'CONCURRENT_REQUESTS': Config.olx.CONCURRENT_REQUESTS,
        'CONCURRENT_REQUESTS_PER_DOMAIN': Config.olx.CONCURRENT_REQUESTS_PER_DOMAIN,
        'AUTOTHROTTLE_ENABLED': Config.olx.AUTOTHROTTLE_ENABLED,
        'AUTOTHROTTLE_START_DELAY': Config.olx.AUTOTHROTTLE_START_DELAY,
        'AUTOTHROTTLE_MAX_DELAY': Config.olx.AUTOTHROTTLE_MAX_DELAY,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': Config.olx.AUTOTHROTTLE_TARGET_CONCURRENCY,
        'ITEM_PIPELINES': {
            'olx_marketplace.pipelines.OlxPipeline': 300,
        },
        'COOKIES_ENABLED': True,
        'REDIRECT_ENABLED': True,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
    }
    
    def __init__(self, palavra_chave=None, estado='sp', categoria=None, 
                 filtrar_hoje=True, *args, **kwargs):
        """
        Inicializa o spider da OLX
        
        Args:
            palavra_chave: Palavra-chave para buscar
            estado: Estado para buscar (sp, rj, pr, mg, etc)
            categoria: Categoria da OLX (motos, carros, eletronicos, etc)
            filtrar_hoje: Se True, filtra apenas anúncios de hoje
        """
        super(OlxSpider, self).__init__(*args, **kwargs)
        
        if not palavra_chave:
            raise ValueError("palavra_chave é obrigatório")
        
        self.palavra_chave = palavra_chave
        self.estado = estado.lower()
        self.categoria = categoria or Config.olx.CATEGORIA_PADRAO
        self.filtrar_hoje = filtrar_hoje
        
        # Guardar URL de busca para usar depois de coletar cookies
        self.search_url = self._construir_url()
        
        # Primeira requisição vai para homepage para coletar cookies do Cloudflare
        self.start_urls = ['https://www.olx.com.br']
        
        self.logger.info(f"Iniciando OlxSpider - Palavra-chave: {self.palavra_chave}, "
                        f"Estado: {self.estado}, Categoria: {self.categoria}")
        self.logger.info(f"Estratégia: Visitar homepage primeiro para coletar cookies do Cloudflare")
    
    def _construir_url(self) -> str:
        """
        Constrói a URL de busca na OLX
        
        Returns:
            URL de busca formatada
        """
        url = Config.olx.get_search_url(
            palavra_chave=self.palavra_chave,
            estado=self.estado,
            categoria=self.categoria
        )
        
        self.logger.info(f"URL de busca: {url}")
        return url
    
    def parse(self, response):
        """
        Parse da homepage da OLX
        Coleta cookies do Cloudflare e redireciona para busca
        """
        # Força este método a ser um generator (mesmo se não houver yields de items)
        if False:
            yield
        
        self.logger.info(f"✅ Homepage acessada - Status: {response.status}")
        self.logger.info(f"🍪 Cookies coletados: {len(response.request.cookies)} cookies")
        
        # Log dos cookies para debug
        for cookie_name in response.request.cookies:
            self.logger.debug(f"   Cookie: {cookie_name}")
        
        # Verificar se recebemos cookies do Cloudflare
        cloudflare_cookies = ['__cf_bm', '_cfuvid', 'cf_clearance']
        has_cf_cookies = any(cookie in response.request.cookies for cookie in cloudflare_cookies)
        
        if has_cf_cookies:
            self.logger.info("✅ Cookies do Cloudflare detectados!")
        else:
            self.logger.warning("⚠️  Nenhum cookie do Cloudflare detectado (pode ter problemas)")
        
        # Agora fazer a requisição de busca com os cookies coletados
        self.logger.info(f"🔍 Fazendo requisição de busca: {self.search_url}")
        yield scrapy.Request(
            url=self.search_url,
            callback=self.parse_search,
            dont_filter=True,
            errback=self.errback_search
        )
    
    def errback_search(self, failure):
        """Callback de erro para requisição de busca"""
        self.logger.error(f"❌ Erro na requisição de busca: {failure}")
        self.logger.error(f"   Tipo: {failure.type}")
        self.logger.error(f"   Valor: {failure.value}")
    
    def parse_search(self, response):
        """
        Parse da página de busca da OLX
        Extrai dados do JSON __NEXT_DATA__
        """
        # Força este método a ser um generator (mesmo se não houver yields de items)
        if False:
            yield
            
        self.logger.info(f"Processando URL de busca: {response.url}")
        self.logger.info(f"Status Code: {response.status}")
        
        # Verificar se houve bloqueio (403, 503, etc)
        if response.status in [403, 503]:
            self.logger.error(f"❌ Requisição bloqueada pela OLX (HTTP {response.status})")
            self.logger.error("Possíveis causas:")
            self.logger.error("  - Anti-bot detectou User-Agent suspeito")
            self.logger.error("  - IP bloqueado por excesso de requisições")
            self.logger.error("  - Necessário usar proxy ou ajustar headers")
            self.logger.error("")
            self.logger.error("💡 Soluções possíveis:")
            self.logger.error("  1. Adicionar mais headers (Accept, Accept-Language, etc)")
            self.logger.error("  2. Usar cookies de sessão real")
            self.logger.error("  3. Usar proxy rotativo")
            self.logger.error("  4. Aumentar delay entre requisições")
            return
        
        # Extrair JSON do __NEXT_DATA__
        next_data = self._extrair_next_data(response)
        
        if not next_data:
            self.logger.warning("Não foi possível extrair __NEXT_DATA__ da página")
            # Tentar salvar HTML para debug
            self.logger.debug(f"Primeiros 500 chars da resposta: {response.text[:500]}")
            return
        
        # Extrair anúncios do JSON
        anuncios = self._extrair_anuncios(next_data)
        
        if not anuncios:
            self.logger.warning("Nenhum anúncio encontrado no JSON")
            self.logger.debug(f"Estrutura do JSON: {list(next_data.keys())}")
            return
        
        self.logger.info(f"Total de anúncios encontrados: {len(anuncios)}")
        
        # Processar cada anúncio
        anuncios_hoje = 0
        anuncios_processados = 0
        
        for ad_data in anuncios:
            item = self._processar_anuncio(ad_data)
            
            if item:
                anuncios_processados += 1
                
                # Verificar se é de hoje (se filtro estiver ativado)
                if self.filtrar_hoje:
                    if self._e_anuncio_de_hoje(item):
                        anuncios_hoje += 1
                        yield item
                    else:
                        self.logger.debug(f"Anúncio filtrado (não é de hoje): {item['titulo']}")
                else:
                    yield item
        
        self.logger.info(f"Anúncios processados: {anuncios_processados}")
        if self.filtrar_hoje:
            self.logger.info(f"Anúncios de hoje: {anuncios_hoje}")
    
    def _extrair_next_data(self, response) -> dict:
        """
        Extrai o JSON do script __NEXT_DATA__
        
        Args:
            response: Response do Scrapy
        
        Returns:
            Dict com os dados ou None se não encontrado
        """
        # Buscar script __NEXT_DATA__
        script_content = response.xpath(
            '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        ).get()
        
        if not script_content:
            # Tentar com regex como fallback
            match = re.search(
                r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
                response.text,
                re.DOTALL
            )
            if match:
                script_content = match.group(1)
            else:
                return None
        
        try:
            data = json.loads(script_content)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao fazer parse do JSON: {e}")
            return None
    
    def _extrair_anuncios(self, next_data: dict) -> list:
        """
        Extrai lista de anúncios do JSON __NEXT_DATA__
        
        Args:
            next_data: Dicionário com os dados do __NEXT_DATA__
        
        Returns:
            Lista de dicionários com dados dos anúncios
        """
        try:
            # A estrutura pode variar, tentar diferentes caminhos
            ads = next_data.get('props', {}).get('pageProps', {}).get('ads', [])
            
            if not ads:
                # Tentar caminho alternativo
                ads = next_data.get('props', {}).get('pageProps', {}).get('data', {}).get('ads', [])
            
            return ads if isinstance(ads, list) else []
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair anúncios do JSON: {e}")
            return []
    
    def _processar_anuncio(self, ad_data: dict) -> OlxAnuncioItem:
        """
        Processa dados de um anúncio e cria um OlxAnuncioItem
        
        Args:
            ad_data: Dicionário com dados do anúncio
        
        Returns:
            OlxAnuncioItem ou None se dados inválidos
        """
        try:
            # Extrair dados básicos (campo pode ter nomes diferentes)
            titulo = ad_data.get('title') or ad_data.get('subject')
            preco = ad_data.get('price') or ad_data.get('priceValue')
            url = ad_data.get('url') or ad_data.get('friendlyUrl')
            
            # URL completa
            if url and not url.startswith('http'):
                url = urljoin(f'https://{self.estado}.olx.com.br', url)
            
            # Timestamp de criação
            timestamp = (ad_data.get('created') or 
                        ad_data.get('date') or 
                        ad_data.get('origListTime') or 
                        ad_data.get('createdAt'))
            
            # Validar dados essenciais
            if not titulo or not url:
                self.logger.debug(f"Anúncio sem título ou URL, ignorando")
                return None
            
            # Converter timestamp para datetime
            data_publicacao = None
            if timestamp:
                try:
                    data_publicacao = datetime.fromtimestamp(int(timestamp)).isoformat()
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"Erro ao converter timestamp {timestamp}: {e}")
            
            # Localização
            location = ad_data.get('location', {})
            if isinstance(location, dict):
                cidade = location.get('municipality') or location.get('city') or ''
                estado_loc = location.get('state') or location.get('uf') or self.estado.upper()
                localizacao = f"{cidade}, {estado_loc}".strip(', ')
            else:
                localizacao = str(location) if location else f"{self.estado.upper()}"
            
            # Imagens
            images = ad_data.get('images', [])
            imagem_url = ''
            if images and isinstance(images, list) and len(images) > 0:
                primeira_imagem = images[0]
                if isinstance(primeira_imagem, dict):
                    imagem_url = primeira_imagem.get('original') or primeira_imagem.get('url') or ''
                elif isinstance(primeira_imagem, str):
                    imagem_url = primeira_imagem
            
            # Criar item
            item = OlxAnuncioItem()
            item['titulo'] = titulo
            item['descricao'] = ad_data.get('body') or titulo  # Descrição completa ou título
            item['preco'] = str(preco) if preco else 'N/A'
            item['localizacao'] = localizacao
            item['url'] = url
            item['imagem_url'] = imagem_url
            item['vendedor'] = ad_data.get('user', {}).get('name') or 'N/A'
            item['categoria'] = self.categoria
            item['palavra_chave'] = self.palavra_chave
            item['origem'] = 'olx'
            item['data_publicacao'] = data_publicacao
            item['data_coleta'] = datetime.now().isoformat()
            item['enviado_telegram'] = 0
            
            self.logger.debug(f"Anúncio processado: {titulo} - {preco} - {url}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Erro ao processar anúncio: {e}", exc_info=True)
            return None
    
    def _e_anuncio_de_hoje(self, item: OlxAnuncioItem) -> bool:
        """
        Verifica se o anúncio foi publicado hoje
        
        Args:
            item: OlxAnuncioItem
        
        Returns:
            True se foi publicado hoje, False caso contrário
        """
        if not item.get('data_publicacao'):
            return False
        
        try:
            data_pub = datetime.fromisoformat(item['data_publicacao'])
            hoje = datetime.now().date()
            return data_pub.date() == hoje
        except (ValueError, TypeError):
            return False
