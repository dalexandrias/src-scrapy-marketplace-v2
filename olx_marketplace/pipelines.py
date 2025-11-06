"""
Pipeline para processar e salvar anúncios da OLX no banco de dados SQLite
"""

import sqlite3
import logging
from datetime import datetime
from itemadapter import ItemAdapter


class OlxPipeline:
    """Pipeline para salvar anúncios da OLX no banco de dados SQLite"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.logger = logging.getLogger(__name__)
    
    def open_spider(self, spider):
        """Conecta ao banco de dados quando o spider inicia"""
        try:
            self.conn = sqlite3.connect('marketplace_anuncios.db')
            self.cursor = self.conn.cursor()
            
            # Cria a tabela se não existir (com novos campos)
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
                    origem TEXT DEFAULT 'olx',
                    categoria TEXT,
                    data_publicacao TIMESTAMP,
                    data_coleta TIMESTAMP,
                    enviado_telegram BOOLEAN DEFAULT 0,
                    data_envio_telegram TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Cria índices para melhorar performance
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON anuncios(url)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_palavra_chave ON anuncios(palavra_chave)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_origem ON anuncios(origem)
            ''')
            
            self.cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_enviado_telegram ON anuncios(enviado_telegram)
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
        """Processa e salva cada item no banco de dados"""
        try:
            adapter = ItemAdapter(item)
            
            # Prepara os dados
            data = {
                'titulo': adapter.get('titulo', 'N/A'),
                'descricao': adapter.get('descricao', ''),
                'preco': adapter.get('preco', 'N/A'),
                'localizacao': adapter.get('localizacao', ''),
                'url': adapter.get('url'),
                'imagem_url': adapter.get('imagem_url', ''),
                'vendedor': adapter.get('vendedor', 'N/A'),
                'palavra_chave': adapter.get('palavra_chave', ''),
                'origem': adapter.get('origem', 'olx'),
                'categoria': adapter.get('categoria', ''),
                'data_publicacao': adapter.get('data_publicacao'),
                'data_coleta': adapter.get('data_coleta'),
                'enviado_telegram': adapter.get('enviado_telegram', 0),
            }
            
            # Insere no banco (INSERT OR IGNORE para evitar duplicatas)
            self.cursor.execute('''
                INSERT OR IGNORE INTO anuncios (
                    titulo, descricao, preco, localizacao, url, imagem_url,
                    vendedor, palavra_chave, origem, categoria,
                    data_publicacao, data_coleta, enviado_telegram
                ) VALUES (
                    :titulo, :descricao, :preco, :localizacao, :url, :imagem_url,
                    :vendedor, :palavra_chave, :origem, :categoria,
                    :data_publicacao, :data_coleta, :enviado_telegram
                )
            ''', data)
            
            if self.cursor.rowcount > 0:
                self.conn.commit()
                self.logger.info(f"Anúncio salvo: {data['titulo']}")
            else:
                self.logger.debug(f"Anúncio já existe no banco: {data['url']}")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar anúncio no banco: {e}")
            return item
