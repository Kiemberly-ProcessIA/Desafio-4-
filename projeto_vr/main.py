#!/usr/bin/env python3
# main.py - Orquestrador Principal do Sistema VR

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Adicionar o diretório atual ao path para importações
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Configurar logging padronizado
from utils.logging_config import configure_project_logging, log_inicio_passo, log_fim_passo, log_erro_critico

# Configurar logger principal do sistema
logger = configure_project_logging()

def output_json(step, status, message=None, data=None):
    """Padroniza outputs em formato JSON."""
    output = {
        "step": step,
        "status": status
    }
    if message:
        output["message"] = message
    if data:
        output["data"] = data
    
    # Log estruturado + saída JSON
    if status == "iniciando":
        logger.info(f"🚀 {step.upper()}: {message}")
    elif status == "concluido":
        logger.info(f"✅ {step.upper()}: {message}")
    elif status == "erro":
        logger.error(f"❌ {step.upper()}: {message}")
    else:
        logger.info(f"ℹ️  {step.upper()}: {message}")
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

# Importações dos passos
from passo_1_leitura_validacao.consolidador_json import OrquestradorPasso1
from passo_2_tratamento_exclusoes.analisador_exclusoes_llm import AnalisadorExclusions
from passo_3_aplicacao_exclusoes.aplicador_exclusoes import executar_passo3_completo
from passo_4_validacao_calculo.orquestrador_passo4 import executar_passo4
from passo_5_entrega_final.orquestrador_passo5 import OrquestradorPasso5
from passo_6_validacao_final.orquestrador_passo6 import OrquestradorPasso6

def _gerar_json_agrupamentos(dados_json_str):
    """Gera JSON agrupado por cargos, status e situações."""
    import json
    from datetime import datetime
    
    dados = json.loads(dados_json_str)
    colaboradores = dados.get('colaboradores', {})
    
    # Conjuntos para valores únicos
    cargos_unicos = set()
    status_unicos = set()
    situacoes_unicas = set()
    
    # Processar cada colaborador para extrair valores únicos
    for matricula, colab in colaboradores.items():
        cargo = str(colab.get('cargo', '')).strip() if colab.get('cargo') is not None else ''
        status = str(colab.get('status', '')).strip() if colab.get('status') is not None else ''
        situacao = str(colab.get('situacao', '')).strip() if colab.get('situacao') is not None else ''
        
        # Adicionar apenas valores válidos (não vazios)
        if cargo and cargo != 'N/A':
            cargos_unicos.add(cargo)
        if status and status != 'N/A':
            status_unicos.add(status)
        if situacao and situacao != 'N/A':
            situacoes_unicas.add(situacao)
    
    # Estrutura de retorno simples com listas ordenadas
    resultado = {
        "cargos": sorted(list(cargos_unicos)),
        "status": sorted(list(status_unicos)),
        "situacoes": sorted(list(situacoes_unicas)),
        "metadata": {
            "gerado_em": datetime.now().isoformat(),
            "total_cargos": len(cargos_unicos),
            "total_status": len(status_unicos),
            "total_situacoes": len(situacoes_unicas),
            "total_colaboradores": len(colaboradores)
        }
    }
    
    return resultado

