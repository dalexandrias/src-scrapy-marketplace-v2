#!/bin/bash
# Entrypoint script para Docker
# Inicializa o banco de dados se não existir e executa a aplicação

set -e

echo "🚀 Iniciando Scraper Marketplace..."

# Verificar se o diretório data existe
if [ ! -d "/app/data" ]; then
    echo "📁 Criando diretório /app/data..."
    mkdir -p /app/data
fi

# Verificar se o banco de dados existe
DB_PATH="/app/data/marketplace_anuncios.db"
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Banco de dados não encontrado. Criando estrutura inicial..."
    
    # Criar banco de dados com as tabelas necessárias
    python -c "
import sqlite3
import sys
from pathlib import Path

db_path = '/app/data/marketplace_anuncios.db'
print(f'📊 Criando banco de dados em: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabela de anúncios
    cursor.execute('''
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origem TEXT DEFAULT 'facebook',
            categoria TEXT,
            enviado_telegram INTEGER DEFAULT 0,
            data_envio_telegram TEXT,
            data_publicacao TEXT
        )
    ''')
    
    # Tabela de migrações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de credenciais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            username TEXT,
            password TEXT,
            cookies TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de palavras-chave
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palavras_chave (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palavra TEXT UNIQUE NOT NULL,
            categoria TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de configuração do scheduler
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduler_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enabled INTEGER DEFAULT 1,
            interval_minutes INTEGER DEFAULT 30,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de logs de execução
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_type TEXT,
            status TEXT,
            message TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir configuração padrão do scheduler
    cursor.execute('''
        INSERT OR IGNORE INTO scheduler_config (id, enabled, interval_minutes)
        VALUES (1, 1, 30)
    ''')
    
    conn.commit()
    conn.close()
    
    print('✅ Banco de dados criado com sucesso!')
    sys.exit(0)
    
except Exception as e:
    print(f'❌ Erro ao criar banco de dados: {e}')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo "✅ Banco de dados inicializado com sucesso!"
    else
        echo "❌ Falha ao inicializar banco de dados"
        exit 1
    fi
else
    echo "✅ Banco de dados encontrado: $DB_PATH"
fi

# Executar o comando principal
echo "🏃 Executando aplicação..."
exec "$@"
