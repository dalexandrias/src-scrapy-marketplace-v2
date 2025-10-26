"""
Exemplo de uso do sistema de scraping do Facebook Marketplace

Este arquivo demonstra como usar o sistema para buscar anúncios
e consultar os resultados salvos no banco de dados.
"""

from buscar_marketplace import buscar_anuncios
import sqlite3
import logging

# Configurar logging para ver o que está acontecendo
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def exemplo_busca_simples():
    """Exemplo de busca simples sem login"""
    logger.info("=== EXEMPLO 1: Busca Simples ===\n")
    
    buscar_anuncios(
        palavra_chave="honda civic",
        cidade="curitiba"
    )


def exemplo_busca_com_login():
    """Exemplo de busca com login no Facebook"""
    logger.info("=== EXEMPLO 2: Busca com Login ===\n")
    
    # IMPORTANTE: Substitua com suas credenciais reais
    EMAIL = "seu_email@exemplo.com"
    SENHA = "sua_senha"
    
    buscar_anuncios(
        palavra_chave="honda civic",
        email=EMAIL,
        senha=SENHA,
        cidade="curitiba"
    )


def exemplo_consultar_banco():
    """Exemplo de como consultar os dados salvos no banco"""
    logger.info("=== EXEMPLO 3: Consultar Banco de Dados ===\n")
    
    try:
        conn = sqlite3.connect('marketplace_anuncios.db')
        cursor = conn.cursor()
        
        # Contar total de anúncios
        cursor.execute("SELECT COUNT(*) FROM anuncios")
        total = cursor.fetchone()[0]
        logger.info(f"Total de anúncios no banco: {total}\n")
        
        # Buscar últimos 10 anúncios
        cursor.execute("""
            SELECT titulo, preco, localizacao, url, data_coleta
            FROM anuncios
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        logger.info("Últimos 10 anúncios:")
        logger.info("-" * 80)
        
        for titulo, preco, localizacao, url, data_coleta in cursor.fetchall():
            print(f"\n📌 {titulo}")
            print(f"   💰 Preço: {preco}")
            print(f"   📍 Local: {localizacao}")
            print(f"   🔗 Link: {url}")
            print(f"   📅 Coletado em: {data_coleta}")
        
        # Buscar por palavra-chave específica
        logger.info("\n" + "=" * 80)
        logger.info("Anúncios com 'honda civic':")
        logger.info("-" * 80)
        
        cursor.execute("""
            SELECT titulo, preco, url
            FROM anuncios
            WHERE palavra_chave LIKE '%honda civic%'
            ORDER BY created_at DESC
        """)
        
        for titulo, preco, url in cursor.fetchall():
            print(f"\n{titulo} - {preco}")
            print(f"Link: {url}")
        
        conn.close()
        
    except sqlite3.OperationalError:
        logger.error("Banco de dados não encontrado. Execute uma busca primeiro!")
    except Exception as e:
        logger.error(f"Erro ao consultar banco: {e}")


def exemplo_busca_multiplas_palavras():
    """Exemplo de buscar múltiplas palavras-chave"""
    logger.info("=== EXEMPLO 4: Buscar Múltiplas Palavras-Chave ===\n")
    
    palavras_chave = [
        "honda civic",
        "toyota corolla",
        "ford focus"
    ]
    
    for palavra in palavras_chave:
        logger.info(f"\n🔍 Buscando: {palavra}")
        logger.info("-" * 80)
        
        buscar_anuncios(
            palavra_chave=palavra,
            cidade="curitiba"
        )
        
        logger.info(f"✓ Busca por '{palavra}' concluída!\n")


def exemplo_estatisticas_banco():
    """Exemplo de estatísticas dos anúncios no banco"""
    logger.info("=== EXEMPLO 5: Estatísticas do Banco ===\n")
    
    try:
        conn = sqlite3.connect('marketplace_anuncios.db')
        cursor = conn.cursor()
        
        # Total de anúncios
        cursor.execute("SELECT COUNT(*) FROM anuncios")
        total = cursor.fetchone()[0]
        print(f"📊 Total de anúncios: {total}")
        
        # Anúncios por palavra-chave
        cursor.execute("""
            SELECT palavra_chave, COUNT(*) as quantidade
            FROM anuncios
            GROUP BY palavra_chave
            ORDER BY quantidade DESC
        """)
        
        print("\n📈 Anúncios por palavra-chave:")
        for palavra, quantidade in cursor.fetchall():
            print(f"   {palavra}: {quantidade} anúncios")
        
        # Anúncios por localização
        cursor.execute("""
            SELECT localizacao, COUNT(*) as quantidade
            FROM anuncios
            GROUP BY localizacao
            ORDER BY quantidade DESC
            LIMIT 10
        """)
        
        print("\n📍 Top 10 localizações:")
        for local, quantidade in cursor.fetchall():
            print(f"   {local}: {quantidade} anúncios")
        
        # Anúncios mais recentes
        cursor.execute("""
            SELECT titulo, preco, created_at
            FROM anuncios
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        print("\n🆕 5 Anúncios mais recentes:")
        for titulo, preco, data in cursor.fetchall():
            print(f"   {titulo} - {preco} (em {data})")
        
        conn.close()
        
    except sqlite3.OperationalError:
        logger.error("Banco de dados não encontrado. Execute uma busca primeiro!")
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")


if __name__ == '__main__':
    """
    Execute este arquivo para ver os exemplos em ação
    
    Descomente o exemplo que deseja executar:
    """
    
    # EXEMPLO 1: Busca simples sem login
    # exemplo_busca_simples()
    
    # EXEMPLO 2: Busca com login (configure EMAIL e SENHA primeiro!)
    # exemplo_busca_com_login()
    
    # EXEMPLO 3: Consultar dados do banco
    exemplo_consultar_banco()
    
    # EXEMPLO 4: Buscar múltiplas palavras-chave
    # exemplo_busca_multiplas_palavras()
    
    # EXEMPLO 5: Estatísticas do banco
    # exemplo_estatisticas_banco()
