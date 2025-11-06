"""
Gerenciador de Palavras-Chave
Gerencia palavras de busca para OLX e Facebook Marketplace
"""

import sqlite3
import sys
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.utils.logger import logger


class KeywordsManager:
    """Gerenciador de palavras-chave para busca"""
    
    def __init__(self):
        self.db_path = Config.database.get_connection_string()
    
    def add_keyword(self, palavra: str, origem: str = "ambos", prioridade: int = 1) -> bool:
        """
        Adiciona uma palavra-chave para busca
        
        Args:
            palavra: Palavra ou termo de busca
            origem: Onde buscar (olx, facebook, ambos)
            prioridade: Prioridade da busca (1=baixa, 2=média, 3=alta)
        
        Returns:
            True se adicionou com sucesso, False se já existe ou erro
        """
        try:
            # Validar origem
            origem = origem.lower()
            if origem not in ['olx', 'facebook', 'ambos']:
                logger.error(f"Origem inválida: {origem}. Use: olx, facebook ou ambos")
                return False
            
            # Validar prioridade
            if prioridade not in [1, 2, 3]:
                logger.warning(f"Prioridade inválida: {prioridade}. Usando prioridade 1 (baixa)")
                prioridade = 1
            
            # Normalizar palavra (minúsculas, espaços removidos)
            palavra_normalizada = palavra.strip().lower()
            
            if not palavra_normalizada:
                logger.error("Palavra-chave vazia não pode ser adicionada")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar se já existe
            cursor.execute("""
                SELECT id, ativo FROM palavras_chave
                WHERE LOWER(palavra) = ?
            """, (palavra_normalizada,))
            
            result = cursor.fetchone()
            
            if result:
                keyword_id, ativo = result
                if ativo:
                    logger.warning(f"Palavra-chave '{palavra}' já existe e está ativa")
                    conn.close()
                    return False
                else:
                    # Reativar palavra existente
                    cursor.execute("""
                        UPDATE palavras_chave
                        SET ativo = 1, origem = ?, prioridade = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (origem, prioridade, keyword_id))
                    logger.success(f"Palavra-chave '{palavra}' reativada")
            else:
                # Verificar limite de palavras ativas (baseado em MAX_WORKERS)
                max_workers = Config.scheduler.get_max_workers()
                cursor.execute("SELECT COUNT(*) FROM palavras_chave WHERE ativo = 1")
                count = cursor.fetchone()[0]
                
                if count >= max_workers:
                    logger.error(f"❌ Limite de palavras-chave atingido ({count}/{max_workers})")
                    logger.info(f"💡 Aumente SCHEDULER_MAX_WORKERS no .env (atual: {max_workers}) ou remova palavras inativas")
                    conn.close()
                    return False
                
                # Adicionar nova palavra
                cursor.execute("""
                    INSERT INTO palavras_chave (palavra, origem, ativo, prioridade)
                    VALUES (?, ?, 1, ?)
                """, (palavra_normalizada, origem, prioridade))
                logger.success(f"Palavra-chave '{palavra}' adicionada (origem: {origem}, prioridade: {prioridade}) [{count + 1}/{max_workers}]")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao adicionar palavra-chave: {e}", exc_info=True)
            return False
    
    def remove_keyword(self, palavra: str) -> bool:
        """
        Remove (desativa) uma palavra-chave
        
        Args:
            palavra: Palavra a ser removida
        
        Returns:
            True se removeu, False caso contrário
        """
        try:
            palavra_normalizada = palavra.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE palavras_chave
                SET ativo = 0, updated_at = CURRENT_TIMESTAMP
                WHERE LOWER(palavra) = ? AND ativo = 1
            """, (palavra_normalizada,))
            
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected > 0:
                logger.success(f"Palavra-chave '{palavra}' removida")
                return True
            else:
                logger.warning(f"Palavra-chave '{palavra}' não encontrada ou já está inativa")
                return False
            
        except Exception as e:
            logger.error(f"Erro ao remover palavra-chave: {e}", exc_info=True)
            return False
    
    def toggle_keyword(self, palavra: str) -> Tuple[bool, bool]:
        """
        Alterna o status ativo/inativo de uma palavra-chave
        
        Args:
            palavra: Palavra a ser alternada
        
        Returns:
            Tupla (sucesso: bool, novo_status: bool)
        """
        try:
            palavra_normalizada = palavra.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar status atual
            cursor.execute("""
                SELECT id, ativo FROM palavras_chave
                WHERE LOWER(palavra) = ?
            """, (palavra_normalizada,))
            
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Palavra-chave '{palavra}' não encontrada")
                conn.close()
                return False, False
            
            keyword_id, ativo_atual = result
            novo_status = 0 if ativo_atual else 1
            
            cursor.execute("""
                UPDATE palavras_chave
                SET ativo = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_status, keyword_id))
            
            conn.commit()
            conn.close()
            
            status_text = "ativada" if novo_status else "desativada"
            logger.success(f"Palavra-chave '{palavra}' {status_text}")
            
            return True, bool(novo_status)
            
        except Exception as e:
            logger.error(f"Erro ao alternar palavra-chave: {e}", exc_info=True)
            return False, False
    
    def list_keywords(self, origem: Optional[str] = None, only_active: bool = True) -> List[Dict]:
        """
        Lista palavras-chave cadastradas
        
        Args:
            origem: Filtrar por origem (olx, facebook, ambos) ou None para todas
            only_active: Se True, retorna apenas palavras ativas
        
        Returns:
            Lista de dicts com informações das palavras-chave
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id, palavra, origem, ativo, prioridade, 
                    total_encontrados, ultima_busca, created_at
                FROM palavras_chave
                WHERE 1=1
            """
            params = []
            
            if origem:
                query += " AND origem = ?"
                params.append(origem.lower())
            
            if only_active:
                query += " AND ativo = 1"
            
            query += " ORDER BY prioridade DESC, created_at ASC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            
            keywords_list = []
            for row in results:
                keywords_list.append({
                    'id': row[0],
                    'palavra': row[1],
                    'origem': row[2],
                    'ativo': bool(row[3]),
                    'prioridade': row[4],
                    'total_encontrados': row[5] or 0,
                    'ultima_busca': row[6],
                    'created_at': row[7]
                })
            
            return keywords_list
            
        except Exception as e:
            logger.error(f"Erro ao listar palavras-chave: {e}", exc_info=True)
            return []
    
    def get_keyword_stats(self, palavra: str) -> Optional[Dict]:
        """
        Retorna estatísticas de uma palavra-chave
        
        Args:
            palavra: Palavra a consultar
        
        Returns:
            Dict com estatísticas ou None se não encontrado
        """
        try:
            palavra_normalizada = palavra.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    palavra, origem, ativo, prioridade,
                    total_encontrados, ultima_busca, created_at, updated_at
                FROM palavras_chave
                WHERE LOWER(palavra) = ?
            """, (palavra_normalizada,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            return {
                'palavra': result[0],
                'origem': result[1],
                'ativo': bool(result[2]),
                'prioridade': result[3],
                'total_encontrados': result[4] or 0,
                'ultima_busca': result[5],
                'created_at': result[6],
                'updated_at': result[7]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}", exc_info=True)
            return None
    
    def update_keyword_stats(self, palavra: str, novos_encontrados: int) -> bool:
        """
        Atualiza estatísticas de uma palavra-chave após busca
        
        Args:
            palavra: Palavra que foi buscada
            novos_encontrados: Quantidade de resultados encontrados
        
        Returns:
            True se atualizou, False caso contrário
        """
        try:
            palavra_normalizada = palavra.strip().lower()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE palavras_chave
                SET 
                    total_encontrados = total_encontrados + ?,
                    ultima_busca = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE LOWER(palavra) = ?
            """, (novos_encontrados, palavra_normalizada))
            
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"Estatísticas atualizadas para '{palavra}': +{novos_encontrados} resultados")
                return True
            else:
                logger.warning(f"Palavra-chave '{palavra}' não encontrada para atualização de stats")
                return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}", exc_info=True)
            return False
    
    def get_keywords_for_search(self, origem: str) -> List[str]:
        """
        Retorna lista de palavras ativas para uma origem específica
        
        Args:
            origem: Origem da busca (olx ou facebook)
        
        Returns:
            Lista de palavras-chave prontas para busca
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT palavra FROM palavras_chave
                WHERE ativo = 1 
                AND (origem = ? OR origem = 'ambos')
                ORDER BY prioridade DESC
            """, (origem.lower(),))
            
            results = cursor.fetchall()
            conn.close()
            
            return [row[0] for row in results]
            
        except Exception as e:
            logger.error(f"Erro ao buscar palavras para pesquisa: {e}", exc_info=True)
            return []
    
    def get_keywords_limit_status(self) -> Dict:
        """
        Retorna o status do limite de palavras-chave
        
        Returns:
            Dict com: total_ativas, limite, disponivel, percentual_uso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM palavras_chave WHERE ativo = 1")
            total_ativas = cursor.fetchone()[0]
            conn.close()
            
            limite = Config.scheduler.get_max_workers()
            disponivel = max(0, limite - total_ativas)
            percentual = (total_ativas / limite * 100) if limite > 0 else 0
            
            return {
                'total_ativas': total_ativas,
                'limite': limite,
                'disponivel': disponivel,
                'percentual_uso': round(percentual, 1),
                'no_limite': total_ativas >= limite
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar limite de palavras: {e}", exc_info=True)
            return {
                'total_ativas': 0,
                'limite': 0,
                'disponivel': 0,
                'percentual_uso': 0,
                'no_limite': False
            }


if __name__ == "__main__":
    # Teste do módulo
    print("=" * 60)
    print("TESTE DO KEYWORDS MANAGER")
    print("=" * 60)
    
    manager = KeywordsManager()
    
    # Teste 1: Adicionar palavras-chave
    print("\n1. Adicionando palavras-chave...")
    palavras_teste = [
        ("honda civic", "ambos", 3),
        ("corolla", "olx", 2),
        ("ford focus", "facebook", 1),
    ]
    
    for palavra, origem, prioridade in palavras_teste:
        success = manager.add_keyword(palavra, origem, prioridade)
        print(f"   {palavra}: {'✅' if success else '❌'}")
    
    # Teste 2: Listar palavras-chave
    print("\n2. Listando palavras-chave ativas...")
    keywords = manager.list_keywords()
    for kw in keywords:
        print(f"   - {kw['palavra']} ({kw['origem']}) - Prioridade: {kw['prioridade']}")
    
    # Teste 3: Estatísticas
    print("\n3. Consultando estatísticas de 'honda civic'...")
    stats = manager.get_keyword_stats("honda civic")
    if stats:
        print(f"   ✅ Palavra: {stats['palavra']}")
        print(f"      Origem: {stats['origem']}")
        print(f"      Prioridade: {stats['prioridade']}")
        print(f"      Total encontrados: {stats['total_encontrados']}")
    
    # Teste 4: Atualizar stats
    print("\n4. Simulando busca (10 resultados)...")
    updated = manager.update_keyword_stats("honda civic", 10)
    print(f"   {'✅ Atualizado' if updated else '❌ Falha'}")
    
    # Teste 5: Palavras para busca
    print("\n5. Buscando palavras ativas para OLX...")
    olx_keywords = manager.get_keywords_for_search("olx")
    print(f"   Encontradas: {olx_keywords}")
    
    # Teste 6: Remover palavra
    print("\n6. Removendo 'ford focus'...")
    removed = manager.remove_keyword("ford focus")
    print(f"   {'✅ Removida' if removed else '❌ Falha'}")
    
    # Teste 7: Listar novamente
    print("\n7. Listando palavras ativas (após remoção)...")
    keywords_after = manager.list_keywords()
    print(f"   Total ativas: {len(keywords_after)}")
    for kw in keywords_after:
        print(f"   - {kw['palavra']}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
