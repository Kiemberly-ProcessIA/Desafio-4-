#!/usr/bin/env python3
"""
Gerador de Planilha Final - Passo 5
Gera a planilha final no formato exato da operadora para envio,
seguindo o modelo "VR MENSAL 05.2025.xlsx".
"""

import csv
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

# Importar sistema de logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import log_fim_passo, log_inicio_passo, setup_logging

logger = setup_logging()


class GeradorPlanilhaFinal:
    """Gera planilha final para envio à operadora."""

    def __init__(self):
        self.diretorio_output = self._encontrar_diretorio_output()
        self.custo_empresa_percentual = 0.80
        self.custo_funcionario_percentual = 0.20

    def _encontrar_diretorio_output(self) -> Path:
        """Encontra o diretório output."""
        current_dir = Path(__file__).parent
        while current_dir.name != "desafio_4" and current_dir.parent != current_dir:
            current_dir = current_dir.parent

        output_dir = current_dir / "output"
        output_dir.mkdir(exist_ok=True)

        return output_dir

    def gerar_planilha_operadora(
        self, dados_validados: Dict[str, Any]
    ) -> Dict[str, str]:
        """Gera APENAS a planilha Excel final. Outros arquivos são temporários."""
        logger.info("Gerando planilha Excel final para operadora")

        arquivos_gerados = {}

        # ÚNICO ARQUIVO PERMANENTE: Planilha Excel
        try:
            arquivo_excel = self._gerar_excel_operadora(dados_validados)
            arquivos_gerados["planilha_excel"] = arquivo_excel
            logger.info("✅ Excel gerado com sucesso como ÚNICO output permanente")
        except ImportError as e:
            logger.error(f"❌ Erro ao gerar Excel: {e}")
            raise Exception("Excel é obrigatório. Instale pandas e openpyxl.")
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao gerar Excel: {e}")
            raise

        # Arquivos temporários para controle (não ficam em output/)
        import os
        import tempfile

        # JSON temporário para debug
        temp_json = os.path.join(
            tempfile.gettempdir(),
            f"vr_dados_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(temp_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "colaboradores": dados_validados.get("colaboradores", {}),
                    "metadata": dados_validados.get("metadata", {}),
                    "estatisticas": {
                        "total_colaboradores": len(
                            dados_validados.get("colaboradores", {})
                        ),
                        "data_geracao": datetime.now().isoformat(),
                    },
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info(f"📄 Dados temporários salvos em: {temp_json}")

        # Relatório temporário
        temp_relatorio = os.path.join(
            tempfile.gettempdir(),
            f"vr_relatorio_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        self._gerar_relatorio_temporario(dados_validados, temp_relatorio)
        logger.info(f"📋 Relatório temporário salvo em: {temp_relatorio}")

        logger.info(f"✅ ÚNICA saída permanente: {os.path.basename(arquivo_excel)}")
        return arquivos_gerados

    def _gerar_csv_operadora(self, dados: Dict[str, Any]) -> str:
        """Gera arquivo CSV no formato da operadora."""
        nome_arquivo = (
            f"VR_MENSAL_OPERADORA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        caminho_arquivo = self.diretorio_output / nome_arquivo

        logger.info(f"Gerando CSV: {caminho_arquivo}")

        # Cabeçalhos conforme modelo da operadora (exatamente como no modelo)
        cabecalhos = [
            "matricula",  # Matricula do colaborador
            "admissao",  # Data de admissão
            "sindicato",  # Sindicato do colaborador
            "competencia",  # Mês/ano de competência
            "dias",  # Dias úteis
            "valor diario",  # Valor diário do VR
            "TOTAL",  # Valor total VR
            "custo empresa",  # 80% do valor (empresa paga)
            "deconto funcionario",  # 20% do valor (desconto funcionário)
            "OBS GERAL",  # Observações gerais
        ]

        with open(caminho_arquivo, "w", newline="", encoding="utf-8") as arquivo:
            writer = csv.writer(
                arquivo, delimiter=";"
            )  # Usar ponto e vírgula como separador
            writer.writerow(cabecalhos)

            for matricula, colaborador in dados.get("colaboradores", {}).items():
                linha = self._preparar_linha_csv(matricula, colaborador)
                writer.writerow(linha)

        logger.info(f"CSV gerado com {len(dados.get('colaboradores', {}))} registros")
        return str(caminho_arquivo)

    def _preparar_linha_csv(self, matricula: str, colaborador: Dict) -> List[str]:
        """Prepara uma linha de dados para o CSV da operadora seguindo modelo exato."""
        # Obter valor VR de diferentes possíveis locais
        valor_vr = 0

        if "valor_vr_calculado" in colaborador and colaborador["valor_vr_calculado"]:
            valor_vr = Decimal(str(colaborador["valor_vr_calculado"]))
        elif "calculo_vr" in colaborador and isinstance(
            colaborador["calculo_vr"], dict
        ):
            calculo_vr = colaborador["calculo_vr"]
            if "valor_total" in calculo_vr and calculo_vr["valor_total"]:
                valor_vr = Decimal(str(calculo_vr["valor_total"]))

        # Calcular valores empresa (80%) e funcionário (20%)
        valor_empresa = valor_vr * Decimal(str(self.custo_empresa_percentual))
        valor_funcionario = valor_vr * Decimal(str(self.custo_funcionario_percentual))

        # Obter dados do sindicato e dias úteis
        sindicato_info = colaborador.get("sindicato", {})
        sindicato_nome = ""
        dias_uteis = 22  # Valor padrão
        valor_diario = 0

        if isinstance(sindicato_info, dict):
            sindicato_nome = sindicato_info.get("nome", "")
            dias_uteis = sindicato_info.get("dias_uteis", 22)
        elif isinstance(sindicato_info, str):
            sindicato_nome = sindicato_info

        # Calcular valor diário
        if valor_vr > 0 and dias_uteis > 0:
            valor_diario = valor_vr / Decimal(str(dias_uteis))

        # Formatar datas conforme modelo (YYYY-MM-DD para Excel processar corretamente)
        def formatar_data_excel(data_valor):
            if not data_valor:
                return ""
            if isinstance(data_valor, (date, datetime)):
                return data_valor.strftime("%Y-%m-%d")
            if isinstance(data_valor, str):
                # Tentar converter diferentes formatos
                for formato in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        data_obj = datetime.strptime(data_valor, formato)
                        return data_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            return str(data_valor)

        # Competência (primeiro dia do mês de referência)
        competencia = "2025-05-01"  # Maio 2025 conforme modelo

        # Observações baseadas na situação
        observacoes = ""
        situacao = colaborador.get("situacao", "")
        if situacao and situacao.lower() != "trabalhando":
            observacoes = f"Situação: {situacao}"

        return [
            matricula,  # matricula
            formatar_data_excel(colaborador.get("admissao", "")),  # admissao
            sindicato_nome,  # sindicato
            competencia,  # competencia
            str(dias_uteis),  # dias
            f"{valor_diario:.1f}".replace(".", ","),  # valor diario
            f"{valor_vr:.0f}".replace(".", ","),  # TOTAL
            f"{valor_empresa:.0f}".replace(".", ","),  # custo empresa
            f"{valor_funcionario:.0f}".replace(".", ","),  # deconto funcionario
            observacoes,  # OBS GERAL
        ]

    def _formatar_cpf(self, cpf: str) -> str:
        """Formata CPF no padrão XXX.XXX.XXX-XX."""
        if not cpf:
            return ""

        # Remover formatação existente
        cpf_numeros = "".join(filter(str.isdigit, str(cpf)))

        if len(cpf_numeros) == 11:
            return f"{cpf_numeros[:3]}.{cpf_numeros[3:6]}.{cpf_numeros[6:9]}-{cpf_numeros[9:]}"

        return str(cpf)

    def _gerar_json_operadora(self, dados: Dict[str, Any]) -> str:
        """Gera arquivo JSON estruturado para a operadora."""
        nome_arquivo = (
            f"VR_MENSAL_DADOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        caminho_arquivo = self.diretorio_output / nome_arquivo

        logger.info(f"Gerando JSON: {caminho_arquivo}")

        # Preparar dados estruturados
        dados_operadora = {
            "cabecalho": {
                "empresa": "I2A2 TECNOLOGIA",
                "periodo_referencia": "15/04/2025 a 15/05/2025",
                "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "total_colaboradores": len(dados.get("colaboradores", {})),
                "valor_total_vr": 0,
                "valor_total_empresa": 0,
                "valor_total_funcionario": 0,
            },
            "colaboradores": [],
            "resumo": {
                "distribuicao_por_estado": {},
                "distribuicao_por_situacao": {},
                "estatisticas_valores": {},
            },
        }

        # Processar colaboradores
        total_vr = Decimal("0")
        total_empresa = Decimal("0")
        total_funcionario = Decimal("0")

        distribuicao_estado = {}
        distribuicao_situacao = {}

        for matricula, colaborador in dados.get("colaboradores", {}).items():
            # Obter valor VR de diferentes possíveis locais
            valor_vr = 0

            if (
                "valor_vr_calculado" in colaborador
                and colaborador["valor_vr_calculado"]
            ):
                valor_vr = Decimal(str(colaborador["valor_vr_calculado"]))
            elif "calculo_vr" in colaborador and isinstance(
                colaborador["calculo_vr"], dict
            ):
                calculo_vr = colaborador["calculo_vr"]
                if "valor_total" in calculo_vr and calculo_vr["valor_total"]:
                    valor_vr = Decimal(str(calculo_vr["valor_total"]))

            # Calcular valores empresa e funcionário
            valor_empresa = valor_vr * Decimal(str(self.custo_empresa_percentual))
            valor_funcionario = valor_vr * Decimal(
                str(self.custo_funcionario_percentual)
            )

            # Somar totais
            total_vr += valor_vr
            total_empresa += valor_empresa
            total_funcionario += valor_funcionario

            # Contabilizar distribuições
            estado = colaborador.get("endereco", {}).get("estado", "Não informado")
            situacao = colaborador.get("situacao", "Trabalhando")

            distribuicao_estado[estado] = distribuicao_estado.get(estado, 0) + 1
            distribuicao_situacao[situacao] = distribuicao_situacao.get(situacao, 0) + 1

            # Preparar dados do colaborador
            dados_colaborador = {
                "matricula": matricula,
                "nome": colaborador.get("nome", ""),
                "cpf": colaborador.get("cpf", ""),
                "valores": {
                    "vr_total": float(valor_vr),
                    "empresa_80pct": float(valor_empresa),
                    "funcionario_20pct": float(valor_funcionario),
                },
                "vigencia": {
                    "inicio": colaborador.get("data_inicio_vigencia", "15/04/2025"),
                    "fim": colaborador.get("data_fim_vigencia", "15/05/2025"),
                },
                "dados_funcionais": {
                    "empresa": colaborador.get("empresa", ""),
                    "cargo": colaborador.get("cargo", ""),
                    "situacao": situacao,
                    "admissao": colaborador.get("admissao", ""),
                    "demissao": colaborador.get("demissao", ""),
                },
                "endereco": colaborador.get("endereco", {}),
            }

            dados_operadora["colaboradores"].append(dados_colaborador)

        # Atualizar totais no cabeçalho
        dados_operadora["cabecalho"]["valor_total_vr"] = float(total_vr)
        dados_operadora["cabecalho"]["valor_total_empresa"] = float(total_empresa)
        dados_operadora["cabecalho"]["valor_total_funcionario"] = float(
            total_funcionario
        )

        # Atualizar resumo
        dados_operadora["resumo"]["distribuicao_por_estado"] = distribuicao_estado
        dados_operadora["resumo"]["distribuicao_por_situacao"] = distribuicao_situacao
        dados_operadora["resumo"]["estatisticas_valores"] = {
            "valor_medio_vr": (
                float(total_vr / len(dados.get("colaboradores", {})))
                if dados.get("colaboradores")
                else 0
            ),
            "maior_valor": max(
                [
                    float(c.get("valor_vr_calculado", 0))
                    for c in dados.get("colaboradores", {}).values()
                ],
                default=0,
            ),
            "menor_valor": min(
                [
                    float(c.get("valor_vr_calculado", 0))
                    for c in dados.get("colaboradores", {}).values()
                    if float(c.get("valor_vr_calculado", 0)) > 0
                ],
                default=0,
            ),
        }

        # Salvar JSON
        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            json.dump(
                dados_operadora, arquivo, indent=2, ensure_ascii=False, default=str
            )

        logger.info(
            f"JSON gerado com dados de {len(dados_operadora['colaboradores'])} colaboradores"
        )
        return str(caminho_arquivo)

    def _gerar_relatorio_controle(self, dados: Dict[str, Any]) -> str:
        """Gera relatório de controle para conferência."""
        nome_arquivo = f"RELATORIO_CONTROLE_OPERADORA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        caminho_arquivo = self.diretorio_output / nome_arquivo

        logger.info(f"Gerando relatório de controle: {caminho_arquivo}")

        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO DE CONTROLE - ENTREGA OPERADORA VR")
        relatorio.append("=" * 80)
        relatorio.append(
            f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        relatorio.append(f"Período de referência: 15/04/2025 a 15/05/2025")
        relatorio.append("")

        # Estatísticas gerais
        colaboradores = dados.get("colaboradores", {})
        total_colaboradores = len(colaboradores)

        relatorio.append("ESTATÍSTICAS GERAIS:")
        relatorio.append("-" * 40)
        relatorio.append(f"Total de colaboradores: {total_colaboradores}")

        # Calcular totais
        total_vr = Decimal("0")
        total_empresa = Decimal("0")
        total_funcionario = Decimal("0")

        for colaborador in colaboradores.values():
            # Obter valor VR de diferentes possíveis locais
            valor_vr = 0

            if (
                "valor_vr_calculado" in colaborador
                and colaborador["valor_vr_calculado"]
            ):
                valor_vr = Decimal(str(colaborador["valor_vr_calculado"]))
            elif "calculo_vr" in colaborador and isinstance(
                colaborador["calculo_vr"], dict
            ):
                calculo_vr = colaborador["calculo_vr"]
                if "valor_total" in calculo_vr and calculo_vr["valor_total"]:
                    valor_vr = Decimal(str(calculo_vr["valor_total"]))

            total_vr += valor_vr
            total_empresa += valor_vr * Decimal(str(self.custo_empresa_percentual))
            total_funcionario += valor_vr * Decimal(
                str(self.custo_funcionario_percentual)
            )

        relatorio.append(f"Valor total VR: R$ {total_vr:,.2f}")
        relatorio.append(f"Valor total empresa (80%): R$ {total_empresa:,.2f}")
        relatorio.append(f"Valor total funcionário (20%): R$ {total_funcionario:,.2f}")
        relatorio.append(
            f"Valor médio por colaborador: R$ {total_vr/total_colaboradores if total_colaboradores > 0 else 0:,.2f}"
        )
        relatorio.append("")

        # Distribuição por estado
        distribuicao_estado = {}
        distribuicao_situacao = {}

        for colaborador in colaboradores.values():
            estado = colaborador.get("endereco", {}).get("estado", "Não informado")
            situacao = colaborador.get("situacao", "Trabalhando")

            if estado not in distribuicao_estado:
                distribuicao_estado[estado] = {"count": 0, "valor": Decimal("0")}
            if situacao not in distribuicao_situacao:
                distribuicao_situacao[situacao] = {"count": 0, "valor": Decimal("0")}

            valor_vr = Decimal(str(colaborador.get("valor_vr_calculado", 0)))
            distribuicao_estado[estado]["count"] += 1
            distribuicao_estado[estado]["valor"] += valor_vr
            distribuicao_situacao[situacao]["count"] += 1
            distribuicao_situacao[situacao]["valor"] += valor_vr

        relatorio.append("DISTRIBUIÇÃO POR ESTADO:")
        relatorio.append("-" * 40)
        for estado, dados in sorted(distribuicao_estado.items()):
            relatorio.append(
                f"{estado}: {dados['count']} colaboradores - R$ {dados['valor']:,.2f}"
            )
        relatorio.append("")

        relatorio.append("DISTRIBUIÇÃO POR SITUAÇÃO:")
        relatorio.append("-" * 40)
        for situacao, dados in sorted(distribuicao_situacao.items()):
            relatorio.append(
                f"{situacao}: {dados['count']} colaboradores - R$ {dados['valor']:,.2f}"
            )
        relatorio.append("")

        # Validações aplicadas
        validacao = dados.get("validacao", {})
        if validacao:
            estatisticas = validacao.get("estatisticas", {})
            relatorio.append("VALIDAÇÕES APLICADAS:")
            relatorio.append("-" * 40)
            relatorio.append(
                f"Registros processados: {estatisticas.get('total_registros', 0)}"
            )
            relatorio.append(
                f"Registros válidos: {estatisticas.get('registros_validos', 0)}"
            )
            relatorio.append(
                f"Registros com erro: {estatisticas.get('registros_com_erro', 0)}"
            )
            relatorio.append(
                f"Registros com warning: {estatisticas.get('registros_com_warning', 0)}"
            )

            if estatisticas.get("total_registros", 0) > 0:
                taxa_aprovacao = (
                    estatisticas.get("registros_validos", 0)
                    / estatisticas["total_registros"]
                ) * 100
                relatorio.append(f"Taxa de aprovação: {taxa_aprovacao:.2f}%")
            relatorio.append("")

        # Instruções para a operadora
        relatorio.append("INSTRUÇÕES PARA OPERADORA:")
        relatorio.append("-" * 40)
        relatorio.append("1. Conferir total de colaboradores")
        relatorio.append("2. Validar soma dos valores (VR = Empresa + Funcionário)")
        relatorio.append("3. Verificar formatação de datas (DD/MM/YYYY)")
        relatorio.append("4. Confirmar CPFs formatados (XXX.XXX.XXX-XX)")
        relatorio.append("5. Validar período de vigência (15/04/2025 a 15/05/2025)")
        relatorio.append("")

        relatorio.append("OBSERVAÇÕES:")
        relatorio.append("-" * 40)
        relatorio.append("• Valor empresa: 80% do VR total")
        relatorio.append("• Valor funcionário: 20% do VR total (desconto em folha)")
        relatorio.append("• Apenas colaboradores ativos estão inclusos")
        relatorio.append("• Cálculo baseado em dias úteis do período")
        relatorio.append("")

        relatorio.append("=" * 80)

        # Salvar relatório
        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(relatorio))

        logger.info("Relatório de controle gerado")
        return str(caminho_arquivo)

    def _gerar_excel_operadora(self, dados: Dict[str, Any]) -> str:
        """Gera arquivo Excel no formato da operadora (usando openpyxl)."""
        try:
            import openpyxl
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas e openpyxl necessários para geração de Excel")

        nome_arquivo = (
            f"VR_MENSAL_OPERADORA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        caminho_arquivo = self.diretorio_output / nome_arquivo

        logger.info(f"Gerando Excel: {caminho_arquivo}")

        # Preparar dados para DataFrame
        dados_planilha = []

        for matricula, colaborador in dados.get("colaboradores", {}).items():
            linha = self._preparar_linha_csv(matricula, colaborador)

            # Converter valores monetários para float
            for i in [9, 10, 11]:  # Índices dos valores monetários
                if i < len(linha) and linha[i]:
                    valor_str = str(linha[i]).replace(",", ".")
                    try:
                        linha[i] = float(valor_str)
                    except ValueError:
                        linha[i] = 0.0

            dados_planilha.append(linha)

        # Criar DataFrame
        colunas = [
            "matricula",
            "admissao",
            "sindicato",
            "competencia",
            "dias",
            "valor diario",
            "TOTAL",
            "custo empresa",
            "deconto funcionario",
            "OBS GERAL",
        ]

        df = pd.DataFrame(dados_planilha, columns=colunas)

        # Salvar Excel usando openpyxl
        with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="VR MENSAL 05.2025", index=False)

            # Obter worksheet para formatação
            worksheet = writer.sheets["VR MENSAL 05.2025"]

            # Formatar cabeçalhos
            from openpyxl.styles import Alignment, Font, PatternFill

            # Estilo do cabeçalho
            header_font = Font(bold=True, color="000000")
            header_fill = PatternFill(
                start_color="D7E4BC", end_color="D7E4BC", fill_type="solid"
            )
            center_alignment = Alignment(horizontal="center", vertical="center")

            # Aplicar estilo no cabeçalho
            for col in range(1, len(colunas) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_alignment

            # Ajustar largura das colunas conforme modelo
            column_widths = {
                "A": 12,  # matricula
                "B": 15,  # admissao
                "C": 35,  # sindicato
                "D": 15,  # competencia
                "E": 8,  # dias
                "F": 12,  # valor diario
                "G": 12,  # TOTAL
                "H": 15,  # custo empresa
                "I": 18,  # deconto funcionario
                "J": 25,  # OBS GERAL
            }

            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width

        logger.info(f"Excel gerado com {len(dados_planilha)} registros")
        return str(caminho_arquivo)

    def _gerar_relatorio_temporario(self, dados: Dict[str, Any], caminho_arquivo: str):
        """Gera relatório temporário de controle."""
        colaboradores = dados.get("colaboradores", {})
        total_colaboradores = len(colaboradores)

        # Calcular estatísticas
        valor_total = 0
        valor_empresa_total = 0
        valor_funcionario_total = 0

        for colaborador in colaboradores.values():
            if (
                "valor_vr_calculado" in colaborador
                and colaborador["valor_vr_calculado"]
            ):
                vr = float(colaborador["valor_vr_calculado"])
            elif "calculo_vr" in colaborador and isinstance(
                colaborador["calculo_vr"], dict
            ):
                vr = float(colaborador["calculo_vr"].get("valor_total", 0))
            else:
                vr = 0

            valor_total += vr
            valor_empresa_total += vr * self.custo_empresa_percentual
            valor_funcionario_total += vr * self.custo_funcionario_percentual

        # Gerar relatório
        relatorio = []
        relatorio.append("=" * 60)
        relatorio.append("RELATÓRIO TEMPORÁRIO - VR OPERADORA")
        relatorio.append("=" * 60)
        relatorio.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append("")
        relatorio.append("RESUMO EXECUTIVO:")
        relatorio.append(f"• Total colaboradores: {total_colaboradores:,}")
        relatorio.append(f"• Valor total VR: R$ {valor_total:,.2f}")
        relatorio.append(f"• Custo empresa (80%): R$ {valor_empresa_total:,.2f}")
        relatorio.append(
            f"• Desconto funcionário (20%): R$ {valor_funcionario_total:,.2f}"
        )
        relatorio.append("")
        relatorio.append("STATUS: ✅ Excel gerado com sucesso")
        relatorio.append("=" * 60)

        with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(relatorio))


def main():
    """Função principal para testar o gerador."""
    logger.info("📊 TESTANDO GERADOR DE PLANILHA FINAL")
    logger.info("=" * 50)

    # Dados de teste
    dados_teste = {
        "metadata": {"data_processamento": datetime.now().isoformat()},
        "colaboradores": {
            "12345": {
                "nome": "João Silva",
                "cpf": "12345678901",
                "valor_vr_calculado": 750.00,
                "empresa": "1410",
                "cargo": "ANALISTA",
                "situacao": "Trabalhando",
                "admissao": "2024-01-15",
                "endereco": {"estado": "São Paulo", "municipio": "São Paulo"},
            },
            "67890": {
                "nome": "Maria Santos",
                "cpf": "98765432100",
                "valor_vr_calculado": 825.00,
                "empresa": "1410",
                "cargo": "COORDENADOR",
                "situacao": "Trabalhando",
                "admissao": "2023-05-20",
                "endereco": {"estado": "Rio de Janeiro", "municipio": "Rio de Janeiro"},
            },
        },
    }

    gerador = GeradorPlanilhaFinal()
    arquivos = gerador.gerar_planilha_operadora(dados_teste)

    logger.info("📁 ARQUIVOS GERADOS:")
    for tipo, arquivo in arquivos.items():
        logger.info(f"  {tipo}: {arquivo}")

    logger.info("✅ Geração concluída!")


if __name__ == "__main__":
    main()
