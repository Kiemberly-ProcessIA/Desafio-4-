#!/usr/bin/env python3
"""
Calculador de Benefícios VR - Passo 4
Responsável pelo cálculo automatizado do benefício de Vale Refeição.
"""

import calendar
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculadorBeneficios:
    """Classe responsável pelo cálculo automatizado de benefícios de VR."""

    def __init__(self, config_path: str = None):
        """
        Inicializa o calculador de benefícios.

        Args:
            config_path: Caminho para arquivos de configuração
        """
        if config_path is None:
            # Determinar o caminho correto baseado na estrutura do projeto
            projeto_root = Path(__file__).parent.parent.parent
            self.config_path = str(projeto_root / "input_data" / "configuracoes")
        else:
            self.config_path = config_path
        self.dados_sindicatos = self._carregar_dados_sindicatos()
        self.valores_vr = self._carregar_valores_vr()
        self.relatorio_calculo = []

        # Período de referência (15/04 a 15/05)
        self.data_inicio = date(2025, 4, 15)
        self.data_fim = date(2025, 5, 15)

    def _carregar_dados_sindicatos(self) -> Dict[str, int]:
        """Carrega dados de dias úteis por sindicato usando LLM quando possível."""
        try:
            import pandas as pd

            arquivo = f"{self.config_path}/Base dias uteis.xlsx"
            df = pd.read_excel(arquivo)

            dados = {}
            for _, row in df.iterrows():
                sindicato = str(row["sindicato"]).strip()
                dias_uteis = int(row["dias uteis"])
                dados[sindicato] = dias_uteis

            logger.info(
                f"Dados de sindicatos carregados do arquivo: {len(dados)} sindicatos"
            )
            return dados

        except Exception as e:
            logger.warning(f"Erro ao carregar dados de sindicatos do arquivo: {e}")
            logger.info("Usando consultor LLM para obter dias úteis por estado")

            # Usar LLM para obter informações dinâmicas
            from .gerenciador_feriados import (gerenciador_feriados,
                                               obter_dias_uteis_estado)

            dados_llm = {}

            # Mapear sindicatos conhecidos para estados
            mapeamento_sindicatos = {
                "SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS EST PR": "Paraná",
                "SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL": "Rio Grande do Sul",
                "SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.": "São Paulo",
                "SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS EST RIO DE JANEIRO": "Rio de Janeiro",
            }

            for sindicato, estado in mapeamento_sindicatos.items():
                try:
                    dias_uteis_llm = obter_dias_uteis_estado(estado)
                    dados_llm[sindicato] = dias_uteis_llm
                    logger.info(f"LLM: {estado} = {dias_uteis_llm} dias úteis")
                except Exception as e_llm:
                    logger.error(f"Erro ao consultar LLM para {estado}: {e_llm}")
                    # Fallback para valores conhecidos
                    valores_fallback = {
                        "Paraná": 22,
                        "Rio Grande do Sul": 21,
                        "São Paulo": 22,
                        "Rio de Janeiro": 21,
                    }
                    dados_llm[sindicato] = valores_fallback.get(estado, 22)

            return (
                dados_llm
                if dados_llm
                else {
                    "SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS EST PR": 22,
                    "SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL": 21,
                    "SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.": 22,
                    "SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS EST RIO DE JANEIRO": 21,
                }
            )

    def _carregar_valores_vr(self) -> Dict[str, float]:
        """Carrega valores de VR por estado/sindicato usando LLM quando possível."""
        try:
            import pandas as pd

            arquivo = f"{self.config_path}/Base sindicato x valor.xlsx"
            df = pd.read_excel(arquivo)

            dados = {}
            for _, row in df.iterrows():
                estado = str(row["estado"]).strip()
                valor = float(row["valor"])
                if estado and not pd.isna(valor):
                    dados[estado] = valor

            logger.info(f"Valores de VR carregados do arquivo: {len(dados)} estados")
            return dados

        except Exception as e:
            logger.warning(f"Erro ao carregar valores de VR do arquivo: {e}")
            logger.info("Usando consultor LLM para obter valores de VR")

            # Usar LLM para obter valores dinâmicos
            from .gerenciador_feriados import obter_valor_vr_estado

            estados = ["Paraná", "Rio de Janeiro", "Rio Grande do Sul", "São Paulo"]
            dados_llm = {}

            for estado in estados:
                try:
                    valor_llm = obter_valor_vr_estado(estado)
                    dados_llm[estado] = valor_llm
                    logger.info(f"LLM: {estado} = R$ {valor_llm:.2f}")
                except Exception as e_llm:
                    logger.error(
                        f"Erro ao consultar valor VR via LLM para {estado}: {e_llm}"
                    )
                    # Fallback para valores conhecidos
                    valores_fallback = {
                        "Paraná": 35.0,
                        "Rio de Janeiro": 35.0,
                        "Rio Grande do Sul": 35.0,
                        "São Paulo": 37.5,
                    }
                    dados_llm[estado] = valores_fallback.get(estado, 35.0)

            return (
                dados_llm
                if dados_llm
                else {
                    "Paraná": 35.0,
                    "Rio de Janeiro": 35.0,
                    "Rio Grande do Sul": 35.0,
                    "São Paulo": 37.5,
                }
            )

    def _identificar_estado_sindicato(self, sindicato: str) -> str:
        """Identifica o estado baseado no sindicato."""
        if not sindicato or sindicato.strip() == "":
            # Para colaboradores sem sindicato, usar distribuição proporcional baseada na empresa
            return self._inferir_estado_por_empresa()

        sindicato_lower = sindicato.lower()

        # Mapeamentos mais específicos e abrangentes
        if any(
            x in sindicato_lower for x in ["sp", "são paulo", "sindpd", "sindpd-sp"]
        ):
            return "São Paulo"
        elif any(
            x in sindicato_lower
            for x in ["rs", "rio grande do sul", "gaúcho", "gaucho", "sindppd"]
        ):
            return "Rio Grande do Sul"
        elif any(x in sindicato_lower for x in ["rj", "rio de janeiro", "carioca"]):
            return "Rio de Janeiro"
        elif any(
            x in sindicato_lower
            for x in ["pr", "paraná", "parana", "curitiba", "sitepd"]
        ):
            return "Paraná"
        else:
            # Para casos não identificados, usar distribuição inteligente
            return self._inferir_estado_por_empresa()

    def _inferir_estado_por_empresa(self) -> str:
        """
        Infere o estado baseado na distribuição proporcional dos sindicatos conhecidos.
        Estratégia: distribuir colaboradores sem sindicato proporcionalmente.
        """
        # Distribuição baseada nos dados atuais da empresa 1410:
        # RS: 63.9%, SP: 23.0%, PR: 7.5%, RJ: 5.6%

        import random

        # Usar matrícula como seed para consistência
        # (se não tiver matrícula disponível, usar valor determinístico)
        random.seed(hash(str(getattr(self, "_current_matricula", "1410"))) % 1000)

        rand = random.random()

        if rand < 0.639:  # 63.9%
            return "Rio Grande do Sul"
        elif rand < 0.639 + 0.230:  # 23.0%
            return "São Paulo"
        elif rand < 0.639 + 0.230 + 0.075:  # 7.5%
            return "Paraná"
        else:  # 5.6%
            return "Rio de Janeiro"

    def calcular_dias_uteis_colaborador(self, colaborador: Dict[str, Any]) -> int:
        """
        Calcula quantidade de dias úteis para o colaborador.
        Considera sindicato, férias, afastamentos e data de desligamento.
        """
        matricula = colaborador.get("matricula", "N/A")
        sindicato = colaborador.get("sindicato", "")

        # Obter dias úteis base do sindicato
        dias_uteis_base = self.dados_sindicatos.get(sindicato, 22)  # Padrão: 22 dias

        # Verificar situação do colaborador
        situacao = colaborador.get("situacao", "").lower()
        status = colaborador.get("status", "").lower()

        # Colaborador inativo não recebe VR
        if status == "inativo":
            self.relatorio_calculo.append(
                {
                    "matricula": matricula,
                    "tipo": "colaborador_inativo",
                    "dias_uteis": 0,
                    "valor_vr": 0.0,
                    "motivo": "Colaborador com status inativo",
                }
            )
            return 0

        dias_desconto = 0
        motivos_desconto = []

        # Descontar férias
        if situacao == "férias" or colaborador.get("ferias"):
            ferias = colaborador.get("ferias", {})
            if isinstance(ferias, dict):
                dias_ferias = ferias.get("dias_ferias", 0)
                try:
                    dias_ferias = int(dias_ferias)
                    dias_desconto += dias_ferias
                    motivos_desconto.append(f"Férias: {dias_ferias} dias")
                except (ValueError, TypeError):
                    pass

        # Verificar afastamentos
        if situacao in ["afastado", "afastamento", "licença"]:
            # Assumir afastamento completo se não tiver dados específicos
            dias_desconto += dias_uteis_base
            motivos_desconto.append("Afastamento completo")

        # Verificar data de desligamento
        demissao = colaborador.get("demissao")
        if demissao:
            dias_proporcional = self._calcular_dias_proporcional_demissao(demissao)
            if dias_proporcional < dias_uteis_base:
                dias_uteis_base = dias_proporcional
                motivos_desconto.append(
                    f"Demissão proporcional: {dias_proporcional} dias"
                )

        # Calcular dias finais
        dias_uteis_final = max(0, dias_uteis_base - dias_desconto)

        # Registrar no relatório
        if dias_desconto > 0:
            self.relatorio_calculo.append(
                {
                    "matricula": matricula,
                    "tipo": "calculo_dias_uteis",
                    "dias_base": dias_uteis_base,
                    "dias_desconto": dias_desconto,
                    "dias_final": dias_uteis_final,
                    "motivos_desconto": motivos_desconto,
                }
            )

        return dias_uteis_final

    def _calcular_dias_proporcional_demissao(self, data_demissao: str) -> int:
        """
        Calcula dias proporcionais baseado na regra de desligamento:
        - Comunicado até dia 15: não considera para pagamento
        - Comunicado após dia 15: proporcional
        """
        try:
            data_demissao_obj = datetime.strptime(data_demissao, "%Y-%m-%d").date()

            # Verificar se demissão está no período de referência
            if data_demissao_obj < self.data_inicio:
                return 0  # Demitido antes do período
            elif data_demissao_obj > self.data_fim:
                return self._get_dias_uteis_periodo()  # Demissão após período

            # Demissão dentro do período - calcular proporcional
            if data_demissao_obj.day <= 15:
                # Comunicado até dia 15 - verificar se é do mês de referência
                if data_demissao_obj.month == 4 and data_demissao_obj.year == 2025:
                    return 0  # Não considera para pagamento
                elif data_demissao_obj.month == 5 and data_demissao_obj.year == 2025:
                    # Trabalhou todo abril, proporcional até dia 15 de maio
                    return self._calcular_dias_trabalhados(
                        self.data_inicio, data_demissao_obj
                    )

            # Demissão após dia 15 - proporcional
            return self._calcular_dias_trabalhados(self.data_inicio, data_demissao_obj)

        except (ValueError, TypeError):
            # Se não conseguir parsear a data, assume período completo
            return self._get_dias_uteis_periodo()

    def _calcular_dias_trabalhados(self, data_inicio: date, data_fim: date) -> int:
        """Calcula dias úteis trabalhados entre duas datas."""
        if data_fim <= data_inicio:
            return 0

        dias_uteis = 0
        data_atual = data_inicio

        while data_atual <= data_fim:
            # Contar apenas dias úteis (segunda a sexta)
            if data_atual.weekday() < 5:  # 0-4 = segunda a sexta
                dias_uteis += 1
            data_atual += timedelta(days=1)

        return dias_uteis

    def _get_dias_uteis_periodo(self) -> int:
        """Retorna dias úteis do período de referência (média dos sindicatos)."""
        if self.dados_sindicatos:
            return int(sum(self.dados_sindicatos.values()) / len(self.dados_sindicatos))
        return 22  # Padrão

    def calcular_valor_vr(self, colaborador: Dict[str, Any], dias_uteis: int) -> float:
        """
        Calcula o valor total de VR para o colaborador.

        Args:
            colaborador: Dados do colaborador
            dias_uteis: Número de dias úteis calculados

        Returns:
            Valor total de VR
        """
        if dias_uteis <= 0:
            return 0.0

        sindicato = colaborador.get("sindicato", "")
        estado = self._identificar_estado_sindicato(sindicato)

        # Obter valor unitário do VR
        valor_unitario = self.valores_vr.get(estado, 35.0)  # Padrão: R$ 35,00

        # Calcular valor total
        valor_total = dias_uteis * valor_unitario

        matricula = colaborador.get("matricula", "N/A")
        self.relatorio_calculo.append(
            {
                "matricula": matricula,
                "tipo": "calculo_vr",
                "estado": estado,
                "valor_unitario": valor_unitario,
                "dias_uteis": dias_uteis,
                "valor_total": valor_total,
            }
        )

        return valor_total

    def processar_base_completa(self, dados_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa toda a base calculando VR para todos os colaboradores.

        Args:
            dados_json: Dados consolidados

        Returns:
            Dados com cálculos de VR
        """
        logger.info("Iniciando cálculo de VR para toda a base")

        dados_calculados = dados_json.copy()
        colaboradores = dados_calculados.get("colaboradores", {})

        total_colaboradores = len(colaboradores)
        total_valor_vr = 0.0
        colaboradores_elegíveis = 0

        for matricula, colaborador in colaboradores.items():
            # Definir matrícula atual para inferência de estado
            self._current_matricula = matricula

            # Calcular dias úteis
            dias_uteis = self.calcular_dias_uteis_colaborador(colaborador)

            # Calcular valor VR
            valor_vr = self.calcular_valor_vr(colaborador, dias_uteis)

            # Identificar estado (considerando a matrícula atual)
            estado = self._identificar_estado_sindicato(
                colaborador.get("sindicato", "")
            )

            # Adicionar informações de cálculo ao colaborador
            colaborador["calculo_vr"] = {
                "dias_uteis": dias_uteis,
                "valor_unitario": self._get_valor_unitario(colaborador),
                "valor_total": valor_vr,
                "estado": estado,
                "elegivel": valor_vr > 0,
            }

            if valor_vr > 0:
                colaboradores_elegíveis += 1
                total_valor_vr += valor_vr

        # Atualizar metadados
        dados_calculados["metadata"]["calculo_vr"] = {
            "data_calculo": datetime.now().isoformat(),
            "periodo_referencia": f"{self.data_inicio} a {self.data_fim}",
            "total_colaboradores": total_colaboradores,
            "colaboradores_elegíveis": colaboradores_elegíveis,
            "valor_total_vr": total_valor_vr,
            "relatorio_calculo": len(self.relatorio_calculo),
        }

        logger.info(
            f"Cálculo concluído. {colaboradores_elegíveis}/{total_colaboradores} colaboradores elegíveis"
        )
        logger.info(f"Valor total de VR: R$ {total_valor_vr:,.2f}")

        return dados_calculados

    def _get_valor_unitario(self, colaborador: Dict[str, Any]) -> float:
        """Obtém o valor unitário de VR para o colaborador."""
        sindicato = colaborador.get("sindicato", "")
        estado = self._identificar_estado_sindicato(sindicato)
        return self.valores_vr.get(estado, 35.0)

    def gerar_relatorio_calculo(self, arquivo_saida: str = "relatorio_calculo_vr.txt"):
        """Gera relatório detalhado dos cálculos."""
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE CÁLCULO DE VALE REFEIÇÃO\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Período: {self.data_inicio} a {self.data_fim}\n")
            f.write(f"Total de cálculos realizados: {len(self.relatorio_calculo)}\n\n")

            # Agrupar por tipo
            tipos = {}
            for item in self.relatorio_calculo:
                tipo = item["tipo"]
                if tipo not in tipos:
                    tipos[tipo] = []
                tipos[tipo].append(item)

            for tipo, itens in tipos.items():
                f.write(
                    f"\n{tipo.upper().replace('_', ' ')} ({len(itens)} ocorrências):\n"
                )
                f.write("-" * 40 + "\n")

                for item in itens:
                    f.write(f"  Matrícula: {item['matricula']}\n")
                    for chave, valor in item.items():
                        if chave not in ["tipo", "matricula"]:
                            if isinstance(valor, float):
                                f.write(f"    {chave}: R$ {valor:.2f}\n")
                            else:
                                f.write(f"    {chave}: {valor}\n")
                    f.write("\n")

        logger.info(f"Relatório de cálculo salvo em: {arquivo_saida}")

    def gerar_planilha_pagamento(
        self,
        dados_json: Dict[str, Any],
        arquivo_saida: str = "planilha_pagamento_vr.json",
    ):
        """Gera planilha final de pagamento."""
        colaboradores = dados_json.get("colaboradores", {})
        planilha_pagamento = []

        for matricula, colaborador in colaboradores.items():
            calculo_vr = colaborador.get("calculo_vr", {})

            if calculo_vr.get("elegivel", False):
                planilha_pagamento.append(
                    {
                        "matricula": matricula,
                        "nome": colaborador.get("nome", "N/A"),
                        "cargo": colaborador.get("cargo", "N/A"),
                        "empresa": colaborador.get("empresa", "N/A"),
                        "sindicato": colaborador.get("sindicato", "N/A"),
                        "estado": calculo_vr.get("estado", "N/A"),
                        "situacao": colaborador.get("situacao", "N/A"),
                        "dias_uteis": calculo_vr.get("dias_uteis", 0),
                        "valor_unitario": calculo_vr.get("valor_unitario", 0.0),
                        "valor_total": calculo_vr.get("valor_total", 0.0),
                    }
                )

        # Ordenar por valor total (decrescente)
        planilha_pagamento.sort(key=lambda x: x["valor_total"], reverse=True)

        # Salvar planilha
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "metadata": {
                        "data_geracao": datetime.now().isoformat(),
                        "periodo": f"{self.data_inicio} a {self.data_fim}",
                        "total_colaboradores": len(planilha_pagamento),
                        "valor_total": sum(
                            item["valor_total"] for item in planilha_pagamento
                        ),
                    },
                    "pagamentos": planilha_pagamento,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(f"Planilha de pagamento salva em: {arquivo_saida}")
        return planilha_pagamento


def executar_calculo_vr(
    arquivo_entrada: str, arquivo_saida: str = None
) -> Dict[str, Any]:
    """
    Executa o processo completo de cálculo de VR.

    Args:
        arquivo_entrada: Arquivo JSON com dados validados
        arquivo_saida: Arquivo de saída (opcional)

    Returns:
        Dados com cálculos de VR
    """
    logger.info(f"Iniciando cálculo de VR do arquivo: {arquivo_entrada}")

    # Carregar dados
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Calcular VR
    calculador = CalculadorBeneficios()
    dados_calculados = calculador.processar_base_completa(dados)

    # Salvar dados calculados
    if arquivo_saida:
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            json.dump(dados_calculados, f, indent=2, ensure_ascii=False)
        logger.info(f"Dados com cálculos salvos em: {arquivo_saida}")

    # Gerar relatórios
    calculador.gerar_relatorio_calculo("output/relatorio_calculo_vr.txt")
    calculador.gerar_planilha_pagamento(
        dados_calculados, "output/planilha_pagamento_vr.json"
    )

    return dados_calculados


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python calculador_beneficios.py <arquivo_entrada> [arquivo_saida]")
        sys.exit(1)

    arquivo_entrada = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else None

    dados_calculados = executar_calculo_vr(arquivo_entrada, arquivo_saida)
    print(
        f"Cálculo concluído. {len(dados_calculados.get('colaboradores', {}))} colaboradores processados."
    )
