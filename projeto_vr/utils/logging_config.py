#!/usr/bin/env python3
"""
Configuração padronizada de logging para o projeto VR.
Este módulo fornece configuração profissional e padronizada para todos os logs do sistema.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Formatador com cores para saída no console."""
    
    # Códigos de cores ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Aplicar cor baseada no nível do log
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Configura logging padronizado para o projeto VR.
    
    Args:
        log_level: Nível do log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para arquivo de log (opcional)
        enable_colors: Habilitar cores no console
        module_name: Nome do módulo (para identificação nos logs)
    
    Returns:
        Logger configurado
    """
    
    # Criar diretório de logs se necessário
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuração base
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)-8s | %(message)s'
            },
            'file': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'detailed',
                'stream': 'ext://sys.stdout'
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    # Adicionar handler de arquivo se especificado
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'level': log_level,
            'formatter': 'file',
            'filename': log_file,
            'mode': 'a',
            'encoding': 'utf-8'
        }
        config['root']['handlers'].append('file')
    
    # Configurar cores se habilitado
    if enable_colors and sys.stdout.isatty():
        config['formatters']['detailed']['()'] = ColoredFormatter
        config['formatters']['detailed']['format'] = '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    
    # Aplicar configuração
    logging.config.dictConfig(config)
    
    # Retornar logger específico do módulo
    logger_name = module_name if module_name else 'VR_SYSTEM'
    logger = logging.getLogger(logger_name)
    
    return logger

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Obtém um logger configurado para um módulo específico.
    
    Args:
        name: Nome do logger/módulo
        log_file: Arquivo de log específico (opcional)
    
    Returns:
        Logger configurado
    """
    # Se já foi configurado, apenas retorna o logger
    if logging.getLogger().handlers:
        return logging.getLogger(name)
    
    # Configurar logging se ainda não foi feito
    return setup_logging(module_name=name, log_file=log_file)

class LoggerContextManager:
    """Context manager para logging com contexto específico."""
    
    def __init__(self, logger: logging.Logger, step: str, operation: str):
        self.logger = logger
        self.step = step
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"🚀 INICIANDO {self.step}: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"✅ CONCLUÍDO {self.step}: {self.operation} | Duração: {duration.total_seconds():.2f}s")
        else:
            self.logger.error(f"❌ ERRO {self.step}: {self.operation} | Erro: {exc_val} | Duração: {duration.total_seconds():.2f}s")
        
        return False

def log_step(step: str, operation: str):
    """
    Decorator para logging automático de início/fim de operações.
    
    Args:
        step: Nome do passo (ex: "PASSO_1", "VALIDAÇÃO")  
        operation: Nome da operação (ex: "Carregamento de dados")
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Tentar obter logger do self se disponível
            logger = None
            if args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            else:
                logger = logging.getLogger(func.__module__)
            
            with LoggerContextManager(logger, step, operation):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def configure_project_logging():
    """
    Configura logging para todo o projeto VR com as melhores práticas.
    """
    # Diretório de logs dentro de output
    project_root = Path(__file__).parent.parent.parent  # Subir para desafio_4
    logs_dir = project_root / "output" / "logs"
    
    # Arquivo de log com timestamp
    log_filename = f"vr_system_{datetime.now().strftime('%Y%m%d')}.log"
    log_file = logs_dir / log_filename
    
    # Configurar com arquivo de log
    logger = setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=str(log_file),
        enable_colors=True
    )
    
    logger.info("="*60)
    logger.info("🎯 SISTEMA VR - LOGGING CONFIGURADO")
    logger.info(f"📁 Log file: {log_file}")
    logger.info(f"🔧 Log level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info("="*60)
    
    return logger

# Configuração padrão para importação direta
default_logger = None

def init_default_logger():
    """Inicializa o logger padrão do projeto."""
    global default_logger
    if default_logger is None:
        default_logger = configure_project_logging()
    return default_logger

# Funções de conveniência para logging padronizado
def log_inicio_passo(passo: str, descricao: str, logger: Optional[logging.Logger] = None):
    """Log padronizado para início de passo."""
    if logger is None:
        logger = init_default_logger()
    logger.info("="*80)
    logger.info(f"🚀 INICIANDO {passo}: {descricao}")
    logger.info("="*80)

def log_fim_passo(passo: str, descricao: str, estatisticas: dict = None, logger: Optional[logging.Logger] = None):
    """Log padronizado para fim de passo."""
    if logger is None:
        logger = init_default_logger()
    
    logger.info("="*80)
    logger.info(f"✅ FINALIZADO {passo}: {descricao}")
    
    if estatisticas:
        logger.info("📊 ESTATÍSTICAS:")
        for chave, valor in estatisticas.items():
            logger.info(f"   • {chave}: {valor}")
    
    logger.info("="*80)

def log_erro_critico(mensagem: str, erro: Exception = None, logger: Optional[logging.Logger] = None):
    """Log padronizado para erros críticos."""
    if logger is None:
        logger = init_default_logger()
    
    logger.critical("🔥"*20)
    logger.critical(f"💀 ERRO CRÍTICO: {mensagem}")
    if erro:
        logger.critical(f"📝 Detalhes: {str(erro)}")
        logger.critical(f"🔍 Tipo: {type(erro).__name__}")
    logger.critical("🔥"*20)

def log_processamento(item: str, atual: int, total: int, detalhes: str = "", logger: Optional[logging.Logger] = None):
    """Log padronizado para acompanhar processamento."""
    if logger is None:
        logger = init_default_logger()
    
    percentual = (atual / total) * 100 if total > 0 else 0
    logger.info(f"⚙️  Processando {item} ({atual}/{total} - {percentual:.1f}%) {detalhes}")

def log_resultado_validacao(tipo: str, validos: int, invalidos: int, warnings: int = 0, logger: Optional[logging.Logger] = None):
    """Log padronizado para resultados de validação."""
    if logger is None:
        logger = init_default_logger()
    
    total = validos + invalidos
    logger.info(f"📋 RESULTADO VALIDAÇÃO {tipo}:")
    logger.info(f"   ✅ Válidos: {validos} ({(validos/total)*100:.1f}%)" if total > 0 else f"   ✅ Válidos: {validos}")
    logger.info(f"   ❌ Inválidos: {invalidos} ({(invalidos/total)*100:.1f}%)" if total > 0 else f"   ❌ Inválidos: {invalidos}")
    if warnings > 0:
        logger.info(f"   ⚠️  Warnings: {warnings}")
    logger.info(f"   📊 Total: {total}")
