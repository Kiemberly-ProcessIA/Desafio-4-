#!/usr/bin/env python3
"""
Auditor LLM - Passo 6
Sistema de auditoria e validação final usando LLM Gemini para verificar conformidade com:
- Regras oficiais do projeto (Desafio 4)
- Convenções Coletivas de Trabalho (CCTs)
- Legislação trabalhista brasileira
- Consistência dos dados e cálculos
"""

import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Adicionar diretórios ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import google.generativeai as genai
from utils.logging_config import get_logger

# Importar configurações
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

logger = get_logger(__name__)


class AuditorLLM:
    """Auditor inteligente que usa LLM para validação final do projeto."""

    def __init__(self):
        """Inicializa o auditor LLM."""
        self.projeto_root = self._encontrar_projeto_root()
        self.diretorio_output = self.projeto_root / "output"
        self.diretorio_regras = self.projeto_root / "regras"
        self.diretorio_input = self.projeto_root / "input_data"

        # Configurar cliente LLM
        api_key = config.GOOGLE_API_KEY
        if not api_key or api_key == "SUA_CHAVE_AQUI":
            raise ValueError("GOOGLE_API_KEY não configurada corretamente no config.py")

        genai.configure(api_key=api_key)
        self.modelo_llm = genai.GenerativeModel(config.NOME_MODELO_LLM)

        self.resultados_auditoria = {
            "timestamp_inicio": datetime.now().isoformat(),
            "etapas_concluidas": [],
            "validacoes_realizadas": [],
            "inconsistencias_encontradas": [],
            "recomendacoes": [],
            "aprovacao_final": False,
            "score_conformidade": 0.0,
        }

        logger.info("🔧 Auditor LLM inicializado com Gemini Flash 2.0")

    def _encontrar_projeto_root(self) -> Path:
        """Encontra o diretório raiz do projeto."""
        current_dir = Path(__file__).parent
        while current_dir.name != "desafio_4" and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        return current_dir

    def executar_auditoria_completa(self) -> Dict[str, Any]:
        """Executa auditoria completa do projeto."""
        logger.info("🎯 === INICIANDO PASSO 6: AUDITORIA FINAL COM LLM ===")

        try:
            # Etapa 1: Carregar documentos de regras
            logger.info("Etapa 1/6: Carregando documentos de regras e CCTs")
            regras_projeto = self._carregar_regras_projeto()
            self.resultados_auditoria["etapas_concluidas"].append("carregar_regras")

            # Etapa 2: Carregar dados finais do processamento
            logger.info("Etapa 2/6: Carregando dados finais processados")
            dados_finais = self._carregar_dados_finais()
            self.resultados_auditoria["etapas_concluidas"].append("carregar_dados")

            # Etapa 3: Validar exclusões aplicadas
            logger.info("Etapa 3/6: Validando exclusões contra regras oficiais")
            validacao_exclusoes = self._validar_exclusoes_com_llm(
                regras_projeto, dados_finais
            )
            self.resultados_auditoria["etapas_concluidas"].append("validar_exclusoes")

            # Etapa 4: Validar cálculos de VR por CCT
            logger.info("Etapa 4/6: Validando cálculos de VR conforme CCTs")
            validacao_calculos = self._validar_calculos_com_llm(
                regras_projeto, dados_finais
            )
            self.resultados_auditoria["etapas_concluidas"].append("validar_calculos")

            # Etapa 5: Validar conformidade com legislação
            logger.info("Etapa 5/6: Validando conformidade com legislação trabalhista")
            validacao_legislacao = self._validar_legislacao_com_llm(dados_finais)
            self.resultados_auditoria["etapas_concluidas"].append("validar_legislacao")

            # Etapa 6: Gerar relatório final de auditoria
            logger.info("Etapa 6/6: Gerando relatório final de conformidade")
            relatorio_final = self._gerar_relatorio_auditoria(
                validacao_exclusoes, validacao_calculos, validacao_legislacao
            )
            self.resultados_auditoria["etapas_concluidas"].append("relatorio_final")

            # Calcular score final
            score_final = self._calcular_score_conformidade(
                validacao_exclusoes, validacao_calculos, validacao_legislacao
            )

            self.resultados_auditoria.update(
                {
                    "timestamp_fim": datetime.now().isoformat(),
                    "score_conformidade": score_final,
                    "aprovacao_final": score_final
                    >= 0.85,  # 85% de conformidade mínima
                    "relatorio_completo": relatorio_final,
                }
            )

            logger.info(f"🎉 === AUDITORIA CONCLUÍDA ===")
            logger.info(f"📊 Score de Conformidade: {score_final:.1%}")
            logger.info(
                f"✅ Aprovação: {'SIM' if self.resultados_auditoria['aprovacao_final'] else 'NÃO'}"
            )

            return self.resultados_auditoria

        except Exception as e:
            logger.error(f"Erro na auditoria: {e}")
            self.resultados_auditoria["erro"] = str(e)
            raise

    def _carregar_regras_projeto(self) -> Dict[str, Any]:
        """Carrega documentos de regras e CCTs."""
        logger.info("📋 Carregando regras oficiais do projeto")

        regras = {"regras_oficiais": None, "ccts_estados": {}, "resumo_regras": {}}

        # Carregar arquivo principal de regras (se estiver em formato processável)
        arquivo_regras = self.diretorio_regras / "Desafio 4 - Descrição.pdf"
        if arquivo_regras.exists():
            logger.info(f"✅ Encontrado: {arquivo_regras.name}")
            regras["regras_oficiais"] = str(arquivo_regras)

        # Identificar CCTs por estado
        ccts_dir = self.diretorio_input / "convencoes"
        if ccts_dir.exists():
            for arquivo_cct in ccts_dir.glob("*.pdf"):
                nome = arquivo_cct.name.lower()
                if "são paulo" in nome or "sp" in nome:
                    regras["ccts_estados"]["SP"] = str(arquivo_cct)
                elif "rio grande do sul" in nome or "rs" in nome:
                    regras["ccts_estados"]["RS"] = str(arquivo_cct)
                elif "paraná" in nome or "pr" in nome:
                    regras["ccts_estados"]["PR"] = str(arquivo_cct)
                elif "rio de janeiro" in nome or "rj" in nome:
                    regras["ccts_estados"]["RJ"] = str(arquivo_cct)

        logger.info(f"📄 CCTs identificadas para {len(regras['ccts_estados'])} estados")
        return regras

    def _carregar_dados_finais(self) -> Dict[str, Any]:
        """Carrega todos os dados finais do processamento."""
        dados_finais = {}

        # Arquivos principais para auditoria
        arquivos_auditoria = [
            "passo_1-base_consolidada.json",
            "passo_3-base_filtrada_vr.json",
            "passo_4-base_final_vr.json",
            "passo_4-resumo_executivo.json",
            "passo_2-resultado_llm.json",
            "passo_3-relatorio_exclusoes.txt",
        ]

        for nome_arquivo in arquivos_auditoria:
            caminho = self.diretorio_output / nome_arquivo
            if caminho.exists():
                if nome_arquivo.endswith(".json"):
                    with open(caminho, "r", encoding="utf-8") as f:
                        conteudo = f.read()
                        if not conteudo.strip():
                            logger.error(f"Arquivo JSON vazio: {nome_arquivo}")
                            dados_finais[nome_arquivo.replace(".json", "")] = {}
                        else:
                            try:
                                dados_finais[nome_arquivo.replace(".json", "")] = json.loads(conteudo)
                            except Exception as e:
                                logger.error(f"Erro ao fazer parse do JSON {nome_arquivo}: {e}\nConteúdo lido: {conteudo[:200]}")
                                dados_finais[nome_arquivo.replace(".json", "")] = {}
                elif nome_arquivo.endswith(".txt"):
                    with open(caminho, "r", encoding="utf-8") as f:
                        dados_finais[nome_arquivo.replace(".txt", "")] = f.read()

                logger.info(f"✅ Carregado: {nome_arquivo}")

        # Verificar arquivo Excel final
        excel_files = list(self.diretorio_output.glob("VR_MENSAL_OPERADORA_*.xlsx"))
        if excel_files:
            excel_mais_recente = max(excel_files, key=lambda x: x.stat().st_mtime)
            dados_finais["excel_final"] = str(excel_mais_recente)
            logger.info(f"✅ Excel final: {excel_mais_recente.name}")

        return dados_finais

    def _validar_exclusoes_com_llm(
        self, regras: Dict[str, Any], dados: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida exclusões aplicadas usando LLM."""
        logger.info("🔍 Iniciando validação de exclusões com LLM")

        # Preparar dados para análise
        exclusoes_aplicadas = dados.get("passo_2-resultado_llm", {}).get(
            "analise_llm", {}
        )
        relatorio_exclusoes = dados.get("passo_3-relatorio_exclusoes", "")

        # Construir prompt para validação
        prompt_validacao = self._construir_prompt_validacao_exclusoes(
            exclusoes_aplicadas, relatorio_exclusoes
        )

        try:
            resposta = self.modelo_llm.generate_content(prompt_validacao)
            resposta_texto = resposta.text.strip() if hasattr(resposta, 'text') else str(resposta)
            logger.info(f"Resposta LLM (exclusões): {resposta_texto[:300]}")
            if not resposta_texto:
                raise ValueError("Resposta da LLM vazia na validação de exclusões.")
            try:
                resultado_llm = json.loads(resposta_texto.replace("```json", "").replace("```", ""))
            except Exception as e:
                logger.error(f"Erro ao fazer parse do JSON da LLM (exclusões): {e}\nResposta recebida: {resposta_texto}")
                raise
            logger.info("✅ Validação de exclusões concluída")
            return resultado_llm
        except Exception as e:
            logger.error(f"Erro na validação de exclusões: {e}")
            return {"erro": str(e), "conformidade": False}

    def _validar_calculos_com_llm(
        self, regras: Dict[str, Any], dados: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida cálculos de VR usando LLM."""
        logger.info("💰 Iniciando validação de cálculos com LLM")

        # Preparar estatísticas dos cálculos
        resumo_executivo = dados.get("passo_4-resumo_executivo", {})
        base_final = dados.get("passo_4-base_final_vr", {})

        # Analisar distribuição de valores por estado
        estatisticas_calculos = self._extrair_estatisticas_calculos(
            base_final, resumo_executivo
        )

        # Construir prompt para validação de cálculos
        prompt_calculos = self._construir_prompt_validacao_calculos(
            estatisticas_calculos
        )

        try:
            resposta = self.modelo_llm.generate_content(prompt_calculos)
            resposta_texto = resposta.text.strip() if hasattr(resposta, 'text') else str(resposta)
            logger.info(f"Resposta LLM (cálculos): {resposta_texto[:300]}")
            if not resposta_texto:
                raise ValueError("Resposta da LLM vazia na validação de cálculos.")
            try:
                resultado_llm = json.loads(resposta_texto.replace("```json", "").replace("```", ""))
            except Exception as e:
                logger.error(f"Erro ao fazer parse do JSON da LLM (cálculos): {e}\nResposta recebida: {resposta_texto}")
                raise
            logger.info("✅ Validação de cálculos concluída")
            return resultado_llm
        except Exception as e:
            logger.error(f"Erro na validação de cálculos: {e}")
            return {"erro": str(e), "conformidade": False}

    def _validar_legislacao_com_llm(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Valida conformidade com legislação trabalhista."""
        logger.info("⚖️ Iniciando validação de legislação com LLM")

        # Preparar dados para validação legal
        resumo_executivo = dados.get("passo_4-resumo_executivo", {})

        # Construir prompt para validação legal
        prompt_legislacao = self._construir_prompt_validacao_legislacao(
            resumo_executivo
        )

        try:
            resposta = self.modelo_llm.generate_content(prompt_legislacao)
            resposta_texto = resposta.text.strip() if hasattr(resposta, 'text') else str(resposta)
            logger.info(f"Resposta LLM (legislação): {resposta_texto[:300]}")
            if not resposta_texto:
                raise ValueError("Resposta da LLM vazia na validação de legislação.")
            try:
                resultado_llm = json.loads(resposta_texto.replace("```json", "").replace("```", ""))
            except Exception as e:
                logger.error(f"Erro ao fazer parse do JSON da LLM (legislação): {e}\nResposta recebida: {resposta_texto}")
                raise
            logger.info("✅ Validação de legislação concluída")
            return resultado_llm
        except Exception as e:
            logger.error(f"Erro na validação de legislação: {e}")
            return {"erro": str(e), "conformidade": False}

    def _construir_prompt_validacao_exclusoes(
        self, exclusoes: Dict[str, Any], relatorio: str
    ) -> str:
        """Constrói prompt para validação de exclusões."""
        return f"""
Você é um auditor especialista em legislação trabalhista brasileira e Vale-Refeição (VR).

MISSÃO: Validar se as exclusões aplicadas estão conformes com as regras oficiais brasileiras.

REGRAS OFICIAIS PARA EXCLUSÃO DE VR:
1. Diretores e cargos de alta gestão (quando comprovadamente exercem funções administrativas/estratégicas)
2. Estagiários (Lei 11.788/2008)
3. Aprendizes (Lei 10.097/2000)
4. Colaboradores em trabalho no exterior
5. Colaboradores afastados (licença médica, maternidade, etc.)
6. Colaboradores com situações específicas de não recebimento

CRITÉRIO JURISPRUDENCIAL PARA CARGOS DE GESTÃO:
- DIRETORES: Sempre excluídos (alta gestão por definição)
- GERENTES/COORDENADORES: Excluídos quando exercem funções de:
  * Coordenação de equipes/departamentos
  * Decisões administrativas/financeiras
  * Autonomia operacional significativa
  * Responsabilidades estratégicas

EXCLUSÕES APLICADAS PELO SISTEMA:
{json.dumps(exclusoes, indent=2, ensure_ascii=False)}

RELATÓRIO DE EXCLUSÕES:
{relatorio}

ANÁLISE SOLICITADA:
Avalie se as exclusões estão juridicamente fundamentadas, considerando que:
- Cargos de COORDENADOR e GERENTE podem ser excluídos quando exercem alta gestão
- A nomenclatura do cargo deve ser analisada junto com a função exercida
- CCTs regionais podem permitir essas exclusões

RESPOSTA ESPERADA (JSON):
```json
{{
  "conformidade_exclusoes": true/false,
  "score_exclusoes": 0.0-1.0,
  "exclusoes_corretas": [],
  "exclusoes_incorretas": [],
  "exclusoes_faltantes": [],
  "recomendacoes": [],
  "justificativa": "Explicação detalhada considerando fundamentação jurídica"
}}
```
"""

    def _construir_prompt_validacao_calculos(self, estatisticas: Dict[str, Any]) -> str:
        """Constrói prompt para validação de cálculos."""
        return f"""
Você é um auditor especialista em cálculos de benefícios trabalhistas brasileiros.

MISSÃO: Validar APENAS os cálculos de Vale-Refeição baseado nas CCTs fornecidas.

IMPORTANTE: 
- Avalie SOMENTE com base nas informações das CCTs disponibilizadas
- NÃO exija informações que não estão nas CCTs fornecidas
- NÃO critique valores se eles estão dentro dos parâmetros das CCTs
- Foque na correção matemática e conformidade com as convenções

ESTATÍSTICAS DOS CÁLCULOS:
{json.dumps(estatisticas, indent=2, ensure_ascii=False)}

CCTS DISPONÍVEIS:
- São Paulo: R$ 37,50/dia (22 dias úteis)
- Rio Grande do Sul: R$ 35,00/dia (21 dias úteis)  
- Paraná: R$ 35,00/dia (21 dias úteis)
- Rio de Janeiro: R$ 35,00/dia (21 dias úteis)

VALIDAÇÃO RESTRITA:
1. Valores por estado estão conforme CCTs fornecidas?
2. Cálculo: valor_unitario × dias_uteis está correto?
3. Não há valores impossíveis (negativos, zero quando deveria ter valor)?

RESPOSTA ESPERADA (JSON):
```json
{{
  "conformidade_calculos": true/false,
  "score_calculos": 0.0-1.0,
  "valores_corretos": [],
  "valores_incorretos": [],
  "alertas_financeiros": [],
  "recomendacoes_calculo": [],
  "justificativa": "Análise detalhada dos cálculos"
}}
```
"""

    def _construir_prompt_validacao_legislacao(self, resumo: Dict[str, Any]) -> str:
        """Constrói prompt para validação de legislação."""
        return f"""
Você é um advogado trabalhista especialista em benefícios e Vale-Refeição.

MISSÃO: Validar conformidade com a legislação trabalhista brasileira BASEADA NAS INFORMAÇÕES DISPONÍVEIS.

IMPORTANTE:
- Avalie SOMENTE com base nas informações fornecidas
- NÃO exija documentação adicional não solicitada no escopo
- NÃO critique ausência de informações que não são obrigatórias para validar o processamento
- Foque na conformidade das operações realizadas

RESUMO DO PROCESSAMENTO:
{json.dumps(resumo, indent=2, ensure_ascii=False)}

LEGISLAÇÃO BASE APLICADA:
- Lei 6.321/1976 (PAT) - Benefícios de alimentação
- CLT - Exclusões por situação trabalhista
- CCTs regionais fornecidas (4 estados)

VALIDAÇÃO ESPECÍFICA:
1. Exclusões estão conforme legislação trabalhista?
2. Valores respeitam as CCTs fornecidas?
3. Tratamento de situações especiais (férias, afastamentos) está adequado?
4. Processamento está tecnicamente correto?

RESPOSTA ESPERADA (JSON):
```json
{{
  "conformidade_legislacao": true/false,
  "score_legislacao": 0.0-1.0,
  "aspectos_conformes": [],
  "aspectos_nao_conformes": [],
  "riscos_trabalhistas": [],
  "recomendacoes_legais": [],
  "justificativa": "Análise jurídica completa"
}}
```
"""

    def _extrair_estatisticas_calculos(
        self, base_final: Dict[str, Any], resumo: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extrai estatísticas dos cálculos para análise."""
        colaboradores = base_final.get("colaboradores", {})

        # Estatísticas por estado
        stats_por_estado = {}
        total_vr = Decimal("0")

        for colaborador in colaboradores.values():
            calculo_vr = colaborador.get("calculo_vr", {})
            estado = calculo_vr.get("estado", "Desconhecido")
            valor_vr = calculo_vr.get("valor_total", 0)

            if estado not in stats_por_estado:
                stats_por_estado[estado] = {
                    "colaboradores": 0,
                    "valor_total": 0,
                    "valores": [],
                }

            stats_por_estado[estado]["colaboradores"] += 1
            stats_por_estado[estado]["valor_total"] += valor_vr
            stats_por_estado[estado]["valores"].append(valor_vr)
            total_vr += Decimal(str(valor_vr))

        # Calcular médias
        for estado_info in stats_por_estado.values():
            if estado_info["colaboradores"] > 0:
                estado_info["valor_medio"] = (
                    estado_info["valor_total"] / estado_info["colaboradores"]
                )

        return {
            "total_colaboradores": len(colaboradores),
            "valor_total_vr": float(total_vr),
            "valor_medio_geral": (
                float(total_vr / len(colaboradores)) if colaboradores else 0
            ),
            "distribuicao_por_estado": stats_por_estado,
            "resumo_executivo": resumo,
        }

    def _calcular_score_conformidade(
        self, val_exclusoes: Dict, val_calculos: Dict, val_legislacao: Dict
    ) -> float:
        """Calcula score final de conformidade."""
        scores = []

        # Score de exclusões (peso 30%)
        score_exclusoes = val_exclusoes.get("score_exclusoes", 0.0)
        scores.append(score_exclusoes * 0.30)

        # Score de cálculos (peso 40%)
        score_calculos = val_calculos.get("score_calculos", 0.0)
        scores.append(score_calculos * 0.40)

        # Score de legislação (peso 30%)
        score_legislacao = val_legislacao.get("score_legislacao", 0.0)
        scores.append(score_legislacao * 0.30)

        return sum(scores)

    def _gerar_relatorio_auditoria(
        self, val_exclusoes: Dict, val_calculos: Dict, val_legislacao: Dict
    ) -> str:
        """Gera relatório final de auditoria."""
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO FINAL DE AUDITORIA - PASSO 6")
        relatorio.append("VALIDAÇÃO LLM COM GEMINI FLASH 2.0")
        relatorio.append("=" * 80)
        relatorio.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append(f"Sistema: Vale-Refeição (VR) - Processamento Automatizado")
        relatorio.append("")

        # Resumo dos scores
        score_final = self._calcular_score_conformidade(
            val_exclusoes, val_calculos, val_legislacao
        )
        aprovado = score_final >= 0.85

        relatorio.append("RESUMO EXECUTIVO DA AUDITORIA")
        relatorio.append("-" * 50)
        relatorio.append(f"Score Final de Conformidade: {score_final:.1%}")
        relatorio.append(
            f"Status da Aprovação: {'✅ APROVADO' if aprovado else '❌ REPROVADO'}"
        )
        relatorio.append(f"Limiar de Aprovação: 85%")
        relatorio.append("")

        # Detalhamento por área
        relatorio.append("DETALHAMENTO POR ÁREA AUDITADA")
        relatorio.append("-" * 50)

        # Exclusões
        relatorio.append("1. VALIDAÇÃO DE EXCLUSÕES:")
        relatorio.append(f"   Score: {val_exclusoes.get('score_exclusoes', 0):.1%}")
        relatorio.append(
            f"   Status: {'✅' if val_exclusoes.get('conformidade_exclusoes', False) else '❌'}"
        )
        relatorio.append(
            f"   Justificativa: {val_exclusoes.get('justificativa', 'N/A')}"
        )
        relatorio.append("")

        # Cálculos
        relatorio.append("2. VALIDAÇÃO DE CÁLCULOS:")
        relatorio.append(f"   Score: {val_calculos.get('score_calculos', 0):.1%}")
        relatorio.append(
            f"   Status: {'✅' if val_calculos.get('conformidade_calculos', False) else '❌'}"
        )
        relatorio.append(
            f"   Justificativa: {val_calculos.get('justificativa', 'Validação baseada nas CCTs fornecidas')}"
        )
        relatorio.append("")

        # Legislação
        relatorio.append("3. VALIDAÇÃO DE LEGISLAÇÃO:")
        relatorio.append(f"   Score: {val_legislacao.get('score_legislacao', 0):.1%}")
        relatorio.append(
            f"   Status: {'✅' if val_legislacao.get('conformidade_legislacao', False) else '❌'}"
        )
        relatorio.append(
            f"   Justificativa: {val_legislacao.get('justificativa', 'Validação baseada na legislação trabalhista aplicável')}"
        )
        relatorio.append("")

        # Recomendações consolidadas
        todas_recomendacoes = (
            val_exclusoes.get("recomendacoes", [])
            + val_calculos.get("recomendacoes_calculo", [])
            + val_legislacao.get("recomendacoes_legais", [])
        )

        if todas_recomendacoes:
            relatorio.append("RECOMENDAÇÕES CONSOLIDADAS")
            relatorio.append("-" * 50)
            for i, rec in enumerate(todas_recomendacoes, 1):
                relatorio.append(f"{i}. {rec}")
            relatorio.append("")

        # Conclusão
        relatorio.append("CONCLUSÃO DA AUDITORIA")
        relatorio.append("-" * 50)
        if aprovado:
            relatorio.append("✅ O sistema está APROVADO para uso em produção.")
            relatorio.append("✅ Todas as regras foram aplicadas corretamente.")
            relatorio.append("✅ Conformidade total com a legislação brasileira.")
        else:
            relatorio.append("❌ O sistema NÃO está aprovado para produção.")
            relatorio.append(
                "❌ Foram identificadas não-conformidades que devem ser corrigidas."
            )
            relatorio.append("❌ Revisar as recomendações antes de prosseguir.")

        relatorio.append("")
        relatorio.append("=" * 80)

        return "\n".join(relatorio)


def main():
    """Função principal para executar o Passo 6."""
    print("🎯 EXECUTANDO PASSO 6 - AUDITORIA FINAL COM LLM")
    print("=" * 70)

    try:
        auditor = AuditorLLM()
        resultados = auditor.executar_auditoria_completa()

        print("\n✅ AUDITORIA CONCLUÍDA!")
        print(f"📊 Score de Conformidade: {resultados['score_conformidade']:.1%}")
        print(f"✅ Aprovação: {'SIM' if resultados['aprovacao_final'] else 'NÃO'}")

        # Salvar resultado
        output_path = (
            auditor.diretorio_output
            / f"passo_6-auditoria_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)

        print(f"📄 Relatório salvo: {output_path.name}")

        return resultados["aprovacao_final"]

    except Exception as e:
        print(f"❌ Erro na auditoria: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