def executar_passo1_consolidacao(gerar_relatorio=False):
    """Executa o Passo 1 - Leitura e Consolidação dos dados."""
    log_inicio_passo("PASSO 1", "Leitura e Consolidação de Dados", logger)
    output_json("passo_1", "iniciando", "Leitura e consolidação de dados")
    
    try:
        # Configurar caminhos
        projeto_root = Path(__file__).parent.parent
        pasta_input = str(projeto_root / "input_data" / "colaboradores")
        pasta_config = str(projeto_root / "input_data" / "configuracoes")
        pasta_output = str(projeto_root / "output")
        
        logger.info(f"📁 Pasta colaboradores: {pasta_input}")
        logger.info(f"📁 Pasta configurações: {pasta_config}")
        logger.info(f"📁 Pasta output: {pasta_output}")
        
        # Inicializar orquestrador
        orquestrador = OrquestradorPasso1(
            pasta_colaboradores=pasta_input,
            pasta_configuracoes=pasta_config,
            pasta_output=pasta_output
        )
        
        logger.info("🔧 Orquestrador inicializado com sucesso")
        
        # Executar consolidação - sempre em modo debug para pipeline completo
        resultado = orquestrador.executar_processo_completo(modo_debug=True)
        
        if resultado and resultado.get('status') == 'SUCESSO':
            estatisticas = {
                'total_colaboradores': resultado['total_colaboradores'],
                'ativos': resultado.get('ativos', 0),
                'desligados': resultado.get('desligados', 0),
                'sindicatos': resultado.get('total_sindicatos', 0)
            }
            
            log_fim_passo("PASSO 1", "Leitura e Consolidação de Dados", estatisticas, logger)
            output_json("passo_1", "concluido", 
                       f"{resultado['total_colaboradores']} colaboradores processados")
            
            # SEMPRE gerar arquivo de agrupamentos (essencial para o Passo 2)
            try:
                logger.info("📊 Gerando arquivo de agrupamentos para análise LLM...")
                
                # Gerar JSON agrupado por cargos, status e situações
                json_agrupamentos = _gerar_json_agrupamentos(orquestrador.json_consolidado)
                caminho_agrupamentos = os.path.join(pasta_output, "agrupamentos_consolidados.json")
                
                with open(caminho_agrupamentos, 'w', encoding='utf-8') as f:
                    json.dump(json_agrupamentos, f, indent=2, ensure_ascii=False)
                
                logger.info(f"📄 Arquivo de agrupamentos salvo: {caminho_agrupamentos}")
                logger.info(f"🎯 {json_agrupamentos['metadata']['total_cargos']} cargos únicos identificados")
                
            except Exception as e:
                logger.warning(f"⚠️  Erro ao gerar arquivo de agrupamentos: {e}")
                output_json("passo_1", "warning", f"Erro ao gerar arquivo de agrupamentos: {e}")
            
            # Gerar relatórios adicionais se solicitado
            if gerar_relatorio:
                try:
                    logger.info("📊 Gerando relatórios adicionais opcionais...")
                    # Aqui podem ser adicionados outros relatórios futuros
                    
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao gerar relatórios adicionais: {e}")
                    output_json("passo_1", "warning", f"Erro ao gerar relatórios: {e}")
            
            # Extrair dados LLM para o Passo 2
            dados_llm = orquestrador.extrair_dados_para_llm()
            return True, dados_llm, orquestrador.json_consolidado
            
        else:
            erro_msg = resultado.get('erro', 'Erro desconhecido na consolidação') if resultado else 'Resultado nulo'
            log_erro_critico(f"Falha no Passo 1: {erro_msg}", logger=logger)
            output_json("passo_1", "erro", erro_msg)
            return False, None, None
            
    except Exception as e:
        log_erro_critico(f"Exceção no Passo 1: {str(e)}", e, logger)
        output_json("passo_1", "erro", str(e))
        return False, None, None

def executar_passo2_llm(dados_llm=None, dados_consolidados=None):
    """Executa o Passo 2 - Análise LLM de Exclusões."""
    output_json("passo_2", "iniciando", "Análise LLM de exclusões")
    
    try:
        # Inicializar analisador LLM
        analisador = AnalisadorExclusions()
        
        # Detectar caminho do arquivo de agrupamentos
        projeto_root = Path(__file__).parent.parent
        caminho_agrupamentos = str(projeto_root / "output" / "agrupamentos_consolidados.json")
        
        # Verificar se existe o arquivo de agrupamentos (preferência)
        if os.path.exists(caminho_agrupamentos):
            resultado = analisador.analisar_com_agrupamentos_json(caminho_agrupamentos)
        elif dados_consolidados:
            # Usar o método que aceita dados em memória
            import json
            dados_dict = json.loads(dados_consolidados) if isinstance(dados_consolidados, str) else dados_consolidados
            resultado = analisador.analisar_com_dados_memoria(dados_dict)
        else:
            # Usar caminhos padrão (modo standalone)
            pasta_colaboradores = str(projeto_root / "input_data" / "colaboradores")
            pasta_configuracoes = str(projeto_root / "input_data" / "configuracoes")
            
            # Executar análise usando os caminhos
            resultado = analisador.analisar_dados_passo1(pasta_colaboradores, pasta_configuracoes)
        
        if resultado and not resultado.get('erro'):
            output_json("passo_2", "concluido", "Análise LLM realizada com sucesso")
            return True, resultado
        else:
            output_json("passo_2", "erro", resultado.get('erro', 'Resultado vazio') if resultado else 'Resultado vazio')
            return False, None
            
    except Exception as e:
        output_json("passo_2", "erro", str(e))
        return False, None

