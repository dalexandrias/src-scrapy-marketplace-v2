# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MarketplaceAnuncioItem(scrapy.Item):
    """Item para armazenar dados de anúncios do Facebook Marketplace"""
    
    titulo = scrapy.Field()
    descricao = scrapy.Field()
    preco = scrapy.Field()
    localizacao = scrapy.Field()
    url = scrapy.Field()
    imagem_url = scrapy.Field()
    vendedor = scrapy.Field()
    data_coleta = scrapy.Field()
    palavra_chave = scrapy.Field()
