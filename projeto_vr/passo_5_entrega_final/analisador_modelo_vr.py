#!/usr/bin/env python3
"""
Analisador do Modelo VR - Passo 5
Analisa a planilha modelo "VR MENSAL 05.2025.xlsx" para extrair:
- Estrutura das colunas
- Formato dos dados
- Validações necessárias
"""

import os
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importar sistema de logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import setup_logging, log_inicio_passo, log_fim_passo

logger = setup_logging()

class AnalisadorModeloVR:
    """Analisa a planilha modelo VR para extrair formato e validações."""
    
    def __init__(self):
        self.diretorio_input = self._encontrar_diretorio_input()
        self.arquivo_modelo = self._encontrar_arquivo_modelo()
        self.estrutura_modelo = None
        self.validacoes_modelo = None
        
    def _encontrar_diretorio_input(self) -> Path:
        """Encontra o diretório input_data."""
        current_dir = Path(__file__).parent
        while current_dir.name != 'desafio_4' and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        
        input_dir = current_dir / 'input_data'
        if not input_dir.exists():
            raise FileNotFoundError(f"Diretório input_data não encontrado: {input_dir}")
        
        return input_dir
    
    def _encontrar_arquivo_modelo(self) -> Path:
        """Encontra o arquivo modelo VR MENSAL."""
        colaboradores_dir = self.diretorio_input / 'colaboradores'
        
        # Procurar arquivo VR MENSAL
        for arquivo in colaboradores_dir.glob('*VR*MENSAL*.xlsx'):
            logger.info(f"Arquivo modelo encontrado: {arquivo}")
            return arquivo
        
        raise FileNotFoundError("Arquivo modelo VR MENSAL não encontrado")
    
    def analisar_estrutura_modelo(self) -> Dict[str, Any]:
        """Analisa a estrutura da planilha modelo."""
        logger.info(f"Analisando estrutura do modelo: {self.arquivo_modelo}")
        
        try:
            import pandas as pd
            
            # Ler todas as abas da planilha
            excel_file = pd.ExcelFile(self.arquivo_modelo)
            logger.info(f"Abas encontradas: {excel_file.sheet_names}")
            
            estrutura = {
                'arquivo': str(self.arquivo_modelo),
                'abas': excel_file.sheet_names,
                'aba_principal': None,
                'aba_validacoes': None,
                'colunas': [],
                'formato_dados': {},
                'total_registros_modelo': 0
            }
            
            # Identificar aba principal (dados VR)
            for aba in excel_file.sheet_names:
                if any(termo in aba.upper() for termo in ['VR', 'MENSAL', 'DADOS', 'PRINCIPAL']):
                    estrutura['aba_principal'] = aba
                    break
            
            if not estrutura['aba_principal']:
                estrutura['aba_principal'] = excel_file.sheet_names[0]
            
            # Identificar aba de validações
            for aba in excel_file.sheet_names:
                if 'VALIDAC' in aba.upper() or 'VALID' in aba.upper():
                    estrutura['aba_validacoes'] = aba
                    break
            
            # Analisar aba principal
            df_principal = pd.read_excel(self.arquivo_modelo, sheet_name=estrutura['aba_principal'], header=1)
            estrutura['colunas'] = list(df_principal.columns)
            estrutura['total_registros_modelo'] = len(df_principal)
            
            # Analisar tipos e formatos das colunas
            for coluna in df_principal.columns:
                amostra_valores = df_principal[coluna].dropna().head(5).tolist()
                estrutura['formato_dados'][coluna] = {
                    'tipo': str(df_principal[coluna].dtype),
                    'exemplos': amostra_valores,
                    'tem_valores_nulos': df_principal[coluna].isnull().any(),
                    'total_nulos': df_principal[coluna].isnull().sum()
                }
            
            self.estrutura_modelo = estrutura
            logger.info(f"Estrutura analisada: {len(estrutura['colunas'])} colunas, {estrutura['total_registros_modelo']} registros")
            
            return estrutura
            
        except ImportError:
            logger.warning("Pandas não disponível. Analisando sem leitura completa.")
            return self._analisar_estrutura_basica()
        except Exception as e:
            logger.error(f"Erro ao analisar estrutura: {e}")
            return self._analisar_estrutura_basica()
    
    def _analisar_estrutura_basica(self) -> Dict[str, Any]:
        """Análise básica quando pandas não está disponível."""
        return {
            'arquivo': str(self.arquivo_modelo),
            'abas': ['VR_MENSAL', 'validações'],
            'aba_principal': 'VR_MENSAL', 
            'aba_validacoes': 'validações',
            'colunas': [
                'Matrícula', 'Nome', 'CPF', 'Empresa', 'Centro de Custo',
                'Cargo', 'Situação', 'Data Admissão', 'Data Demissão',
                'Valor VR', 'Valor Empresa', 'Valor Funcionário',
                'Data Início Vigência', 'Data Fim Vigência', 'Status'
            ],
            'formato_dados': {},
            'total_registros_modelo': 0
        }
    
    def extrair_validacoes(self) -> Dict[str, Any]:
        """Extrai validações da aba de validações."""
        logger.info("Extraindo validações do modelo")
        
        if not self.estrutura_modelo or not self.estrutura_modelo.get('aba_validacoes'):
            return self._definir_validacoes_padrao()
        
        try:
            import pandas as pd
            
            df_validacoes = pd.read_excel(
                self.arquivo_modelo, 
                sheet_name=self.estrutura_modelo['aba_validacoes']
            )
            
            validacoes = {
                'campos_obrigatorios': [],
                'formatos_data': {},
                'formatos_valor': {},
                'restricoes_texto': {},
                'validacoes_negocio': []
            }
            
            # Processar validações da aba
            for _, row in df_validacoes.iterrows():
                if pd.notna(row.get('Validações')):
                    validacao_texto = str(row['Validações']).strip()
                    
                    # Interpretar validações baseadas no texto
                    if any(termo in validacao_texto.upper() for termo in ['AFASTADOS', 'LICENÇAS']):
                        validacoes['validacoes_negocio'].append({
                            'campo': 'situacao',
                            'regra': 'Excluir colaboradores em licença ou afastamento'
                        })
                    
                    if 'DESLIGADOS' in validacao_texto.upper():
                        if '15' in validacao_texto:
                            validacoes['validacoes_negocio'].append({
                                'campo': 'data_desligamento', 
                                'regra': 'Desligados até dia 15: incluir no cálculo VR'
                            })
                        elif '16' in validacao_texto:
                            validacoes['validacoes_negocio'].append({
                                'campo': 'data_desligamento',
                                'regra': 'Desligados após dia 16: excluir do cálculo VR'
                            })
                        else:
                            validacoes['validacoes_negocio'].append({
                                'campo': 'situacao',
                                'regra': 'Excluir colaboradores desligados'
                            })
                    
                    if any(termo in validacao_texto.upper() for termo in ['ESTAGIARIO', 'APRENDIZ']):
                        validacoes['validacoes_negocio'].append({
                            'campo': 'cargo',
                            'regra': f'Excluir {validacao_texto.lower()}'
                        })
                    
                    if 'SINDICATOS' in validacao_texto.upper():
                        validacoes['validacoes_negocio'].append({
                            'campo': 'sindicato',
                            'regra': 'Aplicar valor VR conforme sindicato'
                        })
            
            # Campos obrigatórios baseados na estrutura do modelo
            validacoes['campos_obrigatorios'] = [
                'matricula', 'TOTAL', 'custo empresa', 'deconto funcionario', 'competencia'
            ]
            
            # Formatos baseados no modelo
            validacoes['formatos_data'] = {
                'admissao': 'DD/MM/YYYY',
                'competencia': 'DD/MM/YYYY'
            }
            
            validacoes['formatos_valor'] = {
                'valor diario': 'Decimal com 2 casas',
                'TOTAL': 'Decimal com 2 casas', 
                'custo empresa': 'Decimal com 2 casas',
                'deconto funcionario': 'Decimal com 2 casas'
            }
            
            self.validacoes_modelo = validacoes
            logger.info(f"Validações extraídas: {len(validacoes['campos_obrigatorios'])} campos obrigatórios")
            
            return validacoes
            
        except Exception as e:
            logger.warning(f"Erro ao extrair validações: {e}")
            return self._definir_validacoes_padrao()
    
    def _definir_validacoes_padrao(self) -> Dict[str, Any]:
        """Define validações padrão baseadas no conhecimento do negócio."""
        return {
            'campos_obrigatorios': [
                'Matrícula', 'Nome', 'CPF', 'Valor VR', 'Valor Empresa', 
                'Valor Funcionário', 'Data Início Vigência', 'Data Fim Vigência'
            ],
            'formatos_data': {
                'Data Admissão': 'DD/MM/YYYY',
                'Data Demissão': 'DD/MM/YYYY', 
                'Data Início Vigência': 'DD/MM/YYYY',
                'Data Fim Vigência': 'DD/MM/YYYY'
            },
            'formatos_valor': {
                'Valor VR': 'Decimal(10,2)',
                'Valor Empresa': 'Decimal(10,2)',
                'Valor Funcionário': 'Decimal(10,2)'
            },
            'restricoes_texto': {
                'CPF': '11 dígitos numéricos',
                'Matrícula': 'Alfanumérico até 20 caracteres',
                'Nome': 'Texto até 100 caracteres'
            },
            'validacoes_negocio': [
                {'campo': 'Valor VR', 'regra': 'Valor Empresa + Valor Funcionário = Valor VR'},
                {'campo': 'Valor Empresa', 'regra': 'Deve ser 80% do Valor VR'},
                {'campo': 'Valor Funcionário', 'regra': 'Deve ser 20% do Valor VR'},
                {'campo': 'Data Fim Vigência', 'regra': 'Deve ser posterior à Data Início Vigência'},
                {'campo': 'CPF', 'regra': 'Deve ser válido (algoritmo CPF)'}
            ]
        }
    
    def gerar_relatorio_analise(self) -> str:
        """Gera relatório da análise do modelo."""
        if not self.estrutura_modelo:
            self.analisar_estrutura_modelo()
        
        if not self.validacoes_modelo:
            self.extrair_validacoes()
        
        relatorio = []
        relatorio.append("="*80)
        relatorio.append("RELATÓRIO DE ANÁLISE - MODELO VR OPERADORA")
        relatorio.append("="*80)
        relatorio.append(f"Arquivo: {self.estrutura_modelo['arquivo']}")
        relatorio.append(f"Data da análise: {sys.modules.get('datetime', __import__('datetime')).datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append("")
        
        relatorio.append("ESTRUTURA DA PLANILHA:")
        relatorio.append("-"*40)
        relatorio.append(f"Abas encontradas: {', '.join(self.estrutura_modelo['abas'])}")
        relatorio.append(f"Aba principal: {self.estrutura_modelo['aba_principal']}")
        relatorio.append(f"Aba validações: {self.estrutura_modelo['aba_validacoes']}")
        relatorio.append(f"Total de colunas: {len(self.estrutura_modelo['colunas'])}")
        relatorio.append(f"Registros no modelo: {self.estrutura_modelo['total_registros_modelo']}")
        relatorio.append("")
        
        relatorio.append("COLUNAS IDENTIFICADAS:")
        relatorio.append("-"*40)
        for i, coluna in enumerate(self.estrutura_modelo['colunas'], 1):
            relatorio.append(f"{i:2d}. {coluna}")
        relatorio.append("")
        
        relatorio.append("VALIDAÇÕES EXTRAÍDAS:")
        relatorio.append("-"*40)
        relatorio.append(f"Campos obrigatórios: {len(self.validacoes_modelo['campos_obrigatorios'])}")
        for campo in self.validacoes_modelo['campos_obrigatorios']:
            relatorio.append(f"  • {campo}")
        relatorio.append("")
        
        relatorio.append("FORMATOS DE DATA:")
        for campo, formato in self.validacoes_modelo['formatos_data'].items():
            relatorio.append(f"  • {campo}: {formato}")
        relatorio.append("")
        
        relatorio.append("FORMATOS DE VALOR:")
        for campo, formato in self.validacoes_modelo['formatos_valor'].items():
            relatorio.append(f"  • {campo}: {formato}")
        relatorio.append("")
        
        relatorio.append("REGRAS DE NEGÓCIO:")
        for regra in self.validacoes_modelo['validacoes_negocio']:
            relatorio.append(f"  • {regra['campo']}: {regra['regra']}")
        relatorio.append("")
        
        relatorio.append("="*80)
        
        return "\n".join(relatorio)

def main():
    """Função principal para testar o analisador."""
    logger.info("🔍 ANALISANDO MODELO VR DA OPERADORA")
    logger.info("="*60)
    
    try:
        analisador = AnalisadorModeloVR()
        
        # Analisar estrutura
        logger.info("📋 Analisando estrutura da planilha...")
        estrutura = analisador.analisar_estrutura_modelo()
        
        # Extrair validações
        logger.info("✅ Extraindo validações...")
        validacoes = analisador.extrair_validacoes()
        
        # Gerar relatório
        logger.info("📄 Gerando relatório...")
        relatorio = analisador.gerar_relatorio_analise()
        
        logger.info(relatorio)
        logger.info("✅ Análise concluída com sucesso!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
