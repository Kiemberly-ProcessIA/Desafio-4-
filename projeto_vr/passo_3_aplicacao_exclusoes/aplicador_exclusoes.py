#!/usr/bin/env python3
# aplicador_exclusoes.py - Aplica exclusões sugeridas pela LLM no arquivo consolidado

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Importar sistema de logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import setup_logging, log_inicio_passo, log_fim_passo

logger = setup_logging()

class AplicadorExclusoes:
    """Aplica as exclusões sugeridas pela LLM na base consolidada."""
    
    def __init__(self):
        self.base_original = None
        self.analise_llm = None
        self.base_filtrada = None
        self.estatisticas_exclusao = {}
    
    def carregar_base_original(self, caminho_base: str) -> bool:
        """Carrega a base consolidada original."""
        try:
            logger.info(f"📂 Carregando base original: {caminho_base}")
            with open(caminho_base, 'r', encoding='utf-8') as f:
                self.base_original = json.load(f)
            
            colaboradores = self.base_original.get('colaboradores', {})
            logger.info(f"✅ Base carregada: {len(colaboradores)} colaboradores")
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {caminho_base}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            return False
    
    def carregar_analise_llm(self, analise_resultado: Dict[str, Any]) -> bool:
        """Carrega o resultado da análise LLM."""
        try:
            logger.info("🤖 Carregando resultado da análise LLM")
            self.analise_llm = analise_resultado.get('analise_llm', {})
            
            # Verificar se tem as decisões necessárias
            decisoes_cargo = self.analise_llm.get('decisao_por_cargo', {})
            
            # Novo formato da LLM - extrair listas de exclusões
            cargos_para_excluir = self.analise_llm.get('cargos_para_excluir', [])
            status_para_excluir = self.analise_llm.get('status_para_excluir', [])
            situacoes_para_excluir = self.analise_llm.get('situacoes_para_excluir', [])
            
            # Converter para formato compatível 
            if cargos_para_excluir:
                decisoes_cargo = {}
                for item in cargos_para_excluir:
                    cargo = item.get('cargo', '')
                    if cargo:
                        decisoes_cargo[cargo] = {
                            'acao': 'excluir',
                            'motivo': item.get('motivo', 'Exclusão por cargo'),
                            'regra': item.get('regra_aplicada', 'LLM')
                        }
                self.analise_llm['decisao_por_cargo'] = decisoes_cargo
            
            # Extrair nomes dos status e situações para exclusão
            status_excluidos = [item.get('status', '') for item in status_para_excluir if item.get('status')]
            situacoes_excluidas = [item.get('situacao', '') for item in situacoes_para_excluir if item.get('situacao')]
            
            # Adicionar ao formato compatível
            self.analise_llm['status_excluidos'] = status_excluidos  
            self.analise_llm['situacoes_excluidas'] = situacoes_excluidas
            
            # Para compatibilidade com formato antigo
            if not decisoes_cargo:
                decisoes_cargo = self.analise_llm.get('decisao_por_cargo', {})
            if not status_excluidos:
                status_excluidos = self.analise_llm.get('status_excluidos', [])
            if not situacoes_excluidas:
                situacoes_excluidas = self.analise_llm.get('situacoes_excluidas', [])
            
            logger.info(f"📊 {len(decisoes_cargo)} decisões por cargo")
            logger.info(f"📈 {len(status_excluidos)} status marcados para exclusão")
            logger.info(f"🎯 {len(situacoes_excluidas)} situações marcadas para exclusão")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar análise LLM: {e}")
            return False
    
    def aplicar_exclusoes(self) -> Dict[str, Any]:
        """Aplica as exclusões sugeridas pela LLM."""
        if not self.base_original or not self.analise_llm:
            raise ValueError("Base original e análise LLM devem ser carregadas primeiro")
        
        log_inicio_passo("PASSO 3", "Aplicação de Exclusões Sugeridas pela LLM", logger)
        
        colaboradores_originais = self.base_original.get('colaboradores', {})
        colaboradores_filtrados = {}
        
        # Estatísticas de exclusão
        total_original = len(colaboradores_originais)
        excluidos_por_cargo = 0
        excluidos_por_status = 0
        excluidos_por_situacao = 0
        mantidos = 0
        
        # Obter decisões da LLM
        decisoes_cargo = self.analise_llm.get('decisao_por_cargo', {})
        status_excluidos = self.analise_llm.get('status_excluidos', [])
        situacoes_excluidas = self.analise_llm.get('situacoes_excluidas', [])
        
        # Processar cada colaborador
        for matricula, colaborador in colaboradores_originais.items():
            cargo = str(colaborador.get('cargo', '')).strip()
            status = str(colaborador.get('status', '')).strip()
            situacao = str(colaborador.get('situacao', '')).strip()
            
            excluir = False
            motivo_exclusao = []
            
            # Verificar exclusão por cargo
            if cargo in decisoes_cargo:
                decisao_cargo = decisoes_cargo[cargo]
                if decisao_cargo.get('acao') == 'excluir':
                    excluir = True
                    motivo_exclusao.append(f"Cargo: {decisao_cargo.get('motivo', 'Não especificado')}")
                    excluidos_por_cargo += 1
            
            # Verificar exclusão por status
            if status in status_excluidos:
                excluir = True
                motivo_exclusao.append(f"Status: {status}")
                excluidos_por_status += 1
            
            # Verificar exclusão por situação
            if situacao in situacoes_excluidas:
                excluir = True
                motivo_exclusao.append(f"Situação: {situacao}")
                excluidos_por_situacao += 1
            
            # Aplicar decisão
            if not excluir:
                colaboradores_filtrados[matricula] = colaborador.copy()
                mantidos += 1
            else:
                # Adicionar informações de exclusão para log
                colaborador_log = colaborador.copy()
                colaborador_log['motivo_exclusao'] = '; '.join(motivo_exclusao)
                colaborador_log['excluido_em'] = datetime.now().isoformat()
        
        # Criar base filtrada
        self.base_filtrada = self.base_original.copy()
        self.base_filtrada['colaboradores'] = colaboradores_filtrados
        
        # Atualizar estatísticas
        estatisticas_originais = self.base_original.get('estatisticas', {})
        estatisticas_filtradas = estatisticas_originais.copy()
        estatisticas_filtradas['total_colaboradores'] = len(colaboradores_filtrados)
        
        # Recalcular estatísticas por status
        status_counts = {}
        for colab in colaboradores_filtrados.values():
            status = colab.get('status', 'indefinido')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Atualizar contagens específicas
        estatisticas_filtradas['ativos'] = status_counts.get('ativo', 0)
        estatisticas_filtradas['desligados'] = status_counts.get('desligado', 0)
        estatisticas_filtradas['admitidos_mes'] = status_counts.get('admitido_mes', 0)
        estatisticas_filtradas['em_ferias'] = sum(1 for c in colaboradores_filtrados.values() if c.get('ferias'))
        
        self.base_filtrada['estatisticas'] = estatisticas_filtradas
        
        # Adicionar metadata de exclusão
        self.base_filtrada['metadata_exclusao'] = {
            'aplicado_em': datetime.now().isoformat(),
            'exclusoes_por_cargo': excluidos_por_cargo,
            'exclusoes_por_status': excluidos_por_status,
            'exclusoes_por_situacao': excluidos_por_situacao,
            'total_excluidos': total_original - mantidos,
            'total_mantidos': mantidos,
            'percentual_exclusao': ((total_original - mantidos) / total_original) * 100 if total_original > 0 else 0,
            'criterios_aplicados': {
                'cargos_excluidos': [cargo for cargo, dec in decisoes_cargo.items() if dec.get('acao') == 'excluir'],
                'status_excluidos': status_excluidos,
                'situacoes_excluidas': situacoes_excluidas
            }
        }
        
        # Salvar estatísticas de exclusão
        self.estatisticas_exclusao = {
            'total_original': total_original,
            'total_mantidos': mantidos,
            'total_excluidos': total_original - mantidos,
            'excluidos_por_cargo': excluidos_por_cargo,
            'excluidos_por_status': excluidos_por_status,
            'excluidos_por_situacao': excluidos_por_situacao,
            'percentual_exclusao': ((total_original - mantidos) / total_original) * 100 if total_original > 0 else 0
        }
        
        # Exibir resumo
        logger.info("📊 RESUMO DAS EXCLUSÕES")
        logger.info(f"👥 Total original: {total_original:,}")
        logger.info(f"✅ Mantidos: {mantidos:,}")
        logger.info(f"❌ Excluídos: {total_original - mantidos:,}")
        logger.info(f"📈 Taxa de exclusão: {self.estatisticas_exclusao['percentual_exclusao']:.1f}%")
        logger.info("📋 Detalhamento das exclusões:")
        logger.info(f"   • Por cargo: {excluidos_por_cargo}")
        logger.info(f"   • Por status: {excluidos_por_status}")
        logger.info(f"   • Por situação: {excluidos_por_situacao}")
        
        log_fim_passo("PASSO 3", f"Exclusões aplicadas - {mantidos:,} colaboradores mantidos", None, logger)
        
        return self.estatisticas_exclusao
    
    def salvar_base_filtrada(self, caminho_saida: str) -> bool:
        """Salva a base filtrada em arquivo."""
        if not self.base_filtrada:
            logger.error("❌ Base filtrada não foi gerada. Execute aplicar_exclusoes() primeiro.")
            return False
        
        try:
            logger.info(f"💾 Salvando base filtrada: {caminho_saida}")
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
            
            with open(caminho_saida, 'w', encoding='utf-8') as f:
                json.dump(self.base_filtrada, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ Base filtrada salva com sucesso")
            logger.info(f"📄 {len(self.base_filtrada.get('colaboradores', {}))} colaboradores na base filtrada")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar base filtrada: {e}")
            return False
    
    def gerar_relatorio_exclusoes(self, caminho_relatorio: str) -> bool:
        """Gera relatório detalhado das exclusões aplicadas."""
        if not self.estatisticas_exclusao:
            logger.warning("❌ Estatísticas de exclusão não disponíveis. Execute aplicar_exclusoes() primeiro.")
            return False
        
        try:
            logger.info(f"📄 Gerando relatório de exclusões: {caminho_relatorio}")
            
            with open(caminho_relatorio, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("📊 RELATÓRIO DE EXCLUSÕES - VALE REFEIÇÃO\n")
                f.write("=" * 80 + "\n")
                f.write(f"📅 Data do processamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Estatísticas gerais
                f.write("📈 ESTATÍSTICAS GERAIS\n")
                f.write("-" * 40 + "\n")
                f.write(f"👥 Total de colaboradores originais: {self.estatisticas_exclusao['total_original']:,}\n")
                f.write(f"✅ Colaboradores mantidos: {self.estatisticas_exclusao['total_mantidos']:,}\n")
                f.write(f"❌ Colaboradores excluídos: {self.estatisticas_exclusao['total_excluidos']:,}\n")
                f.write(f"📊 Taxa de exclusão: {self.estatisticas_exclusao['percentual_exclusao']:.1f}%\n\n")
                
                # Detalhamento das exclusões
                f.write("🔍 DETALHAMENTO DAS EXCLUSÕES\n")
                f.write("-" * 40 + "\n")
                f.write(f"🎯 Por cargo: {self.estatisticas_exclusao['excluidos_por_cargo']} exclusões\n")
                f.write(f"📋 Por status: {self.estatisticas_exclusao['excluidos_por_status']} exclusões\n")
                f.write(f"⚠️ Por situação: {self.estatisticas_exclusao['excluidos_por_situacao']} exclusões\n\n")
                
                # Critérios aplicados
                if self.base_filtrada and 'metadata_exclusao' in self.base_filtrada:
                    criterios = self.base_filtrada['metadata_exclusao']['criterios_aplicados']
                    
                    f.write("📝 CRITÉRIOS DE EXCLUSÃO APLICADOS\n")
                    f.write("-" * 40 + "\n")
                    
                    f.write("🎯 Cargos excluídos:\n")
                    for cargo in criterios.get('cargos_excluidos', []):
                        f.write(f"   • {cargo}\n")
                    
                    f.write("\n📋 Status excluídos:\n")
                    for status in criterios.get('status_excluidos', []):
                        f.write(f"   • {status}\n")
                    
                    f.write("\n⚠️ Situações excluídas:\n")
                    for situacao in criterios.get('situacoes_excluidas', []):
                        f.write(f"   • {situacao}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("✅ Exclusões aplicadas com sucesso!\n")
                f.write("💡 Base filtrada disponível para próximas etapas do processamento.\n")
                f.write("=" * 80 + "\n")
            
            logger.info(f"✓ Relatório de exclusões salvo com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar relatório: {e}")
            return False


def executar_passo3_completo(caminho_base: str, analise_llm: Dict[str, Any], 
                           caminho_saida: str, caminho_relatorio: str = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Executa o Passo 3 completo: aplica exclusões e salva resultados.
    
    Args:
        caminho_base: Caminho para base_consolidada.json
        analise_llm: Resultado da análise do Passo 2
        caminho_saida: Caminho para salvar base filtrada
        caminho_relatorio: Caminho para relatório (opcional)
    
    Returns:
        Tuple (sucesso, estatisticas_exclusao)
    """
    try:
        aplicador = AplicadorExclusoes()
        
        # Carregar dados
        if not aplicador.carregar_base_original(caminho_base):
            return False, {}
        
        if not aplicador.carregar_analise_llm(analise_llm):
            return False, {}
        
        # Aplicar exclusões
        estatisticas = aplicador.aplicar_exclusoes()
        
        # Salvar base filtrada
        if not aplicador.salvar_base_filtrada(caminho_saida):
            return False, {}
        
        # Gerar relatório se solicitado
        if caminho_relatorio:
            aplicador.gerar_relatorio_exclusoes(caminho_relatorio)
        
        return True, estatisticas
        
    except Exception as e:
        logger.error(f"❌ Erro no Passo 3: {e}")
        return False, {}


if __name__ == "__main__":
    logger.info("🔧 Módulo do Passo 3 - Aplicação de Exclusões")
    logger.info("Este módulo deve ser importado e usado através do main.py")
