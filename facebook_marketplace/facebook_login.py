"""
Módulo para gerenciar login e autenticação no Facebook
"""

import time
import pickle
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class FacebookLogin:
    """Classe para gerenciar login no Facebook"""
    
    def __init__(self, headless=True):
        """
        Inicializa o FacebookLogin
        
        Args:
            headless (bool): Se True, executa o navegador em modo headless
        """
        self.logger = logging.getLogger(__name__)
        self.headless = headless
        self.driver = None
        self.cookies_file = Path('facebook_cookies.pkl')
        
    def _setup_driver(self):
        """Configura o driver do Chrome com as opções necessárias"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Opções para evitar detecção de automação
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # Remove indicadores de automação
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Instala e configura o ChromeDriver automaticamente
        service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove a propriedade webdriver
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.logger.info("Driver do Chrome configurado com sucesso")
        
    def login(self, email, password, save_cookies=True):
        """
        Realiza login no Facebook
        
        Args:
            email (str): Email ou telefone do Facebook
            password (str): Senha do Facebook
            save_cookies (bool): Se True, salva os cookies após login bem-sucedido
            
        Returns:
            bool: True se login foi bem-sucedido, False caso contrário
        """
        try:
            self.logger.info("Iniciando processo de login no Facebook")
            
            if not self.driver:
                self._setup_driver()
            
            # Acessa a página de login
            self.driver.get('https://www.facebook.com')
            self.logger.info("Página do Facebook carregada")
            
            # Aguarda a página carregar
            time.sleep(3)
            
            # Tenta encontrar e preencher o campo de email
            try:
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                email_field.clear()
                email_field.send_keys(email)
                self.logger.info("Email preenchido")
            except TimeoutException:
                self.logger.error("Campo de email não encontrado")
                return False
            
            # Tenta encontrar e preencher o campo de senha
            try:
                password_field = self.driver.find_element(By.ID, "pass")
                password_field.clear()
                password_field.send_keys(password)
                self.logger.info("Senha preenchida")
            except NoSuchElementException:
                self.logger.error("Campo de senha não encontrado")
                return False
            
            # Aguarda um pouco antes de clicar no botão
            time.sleep(2)
            
            # Tenta encontrar e clicar no botão de login
            try:
                login_button = self.driver.find_element(By.NAME, "login")
                login_button.click()
                self.logger.info("Botão de login clicado")
            except NoSuchElementException:
                self.logger.error("Botão de login não encontrado")
                return False
            
            # Aguarda o login processar
            time.sleep(5)
            
            # Verifica se o login foi bem-sucedido
            if self._verificar_login_sucesso():
                self.logger.info("Login realizado com sucesso!")
                
                if save_cookies:
                    self._salvar_cookies()
                
                return True
            else:
                self.logger.warning("Login pode ter falho ou requer verificação adicional")
                self.logger.warning(f"URL atual: {self.driver.current_url}")
                
                # Verifica se há mensagens de erro
                self._verificar_erros_login()
                
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante o processo de login: {e}")
            return False
    
    def _verificar_login_sucesso(self):
        """
        Verifica se o login foi bem-sucedido
        
        Returns:
            bool: True se login foi bem-sucedido
        """
        try:
            # Verifica se foi redirecionado para a página inicial
            current_url = self.driver.current_url
            
            # Se não está mais na página de login, provavelmente teve sucesso
            if 'login' not in current_url.lower():
                return True
            
            # Tenta encontrar elementos que só aparecem quando logado
            try:
                # Procura por elementos comuns da página inicial do Facebook
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Facebook']"))
                )
                return True
            except TimeoutException:
                pass
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar login: {e}")
            return False
    
    def _verificar_erros_login(self):
        """Verifica se há mensagens de erro na página de login"""
        try:
            # Procura por mensagens de erro comuns
            error_selectors = [
                "._9ay7",  # Mensagem de erro genérica
                "[data-testid='royal_login_error']",
                ".error",
            ]
            
            for selector in error_selectors:
                try:
                    error_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if error_element and error_element.is_displayed():
                        self.logger.error(f"Mensagem de erro encontrada: {error_element.text}")
                        return
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Erro ao verificar mensagens de erro: {e}")
    
    def _salvar_cookies(self):
        """Salva os cookies da sessão em um arquivo"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            self.logger.info(f"Cookies salvos em {self.cookies_file}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar cookies: {e}")
    
    def carregar_cookies(self):
        """
        Carrega cookies salvos anteriormente
        
        Returns:
            bool: True se cookies foram carregados com sucesso
        """
        try:
            if not self.cookies_file.exists():
                self.logger.warning("Arquivo de cookies não encontrado")
                return False
            
            if not self.driver:
                self._setup_driver()
            
            # Precisa acessar o Facebook primeiro para carregar os cookies
            self.driver.get('https://www.facebook.com')
            time.sleep(2)
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.debug(f"Não foi possível adicionar cookie: {e}")
            
            self.logger.info("Cookies carregados com sucesso")
            
            # Recarrega a página para aplicar os cookies
            self.driver.refresh()
            time.sleep(3)
            
            # Verifica se ainda está logado
            if self._verificar_login_sucesso():
                self.logger.info("Sessão restaurada com sucesso usando cookies")
                return True
            else:
                self.logger.warning("Cookies não são mais válidos")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar cookies: {e}")
            return False
    
    def get_cookies_dict(self):
        """
        Retorna os cookies em formato de dicionário para uso com requests/scrapy
        
        Returns:
            dict: Dicionário com os cookies
        """
        if not self.driver:
            self.logger.warning("Driver não inicializado")
            return {}
        
        cookies = self.driver.get_cookies()
        return {cookie['name']: cookie['value'] for cookie in cookies}
    
    def close(self):
        """Fecha o driver do navegador"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Driver fechado")
