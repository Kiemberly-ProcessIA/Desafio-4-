#!/usr/bin/env python3
# analisador_exclusoes_llm.py - Usa LLM para analisar dados do Passo 1 e identificar exclusões por cargo

import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Importar configurações da raiz do projeto
sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar configurações da raiz do projeto
from config import GOOGLE_API_KEY, NOME_MODELO_LLM

# Importar sistema de logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import log_fim_passo, log_inicio_passo, setup_logging

logger = setup_logging()

# Importar dados consolidados (passo 1)
sys.path.append(str(Path(__file__).parent.parent / "passo_1_leitura_validacao"))
from consolidador_json import obter_dados_consolidados


class AnalisadorExclusions:
    """Analisador que usa LLM para identificar, por CARGO, se deve excluir/manter e o motivo."""

    def __init__(self):
        # Inicialização obrigatória do cliente LLM
        self.genai = genai
        self.model = None
        if self.genai is not None:
            try:
                logger.info(f"🔧 Configurando cliente LLM: {NOME_MODELO_LLM}")
                self.genai.configure(api_key=GOOGLE_API_KEY)
                self.model = self.genai.GenerativeModel(NOME_MODELO_LLM)
                logger.info("✅ Cliente LLM inicializado com sucesso")
            except Exception as e:
                raise RuntimeError(
                    f"❌ ERRO CRÍTICO: Não foi possível inicializar o cliente LLM: {e}"
                )
        else:
            raise RuntimeError(
                "❌ ERRO CRÍTICO: Pacote google.generativeai não encontrado. Instale com: pip install google-generativeai"
            )

    def _carregar_ccts(self, caminho_convencoes: str) -> dict:
        """Carrega informações das CCTs disponíveis."""
        ccts_info = {}

        try:
            # Buscar arquivos de CCT na pasta
            caminho_convencoes = Path(caminho_convencoes)
            if not caminho_convencoes.exists():
                logger.warning(
                    f"⚠️ Pasta de convenções não encontrada: {caminho_convencoes}"
                )
                return {}

            arquivos_cct = list(caminho_convencoes.glob("*.pdf"))
            logger.info(f"📋 Encontrados {len(arquivos_cct)} arquivos de CCT")

            for arquivo in arquivos_cct:
                nome = arquivo.stem
                # Identificar o estado baseado no nome do arquivo
                estado = "São Paulo"  # padrão
                if "rio grande do sul" in nome.lower():
                    estado = "Rio Grande do Sul"
                elif "paraná" in nome.lower() or "parana" in nome.lower():
                    estado = "Paraná"
                elif "rio de janeiro" in nome.lower():
                    estado = "Rio de Janeiro"
                elif "são paulo" in nome.lower() or "sao paulo" in nome.lower():
                    estado = "São Paulo"

                ccts_info[estado] = {
                    "arquivo": nome,
                    "caminho": str(arquivo),
                    "descricao": f"CCT {estado}",
                }

            logger.info(
                f"✅ {len(ccts_info)} CCTs identificadas: {list(ccts_info.keys())}"
            )
            return ccts_info

        except Exception as e:
            logger.error(f"❌ Erro ao carregar CCTs: {e}")
            return {}

    def analisar_dados_passo1(
        self, caminho_colaboradores: str, caminho_configuracoes: str
    ) -> dict:
        """Analisa os dados consolidados do Passo 1 usando LLM e retorna o mapeamento por cargo.

        Retorna um dicionário com chaves: timestamp_analise, dados_origem, analise_llm, resposta_completa_llm
        """
        log_inicio_passo(
            "PASSO 2",
            "Análise LLM - Exclusões conforme Regras Oficiais (Diretores/Estagiários/Aprendizes)",
            logger,
        )
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("📂 Carregando dados em memória")

        # 1. Obter dados consolidados do Passo 1
        dados = obter_dados_consolidados(caminho_colaboradores, caminho_configuracoes)

        return self._executar_analise_com_dados(dados)

    def analisar_com_dados_memoria(self, dados_consolidados: dict) -> dict:
        """Analisa dados já consolidados que estão em memória.

        Args:
            dados_consolidados: Dicionário com dados já consolidados do Passo 1

        Returns:
            Dicionário com resultado da análise LLM
        """
        log_inicio_passo(
            "PASSO 2",
            "Análise LLM - Exclusões conforme Regras Oficiais (Diretores/Estagiários/Aprendizes)",
            logger,
        )
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("📊 Usando dados em memória (otimizado)")
        logger.info(
            "💡 Dica: Para máxima eficiência, use o arquivo agrupamentos_consolidados.json"
        )

        return self._executar_analise_com_dados(dados_consolidados)

    def analisar_com_agrupamentos_json(self, caminho_agrupamentos: str) -> dict:
        """Analisa dados do arquivo agrupamentos_consolidados.json.

        Args:
            caminho_agrupamentos: Caminho para o arquivo agrupamentos_consolidados.json

        Returns:
            Dicionário com resultado da análise LLM
        """
        log_inicio_passo(
            "PASSO 2",
            "Análise LLM - Exclusões conforme Regras Oficiais (Diretores/Estagiários/Aprendizes)",
            logger,
        )
        logger.info(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("📂 Carregando dados do arquivo de agrupamentos")

        try:
            with open(caminho_agrupamentos, "r", encoding="utf-8") as f:
                agrupamentos = json.load(f)

            logger.info(f"✅ Arquivo carregado: {caminho_agrupamentos}")
            logger.info(
                f"🎯 {len(agrupamentos.get('cargos', []))} cargos únicos encontrados"
            )
            logger.info(
                f"📊 {len(agrupamentos.get('status', []))} status únicos encontrados"
            )
            logger.info(
                f"🔍 {len(agrupamentos.get('situacoes', []))} situações únicas encontradas"
            )

            # Carregar CCTs
            caminho_projeto = Path(caminho_agrupamentos).parent.parent
            caminho_convencoes = caminho_projeto / "input_data" / "convencoes"
            ccts_info = self._carregar_ccts(str(caminho_convencoes))

            return self._executar_analise_com_agrupamentos(agrupamentos, ccts_info)

        except FileNotFoundError:
            logger.error(f"❌ Arquivo não encontrado: {caminho_agrupamentos}")
            return {"erro": f"Arquivo não encontrado: {caminho_agrupamentos}"}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erro ao decodificar JSON: {e}")
            return {"erro": f"Erro ao decodificar JSON: {e}"}
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            return {"erro": f"Erro inesperado: {e}"}

    def _executar_analise_com_agrupamentos(
        self, agrupamentos: dict, ccts_info: dict = None
    ) -> dict:
        """Método privado que executa a análise LLM usando dados de agrupamentos."""

        # Extrair listas dos agrupamentos
        cargos_unicos = set(agrupamentos.get("cargos", []))
        status_unicos = set(agrupamentos.get("status", []))
        situacoes_unicas = set(agrupamentos.get("situacoes", []))

        logger.info(f"🔍 Análise de {len(cargos_unicos)} cargos únicos identificados")
        logger.info(f"📊 Status encontrados: {', '.join(sorted(status_unicos))}")
        logger.info(f"🎯 Situações encontradas: {', '.join(sorted(situacoes_unicas))}")

        # Criar dados fictícios para análise (necessário para o prompt)
        dados_para_analise = {
            "colaboradores": {},
            "resumo_agrupamentos": {
                "cargos_unicos": list(cargos_unicos),
                "status_unicos": list(status_unicos),
                "situacoes_unicas": list(situacoes_unicas),
            },
            "ccts_info": ccts_info or {},
        }

        return self._executar_analise_com_dados(dados_para_analise)

    def _executar_analise_com_dados(self, dados: dict) -> dict:
        """Método privado que executa a análise LLM usando os dados consolidados."""

        # 1. Extrair cargos únicos dos colaboradores
        colaboradores = dados.get("colaboradores", {})
        cargos_unicos = set()

        for colaborador in colaboradores.values():
            cargo = colaborador.get("cargo", "").strip()
            if cargo:
                cargos_unicos.add(cargo)

        # Se não há colaboradores, usar os agrupamentos
        if not cargos_unicos and "resumo_agrupamentos" in dados:
            cargos_unicos = set(dados["resumo_agrupamentos"].get("cargos_unicos", []))

        cargos_lista = sorted(list(cargos_unicos))
        logger.info(f"🎯 {len(cargos_lista)} cargos únicos para análise")

        # 2. Preparar prompt para LLM
        logger.info("🤖 Enviando dados para análise pela LLM")
        logger.info(f"🚀 Enviando prompt para {NOME_MODELO_LLM}")

        prompt = self._construir_prompt_analise(cargos_lista, dados)

        # 3. Executar consulta LLM
        try:
            response = self.model.generate_content(prompt)
            logger.info("✅ Resposta recebida da LLM")

            # 4. Processar resposta
            resposta_texto = response.text

            # 5. Tentar extrair JSON da resposta
            try:
                # Extrair JSON usando regex (caso a LLM adicione texto extra)
                json_match = re.search(r"\{.*\}", resposta_texto, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analise_llm = json.loads(json_str)
                else:
                    # Se não encontrar JSON, tentar parsear a resposta completa
                    analise_llm = json.loads(resposta_texto)

            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Erro ao parsear JSON da LLM: {e}")
                # Criar estrutura padrão em caso de erro
                analise_llm = {
                    "timestamp_analise": datetime.now().isoformat(),
                    "erro_parsing": str(e),
                    "resposta_bruta": resposta_texto,
                    "cargos_para_excluir": [],
                    "status_para_excluir": [],
                    "situacoes_para_excluir": [],
                    "cargos_para_manter": cargos_lista,
                }

            logger.info("✅ Análise JSON parseada com sucesso")

            # Preparar estatísticas para o log
            estatisticas = {
                "total_cargos_analisados": len(cargos_lista),
                "cargos_para_excluir": len(analise_llm.get("cargos_para_excluir", [])),
                "status_para_excluir": len(analise_llm.get("status_para_excluir", [])),
                "situacoes_para_excluir": len(
                    analise_llm.get("situacoes_para_excluir", [])
                ),
                "cargos_para_manter": len(analise_llm.get("cargos_para_manter", [])),
            }

            # 6. Estruturar resultado final
            resultado = {
                "timestamp_analise": datetime.now().isoformat(),
                "dados_origem": {
                    "total_cargos_analisados": len(cargos_lista),
                    "cargos_lista": cargos_lista,
                },
                "analise_llm": analise_llm,
                "resposta_completa_llm": resposta_texto,
            }

            log_fim_passo(
                "PASSO 2",
                f"Análise LLM concluída para {len(cargos_lista)} cargos",
                estatisticas,
                logger,
            )

            # Salvar resultado para debug/análise
            try:
                import os

                output_dir = Path(__file__).parent.parent.parent / "output"
                resultado_path = output_dir / "passo_2-resultado_llm.json"

                with open(resultado_path, "w", encoding="utf-8") as f:
                    json.dump(resultado, f, indent=2, ensure_ascii=False)
                logger.info(f"📄 Resultado salvo para análise: {resultado_path}")
            except Exception as e:
                logger.warning(f"⚠️ Não foi possível salvar resultado: {e}")

            return resultado

        except Exception as e:
            logger.error(f"❌ Erro ao executar análise LLM: {e}")
            return {
                "erro": str(e),
                "timestamp_erro": datetime.now().isoformat(),
                "cargos_analisados": cargos_lista,
            }

    def _construir_prompt_analise(self, cargos_lista: list, dados: dict) -> str:
        """Constrói o prompt para análise LLM dos cargos."""

        # Extrair informações das CCTs
        ccts_info = dados.get("ccts_info", {})
        ccts_text = ""
        if ccts_info:
            ccts_text = f"\nCCTs DISPONÍVEIS:\n"
            for estado, info in ccts_info.items():
                ccts_text += f"- {estado}: {info.get('descricao', 'CCT disponível')}\n"
            ccts_text += "\nCONSIDERE: As CCTs podem conter regras específicas sobre exclusão de cargos de gestão do Vale-Refeição.\n"

        prompt = f"""
Analise OBRIGATORIAMENTE e determine exclusões para Vale-Refeição conforme regras oficiais.

REGRAS OFICIAIS DE EXCLUSÃO:

CARGOS PARA EXCLUIR (OBRIGATÓRIO):
- DIRETORES: Qualquer cargo que contenha "DIRETOR", "CEO", "PRESIDENTE", "VICE-PRESIDENTE"
- GESTÃO: Cargos de GERENTE e COORDENADOR com funções administrativas, financeiras, estratégicas
- Estagiários e Aprendizes (Lei 11.788/2008 e Lei 10.097/2000)

CRITÉRIO JURÍDICO PARA GERENTES E COORDENADORES:
- São considerados "alta gestão" quando exercem funções de direção, coordenação administrativa
- Cargos que coordenam equipes, projetos estratégicos ou departamentos inteiros
- Funções com autonomia decisória em recursos humanos, finanças ou operações críticas
- Conforme Lei 6.321/76 e interpretação jurisprudencial dos TSTs

STATUS PARA EXCLUIR:
- "aprendiz", "estágio", "exterior"  

SITUAÇÕES PARA EXCLUIR:
- "Licença Maternidade", "Auxílio Doença", "não recebe VR"
- NÃO EXCLUIR: "Atestado" (deve ser tratado proporcionalmente, não excluído totalmente)

{ccts_text}

INSTRUÇÕES CRÍTICAS:
1. ANALISAR RIGOROSAMENTE TODOS OS CARGOS na lista completa
2. IDENTIFICAR obrigatoriamente qualquer cargo contendo: DIRETOR (100% exclusão)
3. AVALIAR COORDENADORES e GERENTES com base na função (não apenas título)
4. INCLUIR justificativa jurídica para cada exclusão de cargo de gestão
5. CONSIDERAR que CCTs podem permitir exclusão de cargos administrativos/gestão

DADOS PARA ANÁLISE:
CARGOS COMPLETOS: {', '.join(cargos_lista)}
STATUS: {', '.join(dados.get('resumo_agrupamentos', {}).get('status_unicos', []))}
SITUAÇÕES: {', '.join(dados.get('resumo_agrupamentos', {}).get('situacoes_unicas', []))}

RESPONDA APENAS COM JSON VÁLIDO - JUSTIFIQUE CADA EXCLUSÃO:
{{
  "cargos_para_excluir": [
    {{"cargo": "NOME_EXATO_DO_CARGO", "motivo": "Cargo de alta gestão com autonomia decisória", "regra_aplicada": "Lei 6.321/76 - Alta Gestão", "fundamento_juridico": "Função administrativa/estratégica"}}
  ],
  "status_para_excluir": [
    {{"status": "NOME", "motivo": "Status de exclusão obrigatória", "regra_aplicada": "Status"}}
  ],
  "situacoes_para_excluir": [
    {{"situacao": "NOME", "motivo": "Situação de afastamento", "regra_aplicada": "Situação"}}
  ],
  "resumo": {{
    "total_cargos_excluir": 0,
    "total_status_excluir": 0,
    "total_situacoes_excluir": 0,
    "criterio_principal": "Regras oficiais do projeto"
  }}
}}"""
        return prompt


def main():
    """Função principal para teste do analisador."""

    logger.info("🧪 TESTE DO ANALISADOR DE EXCLUSÕES LLM")

    # Caminhos para os arquivos de teste
    caminho_colaboradores = (
        Path(__file__).parent.parent.parent / "input_data" / "colaboradores"
    )
    caminho_configuracoes = (
        Path(__file__).parent.parent.parent / "input_data" / "configuracoes"
    )

    if not caminho_colaboradores.exists():
        logger.error(f"❌ Diretório não encontrado: {caminho_colaboradores}")
        return

    # Executar análise
    analisador = AnalisadorExclusions()
    resultado = analisador.analisar_dados_passo1(
        str(caminho_colaboradores), str(caminho_configuracoes)
    )

    # Exibir resultado
    logger.info("📋 RESULTADO DA ANÁLISE:")
    logger.info(
        f"🎯 Total de cargos analisados: {resultado.get('dados_origem', {}).get('total_cargos_analisados', 'N/A')}"
    )

    if "analise_llm" in resultado:
        analise = resultado["analise_llm"]
        logger.info(
            f"❌ Cargos para excluir: {len(analise.get('cargos_para_excluir', []))}"
        )
        logger.info(
            f"✅ Cargos para manter: {len(analise.get('cargos_para_manter', []))}"
        )

        # Mostrar alguns exemplos
        if analise.get("cargos_para_excluir"):
            logger.info("🔴 Exemplos de exclusões:")
            for cargo in analise["cargos_para_excluir"][:3]:
                logger.info(
                    f"  • {cargo.get('cargo', 'N/A')}: {cargo.get('motivo', 'N/A')}"
                )


if __name__ == "__main__":
    main()
