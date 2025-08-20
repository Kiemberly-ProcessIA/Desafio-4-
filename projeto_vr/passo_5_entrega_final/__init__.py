"""
Passo 5: Entrega Final - Geração de Planilha VR para Operadora

Este módulo é responsável pela entrega final do projeto, gerando uma planilha
no formato exato da operadora, seguindo o modelo "VR Mensal 05.2025".

Módulos:
- analisador_modelo_vr.py: Analisa a planilha modelo para extrair formato
- validador_operadora.py: Aplica validações conforme aba "validações"
- gerador_planilha_final.py: Gera a planilha final para envio
- orquestrador_passo5.py: Coordena todo o processo de entrega final
"""

__version__ = "1.0.0"
__author__ = "Sistema VR I2A2"

# Constantes do módulo
CUSTO_EMPRESA_PERCENTUAL = 0.80  # 80% do valor pago pela empresa
CUSTO_FUNCIONARIO_PERCENTUAL = 0.20  # 20% descontado do funcionário

FORMATO_DATA_OPERADORA = "%d/%m/%Y"
FORMATO_VALOR_OPERADORA = "%.2f"

# Campos obrigatórios para a operadora
CAMPOS_OBRIGATORIOS_OPERADORA = [
    "matricula",
    "nome",
    "cpf",
    "valor_vr",
    "valor_empresa",
    "valor_funcionario",
    "data_inicio_vigencia",
    "data_fim_vigencia",
]
