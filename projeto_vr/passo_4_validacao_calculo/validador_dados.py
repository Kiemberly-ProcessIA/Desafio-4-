#!/usr/bin/env python3
"""
Validador de Dados - Passo 4
Responsável por validar e corrigir dados inconsistentes, datas quebradas e campos faltantes.
"""

import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidadorDados:
    """Classe responsável pela validação e correção de dados inconsistentes."""

    def __init__(self, config_path: str = None):
        """
        Inicializa o validador de dados.

        Args:
            config_path: Caminho para arquivos de configuração
        """
        if config_path is None:
            # Determinar o caminho correto baseado na estrutura do projeto
            projeto_root = Path(__file__).parent.parent.parent
            self.config_path = str(projeto_root / "input_data" / "configuracoes")
        else:
            self.config_path = config_path
        self.relatorio_validacao = []

        # Padrões de data válidos
        self.patterns_data = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{2}/\d{2}/\d{4}",  # DD/MM/YYYY
            r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
            r"\d{1,2}/\d{1,2}/\d{4}",  # D/M/YYYY ou DD/M/YYYY
        ]

        # Campos obrigatórios
        self.campos_obrigatorios = [
            "matricula",
            "empresa",
            "cargo",
            "situacao",
            "sindicato",
            "status",
        ]

    def validar_base_completa(self, dados_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e corrige toda a base de dados.

        Args:
            dados_json: Dados consolidados em formato JSON

        Returns:
            Dados validados e corrigidos
        """
        logger.info("Iniciando validação completa da base de dados")

        dados_validados = dados_json.copy()
        colaboradores = dados_validados.get("colaboradores", {})

        total_colaboradores = len(colaboradores)
        corrigidos = 0

        for matricula, colaborador in colaboradores.items():
            dados_originais = colaborador.copy()

            # Validar campos obrigatórios
            colaborador = self._validar_campos_obrigatorios(colaborador, matricula)

            # Validar e corrigir datas
            colaborador = self._validar_corrigir_datas(colaborador, matricula)

            # Validar férias
            colaborador = self._validar_ferias(colaborador, matricula)

            # Validar sindicato
            colaborador = self._validar_sindicato(colaborador, matricula)

            # Verificar se houve alterações
            if colaborador != dados_originais:
                corrigidos += 1

            colaboradores[matricula] = colaborador

        # Atualizar metadados
        dados_validados["metadata"]["validacao"] = {
            "data_validacao": datetime.now().isoformat(),
            "total_colaboradores": total_colaboradores,
            "colaboradores_corrigidos": corrigidos,
            "relatorio": self.relatorio_validacao,
        }

        logger.info(
            f"Validação concluída. {corrigidos}/{total_colaboradores} colaboradores corrigidos"
        )
        return dados_validados

    def _validar_campos_obrigatorios(
        self, colaborador: Dict[str, Any], matricula: str
    ) -> Dict[str, Any]:
        """Valida se todos os campos obrigatórios estão preenchidos."""
        campos_faltantes = []

        for campo in self.campos_obrigatorios:
            valor = colaborador.get(campo)
            if valor is None or valor == "" or str(valor).strip() == "":
                campos_faltantes.append(campo)

                # Tentar inferir valores padrão
                if campo == "status" and colaborador.get("situacao"):
                    if colaborador["situacao"].lower() in ["desligado", "demitido"]:
                        colaborador["status"] = "inativo"
                    else:
                        colaborador["status"] = "ativo"
                elif campo == "empresa":
                    colaborador["empresa"] = "1410"  # Valor padrão baseado nos dados

        if campos_faltantes:
            self.relatorio_validacao.append(
                {
                    "tipo": "campos_faltantes",
                    "matricula": matricula,
                    "campos": campos_faltantes,
                    "acao": "preenchimento_automatico",
                }
            )

        return colaborador

    def _validar_corrigir_datas(
        self, colaborador: Dict[str, Any], matricula: str
    ) -> Dict[str, Any]:
        """Valida e corrige datas inconsistentes ou quebradas."""
        campos_data = ["admissao", "demissao"]

        for campo in campos_data:
            valor_original = colaborador.get(campo)
            if valor_original:
                data_corrigida = self._corrigir_data(valor_original)
                if data_corrigida != valor_original:
                    colaborador[campo] = data_corrigida
                    self.relatorio_validacao.append(
                        {
                            "tipo": "data_corrigida",
                            "matricula": matricula,
                            "campo": campo,
                            "valor_original": valor_original,
                            "valor_corrigido": data_corrigida,
                            "acao": "normalizacao_data",
                        }
                    )

        # Validar coerência entre datas
        self._validar_coerencia_datas(colaborador, matricula)

        return colaborador

    def _corrigir_data(self, valor_data: Any) -> Optional[str]:
        """Corrige formato de data quebrado ou inconsistente."""
        if valor_data is None:
            return None

        valor_str = str(valor_data).strip()
        if not valor_str or valor_str.lower() in ["nan", "none", "null", ""]:
            return None

        # Tentar parsear com diferentes formatos
        formatos_data = [
            "%Y-%m-%d",  # 2024-01-15
            "%d/%m/%Y",  # 15/01/2024
            "%d-%m-%Y",  # 15-01-2024
            "%Y/%m/%d",  # 2024/01/15
            "%d/%m/%y",  # 15/01/24
            "%d-%m-%y",  # 15-01-24
        ]

        for formato in formatos_data:
            try:
                data_obj = datetime.strptime(valor_str, formato)
                return data_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Tentar extrair números e reconstruir data
        numeros = re.findall(r"\d+", valor_str)
        if len(numeros) >= 3:
            try:
                # Assumir DD/MM/YYYY se dia <= 31
                if len(numeros[0]) <= 2 and int(numeros[0]) <= 31:
                    dia, mes, ano = numeros[0], numeros[1], numeros[2]
                else:
                    # Assumir YYYY/MM/DD
                    ano, mes, dia = numeros[0], numeros[1], numeros[2]

                # Ajustar ano se necessário
                if len(ano) == 2:
                    ano = "20" + ano if int(ano) < 50 else "19" + ano

                data_obj = datetime(int(ano), int(mes), int(dia))
                return data_obj.strftime("%Y-%m-%d")
            except ValueError:
                pass

        logger.warning(f"Não foi possível corrigir a data: {valor_data}")
        return valor_str

    def _validar_coerencia_datas(self, colaborador: Dict[str, Any], matricula: str):
        """Valida coerência entre datas de admissão e demissão."""
        admissao = colaborador.get("admissao")
        demissao = colaborador.get("demissao")

        if admissao and demissao:
            try:
                data_admissao = datetime.strptime(admissao, "%Y-%m-%d")
                data_demissao = datetime.strptime(demissao, "%Y-%m-%d")

                if data_demissao <= data_admissao:
                    self.relatorio_validacao.append(
                        {
                            "tipo": "data_incoerente",
                            "matricula": matricula,
                            "problema": "Data de demissão anterior ou igual à admissão",
                            "admissao": admissao,
                            "demissao": demissao,
                            "acao": "revisao_manual_necessaria",
                        }
                    )
            except ValueError:
                pass

    def _validar_ferias(
        self, colaborador: Dict[str, Any], matricula: str
    ) -> Dict[str, Any]:
        """Valida e corrige dados de férias mal preenchidos."""
        ferias = colaborador.get("ferias")
        situacao = colaborador.get("situacao", "").lower()

        if situacao == "férias" and not ferias:
            # Colaborador em férias sem dados de férias
            colaborador["ferias"] = {
                "situacao": "Férias",
                "dias_ferias": 30,  # Valor padrão
            }
            self.relatorio_validacao.append(
                {
                    "tipo": "ferias_corrigidas",
                    "matricula": matricula,
                    "problema": 'Situação "Férias" sem dados de férias',
                    "acao": "adicionados_dados_padrao",
                }
            )

        elif ferias and situacao != "férias":
            # Colaborador com dados de férias mas não em férias
            if isinstance(ferias, dict):
                dias_ferias = ferias.get("dias_ferias", 0)
                if dias_ferias > 0:
                    self.relatorio_validacao.append(
                        {
                            "tipo": "ferias_inconsistente",
                            "matricula": matricula,
                            "problema": 'Dados de férias presentes mas situação não é "Férias"',
                            "situacao_atual": colaborador.get("situacao"),
                            "acao": "revisao_manual_recomendada",
                        }
                    )

        # Validar dias de férias
        if ferias and isinstance(ferias, dict):
            dias_ferias = ferias.get("dias_ferias")
            if dias_ferias is not None:
                try:
                    dias_ferias_int = int(dias_ferias)
                    if dias_ferias_int < 0 or dias_ferias_int > 30:
                        colaborador["ferias"]["dias_ferias"] = min(
                            max(dias_ferias_int, 0), 30
                        )
                        self.relatorio_validacao.append(
                            {
                                "tipo": "dias_ferias_corrigido",
                                "matricula": matricula,
                                "valor_original": dias_ferias,
                                "valor_corrigido": colaborador["ferias"]["dias_ferias"],
                                "acao": "limitado_entre_0_e_30",
                            }
                        )
                except (ValueError, TypeError):
                    colaborador["ferias"]["dias_ferias"] = 0

        return colaborador

    def _validar_sindicato(
        self, colaborador: Dict[str, Any], matricula: str
    ) -> Dict[str, Any]:
        """Valida e normaliza dados do sindicato."""
        sindicato = colaborador.get("sindicato", "").strip()

        # Mapeamento de sindicatos conhecidos
        mapeamento_sindicatos = {
            "SINDPD SP": "SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.",
            "SINDPPD RS": "SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL",
            "SINDPD RJ": "SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS EST RIO DE JANEIRO",
            "SITEPD PR": "SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS EST PR",
        }

        # Tentar identificar sindicato por palavras-chave
        if sindicato:
            for sigla, nome_completo in mapeamento_sindicatos.items():
                if (
                    sigla.lower() in sindicato.lower()
                    or nome_completo.lower() in sindicato.lower()
                ):
                    if colaborador["sindicato"] != nome_completo:
                        colaborador["sindicato"] = nome_completo
                        self.relatorio_validacao.append(
                            {
                                "tipo": "sindicato_normalizado",
                                "matricula": matricula,
                                "valor_original": sindicato,
                                "valor_normalizado": nome_completo,
                                "acao": "normalizacao_sindicato",
                            }
                        )
                    break

        return colaborador

    def gerar_relatorio_validacao(self, arquivo_saida: str = "relatorio_validacao.txt"):
        """Gera relatório detalhado da validação."""
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            f.write("RELATÓRIO DE VALIDAÇÃO DE DADOS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(
                f"Total de problemas encontrados: {len(self.relatorio_validacao)}\n\n"
            )

            # Agrupar por tipo
            tipos = {}
            for item in self.relatorio_validacao:
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
                            f.write(f"    {chave}: {valor}\n")
                    f.write("\n")

        logger.info(f"Relatório de validação salvo em: {arquivo_saida}")


def executar_validacao(
    arquivo_entrada: str, arquivo_saida: str = None
) -> Dict[str, Any]:
    """
    Executa o processo completo de validação de dados.

    Args:
        arquivo_entrada: Arquivo JSON com dados consolidados
        arquivo_saida: Arquivo de saída (opcional)

    Returns:
        Dados validados
    """
    logger.info(f"Iniciando validação do arquivo: {arquivo_entrada}")

    # Carregar dados
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Validar
    validador = ValidadorDados()
    dados_validados = validador.validar_base_completa(dados)

    # Salvar dados validados
    if arquivo_saida:
        with open(arquivo_saida, "w", encoding="utf-8") as f:
            json.dump(dados_validados, f, indent=2, ensure_ascii=False)
        logger.info(f"Dados validados salvos em: {arquivo_saida}")

    # Gerar relatório
    validador.gerar_relatorio_validacao("output/relatorio_validacao.txt")

    return dados_validados


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python validador_dados.py <arquivo_entrada> [arquivo_saida]")
        sys.exit(1)

    arquivo_entrada = sys.argv[1]
    arquivo_saida = sys.argv[2] if len(sys.argv) > 2 else None

    dados_validados = executar_validacao(arquivo_entrada, arquivo_saida)
    print(
        f"Validação concluída. {len(dados_validados.get('colaboradores', {}))} colaboradores processados."
    )
