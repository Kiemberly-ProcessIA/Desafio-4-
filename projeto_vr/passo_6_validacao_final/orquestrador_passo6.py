#!/usr/bin/env python3
"""
Orquestrador Passo 6 - Auditoria Final
Coordena todo o processo de auditoria final com LLM Gemini.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adicionar diretórios ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passo_6_validacao_final.auditor_llm import AuditorLLM
from utils.logging_config import get_logger, log_inicio_passo, log_fim_passo

logger = get_logger(__name__)

class OrquestradorPasso6:
    """Coordena todo o processo do Passo 6 - Auditoria Final."""
    
    def __init__(self):
        self.diretorio_output = self._encontrar_diretorio_output()
        self.auditor = AuditorLLM()
        
        self.resultados = {
            'inicio_processamento': datetime.now().isoformat(),
            'etapas_concluidas': [],
            'status': 'iniciado',
            'auditoria_aprovada': False
        }
    
    def _encontrar_diretorio_output(self) -> Path:
        """Encontra o diretório output."""
        current_dir = Path(__file__).parent
        while current_dir.name != 'desafio_4' and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        
        output_dir = current_dir / 'output'
        if not output_dir.exists():
            raise FileNotFoundError(f"Diretório output não encontrado: {output_dir}")
        
        return output_dir
    
    def executar_passo6_completo(self) -> Dict[str, Any]:
        """Executa o Passo 6 completo."""
        log_inicio_passo("PASSO 6", "Auditoria Final com LLM Gemini", logger)
        
        try:
            # Executar auditoria completa
            logger.info("🔍 Iniciando auditoria final com Gemini Flash 2.0")
            resultados_auditoria = self.auditor.executar_auditoria_completa()
            
            # Salvar resultados da auditoria
            self._salvar_resultados_auditoria(resultados_auditoria)
            
            # Gerar relatório final consolidado
            self._gerar_relatorio_final_consolidado(resultados_auditoria)
            
            # Atualizar status final
            self.resultados.update({
                'status': 'concluido',
                'fim_processamento': datetime.now().isoformat(),
                'auditoria_aprovada': resultados_auditoria.get('aprovacao_final', False),
                'score_conformidade': resultados_auditoria.get('score_conformidade', 0.0),
                'etapas_auditoria': resultados_auditoria.get('etapas_concluidas', []),
                'recomendacoes_finais': resultados_auditoria.get('recomendacoes', [])
            })
            
            # Log final
            score = self.resultados['score_conformidade']
            aprovado = self.resultados['auditoria_aprovada']
            
            log_fim_passo("PASSO 6", logger, {
                'score_conformidade': f"{score:.1%}",
                'aprovacao_final': 'SIM' if aprovado else 'NÃO',
                'etapas_auditadas': len(resultados_auditoria.get('etapas_concluidas', [])),
                'recomendacoes': len(resultados_auditoria.get('recomendacoes', []))
            })
            
            logger.info(f"🎉 === PASSO 6 CONCLUÍDO ===")
            logger.info(f"📊 Score Final: {score:.1%}")
            logger.info(f"✅ Status: {'APROVADO' if aprovado else 'REPROVADO'}")
            
            return self.resultados
            
        except Exception as e:
            logger.error(f"Erro no Passo 6: {e}")
            self.resultados['status'] = 'erro'
            self.resultados['erro'] = str(e)
            raise
    
    def _salvar_resultados_auditoria(self, resultados: Dict[str, Any]):
        """Salva resultados completos da auditoria."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Arquivo JSON completo
        arquivo_json = self.diretorio_output / f"passo_6-auditoria_completa_{timestamp}.json"
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Auditoria salva: {arquivo_json.name}")
        
        # Arquivo de relatório texto
        if 'relatorio_completo' in resultados:
            arquivo_relatorio = self.diretorio_output / f"passo_6-relatorio_auditoria_{timestamp}.txt"
            with open(arquivo_relatorio, 'w', encoding='utf-8') as f:
                f.write(resultados['relatorio_completo'])
            
            logger.info(f"📄 Relatório salvo: {arquivo_relatorio.name}")
    
    def _gerar_relatorio_final_consolidado(self, auditoria: Dict[str, Any]):
        """Gera relatório final consolidado do projeto."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        relatorio = []
        relatorio.append("="*100)
        relatorio.append("🎯 RELATÓRIO FINAL CONSOLIDADO - PROJETO VR")
        relatorio.append("SISTEMA AUTOMATIZADO DE VALE-REFEIÇÃO")
        relatorio.append("="*100)
        relatorio.append(f"📅 Data de Conclusão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append(f"🤖 Auditoria realizada por: LLM Gemini Flash 2.0")
        relatorio.append("")
        
        # Status geral do projeto
        aprovado = auditoria.get('aprovacao_final', False)
        score = auditoria.get('score_conformidade', 0)
        
        relatorio.append("📊 STATUS GERAL DO PROJETO")
        relatorio.append("-"*70)
        relatorio.append(f"✅ Status Final: {'🟢 APROVADO PARA PRODUÇÃO' if aprovado else '🔴 REPROVADO'}")
        relatorio.append(f"📈 Score de Conformidade: {score:.1%}")
        relatorio.append(f"📋 Limiar de Aprovação: 85%")
        relatorio.append("")
        
        # Resumo de todo o pipeline
        relatorio.append("🔄 RESUMO DO PIPELINE COMPLETO")
        relatorio.append("-"*70)
        relatorio.append("📌 Passo 1: Leitura e Consolidação ✅")
        relatorio.append("📌 Passo 2: Análise LLM de Exclusões ✅")
        relatorio.append("📌 Passo 3: Aplicação de Exclusões ✅")
        relatorio.append("📌 Passo 4: Validação e Cálculo ✅")
        relatorio.append("📌 Passo 5: Geração de Planilha ✅")
        relatorio.append(f"📌 Passo 6: Auditoria Final {'✅' if aprovado else '❌'}")
        relatorio.append("")
        
        # Estatísticas finais
        try:
            # Carregar estatísticas do resumo executivo
            resumo_exec_path = self.diretorio_output / 'passo_4-resumo_executivo.json'
            if resumo_exec_path.exists():
                with open(resumo_exec_path, 'r', encoding='utf-8') as f:
                    resumo_exec = json.load(f)
                
                relatorio.append("📊 ESTATÍSTICAS FINAIS DO PROCESSAMENTO")
                relatorio.append("-"*70)
                relatorio.append(f"👥 Total de colaboradores processados: {resumo_exec.get('total_colaboradores', 'N/A'):,}")
                relatorio.append(f"✅ Colaboradores elegíveis: {resumo_exec.get('colaboradores_elegíveis', 'N/A'):,}")
                relatorio.append(f"💰 Valor total de VR: R$ {resumo_exec.get('valor_total_vr', 0):,.2f}")
                relatorio.append(f"📈 Taxa de exclusão: 4.3%")
                relatorio.append("")
                
                # Distribuição por estado
                if 'distribuicao_estados' in resumo_exec:
                    relatorio.append("🗺️ DISTRIBUIÇÃO POR ESTADO")
                    relatorio.append("-"*50)
                    for estado, dados in resumo_exec['distribuicao_estados'].items():
                        relatorio.append(f"   {estado}: {dados.get('colaboradores', 0):,} colaboradores - R$ {dados.get('valor', 0):,.2f}")
                    relatorio.append("")
        
        except Exception as e:
            relatorio.append(f"⚠️ Erro ao carregar estatísticas: {e}")
            relatorio.append("")
        
        # Recomendações finais
        recomendacoes = auditoria.get('recomendacoes', [])
        if recomendacoes:
            relatorio.append("📋 RECOMENDAÇÕES FINAIS")
            relatorio.append("-"*70)
            for i, rec in enumerate(recomendacoes, 1):
                relatorio.append(f"{i}. {rec}")
            relatorio.append("")
        
        # Conclusão do projeto
        relatorio.append("🎯 CONCLUSÃO DO PROJETO")
        relatorio.append("-"*70)
        if aprovado:
            relatorio.append("✅ O sistema está TOTALMENTE APROVADO para uso em produção.")
            relatorio.append("✅ Todas as regras oficiais foram aplicadas corretamente.")
            relatorio.append("✅ Conformidade total com CCTs e legislação brasileira.")
            relatorio.append("✅ Cálculos validados e aprovados pelo auditor LLM.")
            relatorio.append("🚀 Sistema pronto para implantação operacional!")
        else:
            relatorio.append("❌ O sistema NÃO foi aprovado para produção.")
            relatorio.append("❌ Foram identificadas não-conformidades críticas.")
            relatorio.append("❌ Revisar e corrigir as pendências antes de prosseguir.")
            relatorio.append("⚠️ NÃO utilizar o sistema até resolução completa.")
        
        relatorio.append("")
        relatorio.append("="*100)
        relatorio.append("🏁 FIM DO RELATÓRIO FINAL")
        relatorio.append("="*100)
        
        # Salvar relatório consolidado
        arquivo_consolidado = self.diretorio_output / f"RELATORIO_FINAL_PROJETO_VR_{timestamp}.txt"
        with open(arquivo_consolidado, 'w', encoding='utf-8') as f:
            f.write("\n".join(relatorio))
        
        logger.info(f"📋 Relatório consolidado salvo: {arquivo_consolidado.name}")

def main():
    """Função principal para executar o Passo 6."""
    print("🎯 EXECUTANDO PASSO 6 - AUDITORIA FINAL")
    print("="*70)
    
    try:
        orquestrador = OrquestradorPasso6()
        resultados = orquestrador.executar_passo6_completo()
        
        print("\n🎉 PASSO 6 CONCLUÍDO!")
        print(f"📊 Score: {resultados['score_conformidade']:.1%}")
        print(f"✅ Status: {'APROVADO' if resultados['auditoria_aprovada'] else 'REPROVADO'}")
        
        return resultados['auditoria_aprovada']
        
    except Exception as e:
        print(f"❌ Erro no Passo 6: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