def executar_passo3_exclusoes(analise_passo2=None, pasta_output=None):
    """Executa o Passo 3 - Aplicação de Exclusões."""
    output_json("passo_3", "iniciando", "Aplicação de exclusões")
    
    # Usar caminhos padrão se não especificados
    if not pasta_output:
        projeto_root = Path(__file__).parent.parent
        pasta_output = str(projeto_root / "output")
    
    try:
        # Caminhos dos arquivos
        caminho_base = os.path.join(pasta_output, "passo_1-base_consolidada.json")
        caminho_saida = os.path.join(pasta_output, "passo_3-base_filtrada_vr.json")
        caminho_relatorio = os.path.join(pasta_output, "passo_3-relatorio_exclusoes.txt")
        
        # Verificar se a base consolidada existe
        if not os.path.exists(caminho_base):
            output_json("passo_3", "erro", f"Arquivo base não encontrado: {caminho_base}")
            return False, None
        
        # Verificar se temos resultado do Passo 2
        if not analise_passo2:
            output_json("passo_3", "erro", "Resultado do Passo 2 não disponível")
            return False, None
        
        # Executar aplicação de exclusões
        sucesso, estatisticas = executar_passo3_completo(
            caminho_base=caminho_base,
            analise_llm=analise_passo2,
            caminho_saida=caminho_saida,
            caminho_relatorio=caminho_relatorio
        )
        
        if sucesso:
            output_json("passo_3", "concluido", "Exclusões aplicadas com sucesso")
            return True, estatisticas
        else:
            output_json("passo_3", "erro", "Falha na aplicação das exclusões")
            return False, None
            
    except Exception as e:
        output_json("passo_3", "erro", str(e))
        return False, None

def executar_passo4_validacao_calculo(arquivo_entrada: str = None) -> tuple:
    """Executa o Passo 4: Validação e Cálculo de VR."""
    output_json("passo_4", "iniciando", "Validação e cálculo de VR")
    
    try:
        # Configurar caminhos absolutos
        projeto_root = Path(__file__).parent.parent
        
        # Usar arquivo padrão se não especificado
        if not arquivo_entrada:
            arquivo_entrada = str(projeto_root / "output" / "passo_3-base_filtrada_vr.json")
        
        config_path = str(projeto_root / "input_data" / "configuracoes")
        output_path = str(projeto_root / "output")
        
        # Verificar se arquivo existe
        if not os.path.exists(arquivo_entrada):
            output_json("passo_4", "erro", f"Arquivo de entrada não encontrado: {arquivo_entrada}")
            return False, None
        
        # Executar validação e cálculo com caminhos absolutos
        dados_finais = executar_passo4(arquivo_entrada, config_path, output_path)
        
        output_json("passo_4", "concluido", "Validação e cálculo realizados com sucesso")
        return True, dados_finais
        
    except Exception as e:
        output_json("passo_4", "erro", str(e))
        return False, None

def executar_passo5_entrega_final(arquivo_entrada: str = None) -> tuple:
    """Executa o Passo 5: Entrega Final - Planilha para Operadora."""
    output_json("passo_5", "iniciando", "Geração de planilha final")
    
    try:
        # Inicializar orquestrador do Passo 5
        orquestrador = OrquestradorPasso5()
        
        # Executar processo completo
        resultados = orquestrador.executar_passo5(arquivo_entrada)
        
        # Exibir resumo final detalhado (mantido para resultado final)
        if resultados.get('status') == 'concluido':
            print(f"✅ PASSO 5 CONCLUÍDO! Planilhas geradas para operadora")
            print(f"👥 Colaboradores processados: {resultados.get('total_colaboradores', 0):,}")
            print(f"💰 Valor total VR: R$ {resultados.get('valor_total_vr', 0):,.2f}")
            
            # Mostrar arquivos principais
            arquivos = resultados.get('arquivos_principais', {})
            total_arquivos = 1 if arquivos.get('planilha_excel') else 0
            print(f"📁 Arquivos gerados: {total_arquivos}")
            
            print("\n📄 ARQUIVOS PRINCIPAIS:")
            for tipo, arquivo in arquivos.items():
                if arquivo:
                    nome = Path(arquivo).name
                    print(f"  ✅ {tipo.replace('_', ' ').title()}: {nome}")
            
            return True, resultados
        else:
            output_json("passo_5", "erro", resultados.get('erro', 'Erro desconhecido'))
            return False, resultados
        
    except Exception as e:
        output_json("passo_5", "erro", str(e))
        return False, None

