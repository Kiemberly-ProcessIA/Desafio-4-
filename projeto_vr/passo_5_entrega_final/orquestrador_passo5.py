#!/usr/bin/env python3
"""
Orquestrador Passo 5 - Entrega Final
Coordena todo o processo de entrega final: validação operadora + geração planilha final.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Adicionar diretórios ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from passo_5_entrega_final.analisador_modelo_vr import AnalisadorModeloVR
from passo_5_entrega_final.gerador_planilha_final import GeradorPlanilhaFinal
from passo_5_entrega_final.validador_operadora import ValidadorOperadora

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrquestradorPasso5:
    """Coordena todo o processo do Passo 5 - Entrega Final."""

    def __init__(self):
        self.diretorio_output = self._encontrar_diretorio_output()
        self.analisador = AnalisadorModeloVR()
        self.validador = ValidadorOperadora()
        self.gerador = GeradorPlanilhaFinal()

        self.resultados = {
            "inicio_processamento": datetime.now().isoformat(),
            "etapas_concluidas": [],
            "arquivos_gerados": [],
            "estatisticas": {},
            "status": "iniciado",
        }

    def _encontrar_diretorio_output(self) -> Path:
        """Encontra o diretório output."""
        current_dir = Path(__file__).parent
        while current_dir.name != "desafio_4" and current_dir.parent != current_dir:
            current_dir = current_dir.parent

        output_dir = current_dir / "output"
        if not output_dir.exists():
            raise FileNotFoundError(f"Diretório output não encontrado: {output_dir}")

        return output_dir

    def executar_passo5(self, arquivo_entrada: Optional[str] = None) -> Dict[str, Any]:
        """Executa o Passo 5 completo."""
        logger.info("=== INICIANDO PASSO 5: ENTREGA FINAL ===")

        try:
            # Etapa 1: Carregar dados do Passo 4
            logger.info("Etapa 1/4: Carregando dados do Passo 4")
            dados_passo4 = self._carregar_dados_passo4(arquivo_entrada)
            self.resultados["etapas_concluidas"].append("carregar_dados")

            # Etapa 2: Analisar modelo da operadora
            logger.info("Etapa 2/4: Analisando modelo da operadora")
            self._analisar_modelo_operadora()
            self.resultados["etapas_concluidas"].append("analisar_modelo")

            # Etapa 3: Validar dados para operadora
            logger.info("Etapa 3/4: Validando dados para operadora")
            dados_validados = self._validar_para_operadora(dados_passo4)
            self.resultados["etapas_concluidas"].append("validar_operadora")

            # Etapa 4: Gerar APENAS planilha Excel final
            logger.info("Etapa 4/4: Gerando planilha Excel final")
            arquivos_gerados = self._gerar_planilhas_finais(dados_validados)
            self.resultados["etapas_concluidas"].append("gerar_planilhas")

            # Finalizar com resumo mínimo
            self._finalizar_passo5(dados_validados, arquivos_gerados)

            logger.info("=== PASSO 5 CONCLUÍDO COM SUCESSO ===")
            return self.resultados

        except Exception as e:
            logger.error(f"Erro no Passo 5: {e}")
            self.resultados["status"] = "erro"
            self.resultados["erro"] = str(e)
            raise

    def _carregar_dados_passo4(self, arquivo_entrada: Optional[str]) -> Dict[str, Any]:
        """Carrega dados processados do Passo 4."""
        if arquivo_entrada:
            arquivo_dados = Path(arquivo_entrada)
        else:
            # Procurar arquivo mais recente do Passo 4
            arquivos_candidatos = [
                "passo_4-base_final_vr.json",
                "base_calculada.json",
                "base_validada.json",
            ]

            arquivo_dados = None
            for nome_arquivo in arquivos_candidatos:
                caminho = self.diretorio_output / nome_arquivo
                if caminho.exists():
                    arquivo_dados = caminho
                    break

            if not arquivo_dados:
                raise FileNotFoundError("Nenhum arquivo de saída do Passo 4 encontrado")

        logger.info(f"Carregando dados de: {arquivo_dados}")

        with open(arquivo_dados, "r", encoding="utf-8") as f:
            dados = json.load(f)

        logger.info(
            f"Dados carregados: {len(dados.get('colaboradores', {}))} colaboradores"
        )

        # Preparar dados com campos necessários para operadora
        dados_preparados = self._preparar_dados_operadora(dados)

        self.resultados["estatisticas"]["colaboradores_entrada"] = len(
            dados.get("colaboradores", {})
        )
        return dados_preparados

    def _preparar_dados_operadora(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara dados com campos necessários para a operadora."""
        dados_preparados = {"metadata": dados.get("metadata", {}), "colaboradores": {}}

        for matricula, colaborador in dados.get("colaboradores", {}).items():
            # Garantir campos essenciais para operadora
            colaborador_preparado = dict(colaborador)

            # Extrair valor VR do campo calculo_vr se existir
            if "calculo_vr" in colaborador_preparado:
                calculo_vr = colaborador_preparado["calculo_vr"]
                if "valor_total" in calculo_vr:
                    colaborador_preparado["valor_vr_calculado"] = calculo_vr[
                        "valor_total"
                    ]

            # Garantir campo valor_vr_calculado
            if "valor_vr_calculado" not in colaborador_preparado:
                colaborador_preparado["valor_vr_calculado"] = 0

            # Adicionar datas de vigência se não existirem
            if "data_inicio_vigencia" not in colaborador_preparado:
                colaborador_preparado["data_inicio_vigencia"] = "15/04/2025"

            if "data_fim_vigencia" not in colaborador_preparado:
                colaborador_preparado["data_fim_vigencia"] = "15/05/2025"

            # Garantir campos de endereço
            if "endereco" not in colaborador_preparado:
                colaborador_preparado["endereco"] = {}

            # Normalizar situação
            if "situacao" not in colaborador_preparado:
                if colaborador_preparado.get("status") == "ativo":
                    colaborador_preparado["situacao"] = "Trabalhando"
                else:
                    colaborador_preparado["situacao"] = "Trabalhando"  # Default

            dados_preparados["colaboradores"][matricula] = colaborador_preparado

        return dados_preparados

    def _analisar_modelo_operadora(self):
        """Analisa o modelo da operadora (sem gerar arquivos permanentes)."""
        try:
            estrutura = self.analisador.analisar_estrutura_modelo()
            validacoes = self.analisador.extrair_validacoes()

            # Apenas log - não salvar arquivo
            logger.info(
                f"Modelo analisado: {len(estrutura.get('colunas', []))} colunas identificadas"
            )

        except Exception as e:
            logger.warning(f"Erro ao analisar modelo: {e}")

    def _validar_para_operadora(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados para operadora (sem gerar arquivos permanentes)."""
        logger.info("Iniciando validação para operadora")

        dados_validados = self.validador.validar_base_completa(dados)

        # Estatísticas básicas (apenas log)
        estatisticas_validacao = dados_validados.get("validacao", {}).get(
            "estatisticas", {}
        )
        logger.info(
            f"Validação concluída: {estatisticas_validacao.get('registros_validos', 0)} registros válidos"
        )

        return dados_validados

    def _gerar_planilhas_finais(
        self, dados_validados: Dict[str, Any]
    ) -> Dict[str, str]:
        """Gera APENAS planilha Excel final. Outros arquivos são temporários."""
        logger.info("Gerando planilha Excel única")

        arquivos_gerados = self.gerador.gerar_planilha_operadora(dados_validados)

        # Verificar se Excel foi gerado
        if "planilha_excel" not in arquivos_gerados:
            raise Exception("Falha crítica: Excel não foi gerado")

        excel_path = arquivos_gerados["planilha_excel"]
        logger.info(f"✅ Excel único gerado: {os.path.basename(excel_path)}")

        # Limpar outros arquivos do output (manter apenas Excel)
        self._limpar_outputs_antigos(excel_path)

        # Adicionar apenas Excel aos resultados (não arquivos temporários)
        self.resultados["arquivos_gerados"] = [excel_path]

        logger.info("✅ ÚNICO arquivo permanente gerado")

        return arquivos_gerados

    def _finalizar_passo5(
        self, dados_validados: Dict[str, Any], arquivos_gerados: Dict[str, str]
    ):
        """Finaliza o Passo 5 e gera resumo executivo completo."""
        logger.info("Finalizando Passo 5")

        # Estatísticas finais
        colaboradores = dados_validados.get("colaboradores", {})
        total_colaboradores = len(colaboradores)

        # Calcular totais de VR
        from decimal import Decimal

        total_vr = Decimal("0")

        for colaborador in colaboradores.values():
            # Buscar valor no campo correto: calculo_vr.valor_total
            calculo_vr = colaborador.get("calculo_vr", {})
            valor_vr = calculo_vr.get("valor_total", 0)

            if valor_vr:
                total_vr += Decimal(str(valor_vr))

        total_empresa = total_vr * Decimal("0.80")
        total_funcionario = total_vr * Decimal("0.20")

        # Distribuição por estado
        distribuicao_estado = {}
        for colaborador in colaboradores.values():
            sindicato = colaborador.get("sindicato", "")
            estado = "São Paulo"  # Default para São Paulo

            if "SP" in sindicato or "sindpd" in sindicato.lower():
                estado = "São Paulo"
            elif "RS" in sindicato:
                estado = "Rio Grande do Sul"
            elif "PR" in sindicato:
                estado = "Paraná"
            elif "RJ" in sindicato:
                estado = "Rio de Janeiro"

            if estado not in distribuicao_estado:
                distribuicao_estado[estado] = 0
            distribuicao_estado[estado] += 1

        # Excel gerado
        excel_path = arquivos_gerados.get("planilha_excel", "")

        # Estatísticas detalhadas
        estatisticas = {
            "colaboradores_entrada": total_colaboradores,
            "colaboradores_processados": total_colaboradores,
            "valor_total_vr": float(total_vr),
            "valor_empresa_80_pct": float(total_empresa),
            "valor_funcionario_20_pct": float(total_funcionario),
            "distribuicao_por_estado": distribuicao_estado,
            "total_arquivos_gerados": 1 if excel_path else 0,
            "aprovado_operadora": bool(excel_path),
        }

        # Atualizar resultados finais
        self.resultados.update(
            {
                "status": "concluido",
                "fim_processamento": datetime.now().isoformat(),
                "total_colaboradores": total_colaboradores,
                "valor_total_vr": float(total_vr),
                "arquivo_excel": os.path.basename(excel_path) if excel_path else "",
                "estatisticas": estatisticas,
                "arquivos_principais": {"planilha_excel": excel_path},
            }
        )

        logger.info(f"✅ PASSO 5 CONCLUÍDO!")
        logger.info(f"👥 Colaboradores processados: {total_colaboradores:,}")
        logger.info(f"💰 Valor total VR: R$ {float(total_vr):,.2f}")
        logger.info(f"📁 Arquivos gerados: 1")
        logger.info(f"")
        logger.info(f"📄 ARQUIVOS PRINCIPAIS:")
        if excel_path:
            logger.info(f"✅ Excel: {os.path.basename(excel_path)}")

    def _limpar_outputs_antigos(self, excel_atual: str):
        """Remove arquivos antigos do output, mantendo apenas o Excel atual."""
        import glob

        try:
            # Remover planilhas antigas
            for arquivo in glob.glob(
                str(self.diretorio_output / "VR_MENSAL_OPERADORA_*.xlsx")
            ):
                if arquivo != excel_atual:
                    os.remove(arquivo)
                    logger.debug(
                        f"Removido arquivo antigo: {os.path.basename(arquivo)}"
                    )

            # Remover relatórios e dados antigos do Passo 5
            padroes_remover = [
                "VR_MENSAL_DADOS_*.json",
                "RELATORIO_CONTROLE_OPERADORA_*.txt",
                "analise_modelo_operadora_*.txt",
                "validacao_operadora_*.txt",
                "dados_validados_operadora_*.json",
                "relatorio_final_passo5_*.txt",
                "resumo_executivo_passo5_*.json",
            ]

            for padrao in padroes_remover:
                for arquivo in glob.glob(str(self.diretorio_output / padrao)):
                    os.remove(arquivo)
                    logger.debug(f"Removido: {os.path.basename(arquivo)}")

            logger.info("🧹 Outputs antigos removidos - mantendo apenas Excel")

        except Exception as e:
            logger.warning(f"Erro ao limpar outputs antigos: {e}")


if __name__ == "__main__":
    print("🎯 EXECUTANDO PASSO 5 - ENTREGA FINAL")
    print("=" * 60)

    try:
        orquestrador = OrquestradorPasso5()
        resultados = orquestrador.executar_passo5()

        print("\n✅ PASSO 5 CONCLUÍDO!")
        print(f"Status: {resultados['status']}")
        print(f"Colaboradores processados: {resultados.get('total_colaboradores', 0)}")
        print(f"Valor total: R$ {resultados.get('valor_total_vr', 0):,.2f}")
        print(f"Arquivo Excel: {resultados.get('arquivo_excel', 'N/A')}")

    except Exception as e:
        print(f"❌ Erro no Passo 5: {e}")
        import traceback

        traceback.print_exc()
