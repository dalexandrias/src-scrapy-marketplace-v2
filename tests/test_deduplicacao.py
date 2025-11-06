"""
Script de teste para verificar sistema de deduplicação de anúncios no Telegram
Execute: python tests/test_deduplicacao.py
"""
import sqlite3
from pathlib import Path
import sys

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

db_path = Path(__file__).parent.parent / "data" / "marketplace_anuncios.db"

def verificar_status():
    """Verifica status atual dos anúncios"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("🔍 VERIFICAÇÃO DO SISTEMA DE DEDUPLICAÇÃO")
    print("="*60)

    # 1. Total de anúncios
    cursor.execute("SELECT COUNT(*) FROM anuncios")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total de anúncios no banco: {total}")

    # 2. Já enviados
    cursor.execute("SELECT COUNT(*) FROM anuncios WHERE enviado_telegram = 1")
    enviados = cursor.fetchone()[0]
    print(f"✅ Anúncios já enviados: {enviados} ({enviados/total*100:.1f}%)")

    # 3. Não enviados
    cursor.execute("SELECT COUNT(*) FROM anuncios WHERE enviado_telegram = 0 OR enviado_telegram IS NULL")
    nao_enviados = cursor.fetchone()[0]
    print(f"📭 Anúncios não enviados: {nao_enviados} ({nao_enviados/total*100:.1f}%)")

    # 4. Por origem
    print("\n📈 Estatísticas por origem:")
    for origem in ['olx', 'facebook']:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN enviado_telegram = 1 THEN 1 ELSE 0 END) as enviados
            FROM anuncios 
            WHERE origem = ?
        """, (origem,))
        total_origem, enviados_origem = cursor.fetchone()
        nao_enviados_origem = total_origem - enviados_origem
        print(f"  🔹 {origem.upper()}:")
        print(f"     Total: {total_origem} | Enviados: {enviados_origem} | Novos: {nao_enviados_origem}")

    # 5. Últimos 5 enviados
    cursor.execute("""
        SELECT titulo, origem, data_envio_telegram 
        FROM anuncios 
        WHERE enviado_telegram = 1
        ORDER BY data_envio_telegram DESC
        LIMIT 5
    """)
    enviados_recentes = cursor.fetchall()
    
    if enviados_recentes:
        print("\n📤 Últimos 5 anúncios enviados:")
        for titulo, origem, data in enviados_recentes:
            print(f"  - [{origem.upper()}] {titulo[:40]}... ({data})")
    
    # 6. Próximos 5 a enviar
    cursor.execute("""
        SELECT id, titulo, origem, palavra_chave 
        FROM anuncios 
        WHERE enviado_telegram = 0 OR enviado_telegram IS NULL
        ORDER BY data_coleta DESC
        LIMIT 5
    """)
    proximos = cursor.fetchall()
    
    if proximos:
        print("\n📥 Próximos 5 anúncios a enviar:")
        for id_anuncio, titulo, origem, palavra in proximos:
            print(f"  [{id_anuncio}] {origem.upper()}: {titulo[:40]}... ('{palavra}')")

    conn.close()
    print("\n" + "="*60)
    print("✅ Verificação concluída!")
    print("="*60 + "\n")

def resetar_status():
    """Reseta status de envio de todos os anúncios (APENAS PARA TESTES!)"""
    print("\n⚠️  ATENÇÃO: Esta ação vai resetar o status de TODOS os anúncios!")
    confirmacao = input("Digite 'CONFIRMAR' para prosseguir: ")
    
    if confirmacao != 'CONFIRMAR':
        print("❌ Operação cancelada.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE anuncios SET enviado_telegram = 0, data_envio_telegram = NULL")
    conn.commit()
    
    print(f"✅ {cursor.rowcount} anúncios resetados!")
    print("💡 Todos os anúncios foram marcados como 'não enviados'.")
    
    conn.close()

def main():
    """Menu principal"""
    while True:
        print("\n" + "="*60)
        print("🧪 TESTE DE DEDUPLICAÇÃO - MENU")
        print("="*60)
        print("\n1. Verificar status atual")
        print("2. Resetar status de envio (CUIDADO!)")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == '1':
            verificar_status()
        elif opcao == '2':
            resetar_status()
        elif opcao == '3':
            print("\n👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    main()
