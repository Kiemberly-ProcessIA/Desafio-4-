#!/usr/bin/env python3
"""
Orquestrador do Passo 4 - Validação e Cálculo de VR
Coordena a validação de dados e cálculo automatizado de benefícios.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .calculador_beneficios import CalculadorBeneficios, executar_calculo_vr
# Importar módulos do passo 4
from .validador_dados import ValidadorDados, executar_validacao

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrquestradorPasso4:
    """Orquestrador principal do Passo 4 - Validação e Cálculo."""

    def __init__(self, config_path: str = None, output_path: str = None):
        """
        Inicializa o orquestrador do Passo 4.

        Args:
            config_path: Caminho para arquivos de configuração
            output_path: Diretório de saída
        """
        # Determinar caminhos corretos baseados na estrutura do projeto
        projeto_root = Path(__file__).parent.parent.parent

        if config_path is None:
            self.config_path = str(projeto_root / "input_data" / "configuracoes")
        else:
            self.config_path = config_path

        if output_path is None:
            self.output_path = str(projeto_root / "output")
        else:
            self.output_path = output_path

        self.validador = ValidadorDados(self.config_path)
        self.calculador = CalculadorBeneficios(self.config_path)

        # Garantir que diretório de saída existe
        Path(self.output_path).mkdir(parents=True, exist_ok=True)

    def executar_passo4_completo(self, arquivo_entrada: str) -> Dict[str, Any]:
        """
        Executa o Passo 4 completo: validação e cálculo.

        Args:
            arquivo_entrada: Arquivo com dados filtrados do passo 3

        Returns:
            Dados processados com validação e cálculos
        """
        logger.info("=== INICIANDO PASSO 4: VALIDAÇÃO E CÁLCULO DE VR ===")

        try:
            # Etapa 1: Validar e corrigir dados
            logger.info("Etapa 1/2: Validação e correção de dados")
            dados_validados = self._executar_validacao(arquivo_entrada)

            # Etapa 2: Calcular benefícios de VR
            logger.info("Etapa 2/2: Cálculo automatizado de benefícios")
            dados_finais = self._executar_calculo(dados_validados)

            # Gerar relatório consolidado
            self._gerar_relatorio_consolidado(dados_finais)

            # Salvar dados finais
            arquivo_final = f"{self.output_path}/passo_4-base_final_vr.json"
            with open(arquivo_final, "w", encoding="utf-8") as f:
                json.dump(dados_finais, f, indent=2, ensure_ascii=False)

            logger.info("=== PASSO 4 CONCLUÍDO COM SUCESSO ===")
            logger.info(f"Dados finais salvos em: {arquivo_final}")

            return dados_finais

        except Exception as e:
            logger.error(f"Erro durante execução do Passo 4: {e}")
            raise

    def _executar_validacao(self, arquivo_entrada: str) -> Dict[str, Any]:
        """Executa a validação de dados."""
        logger.info("Iniciando validação de dados inconsistentes e campos faltantes")

        # Carregar dados
        with open(arquivo_entrada, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # Validar
        dados_validados = self.validador.validar_base_completa(dados)

        # Salvar dados validados
        arquivo_validado = f"{self.output_path}/passo_4-base_validada.json"
        with open(arquivo_validado, "w", encoding="utf-8") as f:
            json.dump(dados_validados, f, indent=2, ensure_ascii=False)

        # Gerar relatório de validação
        self.validador.gerar_relatorio_validacao(
            f"{self.output_path}/passo_4-relatorio_validacao.txt"
        )

        logger.info(f"Validação concluída. Dados salvos em: {arquivo_validado}")
        return dados_validados

    def _executar_calculo(self, dados_validados: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o cálculo de benefícios."""
        logger.info("Iniciando cálculo automatizado de benefícios de VR")

        # Calcular VR para todos os colaboradores
        dados_calculados = self.calculador.processar_base_completa(dados_validados)

        # Salvar dados com cálculos
        arquivo_calculado = f"{self.output_path}/passo_4-base_calculada.json"
        logger.info(f"Tentando salvar dados em: {arquivo_calculado}")
        logger.info(f"Diretório existe? {Path(self.output_path).exists()}")

        try:
            with open(arquivo_calculado, "w", encoding="utf-8") as f:
                json.dump(dados_calculados, f, indent=2, ensure_ascii=False)
            logger.info(f"Arquivo salvo com sucesso: {arquivo_calculado}")
        except Exception as e:
            logger.error(f"Erro ao salvar {arquivo_calculado}: {e}")
            raise

        # Gerar relatórios
        self.calculador.gerar_relatorio_calculo(
            f"{self.output_path}/passo_4-relatorio_calculo_vr.txt"
        )

        logger.info(f"Cálculo concluído. Dados salvos em: {arquivo_calculado}")
        return dados_calculados

    def _gerar_relatorio_consolidado(self, dados_finais: Dict[str, Any]):
        """Gera relatório consolidado do Passo 4."""
        colaboradores = dados_finais.get("colaboradores", {})
        metadata_validacao = dados_finais.get("metadata", {}).get("validacao", {})
        metadata_calculo = dados_finais.get("metadata", {}).get("calculo_vr", {})

        # Estatísticas gerais
        total_colaboradores = len(colaboradores)
        colaboradores_elegíveis = sum(
            1
            for c in colaboradores.values()
            if c.get("calculo_vr", {}).get("elegivel", False)
        )
        valor_total_vr = sum(
            c.get("calculo_vr", {}).get("valor_total", 0.0)
            for c in colaboradores.values()
        )

        # Estatísticas por estado
        estatisticas_estado = {}
        for colaborador in colaboradores.values():
            calculo_vr = colaborador.get("calculo_vr", {})
            if calculo_vr.get("elegivel", False):
                estado = calculo_vr.get("estado", "Desconhecido")
                if estado not in estatisticas_estado:
                    estatisticas_estado[estado] = {
                        "colaboradores": 0,
                        "valor_total": 0.0,
                        "dias_uteis_medio": 0,
                    }
                estatisticas_estado[estado]["colaboradores"] += 1
                estatisticas_estado[estado]["valor_total"] += calculo_vr.get(
                    "valor_total", 0.0
                )
                estatisticas_estado[estado]["dias_uteis_medio"] += calculo_vr.get(
                    "dias_uteis", 0
                )

        # Calcular médias
        for estado_data in estatisticas_estado.values():
            if estado_data["colaboradores"] > 0:
                estado_data["dias_uteis_medio"] = (
                    estado_data["dias_uteis_medio"] / estado_data["colaboradores"]
                )

        # Gerar relatório
        arquivo_relatorio = f"{self.output_path}/passo_4-relatorio_consolidado.txt"
        with open(arquivo_relatorio, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO CONSOLIDADO - PASSO 4: VALIDAÇÃO E CÁLCULO VR\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                f"Data de processamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            f.write(f"Período de referência: 15/04/2025 a 15/05/2025\n\n")

            # Resumo executivo
            f.write("RESUMO EXECUTIVO\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total de colaboradores processados: {total_colaboradores}\n")
            f.write(f"Colaboradores elegíveis ao VR: {colaboradores_elegíveis}\n")
            f.write(
                f"Taxa de elegibilidade: {(colaboradores_elegíveis/total_colaboradores*100):.1f}%\n"
            )
            f.write(f"Valor total de VR: R$ {valor_total_vr:,.2f}\n")
            f.write(
                f"Valor médio por colaborador elegível: R$ {(valor_total_vr/colaboradores_elegíveis if colaboradores_elegíveis > 0 else 0):,.2f}\n\n"
            )

            # Estatísticas de validação
            f.write("ESTATÍSTICAS DE VALIDAÇÃO\n")
            f.write("-" * 30 + "\n")
            f.write(
                f"Colaboradores com dados corrigidos: {metadata_validacao.get('colaboradores_corrigidos', 0)}\n"
            )
            f.write(
                f"Total de problemas encontrados: {len(metadata_validacao.get('relatorio', []))}\n\n"
            )

            # Estatísticas por estado
            f.write("DISTRIBUIÇÃO POR ESTADO/SINDICATO\n")
            f.write("-" * 35 + "\n")
            for estado, stats in estatisticas_estado.items():
                f.write(f"{estado}:\n")
                f.write(f"  Colaboradores: {stats['colaboradores']}\n")
                f.write(f"  Valor total: R$ {stats['valor_total']:,.2f}\n")
                f.write(f"  Dias úteis médio: {stats['dias_uteis_medio']:.1f}\n")
                f.write(
                    f"  Valor médio por colaborador: R$ {(stats['valor_total']/stats['colaboradores']):,.2f}\n\n"
                )

            # Principais correções realizadas
            f.write("PRINCIPAIS CORREÇÕES REALIZADAS\n")
            f.write("-" * 35 + "\n")
            tipos_correcao = {}
            for item in metadata_validacao.get("relatorio", []):
                tipo = item.get("tipo", "desconhecido")
                tipos_correcao[tipo] = tipos_correcao.get(tipo, 0) + 1

            for tipo, count in sorted(
                tipos_correcao.items(), key=lambda x: x[1], reverse=True
            ):
                f.write(f"  {tipo.replace('_', ' ').title()}: {count} ocorrências\n")

            # Regras aplicadas
            f.write("\nREGRAS DE NEGÓCIO APLICADAS\n")
            f.write("-" * 30 + "\n")
            f.write("1. Validação de datas inconsistentes e campos faltantes\n")
            f.write("2. Correção de dados de férias mal preenchidos\n")
            f.write("3. Aplicação de feriados estaduais e municipais\n")
            f.write("4. Cálculo de dias úteis por sindicato\n")
            f.write("5. Regra de desligamento (comunicado até dia 15)\n")
            f.write("6. Verificação de elegibilidade ao benefício\n")
            f.write("7. Cálculo proporcional para demissões\n")
            f.write("8. Desconto de férias e afastamentos\n\n")

            # Arquivos gerados
            f.write("ARQUIVOS GERADOS\n")
            f.write("-" * 18 + "\n")
            f.write(f"- passo_4-base_validada.json: Dados após validação\n")
            f.write(f"- passo_4-base_calculada.json: Dados com cálculos de VR\n")
            f.write(f"- passo_4-base_final_vr.json: Dados finais processados\n")
            f.write(f"- passo_4-relatorio_validacao.txt: Detalhes das correções\n")
            f.write(f"- passo_4-relatorio_calculo_vr.txt: Detalhes dos cálculos\n")
            f.write(f"- passo_4-relatorio_consolidado.txt: Este relatório\n")

        logger.info(f"Relatório consolidado salvo em: {arquivo_relatorio}")

    def gerar_resumo_executivo(self, dados_finais: Dict[str, Any]) -> Dict[str, Any]:
        """Gera resumo executivo para tomada de decisão."""
        colaboradores = dados_finais.get("colaboradores", {})

        resumo = {
            "periodo_referencia": "15/04/2025 a 15/05/2025",
            "data_processamento": datetime.now().isoformat(),
            "total_colaboradores": len(colaboradores),
            "colaboradores_elegíveis": 0,
            "valor_total_vr": 0.0,
            "distribuicao_estados": {},
            "situacoes_especiais": {
                "em_ferias": 0,
                "demitidos_periodo": 0,
                "afastados": 0,
            },
        }

        for colaborador in colaboradores.values():
            calculo_vr = colaborador.get("calculo_vr", {})

            if calculo_vr.get("elegivel", False):
                resumo["colaboradores_elegíveis"] += 1
                resumo["valor_total_vr"] += calculo_vr.get("valor_total", 0.0)

                estado = calculo_vr.get("estado", "Desconhecido")
                if estado not in resumo["distribuicao_estados"]:
                    resumo["distribuicao_estados"][estado] = {
                        "colaboradores": 0,
                        "valor": 0.0,
                    }
                resumo["distribuicao_estados"][estado]["colaboradores"] += 1
                resumo["distribuicao_estados"][estado]["valor"] += calculo_vr.get(
                    "valor_total", 0.0
                )

            # Contar situações especiais
            situacao = colaborador.get("situacao", "").lower()
            if "férias" in situacao:
                resumo["situacoes_especiais"]["em_ferias"] += 1
            elif colaborador.get("demissao"):
                resumo["situacoes_especiais"]["demitidos_periodo"] += 1
            elif "afastado" in situacao:
                resumo["situacoes_especiais"]["afastados"] += 1

        # Salvar resumo executivo
        arquivo_resumo = f"{self.output_path}/passo_4-resumo_executivo.json"
        with open(arquivo_resumo, "w", encoding="utf-8") as f:
            json.dump(resumo, f, indent=2, ensure_ascii=False)

        logger.info(f"Resumo executivo salvo em: {arquivo_resumo}")
        return resumo


def executar_passo4(
    arquivo_entrada: str = None, config_path: str = None, output_path: str = None
) -> Dict[str, Any]:
    """
    Executa o Passo 4 completo.

    Args:
        arquivo_entrada: Arquivo com dados do passo 3 (padrão: output/base_filtrada_vr.json)
        config_path: Caminho para configurações (padrão: input_data/configuracoes)
        output_path: Diretório de saída (padrão: output)

    Returns:
        Dados processados
    """
    # Valores padrão
    arquivo_entrada = arquivo_entrada or "output/base_filtrada_vr.json"
    config_path = config_path or "input_data/configuracoes"
    output_path = output_path or "output"

    # Verificar se arquivo de entrada existe
    if not Path(arquivo_entrada).exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {arquivo_entrada}")

    # Executar passo 4
    orquestrador = OrquestradorPasso4(config_path, output_path)
    dados_finais = orquestrador.executar_passo4_completo(arquivo_entrada)

    # Gerar resumo executivo
    resumo = orquestrador.gerar_resumo_executivo(dados_finais)

    logger.info(f"=== PASSO 4 CONCLUÍDO ===")
    logger.info(f"Total de colaboradores: {resumo['total_colaboradores']}")
    logger.info(f"Colaboradores elegíveis: {resumo['colaboradores_elegíveis']}")
    logger.info(f"Valor total de VR: R$ {resumo['valor_total_vr']:,.2f}")
    logger.info(f"Arquivos salvos em: {output_path}/")

    return dados_finais


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Passo 4: Validação e Cálculo de VR")
    parser.add_argument(
        "--entrada",
        "-e",
        help="Arquivo de entrada (JSON)",
        default="output/base_filtrada_vr.json",
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Diretório de configurações",
        default="input_data/configuracoes",
    )
    parser.add_argument("--output", "-o", help="Diretório de saída", default="output")

    args = parser.parse_args()

    try:
        dados_finais = executar_passo4(args.entrada, args.config, args.output)
        logger.info("Passo 4 executado com sucesso!")
    except Exception as e:
        logger.error(f"Erro na execução do Passo 4: {e}")
        sys.exit(1)
