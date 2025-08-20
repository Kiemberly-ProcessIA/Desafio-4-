#!/usr/bin/env python3
# leitor_excel.py - Passo 1: Leitura e Validação de Arquivos Excel

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Adicionar o diretório pai ao path para importações
sys.path.append(str(Path(__file__).parent.parent))
from utils.logging_config import (get_logger, log_processamento,
                                  log_resultado_validacao)

# Configurar logging padronizado
logger = get_logger(__name__)


class LeitorExcel:
    """
    Classe responsável pela leitura e validação inicial dos arquivos Excel.

    Funcionalidades:
    - Leitura segura de arquivos Excel
    - Validação de estrutura e colunas
    - Verificação de integridade dos dados
    - Relatório de status dos arquivos
    """

    def __init__(self, pasta_colaboradores: str, pasta_configuracoes: str):
        self.pasta_colaboradores = pasta_colaboradores
        self.pasta_configuracoes = pasta_configuracoes
        self.arquivos_obrigatorios = {
            "colaboradores": ["ATIVOS.xlsx", "DESLIGADOS.xlsx", "FÉRIAS.xlsx"],
            "configuracoes": ["Base dias uteis.xlsx", "Base sindicato x valor.xlsx"],
        }
        self.arquivos_opcionais = [
            "ADMISSÃO ABRIL.xlsx",
            "APRENDIZ.xlsx",
            "ESTÁGIO.xlsx",
            "EXTERIOR.xlsx",
            "AFASTAMENTOS.xlsx",
            "VR MENSAL 05.2025.xlsx",
        ]
        self.dados_carregados = {}
        self.relatorio_validacao = {}

    def verificar_arquivos_existem(self) -> Dict[str, bool]:
        """Verifica se todos os arquivos obrigatórios existem."""
        logger.info("🔍 VERIFICANDO EXISTÊNCIA DOS ARQUIVOS")

        status_arquivos = {}
        arquivos_obrigatorios_total = 0
        arquivos_encontrados = 0

        # Verificar arquivos de colaboradores
        logger.info("📂 Verificando arquivos de colaboradores...")
        for arquivo in self.arquivos_obrigatorios["colaboradores"]:
            caminho = os.path.join(self.pasta_colaboradores, arquivo)
            existe = os.path.exists(caminho)
            status_arquivos[arquivo] = existe
            arquivos_obrigatorios_total += 1

            if existe:
                arquivos_encontrados += 1
                logger.info(f"✅ {arquivo}")
            else:
                logger.error(f"❌ {arquivo} - NÃO ENCONTRADO")

        # Verificar arquivos de configurações
        logger.info("⚙️  Verificando arquivos de configurações...")
        for arquivo in self.arquivos_obrigatorios["configuracoes"]:
            caminho = os.path.join(self.pasta_configuracoes, arquivo)
            existe = os.path.exists(caminho)
            status_arquivos[arquivo] = existe
            arquivos_obrigatorios_total += 1

            if existe:
                arquivos_encontrados += 1
                logger.info(f"✅ {arquivo}")
            else:
                logger.error(f"❌ {arquivo} - NÃO ENCONTRADO")

        # Verificar arquivos opcionais
        logger.info("📋 Verificando arquivos opcionais...")
        arquivos_opcionais_encontrados = 0
        for arquivo in self.arquivos_opcionais:
            caminho = os.path.join(self.pasta_colaboradores, arquivo)
            existe = os.path.exists(caminho)
            status_arquivos[arquivo] = existe

            if existe:
                arquivos_opcionais_encontrados += 1
                logger.info(f"➕ {arquivo}")
            else:
                logger.info(f"➖ {arquivo} - Opcional, ausente")

        # Log resumo
        log_resultado_validacao(
            "ARQUIVOS",
            validos=arquivos_encontrados,
            invalidos=arquivos_obrigatorios_total - arquivos_encontrados,
            warnings=len(self.arquivos_opcionais) - arquivos_opcionais_encontrados,
            logger=logger,
        )

        return status_arquivos

    def ler_arquivo_excel(
        self, caminho: str, nome_arquivo: str
    ) -> Optional[pd.DataFrame]:
        """Lê um arquivo Excel com tratamento de erros."""
        try:
            logger.info(f"📖 Carregando {nome_arquivo}...")
            df = pd.read_excel(caminho)
            logger.info(
                f"📊 {nome_arquivo}: {len(df)} linhas, {len(df.columns)} colunas"
            )
            return df
        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {nome_arquivo}")
            return None
        except PermissionError:
            logger.error(f"❌ Sem permissão para ler: {nome_arquivo}")
            return None
        except Exception as e:
            logger.error(
                f"❌ Erro ao processar {nome_arquivo}: {type(e).__name__}: {e}"
            )
            return None

    def validar_estrutura_ativos(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida a estrutura do arquivo ATIVOS.xlsx"""
        colunas_esperadas = ["matricula", "empresa", "cargo", "situacao", "sindicato"]
        colunas_presentes = df.columns.tolist()

        validacao = {
            "arquivo": "ATIVOS.xlsx",
            "linhas_total": len(df),
            "colunas_esperadas": colunas_esperadas,
            "colunas_presentes": colunas_presentes,
            "colunas_ausentes": [
                col for col in colunas_esperadas if col not in colunas_presentes
            ],
            "linhas_vazias": df.isnull().all(axis=1).sum(),
            "matriculas_duplicadas": (
                df["matricula"].duplicated().sum()
                if "matricula" in df.columns
                else "N/A"
            ),
            "matriculas_nulas": (
                df["matricula"].isnull().sum() if "matricula" in df.columns else "N/A"
            ),
            "situacoes_unicas": (
                df["situacao"].unique().tolist() if "situacao" in df.columns else "N/A"
            ),
            "empresas_unicas": (
                df["empresa"].unique().tolist() if "empresa" in df.columns else "N/A"
            ),
            "sindicatos_unicos": (
                len(df["sindicato"].unique()) if "sindicato" in df.columns else "N/A"
            ),
        }

        return validacao

    def validar_estrutura_desligados(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida a estrutura do arquivo DESLIGADOS.xlsx"""
        colunas_esperadas = ["matricula", "demissao data", "comunicado de desligamento"]
        colunas_presentes = df.columns.tolist()

        validacao = {
            "arquivo": "DESLIGADOS.xlsx",
            "linhas_total": len(df),
            "colunas_esperadas": colunas_esperadas,
            "colunas_presentes": colunas_presentes,
            "colunas_ausentes": [
                col for col in colunas_esperadas if col not in colunas_presentes
            ],
            "linhas_vazias": df.isnull().all(axis=1).sum(),
            "matriculas_duplicadas": (
                df["matricula"].duplicated().sum()
                if "matricula" in df.columns
                else "N/A"
            ),
            "datas_invalidas": 0,  # TODO: Implementar validação de datas
            "comunicados_vazios": (
                df["comunicado de desligamento"].isnull().sum()
                if "comunicado de desligamento" in df.columns
                else "N/A"
            ),
        }

        return validacao

    def validar_estrutura_ferias(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida a estrutura do arquivo FÉRIAS.xlsx"""
        colunas_esperadas = ["matricula", "situacao", "dias de férias"]
        colunas_presentes = df.columns.tolist()

        validacao = {
            "arquivo": "FÉRIAS.xlsx",
            "linhas_total": len(df),
            "colunas_esperadas": colunas_esperadas,
            "colunas_presentes": colunas_presentes,
            "colunas_ausentes": [
                col for col in colunas_esperadas if col not in colunas_presentes
            ],
            "linhas_vazias": df.isnull().all(axis=1).sum(),
            "matriculas_duplicadas": (
                df["matricula"].duplicated().sum()
                if "matricula" in df.columns
                else "N/A"
            ),
            "dias_ferias_media": (
                df["dias de férias"].mean() if "dias de férias" in df.columns else "N/A"
            ),
            "dias_ferias_max": (
                df["dias de férias"].max() if "dias de férias" in df.columns else "N/A"
            ),
            "situacoes_unicas": (
                df["situacao"].unique().tolist() if "situacao" in df.columns else "N/A"
            ),
        }

        return validacao

    def validar_estrutura_dias_uteis(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida a estrutura do arquivo Base dias uteis.xlsx"""
        colunas_esperadas = ["sindicato", "dias uteis"]
        colunas_presentes = df.columns.tolist()

        validacao = {
            "arquivo": "Base dias uteis.xlsx",
            "linhas_total": len(df),
            "colunas_esperadas": colunas_esperadas,
            "colunas_presentes": colunas_presentes,
            "colunas_ausentes": [
                col for col in colunas_esperadas if col not in colunas_presentes
            ],
            "sindicatos_total": (
                len(df["sindicato"].unique()) if "sindicato" in df.columns else "N/A"
            ),
            "dias_uteis_min": (
                df["dias uteis"].min() if "dias uteis" in df.columns else "N/A"
            ),
            "dias_uteis_max": (
                df["dias uteis"].max() if "dias uteis" in df.columns else "N/A"
            ),
            "dias_uteis_media": (
                df["dias uteis"].mean() if "dias uteis" in df.columns else "N/A"
            ),
        }

        return validacao

    def validar_estrutura_valores(self, df: pd.DataFrame) -> Dict[str, any]:
        """Valida a estrutura do arquivo Base sindicato x valor.xlsx"""
        colunas_esperadas = ["estado", "valor"]
        colunas_presentes = df.columns.tolist()

        validacao = {
            "arquivo": "Base sindicato x valor.xlsx",
            "linhas_total": len(df),
            "colunas_esperadas": colunas_esperadas,
            "colunas_presentes": colunas_presentes,
            "colunas_ausentes": [
                col for col in colunas_esperadas if col not in colunas_presentes
            ],
            "estados_total": (
                len(df["estado"].unique()) if "estado" in df.columns else "N/A"
            ),
            "valor_min": df["valor"].min() if "valor" in df.columns else "N/A",
            "valor_max": df["valor"].max() if "valor" in df.columns else "N/A",
            "valor_medio": df["valor"].mean() if "valor" in df.columns else "N/A",
        }

        return validacao

    def executar_leitura_completa(self) -> Dict[str, any]:
        """Executa a leitura completa de todos os arquivos com validação."""
        logger.info("🚀 INICIANDO LEITURA E VALIDAÇÃO COMPLETA DOS ARQUIVOS")

        # 1. Verificar arquivos existem
        status_arquivos = self.verificar_arquivos_existem()

        # 2. Ler arquivos obrigatórios
        logger.info("\n=== CARREGANDO ARQUIVOS OBRIGATÓRIOS ===")

        # ATIVOS.xlsx
        if status_arquivos.get("ATIVOS.xlsx", False):
            caminho = os.path.join(self.pasta_colaboradores, "ATIVOS.xlsx")
            df = self.ler_arquivo_excel(caminho, "ATIVOS.xlsx")
            if df is not None:
                self.dados_carregados["ativos"] = df
                self.relatorio_validacao["ativos"] = self.validar_estrutura_ativos(df)

        # DESLIGADOS.xlsx
        if status_arquivos.get("DESLIGADOS.xlsx", False):
            caminho = os.path.join(self.pasta_colaboradores, "DESLIGADOS.xlsx")
            df = self.ler_arquivo_excel(caminho, "DESLIGADOS.xlsx")
            if df is not None:
                self.dados_carregados["desligados"] = df
                self.relatorio_validacao["desligados"] = (
                    self.validar_estrutura_desligados(df)
                )

        # FÉRIAS.xlsx
        if status_arquivos.get("FÉRIAS.xlsx", False):
            caminho = os.path.join(self.pasta_colaboradores, "FÉRIAS.xlsx")
            df = self.ler_arquivo_excel(caminho, "FÉRIAS.xlsx")
            if df is not None:
                self.dados_carregados["ferias"] = df
                self.relatorio_validacao["ferias"] = self.validar_estrutura_ferias(df)

        # Base dias uteis.xlsx
        if status_arquivos.get("Base dias uteis.xlsx", False):
            caminho = os.path.join(self.pasta_configuracoes, "Base dias uteis.xlsx")
            df = self.ler_arquivo_excel(caminho, "Base dias uteis.xlsx")
            if df is not None:
                self.dados_carregados["dias_uteis"] = df
                self.relatorio_validacao["dias_uteis"] = (
                    self.validar_estrutura_dias_uteis(df)
                )

        # Base sindicato x valor.xlsx
        if status_arquivos.get("Base sindicato x valor.xlsx", False):
            caminho = os.path.join(
                self.pasta_configuracoes, "Base sindicato x valor.xlsx"
            )
            df = self.ler_arquivo_excel(caminho, "Base sindicato x valor.xlsx")
            if df is not None:
                self.dados_carregados["valores"] = df
                self.relatorio_validacao["valores"] = self.validar_estrutura_valores(df)

        # 3. Ler arquivos opcionais
        logger.info("\n=== CARREGANDO ARQUIVOS OPCIONAIS ===")

        for arquivo in self.arquivos_opcionais:
            if status_arquivos.get(arquivo, False):
                caminho = os.path.join(self.pasta_colaboradores, arquivo)
                df = self.ler_arquivo_excel(caminho, arquivo)
                if df is not None:
                    nome_chave = (
                        arquivo.replace(".xlsx", "")
                        .lower()
                        .replace(" ", "_")
                        .replace("ã", "a")
                    )
                    self.dados_carregados[nome_chave] = df

        # 4. Gerar resumo final
        resumo = self.gerar_resumo_validacao()

        logger.info("✅ LEITURA E VALIDAÇÃO CONCLUÍDA")
        return resumo

    def gerar_resumo_validacao(self) -> Dict[str, any]:
        """Gera um resumo da validação realizada."""
        total_arquivos = len(self.arquivos_obrigatorios["colaboradores"]) + len(
            self.arquivos_obrigatorios["configuracoes"]
        )
        arquivos_carregados = len(self.dados_carregados)

        resumo = {
            "timestamp": datetime.now().isoformat(),
            "total_arquivos_obrigatorios": total_arquivos,
            "arquivos_carregados": arquivos_carregados,
            "arquivos_opcionais_carregados": len(
                [
                    k
                    for k in self.dados_carregados.keys()
                    if k
                    not in ["ativos", "desligados", "ferias", "dias_uteis", "valores"]
                ]
            ),
            "status_geral": (
                "SUCESSO" if arquivos_carregados >= total_arquivos else "PARCIAL"
            ),
            "detalhes_validacao": self.relatorio_validacao,
            "dados_disponíveis": list(self.dados_carregados.keys()),
        }

        return resumo

    def obter_dados(self) -> Dict[str, pd.DataFrame]:
        """Retorna os dados carregados."""
        return self.dados_carregados

    def imprimir_relatorio(self):
        """Imprime um relatório detalhado da validação."""
        print("\n" + "=" * 80)
        print("📋 RELATÓRIO DE VALIDAÇÃO - PASSO 1")
        print("=" * 80)

        for nome, validacao in self.relatorio_validacao.items():
            print(f"\n📄 {validacao['arquivo']}")
            print(f"   📊 Total de linhas: {validacao['linhas_total']}")
            print(f"   📋 Colunas esperadas: {len(validacao['colunas_esperadas'])}")
            print(f"   📋 Colunas presentes: {len(validacao['colunas_presentes'])}")

            if validacao["colunas_ausentes"]:
                print(f"   ❌ Colunas ausentes: {validacao['colunas_ausentes']}")
            else:
                print(f"   ✅ Todas as colunas presentes")

            if validacao.get("linhas_vazias", 0) > 0:
                print(
                    f"   ⚠️  Linhas completamente vazias: {validacao['linhas_vazias']}"
                )

        print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Uso: python leitor_excel.py <pasta_colaboradores> <pasta_configuracoes>")
        sys.exit(1)

    pasta_colaboradores = sys.argv[1]
    pasta_configuracoes = sys.argv[2]

    leitor = LeitorExcel(pasta_colaboradores, pasta_configuracoes)
    resumo = leitor.executar_leitura_completa()
    leitor.imprimir_relatorio()

    print(f"\n🎯 STATUS FINAL: {resumo['status_geral']}")
    print(
        f"📊 Arquivos carregados: {resumo['arquivos_carregados']}/{resumo['total_arquivos_obrigatorios']}"
    )
