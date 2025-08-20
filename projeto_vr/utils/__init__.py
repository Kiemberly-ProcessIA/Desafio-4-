#!/usr/bin/env python3
"""
Utilitários gerais do projeto VR.
"""

from .logging_config import (LoggerContextManager, configure_project_logging,
                             get_logger, log_erro_critico, log_fim_passo,
                             log_inicio_passo, log_processamento,
                             log_resultado_validacao, log_step, setup_logging)

__all__ = [
    "setup_logging",
    "get_logger",
    "configure_project_logging",
    "log_step",
    "log_inicio_passo",
    "log_fim_passo",
    "log_erro_critico",
    "log_processamento",
    "log_resultado_validacao",
    "LoggerContextManager",
]
