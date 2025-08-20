#!/usr/bin/env python3
"""
Utilitários gerais do projeto VR.
"""

from .logging_config import (
    setup_logging,
    get_logger,
    configure_project_logging,
    log_step,
    log_inicio_passo,
    log_fim_passo,
    log_erro_critico,
    log_processamento,
    log_resultado_validacao,
    LoggerContextManager
)

__all__ = [
    'setup_logging',
    'get_logger', 
    'configure_project_logging',
    'log_step',
    'log_inicio_passo',
    'log_fim_passo',
    'log_erro_critico',
    'log_processamento',
    'log_resultado_validacao',
    'LoggerContextManager'
]