def executar_pipeline_completo(modo_debug=False):
    """Executa o pipeline completo: Passo 1 + Passo 2 LLM + Passo 3."""
    output_json("pipeline", "iniciando", "Pipeline completo VR")
    
    # Executar Passo 1
    sucesso_passo1, dados_llm, dados_consolidados = executar_passo1_consolidacao(gerar_relatorio=modo_debug)
    
    if not sucesso_passo1:
        output_json("pipeline", "erro", "Pipeline interrompido - Erro no Passo 1")
        return False
    
    # Executar Passo 2 com dados do Passo 1
    sucesso_passo2, resultado_passo2 = executar_passo2_llm(dados_llm, dados_consolidados)
    
    if not sucesso_passo2:
        output_json("pipeline", "erro", "Pipeline interrompido - Erro no Passo 2")
        return False
    
    # Executar Passo 3 com resultado do Passo 2
    sucesso_passo3, estatisticas_passo3 = executar_passo3_exclusoes(resultado_passo2)
    
    if not sucesso_passo3:
        output_json("pipeline", "erro", "Pipeline interrompido - Erro no Passo 3")
        return False
    
    output_json("pipeline", "concluido", "Pipeline completo executado com sucesso", 
                {"colaboradores_processados": estatisticas_passo3['total_original'] if estatisticas_passo3 else 0,
                 "elegiveis": estatisticas_passo3['total_mantidos'] if estatisticas_passo3 else 0,
                 "excluidos": estatisticas_passo3['total_excluidos'] if estatisticas_passo3 else 0,
                 "percentual_exclusao": estatisticas_passo3['percentual_exclusao'] if estatisticas_passo3 else 0})
    
    return True

def executar_pipeline_completo_sem_auditoria(modo_debug=False):
    """Executa o pipeline completo: Passos 1 a 5 (sem auditoria LLM)."""
    output_json("pipeline_5_passos", "iniciando", "Pipeline com 5 passos (sem auditoria)")
    
    # Executar Passo 1
    sucesso_passo1, dados_llm, dados_consolidados = executar_passo1_consolidacao(gerar_relatorio=modo_debug)
    
    if not sucesso_passo1:
        output_json("pipeline_5_passos", "erro", "Pipeline interrompido - Erro no Passo 1")
        return False
    
    # Executar Passo 2 com dados do Passo 1
    sucesso_passo2, resultado_passo2 = executar_passo2_llm(dados_llm, dados_consolidados)
    
    if not sucesso_passo2:
        output_json("pipeline_5_passos", "erro", "Pipeline interrompido - Erro no Passo 2")
        return False
    
    # Executar Passo 3 com resultado do Passo 2
    sucesso_passo3, estatisticas_passo3 = executar_passo3_exclusoes(resultado_passo2)
    
    if not sucesso_passo3:
        output_json("pipeline_5_passos", "erro", "Pipeline interrompido - Erro no Passo 3")
        return False
    
    # Executar Passo 4 (Validação e Cálculo)
    sucesso_passo4, dados_passo4 = executar_passo4_validacao_calculo()
    
    if not sucesso_passo4:
        output_json("pipeline_5_passos", "erro", "Pipeline interrompido - Erro no Passo 4")
        return False
    
    # Executar Passo 5 (Entrega Final)
    sucesso_passo5, resultados_passo5 = executar_passo5_entrega_final()
    
    if not sucesso_passo5:
        output_json("pipeline_5_passos", "erro", "Pipeline interrompido - Erro no Passo 5")
        return False
    
    # Resultado final
    print("\n" + "=" * 80)
    print("🎉 PIPELINE DE 5 PASSOS EXECUTADO COM SUCESSO!")
    print("=" * 80)
    
    if estatisticas_passo3:
        print(f"\n📊 RESUMO FINAL DO PROCESSAMENTO:")
        print(f"👥 Colaboradores processados: {estatisticas_passo3['total_original']:,}")
        print(f"✅ Elegíveis para VR: {estatisticas_passo3['total_mantidos']:,}")
        print(f"❌ Excluídos: {estatisticas_passo3['total_excluidos']:,}")
        print(f"📈 Taxa de exclusão: {estatisticas_passo3['percentual_exclusao']:.1f}%")
    
    if resultados_passo5 and resultados_passo5.get('valor_total_vr'):
        print(f"💰 Valor total VR: R$ {resultados_passo5.get('valor_total_vr', 0):,.2f}")
        print(f"📁 Arquivos gerados: 1")
    
    output_json("pipeline_5_passos", "concluido", "Pipeline de 5 passos executado com sucesso")
    return True

