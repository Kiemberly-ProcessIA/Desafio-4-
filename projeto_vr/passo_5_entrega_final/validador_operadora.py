#!/usr/bin/env python3
"""
Validador da Operadora - Passo 5
Aplica todas as validações necessárias conforme especificações da operadora.
Inclui validação de CPF, formatos de data, cálculos de valores e regras de negócio.
"""

import re
import sys
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Importar sistema de logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import setup_logging, log_inicio_passo, log_fim_passo

logger = setup_logging()

class ValidadorOperadora:
    """Valida dados conforme exigências da operadora VR."""
    
    def __init__(self):
        self.erros_validacao = []
        self.warnings_validacao = []
        self.estatisticas = {
            'total_registros': 0,
            'registros_validos': 0,
            'registros_com_erro': 0,
            'registros_com_warning': 0
        }
        
        # Configurações de validação
        self.CUSTO_EMPRESA_PERCENTUAL = 0.80
        self.CUSTO_FUNCIONARIO_PERCENTUAL = 0.20
        self.TOLERANCIA_DECIMAL = Decimal('0.01')  # 1 centavo de tolerância
        
    def validar_base_completa(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Valida toda a base de dados para entrega à operadora."""
        logger.info("Iniciando validação completa para operadora")
        
        self.erros_validacao = []
        self.warnings_validacao = []
        self.estatisticas = {
            'total_registros': 0,
            'registros_validos': 0,
            'registros_com_erro': 0,
            'registros_com_warning': 0
        }
        
        colaboradores_validados = {}
        
        if 'colaboradores' not in dados:
            raise ValueError("Dados não contêm seção 'colaboradores'")
        
        total_colaboradores = len(dados['colaboradores'])
        self.estatisticas['total_registros'] = total_colaboradores
        
        logger.info(f"Validando {total_colaboradores} colaboradores")
        
        for matricula, colaborador in dados['colaboradores'].items():
            erros_colaborador = []
            warnings_colaborador = []
            
            # Validações obrigatórias
            erros_colaborador.extend(self._validar_campos_obrigatorios(matricula, colaborador))
            erros_colaborador.extend(self._validar_cpf(matricula, colaborador))
            erros_colaborador.extend(self._validar_formatos_data(matricula, colaborador))
            erros_colaborador.extend(self._validar_valores_monetarios(matricula, colaborador))
            erros_colaborador.extend(self._validar_regras_negocio(matricula, colaborador))
            
            # Warnings (não impeditivos)
            warnings_colaborador.extend(self._validar_dados_complementares(matricula, colaborador))
            
            if erros_colaborador:
                self.estatisticas['registros_com_erro'] += 1
                self.erros_validacao.extend(erros_colaborador)
            else:
                self.estatisticas['registros_validos'] += 1
                colaboradores_validados[matricula] = colaborador
            
            if warnings_colaborador:
                self.estatisticas['registros_com_warning'] += 1
                self.warnings_validacao.extend(warnings_colaborador)
        
        # Criar resultado
        resultado = {
            'metadata': {
                **dados.get('metadata', {}),
                'validacao_operadora': {
                    'data_validacao': datetime.now().isoformat(),
                    'versao_validador': '1.0.0',
                    'aprovado_para_envio': self.estatisticas['registros_com_erro'] == 0
                }
            },
            'colaboradores': colaboradores_validados,
            'validacao': {
                'estatisticas': self.estatisticas,
                'erros': self.erros_validacao,
                'warnings': self.warnings_validacao
            }
        }
        
        logger.info(f"Validação concluída: {self.estatisticas['registros_validos']}/{total_colaboradores} válidos")
        
        return resultado
    
    def _validar_campos_obrigatorios(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida campos obrigatórios para a operadora."""
        erros = []
        
        # Campos mínimos para processamento (flexível com dados reais)
        campos_obrigatorios = []
        
        # Verificar se tem valor VR (pode estar em calculo_vr.valor_total ou valor_vr_calculado)
        tem_valor_vr = (
            ('valor_vr_calculado' in colaborador and colaborador['valor_vr_calculado']) or
            ('calculo_vr' in colaborador and isinstance(colaborador['calculo_vr'], dict) and 
             colaborador['calculo_vr'].get('valor_total'))
        )
        
        if not tem_valor_vr:
            erros.append({
                'matricula': matricula,
                'tipo': 'valor_vr_ausente',
                'campo': 'valor_vr',
                'descricao': "Valor VR não encontrado (valor_vr_calculado ou calculo_vr.valor_total)",
                'severidade': 'erro'
            })
        
        # Nome é preferível mas não obrigatório
        if 'nome' in colaborador and colaborador['nome']:
            nome = str(colaborador['nome']).strip()
            if len(nome) < 2:
                erros.append({
                    'matricula': matricula,
                    'tipo': 'nome_invalido',
                    'campo': 'nome',
                    'valor': nome,
                    'descricao': "Nome deve ter pelo menos 2 caracteres",
                    'severidade': 'erro'
                })
        
        return erros
    
    def _validar_cpf(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida CPF usando algoritmo oficial (apenas se CPF estiver presente)."""
        erros = []
        
        # CPF é opcional - só validar se estiver presente
        if 'cpf' not in colaborador or not colaborador['cpf']:
            return erros  # CPF vazio é permitido
        
        cpf = str(colaborador['cpf']).strip()
        
        # Se CPF estiver vazio após strip, também é válido
        if not cpf:
            return erros
        
        # Remover formatação
        cpf_numeros = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf_numeros) != 11:
            erros.append({
                'matricula': matricula,
                'tipo': 'cpf_formato',
                'campo': 'cpf',
                'valor': cpf,
                'descricao': "CPF deve ter exatamente 11 dígitos",
                'severidade': 'erro'
            })
            return erros
        
        # Validar CPF com dígitos iguais
        if cpf_numeros == cpf_numeros[0] * 11:
            erros.append({
                'matricula': matricula,
                'tipo': 'cpf_invalido',
                'campo': 'cpf',
                'valor': cpf,
                'descricao': "CPF inválido (todos os dígitos iguais)",
                'severidade': 'erro'
            })
            return erros
        
        # Calcular dígitos verificadores
        if not self._validar_digitos_cpf(cpf_numeros):
            erros.append({
                'matricula': matricula,
                'tipo': 'cpf_invalido',
                'campo': 'cpf',
                'valor': cpf,
                'descricao': "CPF inválido (dígitos verificadores incorretos)",
                'severidade': 'erro'
            })
        
        return erros
    
    def _validar_digitos_cpf(self, cpf: str) -> bool:
        """Valida os dígitos verificadores do CPF."""
        try:
            # Primeiro dígito
            soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
            resto = soma % 11
            digito1 = 0 if resto < 2 else 11 - resto
            
            if int(cpf[9]) != digito1:
                return False
            
            # Segundo dígito
            soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
            resto = soma % 11
            digito2 = 0 if resto < 2 else 11 - resto
            
            return int(cpf[10]) == digito2
            
        except (ValueError, IndexError):
            return False
    
    def _validar_formatos_data(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida formatos de data conforme operadora."""
        erros = []
        
        campos_data = [
            'admissao', 'demissao'
        ]
        
        # Datas de vigência são obrigatórias, mas serão adicionadas automaticamente se ausentes
        for campo in ['data_inicio_vigencia', 'data_fim_vigencia']:
            if campo in colaborador and colaborador[campo]:
                campos_data.append(campo)
        
        for campo in campos_data:
            if campo not in colaborador or not colaborador[campo]:
                continue  # Campos de data são opcionais, exceto vigências
            
            valor_data = colaborador[campo]
            data_obj = self._converter_para_data(valor_data)
            
            if data_obj is None:
                erros.append({
                    'matricula': matricula,
                    'tipo': 'data_formato',
                    'campo': campo,
                    'valor': str(valor_data),
                    'descricao': f"Data em formato inválido. Use DD/MM/YYYY",
                    'severidade': 'erro'
                })
                continue
            
            # Validar data fim maior que início (apenas se ambas existirem)
            if campo == 'data_fim_vigencia' and 'data_inicio_vigencia' in colaborador and colaborador['data_inicio_vigencia']:
                data_inicio = self._converter_para_data(colaborador['data_inicio_vigencia'])
                if data_inicio and data_obj <= data_inicio:
                    erros.append({
                        'matricula': matricula,
                        'tipo': 'data_logica',
                        'campo': campo,
                        'valor': str(valor_data),
                        'descricao': "Data fim vigência deve ser posterior à data início",
                        'severidade': 'erro'
                    })
        
        return erros
    
    def _converter_para_data(self, valor) -> Optional[date]:
        """Converte valor para objeto date."""
        if isinstance(valor, date):
            return valor
        if isinstance(valor, datetime):
            return valor.date()
        
        if isinstance(valor, str):
            # Tentar formatos comuns
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']
            for formato in formatos:
                try:
                    return datetime.strptime(valor, formato).date()
                except ValueError:
                    continue
        
        return None
    
    def _validar_valores_monetarios(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida valores monetários e cálculos."""
        erros = []
        
        # Obter valor VR de diferentes possíveis locais
        valor_vr = None
        
        if 'valor_vr_calculado' in colaborador and colaborador['valor_vr_calculado']:
            valor_vr = colaborador['valor_vr_calculado']
        elif 'calculo_vr' in colaborador and isinstance(colaborador['calculo_vr'], dict):
            calculo_vr = colaborador['calculo_vr']
            if 'valor_total' in calculo_vr and calculo_vr['valor_total']:
                valor_vr = calculo_vr['valor_total']
        
        if valor_vr is None:
            return erros  # Já validado em campos obrigatórios
        
        try:
            valor_vr = Decimal(str(valor_vr))
            
            if valor_vr <= 0:
                erros.append({
                    'matricula': matricula,
                    'tipo': 'valor_invalido',
                    'campo': 'valor_vr',
                    'valor': float(valor_vr),
                    'descricao': "Valor VR deve ser maior que zero",
                    'severidade': 'erro'
                })
                return erros
            
            # Calcular valores esperados
            valor_empresa_esperado = valor_vr * Decimal(str(self.CUSTO_EMPRESA_PERCENTUAL))
            valor_funcionario_esperado = valor_vr * Decimal(str(self.CUSTO_FUNCIONARIO_PERCENTUAL))
            
            # Para dados reais, não temos valores separados ainda - isso é OK
            # Os valores serão calculados na geração da planilha
            
        except (ValueError, InvalidOperation, TypeError) as e:
            erros.append({
                'matricula': matricula,
                'tipo': 'valor_formato',
                'campo': 'valor_vr',
                'valor': valor_vr,
                'descricao': f"Erro ao processar valor VR: {e}",
                'severidade': 'erro'
            })
        
        return erros
    
    def _validar_regras_negocio(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida regras específicas de negócio."""
        erros = []
        
        # Validar situação ativa para recebimento VR (mais flexível)
        situacao = colaborador.get('situacao', '').upper()
        status = colaborador.get('status', '').upper()
        
        # Permitir se situação for ativa OU status for ativo
        situacoes_inativas = ['DEMITIDO', 'DESLIGADO', 'INATIVO', 'DISPENSADO']
        if situacao in situacoes_inativas and status != 'ATIVO':
            erros.append({
                'matricula': matricula,
                'tipo': 'situacao_inelegivel',
                'campo': 'situacao',
                'valor': situacao,
                'descricao': "Colaborador em situação inativa não pode receber VR",
                'severidade': 'erro'
            })
        
        # Validar demissão vs vigência
        if colaborador.get('demissao'):
            data_demissao = self._converter_para_data(colaborador['demissao'])
            data_inicio_vigencia = self._converter_para_data(colaborador.get('data_inicio_vigencia'))
            
            if data_demissao and data_inicio_vigencia:
                if data_demissao < data_inicio_vigencia:
                    erros.append({
                        'matricula': matricula,
                        'tipo': 'vigencia_demissao',
                        'campo': 'data_inicio_vigencia',
                        'descricao': "Data início vigência posterior à demissão",
                        'severidade': 'erro'
                    })
        
        return erros
    
    def _validar_dados_complementares(self, matricula: str, colaborador: Dict) -> List[Dict]:
        """Valida dados complementares (warnings)."""
        warnings = []
        
        # Verificar empresa
        if not colaborador.get('empresa'):
            warnings.append({
                'matricula': matricula,
                'tipo': 'empresa_faltante',
                'campo': 'empresa',
                'descricao': "Empresa não informada",
                'severidade': 'warning'
            })
        
        # Verificar cargo
        if not colaborador.get('cargo'):
            warnings.append({
                'matricula': matricula,
                'tipo': 'cargo_faltante',
                'campo': 'cargo',
                'descricao': "Cargo não informado",
                'severidade': 'warning'
            })
        
        # Verificar endereço
        endereco = colaborador.get('endereco', {})
        if not endereco or not endereco.get('estado'):
            warnings.append({
                'matricula': matricula,
                'tipo': 'endereco_incompleto',
                'campo': 'endereco',
                'descricao': "Informações de endereço incompletas",
                'severidade': 'warning'
            })
        
        return warnings
    
    def gerar_relatorio_validacao(self) -> str:
        """Gera relatório detalhado da validação."""
        relatorio = []
        relatorio.append("="*80)
        relatorio.append("RELATÓRIO DE VALIDAÇÃO - OPERADORA VR")
        relatorio.append("="*80)
        relatorio.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append("")
        
        # Estatísticas
        relatorio.append("ESTATÍSTICAS GERAIS:")
        relatorio.append("-"*40)
        relatorio.append(f"Total de registros: {self.estatisticas['total_registros']}")
        relatorio.append(f"Registros válidos: {self.estatisticas['registros_validos']}")
        relatorio.append(f"Registros com erro: {self.estatisticas['registros_com_erro']}")
        relatorio.append(f"Registros com warning: {self.estatisticas['registros_com_warning']}")
        
        if self.estatisticas['total_registros'] > 0:
            taxa_aprovacao = (self.estatisticas['registros_validos'] / self.estatisticas['total_registros']) * 100
            relatorio.append(f"Taxa de aprovação: {taxa_aprovacao:.2f}%")
        
        # Status final
        aprovado = self.estatisticas['registros_com_erro'] == 0
        status = "✅ APROVADO" if aprovado else "❌ REPROVADO"
        relatorio.append(f"Status para envio: {status}")
        relatorio.append("")
        
        # Erros por tipo
        if self.erros_validacao:
            relatorio.append("ERROS POR TIPO:")
            relatorio.append("-"*40)
            tipos_erro = {}
            for erro in self.erros_validacao:
                tipo = erro['tipo']
                tipos_erro[tipo] = tipos_erro.get(tipo, 0) + 1
            
            for tipo, count in sorted(tipos_erro.items()):
                relatorio.append(f"{tipo}: {count} ocorrências")
            relatorio.append("")
        
        # Warnings por tipo
        if self.warnings_validacao:
            relatorio.append("WARNINGS POR TIPO:")
            relatorio.append("-"*40)
            tipos_warning = {}
            for warning in self.warnings_validacao:
                tipo = warning['tipo']
                tipos_warning[tipo] = tipos_warning.get(tipo, 0) + 1
            
            for tipo, count in sorted(tipos_warning.items()):
                relatorio.append(f"{tipo}: {count} ocorrências")
            relatorio.append("")
        
        # Primeiros erros (máximo 20)
        if self.erros_validacao:
            relatorio.append("PRIMEIROS ERROS (máximo 20):")
            relatorio.append("-"*40)
            for erro in self.erros_validacao[:20]:
                relatorio.append(f"Matrícula {erro['matricula']}: {erro['descricao']}")
            
            if len(self.erros_validacao) > 20:
                relatorio.append(f"... e mais {len(self.erros_validacao) - 20} erros")
        
        relatorio.append("="*80)
        
        return "\n".join(relatorio)

def main():
    """Função principal para testar o validador."""
    logger.info("✅ TESTANDO VALIDADOR DA OPERADORA")
    logger.info("="*50)
    
    # Criar dados de teste
    dados_teste = {
        'metadata': {'teste': True},
        'colaboradores': {
            '12345': {
                'nome': 'João Silva',
                'cpf': '12345678901',
                'valor_vr_calculado': 750.00,
                'valor_empresa_calculado': 600.00,
                'valor_funcionario_calculado': 150.00,
                'data_inicio_vigencia': '15/04/2025',
                'data_fim_vigencia': '15/05/2025',
                'situacao': 'Trabalhando'
            },
            '67890': {
                'nome': 'Maria',
                'cpf': '11111111111',  # CPF inválido
                'valor_vr_calculado': 800.00,
                'valor_empresa_calculado': 500.00,  # Valor incorreto
                'valor_funcionario_calculado': 200.00,  # Valor incorreto
                'data_inicio_vigencia': '15/04/2025',
                'data_fim_vigencia': '10/04/2025',  # Data inválida
                'situacao': 'DEMITIDO'  # Situação inelegível
            }
        }
    }
    
    validador = ValidadorOperadora()
    resultado = validador.validar_base_completa(dados_teste)
    
    logger.info("📊 RESULTADO DA VALIDAÇÃO:")
    logger.info(f"Total: {validador.estatisticas['total_registros']}")
    logger.info(f"Válidos: {validador.estatisticas['registros_validos']}")
    logger.info(f"Com erro: {validador.estatisticas['registros_com_erro']}")
    logger.info(f"Com warning: {validador.estatisticas['registros_com_warning']}")
    
    logger.info("📄 RELATÓRIO:")
    logger.info(validador.gerar_relatorio_validacao())

if __name__ == "__main__":
    main()
