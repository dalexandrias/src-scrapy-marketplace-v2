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
    
    # Novos campos para suporte a múltiplas origens e notificações
    origem = scrapy.Field()  # facebook, olx, etc
    categoria = scrapy.Field()  # categoria do anúncio
    data_publicacao = scrapy.Field()  # data de publicação do anúncio
    enviado_telegram = scrapy.Field()  # flag se foi enviado para Telegram
    data_envio_telegram = scrapy.Field()  # data/hora do envio