def executar_pipeline_completo_com_passos4e5(modo_debug=False):
    """Executa o pipeline completo: Passos 1 a 6 (incluindo auditoria LLM)."""
    output_json("pipeline_full", "iniciando", "Pipeline completo com todos os 6 passos")
    
    # Executar Passo 1
    sucesso_passo1, dados_llm, dados_consolidados = executar_passo1_consolidacao(gerar_relatorio=modo_debug)
    
    if not sucesso_passo1:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 1")
        return False
    
    # Executar Passo 2 com dados do Passo 1
    sucesso_passo2, resultado_passo2 = executar_passo2_llm(dados_llm, dados_consolidados)
    
    if not sucesso_passo2:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 2")
        return False
    
    # Executar Passo 3 com resultado do Passo 2
    sucesso_passo3, estatisticas_passo3 = executar_passo3_exclusoes(resultado_passo2)
    
    if not sucesso_passo3:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 3")
        return False
    
    # Executar Passo 4 (Validação e Cálculo)
    sucesso_passo4, dados_passo4 = executar_passo4_validacao_calculo()
    
    if not sucesso_passo4:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 4")
        return False
    
    # Executar Passo 5 (Entrega Final)
    sucesso_passo5, resultados_passo5 = executar_passo5_entrega_final()
    
    if not sucesso_passo5:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 5")
        return False
    
    # Executar Passo 6 (Auditoria Final com LLM)
    sucesso_passo6, resultados_passo6 = executar_passo6_auditoria_final()
    
    if not sucesso_passo6:
        output_json("pipeline_full", "erro", "Pipeline interrompido - Erro no Passo 6")
        return False
    
    # Resultado final completo
    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETO EXECUTADO COM SUCESSO!")
    print("=" * 80)
    
    if estatisticas_passo3:
        print(f"\n📊 RESUMO FINAL DO PROCESSAMENTO:")
        print(f"👥 Colaboradores processados: {estatisticas_passo3['total_original']:,}")
        print(f"✅ Elegíveis para VR: {estatisticas_passo3['total_mantidos']:,}")
        print(f"❌ Excluídos: {estatisticas_passo3['total_excluidos']:,}")
        print(f"📈 Taxa de exclusão: {estatisticas_passo3['percentual_exclusao']:.1f}%")
    
    if resultados_passo5 and resultados_passo5.get('valor_total_vr'):
        print(f"💰 Valor total VR: R$ {resultados_passo5.get('valor_total_vr', 0):,.2f}")
        print(f"📁 Arquivos gerados: 1")
    
    # Mostrar resultado da auditoria
    if resultados_passo6:
        score = resultados_passo6.get('score_conformidade', 0)
        aprovado = resultados_passo6.get('auditoria_aprovada', False)
        print(f"\n🔍 AUDITORIA FINAL LLM:")
        print(f"📊 Score de Conformidade: {score:.1%}")
        print(f"✅ Status: {'🟢 APROVADO' if aprovado else '🔴 REPROVADO'}")
    
    return True

