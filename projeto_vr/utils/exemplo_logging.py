#!/usr/bin/env python3
"""
Exemplo de uso do sistema de logging padronizado.
Este arquivo demonstra as principais funcionalidades do logging profissional.
"""

import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from utils.logging_config import (
    get_logger, 
    log_inicio_passo, 
    log_fim_passo, 
    log_erro_critico,
    log_processamento,
    log_resultado_validacao,
    LoggerContextManager,
    log_step
)

# Obter logger para este módulo
logger = get_logger(__name__)

@log_step("EXEMPLO", "Processamento de dados demonstrativo")
def exemplo_funcao_com_decorator():
    """Exemplo de função usando decorator para logging automático."""
    logger.info("🔄 Processando dados...")
    
    # Simular processamento
    import time
    time.sleep(1)
    
    logger.info("✅ Dados processados com sucesso!")
    return {"status": "ok", "registros": 100}

def exemplo_uso_basico():
    """Demonstra uso básico do logging."""
    logger.info("📋 Exemplo de logging básico")
    logger.debug("🔍 Informação de debug")
    logger.warning("⚠️  Aviso importante")
    logger.error("❌ Erro simulado")
    
def exemplo_logs_padronizados():
    """Demonstra logs padronizados para passos do sistema."""
    
    # Início de passo
    log_inicio_passo("PASSO EXEMPLO", "Demonstração do Sistema de Logging", logger)
    
    # Processamento com logs de progresso
    total_items = 50
    for i in range(1, total_items + 1):
        if i % 10 == 0:  # Log a cada 10 itens
            log_processamento("registros", i, total_items, f"(batch {i//10})", logger)
    
    # Resultado de validação
    log_resultado_validacao("DADOS", validos=45, invalidos=5, warnings=2, logger=logger)
    
    # Fim de passo com estatísticas
    estatisticas = {
        "registros_processados": total_items,
        "válidos": 45,
        "inválidos": 5,
        "tempo_processamento": "2.3s"
    }
    log_fim_passo("PASSO EXEMPLO", "Demonstração do Sistema de Logging", estatisticas, logger)

def exemplo_context_manager():
    """Demonstra uso do context manager para logging."""
    
    with LoggerContextManager(logger, "OPERAÇÃO", "Carregamento de arquivo"):
        logger.info("📁 Carregando arquivo exemplo.xlsx...")
        
        # Simular trabalho
        import time
        time.sleep(0.5)
        
        logger.info("✅ Arquivo carregado com sucesso!")

def exemplo_tratamento_erro():
    """Demonstra logging de erros críticos."""
    
    try:
        # Simular erro
        resultado = 10 / 0
    except ZeroDivisionError as e:
        log_erro_critico("Divisão por zero detectada!", e, logger)
        
def main():
    """Função principal com exemplos de uso."""
    logger.info("🚀 INICIANDO DEMONSTRAÇÃO DO SISTEMA DE LOGGING")
    logger.info("="*60)
    
    # Exemplo 1: Uso básico
    logger.info("📝 Exemplo 1: Logging básico")
    exemplo_uso_basico()
    
    logger.info("\n" + "="*40)
    
    # Exemplo 2: Logs padronizados  
    logger.info("📊 Exemplo 2: Logs padronizados para passos")
    exemplo_logs_padronizados()
    
    logger.info("\n" + "="*40)
    
    # Exemplo 3: Context manager
    logger.info("🎯 Exemplo 3: Context manager")
    exemplo_context_manager()
    
    logger.info("\n" + "="*40)
    
    # Exemplo 4: Função com decorator
    logger.info("🔧 Exemplo 4: Decorator de logging")
    resultado = exemplo_funcao_com_decorator()
    logger.info(f"Resultado: {resultado}")
    
    logger.info("\n" + "="*40)
    
    # Exemplo 5: Tratamento de erro
    logger.info("💥 Exemplo 5: Tratamento de erro")
    exemplo_tratamento_erro()
    
    logger.info("="*60)
    logger.info("✅ DEMONSTRAÇÃO CONCLUÍDA")

if __name__ == "__main__":
    main()
