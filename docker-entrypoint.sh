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
    echo "🔄 Executando migrações do banco de dados..."
    
    # Executar migrações se o banco já existe
    python -c "
import sqlite3
import sys

db_path = '/app/data/marketplace_anuncios.db'
print(f'📊 Executando migrações em: {db_path}')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Função auxiliar para verificar se coluna existe
    def column_exists(table, column):
        cursor.execute(f'PRAGMA table_info({table})')
        columns = [row[1] for row in cursor.fetchall()]
        return column in columns
    
    # Função auxiliar para verificar se tabela existe
    def table_exists(table):
        cursor.execute(
            \"SELECT name FROM sqlite_master WHERE type='table' AND name=?\",
            (table,)
        )
        return cursor.fetchone() is not None
    
    changes_made = False
    
    # 1. Adicionar colunas que faltam na tabela anuncios
    if table_exists('anuncios'):
        if not column_exists('anuncios', 'origem'):
            print('  ➕ Adicionando coluna origem...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN origem TEXT DEFAULT \"facebook\"')
            changes_made = True
        
        if not column_exists('anuncios', 'categoria'):
            print('  ➕ Adicionando coluna categoria...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN categoria TEXT')
            changes_made = True
        
        if not column_exists('anuncios', 'data_publicacao'):
            print('  ➕ Adicionando coluna data_publicacao...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN data_publicacao TIMESTAMP')
            changes_made = True
        
        if not column_exists('anuncios', 'enviado_telegram'):
            print('  ➕ Adicionando coluna enviado_telegram...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN enviado_telegram INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('anuncios', 'data_envio_telegram'):
            print('  ➕ Adicionando coluna data_envio_telegram...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN data_envio_telegram TEXT')
            changes_made = True
        
        if not column_exists('anuncios', 'ultima_visualizacao'):
            print('  ➕ Adicionando coluna ultima_visualizacao...')
            cursor.execute('ALTER TABLE anuncios ADD COLUMN ultima_visualizacao TIMESTAMP')
            changes_made = True
    
    # 2. Criar tabela credentials se não existir
    if not table_exists('credentials'):
        print('  ➕ Criando tabela credentials...')
        cursor.execute('''
            CREATE TABLE credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                identifier TEXT NOT NULL,
                credential TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(service, identifier)
            )
        ''')
        changes_made = True
    
    # 3. Criar/atualizar tabela palavras_chave
    if not table_exists('palavras_chave'):
        print('  ➕ Criando tabela palavras_chave...')
        cursor.execute('''
            CREATE TABLE palavras_chave (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                palavra TEXT NOT NULL UNIQUE,
                ativo INTEGER DEFAULT 1,
                origem TEXT DEFAULT 'todas',
                prioridade INTEGER DEFAULT 0,
                total_encontrados INTEGER DEFAULT 0,
                ultima_busca TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        changes_made = True
    else:
        # Adicionar colunas que faltam na tabela palavras_chave existente
        if not column_exists('palavras_chave', 'ativo'):
            print('  ➕ Adicionando coluna ativo à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN ativo INTEGER DEFAULT 1')
            changes_made = True
        
        if not column_exists('palavras_chave', 'origem'):
            print('  ➕ Adicionando coluna origem à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN origem TEXT DEFAULT \"todas\"')
            changes_made = True
        
        if not column_exists('palavras_chave', 'prioridade'):
            print('  ➕ Adicionando coluna prioridade à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN prioridade INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('palavras_chave', 'total_encontrados'):
            print('  ➕ Adicionando coluna total_encontrados à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN total_encontrados INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('palavras_chave', 'ultima_busca'):
            print('  ➕ Adicionando coluna ultima_busca à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN ultima_busca TIMESTAMP')
            changes_made = True
        
        if not column_exists('palavras_chave', 'updated_at'):
            print('  ➕ Adicionando coluna updated_at à palavras_chave...')
            cursor.execute('ALTER TABLE palavras_chave ADD COLUMN updated_at TIMESTAMP')
            changes_made = True
    
    # 4. Criar/atualizar tabela scheduler_config
    if not table_exists('scheduler_config'):
        print('  ➕ Criando tabela scheduler_config...')
        cursor.execute('''
            CREATE TABLE scheduler_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER DEFAULT 0,
                interval_minutes INTEGER DEFAULT 30,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                total_runs INTEGER DEFAULT 0,
                total_errors INTEGER DEFAULT 0,
                is_running INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute(
            'INSERT OR IGNORE INTO scheduler_config (id, enabled, interval_minutes) VALUES (1, 0, 30)'
        )
        changes_made = True
    else:
        # Adicionar colunas que faltam na tabela scheduler_config
        if not column_exists('scheduler_config', 'last_run'):
            print('  ➕ Adicionando coluna last_run à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN last_run TIMESTAMP')
            changes_made = True
        
        if not column_exists('scheduler_config', 'next_run'):
            print('  ➕ Adicionando coluna next_run à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN next_run TIMESTAMP')
            changes_made = True
        
        if not column_exists('scheduler_config', 'total_runs'):
            print('  ➕ Adicionando coluna total_runs à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN total_runs INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('scheduler_config', 'total_errors'):
            print('  ➕ Adicionando coluna total_errors à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN total_errors INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('scheduler_config', 'created_at'):
            print('  ➕ Adicionando coluna created_at à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN created_at TIMESTAMP')
            changes_made = True
        
        if not column_exists('scheduler_config', 'updated_at'):
            print('  ➕ Adicionando coluna updated_at à scheduler_config...')
            cursor.execute('ALTER TABLE scheduler_config ADD COLUMN updated_at TIMESTAMP')
            changes_made = True
    
    # 5. Criar/atualizar tabela execution_logs
    if not table_exists('execution_logs'):
        print('  ➕ Criando tabela execution_logs...')
        cursor.execute('''
            CREATE TABLE execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL CHECK(tipo IN ('facebook', 'olx', 'manual', 'scheduled')),
                palavra_chave TEXT,
                status TEXT NOT NULL CHECK(status IN ('success', 'error', 'running')),
                total_encontrados INTEGER DEFAULT 0,
                total_novos INTEGER DEFAULT 0,
                mensagem TEXT,
                duracao_segundos REAL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP
            )
        ''')
        changes_made = True
    else:
        # Renomear execution_type para tipo se existir
        if column_exists('execution_logs', 'execution_type') and not column_exists('execution_logs', 'tipo'):
            print('  ➕ Renomeando coluna execution_type para tipo...')
            # SQLite não suporta RENAME COLUMN facilmente, então vamos criar nova coluna
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN tipo TEXT')
            cursor.execute('UPDATE execution_logs SET tipo = execution_type')
            changes_made = True
        
        # Adicionar coluna tipo se não existir
        if not column_exists('execution_logs', 'tipo'):
            print('  ➕ Adicionando coluna tipo à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN tipo TEXT')
            changes_made = True
        
        # Adicionar coluna palavra_chave se não existir
        if not column_exists('execution_logs', 'palavra_chave'):
            print('  ➕ Adicionando coluna palavra_chave à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN palavra_chave TEXT')
            changes_made = True
        
        # Adicionar outras colunas que possam estar faltando
        if not column_exists('execution_logs', 'total_encontrados'):
            print('  ➕ Adicionando coluna total_encontrados à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN total_encontrados INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('execution_logs', 'total_novos'):
            print('  ➕ Adicionando coluna total_novos à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN total_novos INTEGER DEFAULT 0')
            changes_made = True
        
        if not column_exists('execution_logs', 'mensagem'):
            print('  ➕ Adicionando coluna mensagem à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN mensagem TEXT')
            changes_made = True
        
        if not column_exists('execution_logs', 'duracao_segundos'):
            print('  ➕ Adicionando coluna duracao_segundos à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN duracao_segundos REAL')
            changes_made = True
        
        if not column_exists('execution_logs', 'started_at'):
            print('  ➕ Adicionando coluna started_at à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN started_at TIMESTAMP')
            changes_made = True
        
        if not column_exists('execution_logs', 'finished_at'):
            print('  ➕ Adicionando coluna finished_at à execution_logs...')
            cursor.execute('ALTER TABLE execution_logs ADD COLUMN finished_at TIMESTAMP')
            changes_made = True
    
    # COMMIT de todas as tabelas/colunas antes de criar índices
    conn.commit()
    
    # 6. Criar índices (após commit)
    indices = [
        ('anuncios', 'idx_url', 'CREATE INDEX IF NOT EXISTS idx_url ON anuncios(url)'),
        ('anuncios', 'idx_palavra_chave', 'CREATE INDEX IF NOT EXISTS idx_palavra_chave ON anuncios(palavra_chave)'),
        ('anuncios', 'idx_origem', 'CREATE INDEX IF NOT EXISTS idx_origem ON anuncios(origem)'),
        ('anuncios', 'idx_enviado_telegram', 'CREATE INDEX IF NOT EXISTS idx_enviado_telegram ON anuncios(enviado_telegram)'),
        ('anuncios', 'idx_data_publicacao', 'CREATE INDEX IF NOT EXISTS idx_data_publicacao ON anuncios(data_publicacao)'),
        ('anuncios', 'idx_ultima_visualizacao', 'CREATE INDEX IF NOT EXISTS idx_ultima_visualizacao ON anuncios(ultima_visualizacao)'),
        ('credentials', 'idx_credentials_service', 'CREATE INDEX IF NOT EXISTS idx_credentials_service ON credentials(service)'),
        ('credentials', 'idx_credentials_active', 'CREATE INDEX IF NOT EXISTS idx_credentials_active ON credentials(is_active)'),
        ('palavras_chave', 'idx_palavras_ativo', 'CREATE INDEX IF NOT EXISTS idx_palavras_ativo ON palavras_chave(ativo)'),
        ('palavras_chave', 'idx_palavras_origem', 'CREATE INDEX IF NOT EXISTS idx_palavras_origem ON palavras_chave(origem)'),
        ('palavras_chave', 'idx_palavras_prioridade', 'CREATE INDEX IF NOT EXISTS idx_palavras_prioridade ON palavras_chave(prioridade DESC)'),
        ('execution_logs', 'idx_logs_tipo', 'CREATE INDEX IF NOT EXISTS idx_logs_tipo ON execution_logs(tipo)'),
        ('execution_logs', 'idx_logs_status', 'CREATE INDEX IF NOT EXISTS idx_logs_status ON execution_logs(status)'),
        ('execution_logs', 'idx_logs_started_at', 'CREATE INDEX IF NOT EXISTS idx_logs_started_at ON execution_logs(started_at DESC)'),
    ]
    
    for table_name, index_name, index_sql in indices:
        if table_exists(table_name):
            try:
                cursor.execute(index_sql)
            except Exception:
                pass  # Índice já existe ou erro
    
    conn.commit()
    conn.close()
    
    if changes_made:
        print('✅ Migrações aplicadas com sucesso!')
    else:
        print('✅ Banco de dados já está atualizado!')
    
    sys.exit(0)
    
except Exception as e:
    print(f'❌ Erro ao executar migrações: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    
    if [ $? -ne 0 ]; then
        echo "❌ Falha ao executar migrações"
        exit 1
    fi
fi

# Executar o comando principal
echo "🏃 Executando aplicação..."
exec "$@"
