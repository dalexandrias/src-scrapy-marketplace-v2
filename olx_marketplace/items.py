"""
Items para anúncios da OLX
"""

import scrapy


class OlxAnuncioItem(scrapy.Item):
    """Item representando um anúncio da OLX"""
    
    # Informações do anúncio
    titulo = scrapy.Field()
    descricao = scrapy.Field()
    preco = scrapy.Field()
    localizacao = scrapy.Field()
    url = scrapy.Field()
    imagem_url = scrapy.Field()
    vendedor = scrapy.Field()
    
    # Categoria e tags
    categoria = scrapy.Field()  # motos, carros, eletronicos, etc.
    palavra_chave = scrapy.Field()
    
    # Metadados
    origem = scrapy.Field()  # 'olx'
    data_publicacao = scrapy.Field()  # Data que o anúncio foi publicado na OLX
    data_coleta = scrapy.Field()  # Data que coletamos o anúncio
    
    # Controle de notificações
    enviado_telegram = scrapy.Field()
    data_envio_telegram = scrapy.Field()
