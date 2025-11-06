# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3
import logging
from datetime import datetime
from itemadapter import ItemAdapter


class SQLitePipeline:
    """Pipeline para salvar anúncios no banco de dados SQLite"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider):
        """Conecta ao banco de dados quando o spider inicia"""
        try:
            self.conn = sqlite3.connect('marketplace_anuncios.db')
            self.cursor = self.conn.cursor()
            
            # Cria a tabela se não existir
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS anuncios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT,
                    descricao TEXT,
                    preco TEXT,
                    localizacao TEXT,
                    url TEXT UNIQUE,
                    imagem_url TEXT,
                    vendedor TEXT,
                    palavra_chave TEXT,
                    data_coleta TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Cria índice para melhorar busca por URL
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON anuncios(url)
            ''')
            
            # Cria índice para melhorar busca por palavra-chave
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_palavra_chave ON anuncios(palavra_chave)
            ''')
            
            self.conn.commit()
            self.logger.info("Banco de dados SQLite conectado e tabela criada com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise
    
    def close_spider(self, spider):
        """Fecha a conexão quando o spider termina"""
        if self.conn:
            self.conn.close()
            self.logger.info("Conexão com banco de dados fechada")
    
    def process_item(self, item, spider):
        """Processa e salva o item no banco de dados"""
        try:
            adapter = ItemAdapter(item)
            
            # Definir origem como 'facebook' se não estiver definido
            origem = adapter.get('origem', 'facebook')
            
            self.cursor.execute('''
                INSERT OR IGNORE INTO anuncios 
                (titulo, descricao, preco, localizacao, url, imagem_url, vendedor, palavra_chave, 
                 data_coleta, origem, categoria, data_publicacao, enviado_telegram)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('titulo'),
                adapter.get('descricao'),
                adapter.get('preco'),
                adapter.get('localizacao'),
                adapter.get('url'),
                adapter.get('imagem_url'),
                adapter.get('vendedor'),
                adapter.get('palavra_chave'),
                adapter.get('data_coleta'),
                origem,
                adapter.get('categoria'),
                adapter.get('data_publicacao'),
                adapter.get('enviado_telegram', 0)
            ))
            
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                self.logger.info(f"[{origem.upper()}] Anúncio salvo: {adapter.get('titulo')}")
            else:
                self.logger.debug(f"[{origem.upper()}] Anúncio já existe no banco: {adapter.get('url')}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar item no banco de dados: {e}")
            return item
