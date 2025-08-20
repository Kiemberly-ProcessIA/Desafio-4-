# -*- coding: utf-8 -*-
"""
Passo 1: Leitura, Validação e Consolidação Completa

Este módulo é responsável por:
- Ler todos os arquivos Excel necessários
- Validar estrutura e integridade dos dados
- Verificar consistência entre arquivos
- Consolidar dados em JSON estruturado
- Gerar relatórios detalhados
- Preparar dados validados para próximos passos

Componentes:
- LeitorExcel: Leitura e validação inicial dos arquivos
- ValidadorDados: Validações avançadas e regras de negócio
- consolidador_json: Consolidação dos dados em formato JSON
- relatorio_consolidado: Geração de relatórios executivos
- OrquestradorPasso1: Coordena todo o processo

Arquivos processados:
- ATIVOS.xlsx (obrigatório)
- DESLIGADOS.xlsx (obrigatório) 
- FÉRIAS.xlsx (obrigatório)
- Base dias uteis.xlsx (obrigatório)
- Base sindicato x valor.xlsx (obrigatório)
- Arquivos opcionais: ADMISSÃO ABRIL.xlsx, APRENDIZ.xlsx, ESTÁGIO.xlsx, etc.
"""

from .leitor_excel import LeitorExcel
from .validador_dados import ValidadorDados
from .consolidador_json import OrquestradorPasso1

__version__ = "1.0.0"
__all__ = ["LeitorExcel", "ValidadorDados", "OrquestradorPasso1"]

# Facilitar importação direta
def executar_passo1(pasta_colaboradores: str, pasta_configuracoes: str = None, pasta_output: str = "./output"):
    """
    Função de conveniência para executar o Passo 1 completo.
    
    Args:
        pasta_colaboradores: Caminho para pasta com dados de colaboradores
        pasta_configuracoes: Caminho para pasta com configurações (opcional)
        pasta_output: Pasta onde salvar resultados
    
    Returns:
        dict: Resultado da execução com status e detalhes
    """
    pasta_config = pasta_configuracoes or pasta_colaboradores
    orquestrador = OrquestradorPasso1(pasta_colaboradores, pasta_config, pasta_output)
    return orquestrador.executar_passo_completo()
