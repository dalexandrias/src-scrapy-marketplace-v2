"""
Classe base para notificadores
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseNotifier(ABC):
    """Classe abstrata para implementar notificadores"""
    
    @abstractmethod
    async def send(self, message: str) -> bool:
        """
        Envia uma mensagem

        Args:
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def send_anuncio(self, anuncio: Dict) -> bool:
        """
        Envia notificação de um anúncio
        
        Args:
            anuncio: Dicionário com dados do anúncio
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def send_resumo(self, total_facebook: int, total_olx: int, total_novos: int) -> bool:
        """
        Envia resumo diário
        
        Args:
            total_facebook: Total de anúncios do Facebook
            total_olx: Total de anúncios da OLX
            total_novos: Total de novos anúncios
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        pass
