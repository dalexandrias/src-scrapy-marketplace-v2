"""
Gerenciador de Credenciais com Criptografia
Armazena e recupera credenciais (Facebook, OLX) de forma segura usando Fernet
"""

import sqlite3
import secrets
import sys
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path
from cryptography.fernet import Fernet

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import Config
from src.core.utils.logger import logger


class CredentialsManager:
    """Gerenciador de credenciais criptografadas"""
    
    def __init__(self):
        self.db_path = Config.database.get_connection_string()
    
    def _generate_key(self) -> bytes:
        """
        Gera uma chave de criptografia Fernet
        
        Returns:
            Chave de criptografia em bytes
        """
        return Fernet.generate_key()
    
    def _encrypt_password(self, password: str, key: bytes) -> str:
        """
        Criptografa uma senha usando Fernet
        
        Args:
            password: Senha em texto plano
            key: Chave de criptografia
        
        Returns:
            Senha criptografada em string base64
        """
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return encrypted.decode()
    
    def _decrypt_password(self, encrypted_password: str, key: bytes) -> str:
        """
        Descriptografa uma senha usando Fernet
        
        Args:
            encrypted_password: Senha criptografada
            key: Chave de criptografia
        
        Returns:
            Senha em texto plano
        """
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    
    def save_credentials(self, service: str, username: str, password: str) -> bool:
        """
        Salva credenciais criptografadas no banco
        
        Args:
            service: Nome do serviço (facebook, olx)
            username: Nome de usuário/email
            password: Senha em texto plano
        
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Gerar chave de criptografia
            key = self._generate_key()
            
            # Criptografar senha
            encrypted_password = self._encrypt_password(password, key)
            
            # Salvar no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO credentials 
                (service, username, encrypted_password, encryption_key, is_active, updated_at)
                VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            """, (service.lower(), username, encrypted_password, key.decode()))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Credenciais salvas para {service}: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais: {e}", exc_info=True)
            return False
    
    def get_credentials(self, service: str) -> Optional[Dict[str, str]]:
        """
        Recupera credenciais descriptografadas do banco
        
        Args:
            service: Nome do serviço (facebook, olx)
        
        Returns:
            Dict com username e password, ou None se não encontrado
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, encrypted_password, encryption_key
                FROM credentials
                WHERE service = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            """, (service.lower(),))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                logger.warning(f"Nenhuma credencial encontrada para {service}")
                return None
            
            username, encrypted_password, key = result
            
            # Descriptografar senha
            password = self._decrypt_password(encrypted_password, key.encode())
            
            return {
                'username': username,
                'password': password
            }
            
        except Exception as e:
            logger.error(f"Erro ao recuperar credenciais: {e}", exc_info=True)
            return None
    
    def delete_credentials(self, service: str, username: Optional[str] = None) -> bool:
        """
        Remove credenciais do banco (soft delete)
        
        Args:
            service: Nome do serviço
            username: Nome de usuário específico (opcional)
        
        Returns:
            True se removeu, False caso contrário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if username:
                cursor.execute("""
                    UPDATE credentials
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE service = ? AND username = ?
                """, (service.lower(), username))
            else:
                cursor.execute("""
                    UPDATE credentials
                    SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE service = ?
                """, (service.lower(),))
            
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            
            if rows_affected > 0:
                logger.success(f"Credenciais removidas para {service}")
                return True
            else:
                logger.warning(f"Nenhuma credencial encontrada para remover: {service}")
                return False
            
        except Exception as e:
            logger.error(f"Erro ao remover credenciais: {e}", exc_info=True)
            return False
    
    def list_credentials(self, include_inactive: bool = False) -> List[Dict[str, str]]:
        """
        Lista todas as credenciais cadastradas (sem as senhas)
        
        Args:
            include_inactive: Se True, inclui credenciais inativas
        
        Returns:
            Lista de dicts com informações das credenciais
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if include_inactive:
                cursor.execute("""
                    SELECT service, username, is_active, created_at, updated_at
                    FROM credentials
                    ORDER BY created_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT service, username, is_active, created_at, updated_at
                    FROM credentials
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                """)
            
            results = cursor.fetchall()
            conn.close()
            
            credentials_list = []
            for row in results:
                credentials_list.append({
                    'service': row[0],
                    'username': row[1],
                    'is_active': bool(row[2]),
                    'created_at': row[3],
                    'updated_at': row[4]
                })
            
            return credentials_list
            
        except Exception as e:
            logger.error(f"Erro ao listar credenciais: {e}", exc_info=True)
            return []
    
    def test_credentials(self, service: str) -> bool:
        """
        Testa se as credenciais existem e podem ser recuperadas
        
        Args:
            service: Nome do serviço
        
        Returns:
            True se credenciais válidas, False caso contrário
        """
        creds = self.get_credentials(service)
        return creds is not None and 'username' in creds and 'password' in creds


if __name__ == "__main__":
    # Teste do módulo
    print("=" * 60)
    print("TESTE DO CREDENTIALS MANAGER")
    print("=" * 60)
    
    manager = CredentialsManager()
    
    # Teste 1: Salvar credenciais
    print("\n1. Testando salvamento de credenciais...")
    success = manager.save_credentials("facebook", "teste@email.com", "senha_teste_123")
    print(f"   Resultado: {'✅ Sucesso' if success else '❌ Falha'}")
    
    # Teste 2: Recuperar credenciais
    print("\n2. Testando recuperação de credenciais...")
    creds = manager.get_credentials("facebook")
    if creds:
        print(f"   ✅ Credenciais recuperadas:")
        print(f"      Username: {creds['username']}")
        print(f"      Password: {creds['password']}")
    else:
        print("   ❌ Falha ao recuperar")
    
    # Teste 3: Listar credenciais
    print("\n3. Listando todas as credenciais...")
    all_creds = manager.list_credentials()
    for cred in all_creds:
        print(f"   - {cred['service']}: {cred['username']} (Ativo: {cred['is_active']})")
    
    # Teste 4: Testar credenciais
    print("\n4. Testando validação...")
    is_valid = manager.test_credentials("facebook")
    print(f"   Resultado: {'✅ Válido' if is_valid else '❌ Inválido'}")
    
    # Teste 5: Remover credenciais
    print("\n5. Removendo credenciais de teste...")
    removed = manager.delete_credentials("facebook", "teste@email.com")
    print(f"   Resultado: {'✅ Removido' if removed else '❌ Falha'}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