def executar_passo6_auditoria_final() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Executa o Passo 6: Auditoria Final com LLM."""
    output_json("passo_6", "iniciando", "Auditoria final com LLM Gemini")
    
    try:
        # Inicializar orquestrador do Passo 6
        orquestrador = OrquestradorPasso6()
        
        # Executar auditoria completa
        resultados = orquestrador.executar_passo6_completo()
        
        # Exibir resumo final
        if resultados.get('status') == 'concluido':
            score = resultados.get('score_conformidade', 0)
            aprovado = resultados.get('auditoria_aprovada', False)
            
            print(f"✅ PASSO 6 CONCLUÍDO! Auditoria LLM realizada")
            print(f"� Score de Conformidade: {score:.1%}")
            print(f"✅ Status Final: {'🟢 APROVADO' if aprovado else '🔴 REPROVADO'}")
            
            if not aprovado:
                recomendacoes = resultados.get('recomendacoes_finais', [])
                if recomendacoes:
                    print(f"\n⚠️  RECOMENDAÇÕES CRÍTICAS:")
                    for i, rec in enumerate(recomendacoes[:3], 1):  # Mostrar apenas 3 principais
                        print(f"   {i}. {rec}")
            
            output_json("passo_6", "concluido", f"Auditoria concluída - Score: {score:.1%}")
            return True, resultados
        else:
            output_json("passo_6", "erro", resultados.get('erro', 'Erro desconhecido'))
            return False, resultados
        
    except Exception as e:
        output_json("passo_6", "erro", str(e))
        return False, None

def _limpar_output_final():
    """Remove todos os arquivos exceto o Excel mais recente do Passo 5."""
    import glob
    import os
    
    try:
        output_dir = Path("output")
        
        # Encontrar Excel mais recente
        excel_files = glob.glob(str(output_dir / "VR_MENSAL_OPERADORA_*.xlsx"))
        if not excel_files:
            return
        
        excel_mais_recente = max(excel_files, key=os.path.getmtime)
        
        # Remover todos os outros arquivos
        total_removidos = 0
        for arquivo in output_dir.glob("*"):
            if arquivo.is_file() and str(arquivo) != excel_mais_recente:
                arquivo.unlink()
                total_removidos += 1
        
        print(f"🧹 Limpeza automática: {total_removidos} arquivos temporários removidos")
        
    except Exception as e:
        print(f"⚠️ Erro na limpeza automática: {e}")

def _encontrar_excel_final():
    """Encontra o arquivo Excel final gerado."""
    import glob
    import os
    
    excel_files = glob.glob("output/VR_MENSAL_OPERADORA_*.xlsx")
    if excel_files:
        excel_mais_recente = max(excel_files, key=os.path.getmtime)
        return Path(excel_mais_recente).name
    return None

def main():
    """Função principal para executar o sistema."""
    parser = argparse.ArgumentParser(description="Sistema VR - Orquestrador Principal")
    parser.add_argument('comando', choices=['passo1', 'passo2-llm', 'passo3', 'passo4', 'passo5', 'passo6', 'pipeline', 'all'], 
                       help='Comando a executar')
    parser.add_argument('--debug', action='store_true', 
                       help='Executar em modo debug (salva arquivos intermediários)')
    parser.add_argument('--incluir-auditoria', action='store_true',
                       help='Incluir auditoria LLM no pipeline completo (Passo 6)')
    parser.add_argument('--pasta-colaboradores', 
                       help='Pasta com dados dos colaboradores')
    parser.add_argument('--pasta-configuracoes', 
                       help='Pasta com configurações')
    parser.add_argument('--pasta-output', 
                       help='Pasta de saída')
    parser.add_argument('--arquivo-entrada',
                       help='Arquivo de entrada para passos específicos')
    
    args = parser.parse_args()
    
    # Detectar modo debug a partir de variável de ambiente também
    modo_debug = args.debug or os.getenv('DEBUG', '').lower() in ('true', '1', 'yes')
    
    try:
        if args.comando == 'passo1':
            sucesso, _, _ = executar_passo1_consolidacao(gerar_relatorio=modo_debug)
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'passo2-llm':
            sucesso, _ = executar_passo2_llm()
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'passo3':
            sucesso, _ = executar_passo3_exclusoes()
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'passo4':
            sucesso, _ = executar_passo4_validacao_calculo(args.arquivo_entrada)
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'passo5':
            sucesso, _ = executar_passo5_entrega_final(args.arquivo_entrada)
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'passo6':
            sucesso, _ = executar_passo6_auditoria_final()
            sys.exit(0 if sucesso else 1)
            
        elif args.comando == 'pipeline' or args.comando == 'all':
            if args.incluir_auditoria:
                # Pipeline completo com auditoria (6 passos)
                sucesso = executar_pipeline_completo_com_passos4e5(modo_debug)
            else:
                # Pipeline original (5 passos)
                sucesso = executar_pipeline_completo_sem_auditoria(modo_debug)
            sys.exit(0 if sucesso else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
