"""
Gerenciador de Agendamento de Buscas
Usa APScheduler para executar buscas automaticamente em intervalos configuráveis
"""

import sqlite3
import subprocess
import sys
import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from config import Config
from utils.logger import logger
from keywords_manager import KeywordsManager


class SchedulerManager:
    """Gerenciador de agendamento de buscas automáticas"""
    
    # Intervalos disponíveis em minutos
    INTERVAL_10_MIN = 10
    INTERVAL_30_MIN = 30
    INTERVAL_1_HOUR = 60
    
    VALID_INTERVALS = [INTERVAL_10_MIN, INTERVAL_30_MIN, INTERVAL_1_HOUR]
    
    def __init__(self, on_search_complete: Optional[Callable] = None):
        """
        Inicializa o scheduler
        
        Args:
            on_search_complete: Callback chamado ao finalizar busca (para notificar via Telegram)
        """
        self.db_path = Config.database.get_connection_string()
        self.scheduler = BackgroundScheduler(timezone='America/Sao_Paulo')
        self.keywords_manager = KeywordsManager()
        self.on_search_complete = on_search_complete
        self.project_root = Path(__file__).parent
        
        # Adicionar listeners de eventos
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
        
        # Inicializar configuração do scheduler se não existir
        self._init_scheduler_config()
    
    def _init_scheduler_config(self):
        """Inicializa configuração do scheduler no banco se não existir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM scheduler_config")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Criar configuração padrão (30 minutos, desabilitado)
                cursor.execute("""
                    INSERT INTO scheduler_config (interval_minutes, enabled)
                    VALUES (?, 0)
                """, (self.INTERVAL_30_MIN,))
                conn.commit()
                logger.info("Configuração do scheduler inicializada (30 min, desabilitado)")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao inicializar configuração do scheduler: {e}", exc_info=True)
    
    def _job_executed_listener(self, event):
        """Listener para jobs executados com sucesso"""
        logger.info(f"Job executado: {event.job_id}")
    
    def _job_error_listener(self, event):
        """Listener para jobs com erro"""
        logger.error(f"Erro no job {event.job_id}: {event.exception}", exc_info=True)
        self._increment_error_count()
    
    def _increment_error_count(self):
        """Incrementa contador de erros no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduler_config
                SET total_errors = total_errors + 1
                WHERE id = 1
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao incrementar contador de erros: {e}", exc_info=True)
    
    def _log_execution(self, tipo: str, palavra_chave: str, status: str, 
                       total_encontrados: int = 0, total_novos: int = 0, 
                       mensagem: str = "", duracao_segundos: float = 0):
        """
        Registra execução no banco
        
        Args:
            tipo: Tipo de execução (olx, facebook, manual)
            palavra_chave: Palavra buscada
            status: Status da execução (success, error)
            total_encontrados: Total de anúncios encontrados
            total_novos: Total de anúncios novos
            mensagem: Mensagem adicional
            duracao_segundos: Duração da execução
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_logs 
                (tipo, palavra_chave, status, total_encontrados, total_novos, 
                 mensagem, duracao_segundos, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' seconds'), datetime('now'))
            """, (tipo, palavra_chave, status, total_encontrados, total_novos, 
                  mensagem, duracao_segundos, duracao_segundos))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao registrar log de execução: {e}", exc_info=True)
    
    def _run_olx_search(self):
        """Executa busca no OLX para todas as palavras-chave ativas"""
        logger.info("🔍 Iniciando busca automática no OLX...")
        start_time = datetime.now()
        
        try:
            # Buscar palavras-chave ativas para OLX
            keywords = self.keywords_manager.get_keywords_for_search('olx')
            
            if not keywords:
                logger.warning("Nenhuma palavra-chave ativa para OLX")
                return
            
            logger.info(f"Palavras-chave encontradas: {keywords}")
            
            # Executar scraper para cada palavra
            total_encontrados = 0
            total_novos = 0
            
            for palavra in keywords:
                try:
                    logger.info(f"Buscando '{palavra}' no OLX...")
                    
                    # Executar scraper OLX com Playwright (novo método)
                    python_exe = sys.executable
                    script_path = self.project_root / "buscar_olx_new.py"
                    
                    # Configurar ambiente com UTF-8
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    
                    result = subprocess.run(
                        [python_exe, str(script_path), palavra],
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        env=env,
                        timeout=300  # 5 minutos timeout
                    )
                    
                    if result.returncode == 0:
                        logger.success(f"Busca OLX concluída para '{palavra}'")
                        
                        # Parsear output para extrair resultados (formato: RESULT_JSON:{...})
                        encontrados_palavra = 0
                        novos_palavra = 0
                        
                        try:
                            import json
                            import re
                            
                            # Procurar linha com RESULT_JSON: no stdout
                            match = re.search(r'RESULT_JSON:(.+)', result.stdout)
                            if match:
                                resultado = json.loads(match.group(1))
                                encontrados_palavra = resultado.get('encontrados', 0)
                                novos_palavra = resultado.get('salvos', 0)
                                logger.info(f"📊 Resultados parseados: {encontrados_palavra} encontrados, {novos_palavra} novos")
                            else:
                                logger.warning("Não foi possível parsear resultados do scraper")
                        except Exception as e:
                            logger.warning(f"Erro ao parsear resultados: {e}")
                        
                        total_encontrados += encontrados_palavra
                        total_novos += novos_palavra
                        
                        # Atualizar estatísticas da palavra
                        self.keywords_manager.update_keyword_stats(palavra, novos_palavra)
                        
                        self._log_execution('olx', palavra, 'success', encontrados_palavra, novos_palavra)
                    else:
                        logger.error(f"Erro na busca OLX para '{palavra}': {result.stderr}")
                        self._log_execution('olx', palavra, 'error', mensagem=result.stderr[:500])
                
                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout na busca OLX para '{palavra}'")
                    self._log_execution('olx', palavra, 'error', mensagem="Timeout")
                except Exception as e:
                    logger.error(f"Erro ao processar '{palavra}': {e}", exc_info=True)
                    self._log_execution('olx', palavra, 'error', mensagem=str(e)[:500])
            
            # Calcular duração total
            duration = (datetime.now() - start_time).total_seconds()
            
            # Atualizar estatísticas do scheduler
            self._update_scheduler_stats()
            
            # Callback para notificação
            if self.on_search_complete:
                self.on_search_complete(
                    tipo='olx',
                    total_palavras=len(keywords),
                    total_encontrados=total_encontrados,
                    total_novos=total_novos,
                    duracao=duration
                )
            
            logger.success(f"✅ Busca OLX finalizada em {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Erro crítico na busca OLX: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            self._log_execution('olx', 'ALL', 'error', mensagem=str(e)[:500], duracao_segundos=duration)
    
    def _run_facebook_search(self):
        """Executa busca no Facebook Marketplace para todas as palavras-chave ativas"""
        logger.info("🔍 Iniciando busca automática no Facebook...")
        start_time = datetime.now()
        
        try:
            # Buscar credenciais do Facebook
            from credentials_manager import CredentialsManager
            credentials_manager = CredentialsManager()
            fb_credentials = credentials_manager.get_credentials('facebook')
            
            if not fb_credentials:
                logger.warning("⚠️ Nenhuma credencial do Facebook cadastrada. Use /cadastrar_facebook")
                logger.warning("Executando busca sem autenticação (resultados podem ser limitados)")
            else:
                logger.info(f"✓ Credenciais do Facebook encontradas: {fb_credentials['username']}")
            
            # Buscar palavras-chave ativas para Facebook
            keywords = self.keywords_manager.get_keywords_for_search('facebook')
            
            if not keywords:
                logger.warning("Nenhuma palavra-chave ativa para Facebook")
                return
            
            logger.info(f"Palavras-chave encontradas: {keywords}")
            
            # Executar scraper para cada palavra
            total_encontrados = 0
            total_novos = 0
            
            for palavra in keywords:
                try:
                    logger.info(f"Buscando '{palavra}' no Facebook...")
                    
                    # Executar scraper Facebook (novo com Playwright)
                    python_exe = sys.executable
                    script_path = self.project_root / "buscar_facebook_new.py"
                    
                    # Montar comando com credenciais se disponíveis
                    cmd = [python_exe, str(script_path), palavra]
                    
                    if fb_credentials:
                        cmd.extend(['--email', fb_credentials['username']])
                        cmd.extend(['--senha', fb_credentials['password']])
                        logger.info(f"Executando com credenciais: {fb_credentials['username']}")
                    else:
                        logger.warning("Executando sem credenciais (resultados limitados)")
                    
                    # Configurar ambiente com UTF-8
                    env = os.environ.copy()
                    env['PYTHONIOENCODING'] = 'utf-8'
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        env=env,
                        timeout=600  # 10 minutos timeout (Facebook é mais lento)
                    )
                    
                    # Logar stdout e stderr para debug
                    if result.stdout:
                        logger.debug(f"Facebook stdout: {result.stdout[:500]}")
                    if result.stderr:
                        logger.debug(f"Facebook stderr: {result.stderr[:500]}")
                    
                    if result.returncode == 0:
                        logger.success(f"Busca Facebook concluída para '{palavra}'")
                        
                        # Parsear output JSON (similar ao OLX)
                        try:
                            import re
                            match = re.search(r'RESULT_JSON:(.+)', result.stdout)
                            if match:
                                resultado = json.loads(match.group(1))
                                encontrados = resultado.get('encontrados', 0)
                                salvos = resultado.get('salvos', 0)
                                
                                total_encontrados += encontrados
                                total_novos += salvos
                                
                                logger.info(f"📊 Resultados parseados: {encontrados} encontrados, {salvos} novos")
                                
                                # Atualizar estatísticas da palavra
                                self.keywords_manager.update_keyword_stats(palavra, salvos)
                                self._log_execution('facebook', palavra, 'success', encontrados, salvos)
                            else:
                                logger.warning("Não foi possível parsear resultado JSON")
                                self.keywords_manager.update_keyword_stats(palavra, 0)
                                self._log_execution('facebook', palavra, 'success', 0, 0)
                        except Exception as e:
                            logger.error(f"Erro ao parsear resultado: {e}")
                            self.keywords_manager.update_keyword_stats(palavra, 0)
                            self._log_execution('facebook', palavra, 'success', 0, 0)
                    else:
                        logger.error(f"Erro na busca Facebook para '{palavra}' (código: {result.returncode})")
                        if result.stderr:
                            logger.error(f"Stderr: {result.stderr}")
                        if result.stdout:
                            logger.error(f"Stdout: {result.stdout}")
                        self._log_execution('facebook', palavra, 'error', mensagem=result.stderr[:500])
                
                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout na busca Facebook para '{palavra}'")
                    self._log_execution('facebook', palavra, 'error', mensagem="Timeout")
                except Exception as e:
                    logger.error(f"Erro ao processar '{palavra}': {e}", exc_info=True)
                    self._log_execution('facebook', palavra, 'error', mensagem=str(e)[:500])
            
            # Calcular duração total
            duration = (datetime.now() - start_time).total_seconds()
            
            # Atualizar estatísticas do scheduler
            self._update_scheduler_stats()
            
            # Callback para notificação
            if self.on_search_complete:
                self.on_search_complete(
                    tipo='facebook',
                    total_palavras=len(keywords),
                    total_encontrados=total_encontrados,
                    total_novos=total_novos,
                    duracao=duration
                )
            
            logger.success(f"✅ Busca Facebook finalizada em {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Erro crítico na busca Facebook: {e}", exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()
            self._log_execution('facebook', 'ALL', 'error', mensagem=str(e)[:500], duracao_segundos=duration)
    
    def _update_scheduler_stats(self):
        """Atualiza estatísticas do scheduler após execução"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Buscar intervalo atual
            cursor.execute("SELECT interval_minutes FROM scheduler_config WHERE id = 1")
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return
            
            interval_minutes = result[0]
            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            
            cursor.execute("""
                UPDATE scheduler_config
                SET 
                    last_run = CURRENT_TIMESTAMP,
                    next_run = ?,
                    total_runs = total_runs + 1
                WHERE id = 1
            """, (next_run.strftime('%Y-%m-%d %H:%M:%S'),))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Próxima execução: {next_run.strftime('%d/%m/%Y %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas do scheduler: {e}", exc_info=True)
    
    def set_interval(self, interval_minutes: int) -> bool:
        """
        Configura intervalo de execução
        
        Args:
            interval_minutes: Intervalo em minutos (10, 30 ou 60)
        
        Returns:
            True se configurou com sucesso
        """
        if interval_minutes not in self.VALID_INTERVALS:
            logger.error(f"Intervalo inválido: {interval_minutes}. Use: {self.VALID_INTERVALS}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduler_config
                SET interval_minutes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (interval_minutes,))
            
            conn.commit()
            conn.close()
            
            logger.success(f"Intervalo configurado para {interval_minutes} minutos")
            
            # Se scheduler está rodando, reiniciar com novo intervalo
            if self.is_running():
                self.stop()
                self.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar intervalo: {e}", exc_info=True)
            return False
    
    def get_config(self) -> Optional[Dict]:
        """
        Retorna configuração atual do scheduler
        
        Returns:
            Dict com configuração ou None se erro
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT interval_minutes, enabled, last_run, next_run, 
                       total_runs, total_errors, created_at, updated_at
                FROM scheduler_config
                WHERE id = 1
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            return {
                'interval_minutes': result[0],
                'enabled': bool(result[1]),
                'last_run': result[2],
                'next_run': result[3],
                'total_runs': result[4],
                'total_errors': result[5],
                'created_at': result[6],
                'updated_at': result[7]
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter configuração: {e}", exc_info=True)
            return None
    
    def start(self) -> bool:
        """
        Inicia o scheduler
        
        Returns:
            True se iniciou com sucesso
        """
        try:
            config = self.get_config()
            
            if not config:
                logger.error("Configuração do scheduler não encontrada")
                return False
            
            interval_minutes = config['interval_minutes']
            
            # Adicionar jobs
            self.scheduler.add_job(
                self._run_olx_search,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='olx_search',
                name='Busca automática OLX',
                replace_existing=True
            )
            
            self.scheduler.add_job(
                self._run_facebook_search,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='facebook_search',
                name='Busca automática Facebook',
                replace_existing=True
            )
            
            # Iniciar scheduler
            self.scheduler.start()
            
            # Atualizar status no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            next_run = datetime.now() + timedelta(minutes=interval_minutes)
            
            cursor.execute("""
                UPDATE scheduler_config
                SET enabled = 1, next_run = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """, (next_run.strftime('%Y-%m-%d %H:%M:%S'),))
            
            conn.commit()
            conn.close()
            
            logger.success(f"✅ Scheduler iniciado (intervalo: {interval_minutes} min)")
            logger.info(f"Próxima execução: {next_run.strftime('%d/%m/%Y %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao iniciar scheduler: {e}", exc_info=True)
            return False
    
    def stop(self) -> bool:
        """
        Para o scheduler
        
        Returns:
            True se parou com sucesso
        """
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler parado")
            
            # Atualizar status no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE scheduler_config
                SET enabled = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """)
            
            conn.commit()
            conn.close()
            
            logger.success("✅ Scheduler desabilitado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar scheduler: {e}", exc_info=True)
            return False
    
    def is_running(self) -> bool:
        """
        Verifica se o scheduler está rodando
        
        Returns:
            True se está rodando
        """
        return self.scheduler.running
    
    def run_manual_search(self, tipo: str = 'ambos') -> bool:
        """
        Executa busca manual imediata
        
        Args:
            tipo: Tipo de busca (olx, facebook, ambos)
        
        Returns:
            True se executou com sucesso
        """
        try:
            logger.info(f"🔍 Executando busca manual: {tipo}")
            
            if tipo in ['olx', 'ambos']:
                self._run_olx_search()
            
            if tipo in ['facebook', 'ambos']:
                self._run_facebook_search()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro na busca manual: {e}", exc_info=True)
            return False


if __name__ == "__main__":
    # Teste do módulo
    print("=" * 60)
    print("TESTE DO SCHEDULER MANAGER")
    print("=" * 60)
    
    def on_search_complete(tipo, total_palavras, total_encontrados, total_novos, duracao):
        print(f"\n📊 Busca {tipo} concluída:")
        print(f"   Palavras: {total_palavras}")
        print(f"   Encontrados: {total_encontrados}")
        print(f"   Novos: {total_novos}")
        print(f"   Duração: {duracao:.2f}s")
    
    manager = SchedulerManager(on_search_complete=on_search_complete)
    
    # Teste 1: Configuração
    print("\n1. Obtendo configuração atual...")
    config = manager.get_config()
    if config:
        print(f"   ✅ Intervalo: {config['interval_minutes']} min")
        print(f"   Status: {'Ativo' if config['enabled'] else 'Inativo'}")
        print(f"   Total execuções: {config['total_runs']}")
        print(f"   Total erros: {config['total_errors']}")
    
    # Teste 2: Alterar intervalo
    print("\n2. Configurando intervalo para 10 minutos...")
    success = manager.set_interval(10)
    print(f"   {'✅ Sucesso' if success else '❌ Falha'}")
    
    # Teste 3: Status
    print("\n3. Verificando status do scheduler...")
    is_running = manager.is_running()
    print(f"   Status: {'🟢 Rodando' if is_running else '🔴 Parado'}")
    
    # Teste 4: Iniciar (comentado para não executar em teste)
    # print("\n4. Iniciando scheduler...")
    # started = manager.start()
    # print(f"   {'✅ Iniciado' if started else '❌ Falha'}")
    
    print("\n" + "=" * 60)
    print("TESTE CONCLUÍDO")
    print("=" * 60)
    print("\n⚠️  Para iniciar o scheduler, descomente o Teste 4")
