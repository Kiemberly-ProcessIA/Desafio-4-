#!/usr/bin/env python3
# consolidador_json.py - Versão com suporte a modo DEBUG

import pandas as pd
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Adicionar o diretório pai ao path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.logging_config import get_logger, log_inicio_passo, log_fim_passo, log_processamento, log_resultado_validacao

# Configurar logging
logger = get_logger(__name__)

def limpar_string(valor: str) -> str:
    """
    Limpa uma string removendo caracteres invisíveis e espaços desnecessários.
    
    Args:
        valor: String a ser limpa
        
    Returns:
        String limpa ou string vazia se inválida
    """
    if pd.isna(valor) or valor is None:
        return ''
    
    # Converter para string e remover espaços
    valor_limpo = str(valor).strip()
    
    # Remover caracteres zero-width space (U+200B) e outros caracteres de controle
    valor_limpo = ''.join(char for char in valor_limpo if ord(char) > 31 and ord(char) != 8203)
    
    return valor_limpo.strip()

def is_valid_string(valor: str) -> bool:
    """
    Verifica se uma string é válida (não está vazia após limpeza).
    
    Args:
        valor: String a ser verificada
        
    Returns:
        True se a string é válida, False caso contrário
    """
    valor_limpo = limpar_string(valor)
    return valor_limpo != '' and valor_limpo.lower() not in ['nan', 'none', 'null']

def consolidar_bases_para_json(caminho_colaboradores: str, caminho_configuracoes: str = None, 
                               caminho_saida: str = None, debug_mode: bool = False) -> str:
    """
    Consolida todas as bases Excel em um único JSON estruturado.
    
    Args:
        caminho_colaboradores: Caminho para pasta com arquivos de colaboradores
        caminho_configuracoes: Caminho para pasta com configurações (opcional)  
        caminho_saida: Caminho para salvar o JSON (apenas se debug_mode=True)
        debug_mode: Se True, salva arquivo físico; se False, apenas retorna JSON em memória
    
    Returns:
        String JSON com todos os dados consolidados
    """
    modo = "DEBUG" if debug_mode else "PRODUÇÃO"
    log_inicio_passo("CONSOLIDAÇÃO", f"Consolidação de Bases - Modo {modo}", logger)
    
    # Estrutura base dos dados
    dados_consolidados = {
        "metadata": {
            "gerado_em": datetime.now().isoformat(),
            "modo": modo,
            "versao": "1.0"
        },
        "colaboradores": {},
        "sindicatos": {},
        "valores_por_estado": {},
        "dias_uteis_por_sindicato": {},
        "estatisticas": {}
    }
    
    # === 1. CARREGAR COLABORADORES ATIVOS ===
    logger.info("👥 Carregando colaboradores ativos...")
    ativos_path = os.path.join(caminho_colaboradores, 'ATIVOS.xlsx')
    if os.path.exists(ativos_path):
        df_ativos = pd.read_excel(ativos_path)
        colaboradores_validos = 0
        total_linhas = len(df_ativos)
        
        for idx, row in df_ativos.iterrows():
            if (idx + 1) % 100 == 0:  # Log a cada 100 registros
                log_processamento("colaboradores ativos", idx + 1, total_linhas, logger=logger)
            
            matricula = limpar_string(row.get('matricula', ''))
            
            # Pular linhas com matrícula inválida
            if not is_valid_string(matricula):
                continue
    
    # Se não foi especificada pasta de configurações, usar a mesma de colaboradores
    if caminho_configuracoes is None:
        caminho_configuracoes = caminho_colaboradores
    
    # Dicionário principal que conterá todos os dados consolidados
    dados_consolidados = {
        "metadata": {
            "data_processamento": datetime.now().isoformat(),
            "versao": "1.0",
            "descricao": "Base consolidada de funcionários e regras de VR",
            "modo_execucao": modo
        },
        "colaboradores": {},
        "sindicatos": {},
        "valores_por_estado": {},
        "dias_uteis_por_sindicato": {},
        "estatisticas": {}
    }
    
    # === 1. CARREGAR BASE DE ATIVOS ===
    logger.info("👥 Carregando colaboradores ativos...")
    ativos_path = os.path.join(caminho_colaboradores, 'ATIVOS.xlsx')
    if os.path.exists(ativos_path):
        df_ativos = pd.read_excel(ativos_path)
        colaboradores_validos = 0
        for _, row in df_ativos.iterrows():
            matricula = limpar_string(row.get('matricula', ''))
            
            # Pular linhas com matrícula inválida
            if not is_valid_string(matricula):
                continue
                
            dados_consolidados["colaboradores"][matricula] = {
                "matricula": matricula,
                "empresa": limpar_string(row.get('empresa', '')),
                "cargo": limpar_string(row.get('cargo', '')),
                "situacao": limpar_string(row.get('situacao', '')),
                "sindicato": limpar_string(row.get('sindicato', '')),
                "status": "ativo",
                "admissao": None,
                "demissao": None,
                "ferias": None
            }
            colaboradores_validos += 1
        
        logger.info(f"✅ {colaboradores_validos} colaboradores ativos carregados de {total_linhas} linhas")
    else:
        logger.warning("⚠️  Arquivo ATIVOS.xlsx não encontrado")
    
    # === 2. CARREGAR ADMISSÕES DO MÊS ===
    logger.info("📅 Processando admissões do mês...")
    admissoes_path = os.path.join(caminho_colaboradores, 'ADMISSÃO ABRIL.xlsx')
    if os.path.exists(admissoes_path):
        df_admissoes = pd.read_excel(admissoes_path)
        admissoes_validas = 0
        for _, row in df_admissoes.iterrows():
            matricula = limpar_string(row.get('matricula', ''))
            
            # Pular linhas com matrícula inválida
            if not is_valid_string(matricula):
                continue
                
            if matricula not in dados_consolidados["colaboradores"]:
                dados_consolidados["colaboradores"][matricula] = {
                    "matricula": matricula,
                    "empresa": '',
                    "cargo": limpar_string(row.get('cargo', '')),
                    "situacao": limpar_string(row.get('situacao', '')),
                    "sindicato": '',
                    "status": "admitido_mes",
                    "admissao": None,
                    "demissao": None,
                    "ferias": None
                }
            
            # Atualizar data de admissão
            if pd.notna(row.get('admissao')):
                dados_consolidados["colaboradores"][matricula]["admissao"] = row['admissao'].isoformat() if hasattr(row['admissao'], 'isoformat') else str(row['admissao'])
            
            admissoes_validas += 1
        
        logger.info(f"✅ {admissoes_validas} admissões válidas processadas")
    else:
        logger.warning("⚠️  Arquivo ADMISSÃO ABRIL.xlsx não encontrado")
    
    # === 3. CARREGAR DESLIGADOS ===
    logger.info("📋 Processando colaboradores desligados...")
    desligados_path = os.path.join(caminho_colaboradores, 'DESLIGADOS.xlsx')
    if os.path.exists(desligados_path):
        df_desligados = pd.read_excel(desligados_path)
        desligados_validos = 0
        for _, row in df_desligados.iterrows():
            matricula = limpar_string(row.get('matricula', ''))
            
            # Pular linhas com matrícula inválida
            if not is_valid_string(matricula):
                continue
                
            # Para desligados, sempre definir comunicado como "OK"
            comunicado_desligamento = "OK"
            
            if matricula in dados_consolidados["colaboradores"]:
                dados_consolidados["colaboradores"][matricula]["status"] = "desligado"
                if pd.notna(row.get('demissao data')):
                    dados_consolidados["colaboradores"][matricula]["demissao"] = row['demissao data'].isoformat() if hasattr(row['demissao data'], 'isoformat') else str(row['demissao data'])
                dados_consolidados["colaboradores"][matricula]["comunicado_desligamento"] = comunicado_desligamento
            else:
                # Adicionar colaborador desligado que não estava na base de ativos
                dados_consolidados["colaboradores"][matricula] = {
                    "matricula": matricula,
                    "empresa": '',
                    "cargo": '',
                    "situacao": '',
                    "sindicato": '',
                    "status": "desligado",
                    "admissao": None,
                    "demissao": row['demissao data'].isoformat() if pd.notna(row.get('demissao data')) and hasattr(row['demissao data'], 'isoformat') else str(row.get('demissao data', '')),
                    "ferias": None,
                    "comunicado_desligamento": comunicado_desligamento
                }
            desligados_validos += 1
        
        logger.info(f"✅ {desligados_validos} desligamentos válidos processados")
    
    # === 4. CARREGAR FÉRIAS ===
    logger.info("🏖️ Processando informações de férias...")
    ferias_path = os.path.join(caminho_colaboradores, 'FÉRIAS.xlsx')
    if os.path.exists(ferias_path):
        df_ferias = pd.read_excel(ferias_path)
        for _, row in df_ferias.iterrows():
            matricula = str(row['matricula'])
            if matricula in dados_consolidados["colaboradores"]:
                dados_consolidados["colaboradores"][matricula]["ferias"] = {
                    "situacao": row.get('situacao', ''),
                    "dias_ferias": row.get('dias de férias', 0)
                }
        
        logger.info(f"✅ {len(df_ferias)} registros de férias processados")
    
    # === 5. CARREGAR VALORES POR ESTADO ===
    logger.info("💰 Carregando valores de VR por estado...")
    valores_path = os.path.join(caminho_configuracoes, 'Base sindicato x valor.xlsx')
    if os.path.exists(valores_path):
        df_valores = pd.read_excel(valores_path)
        estados_validos = 0
        for _, row in df_valores.iterrows():
            estado = limpar_string(row.get('estado', ''))
            valor = row.get('valor', 0)
            
            # Filtrar linhas vazias ou inválidas
            if not is_valid_string(estado) or pd.isna(valor):
                continue
                
            dados_consolidados["valores_por_estado"][estado] = valor
            estados_validos += 1
        
        logger.info(f"✅ {estados_validos} estados com valores válidos carregados")
    
    # === 6. CARREGAR DIAS ÚTEIS POR SINDICATO ===
    logger.info("📅 Carregando dias úteis por sindicato...")
    dias_uteis_path = os.path.join(caminho_configuracoes, 'Base dias uteis.xlsx')
    if os.path.exists(dias_uteis_path):
        df_dias = pd.read_excel(dias_uteis_path)
        sindicatos_validos = 0
        for _, row in df_dias.iterrows():
            sindicato = limpar_string(row.get('sindicato', ''))
            dias = row.get('dias uteis', 0)
            
            # Filtrar linhas vazias ou inválidas
            if not is_valid_string(sindicato) or pd.isna(dias):
                continue
                
            dados_consolidados["dias_uteis_por_sindicato"][sindicato] = dias
            sindicatos_validos += 1
        
        logger.info(f"✅ {sindicatos_validos} sindicatos com dias úteis válidos carregados")
    
    # === 7. PROCESSAR OUTROS TIPOS DE COLABORADORES ===
    outros_arquivos = ['ESTÁGIO.xlsx', 'APRENDIZ.xlsx', 'EXTERIOR.xlsx']
    for arquivo in outros_arquivos:
        caminho = os.path.join(caminho_colaboradores, arquivo)
        if os.path.exists(caminho):
            logger.info(f"📄 Processando {arquivo}...")
            df = pd.read_excel(caminho)
            tipo_colaborador = arquivo.replace('.xlsx', '').lower()
            
            for _, row in df.iterrows():
                matricula = str(row.get('matricula', ''))
                if matricula and matricula not in dados_consolidados["colaboradores"]:
                    dados_consolidados["colaboradores"][matricula] = {
                        "matricula": matricula,
                        "empresa": row.get('empresa', ''),
                        "cargo": row.get('cargo', ''),
                        "situacao": row.get('situacao', ''),
                        "sindicato": row.get('sindicato', ''),
                        "status": tipo_colaborador,
                        "admissao": None,
                        "demissao": None,
                        "ferias": None
                    }
    
    # === 8. EXTRAIR SINDICATOS ÚNICOS ===
    sindicatos_encontrados = set()
    for colaborador in dados_consolidados["colaboradores"].values():
        if colaborador["sindicato"]:
            sindicatos_encontrados.add(colaborador["sindicato"])
    
    for sindicato in sindicatos_encontrados:
        dados_consolidados["sindicatos"][sindicato] = {
            "nome": sindicato,
            "colaboradores_count": sum(1 for c in dados_consolidados["colaboradores"].values() if c["sindicato"] == sindicato),
            "dias_uteis": dados_consolidados["dias_uteis_por_sindicato"].get(sindicato, 0)
        }
    
    # === 9. GERAR ESTATÍSTICAS ===
    logger.info("📊 Gerando estatísticas finais...")
    total_colaboradores = len(dados_consolidados["colaboradores"])
    ativos = sum(1 for c in dados_consolidados["colaboradores"].values() if c["status"] == "ativo")
    desligados = sum(1 for c in dados_consolidados["colaboradores"].values() if c["status"] == "desligado")
    admitidos = sum(1 for c in dados_consolidados["colaboradores"].values() if c["status"] == "admitido_mes")
    em_ferias = sum(1 for c in dados_consolidados["colaboradores"].values() if c["ferias"] is not None)
    
    dados_consolidados["estatisticas"] = {
        "total_colaboradores": total_colaboradores,
        "ativos": ativos,
        "desligados": desligados,
        "admitidos_mes": admitidos,
        "em_ferias": em_ferias,
        "total_sindicatos": len(dados_consolidados["sindicatos"]),
        "total_estados": len(dados_consolidados["valores_por_estado"])
    }
    
    # === 10. CONVERTER PARA JSON ===
    logger.info("🔄 Convertendo para JSON...")
    json_resultado = json.dumps(dados_consolidados, indent=2, ensure_ascii=False, default=str)
    
    # === 11. SALVAR ARQUIVO APENAS SE DEBUG_MODE ===
    if debug_mode and caminho_saida:
        logger.info(f"💾 Salvando arquivo em modo DEBUG: {caminho_saida}")
        # Criar diretório apenas se necessário
        pasta_destino = os.path.dirname(caminho_saida)
        if pasta_destino:  # Se há uma pasta no caminho
            os.makedirs(pasta_destino, exist_ok=True)
        
        with open(caminho_saida, 'w', encoding='utf-8') as f:
            f.write(json_resultado)
        logger.info(f"✅ Arquivo JSON salvo: {caminho_saida}")
    elif debug_mode:
        logger.warning("⚠️  Modo DEBUG ativado mas caminho de saída não especificado")
    else:
        logger.info("💾 Dados consolidados mantidos em memória (Modo Produção)")
    
    # Estatísticas finais
    estatisticas = {
        'total_colaboradores': total_colaboradores,
        'ativos': ativos,
        'desligados': desligados,
        'admitidos_mes': admitidos,
        'em_ferias': em_ferias,
        'total_sindicatos': len(dados_consolidados['sindicatos'])
    }
    
    log_fim_passo("CONSOLIDAÇÃO", f"Consolidação de Bases - Modo {modo}", estatisticas, logger)
    
    return json_resultado

def obter_dados_consolidados(caminho_colaboradores: str, caminho_configuracoes: str = None) -> dict:
    """
    Obtém os dados consolidados em formato de dicionário Python (sem conversão para JSON).
    Ideal para acessar os dados em memória diretamente.
    
    Args:
        caminho_colaboradores: Caminho para a pasta com dados de colaboradores
        caminho_configuracoes: Caminho para a pasta com as configurações (opcional)
        
    Returns:
        Dict com todos os dados consolidados estruturados
    """
    logger.info("📥 CARREGANDO DADOS EM MEMÓRIA")
    
    # Reutiliza a lógica da função principal, mas retorna o dicionário diretamente
    json_str = consolidar_bases_para_json(
        caminho_colaboradores=caminho_colaboradores,
        caminho_configuracoes=caminho_configuracoes,
        debug_mode=False  # Sempre em modo produção para não salvar arquivos
    )
    
    # Converter de volta para dicionário
    dados = json.loads(json_str)
    logger.info("✅ Dados carregados em memória com sucesso!")
    return dados

def buscar_colaborador(dados: dict, matricula: str) -> dict:
    """
    Busca um colaborador específico pelos dados consolidados em memória.
    
    Args:
        dados: Dicionário com dados consolidados (obtido via obter_dados_consolidados)
        matricula: Matrícula do colaborador
        
    Returns:
        Dict com dados do colaborador ou None se não encontrado
    """
    return dados.get("colaboradores", {}).get(str(matricula))

def listar_colaboradores_por_status(dados: dict, status: str) -> list:
    """
    Lista colaboradores por status específico.
    
    Args:
        dados: Dicionário com dados consolidados
        status: Status desejado ('ativo', 'desligado', 'admitido_mes', etc.)
        
    Returns:
        Lista de colaboradores com o status especificado
    """
    colaboradores = dados.get("colaboradores", {})
    return [colab for colab in colaboradores.values() if colab.get("status") == status]

def obter_estatisticas(dados: dict) -> dict:
    """
    Extrai as estatísticas dos dados consolidados.
    
    Args:
        dados: Dicionário com dados consolidados
        
    Returns:
        Dict com estatísticas detalhadas
    """
    return dados.get("estatisticas", {})

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Consolidar bases de dados em JSON')
    parser.add_argument('--colaboradores', required=True, help='Caminho para a pasta com dados de colaboradores')
    parser.add_argument('--configuracoes', help='Caminho para a pasta com configurações (opcional)')
    parser.add_argument('--saida', help='Caminho para salvar o JSON (apenas se --debug)')
    parser.add_argument('--debug', action='store_true', help='Ativar modo DEBUG (salvar arquivos JSON)')
    
    args = parser.parse_args()
    
    # Verificar se variável de ambiente DEBUG está definida
    debug_env = os.getenv('DEBUG', '').lower() in ['true', '1', 'yes', 'on']
    debug_mode = args.debug or debug_env
    
    try:
        json_resultado = consolidar_bases_para_json(args.colaboradores, args.configuracoes, args.saida, debug_mode)
        if not debug_mode:
            logger.info("="*50)
            logger.info("DADOS CONSOLIDADOS MANTIDOS EM MEMÓRIA")
            logger.info("Para salvar em arquivo, use --debug ou defina DEBUG=true")
            logger.info("="*50)
    except Exception as e:
        logger.error(f"❌ Erro durante a consolidação: {e}")
        sys.exit(1)


class OrquestradorPasso1:
    """Classe para orquestrar todo o processo do Passo 1."""
    
    def __init__(self, pasta_colaboradores: str, pasta_configuracoes: str = None, pasta_output: str = "./output"):
        self.pasta_colaboradores = pasta_colaboradores
        self.pasta_configuracoes = pasta_configuracoes or pasta_colaboradores
        self.pasta_output = pasta_output
        self.json_consolidado = None
        
    def executar_processo_completo(self, modo_debug: bool = False) -> Dict[str, Any]:
        """
        Executa o processo completo do Passo 1.
        
        Args:
            modo_debug: Se True, salva arquivos JSON; se False, mantém apenas em memória
            
        Returns:
            Dict com status do processo e estatísticas
        """
        try:
            # Executar consolidação
            caminho_arquivo = None
            if modo_debug:
                caminho_arquivo = os.path.join(self.pasta_output, "passo_1-base_consolidada.json")
            
            self.json_consolidado = consolidar_bases_para_json(
                self.pasta_colaboradores, 
                self.pasta_configuracoes, 
                caminho_arquivo,
                modo_debug
            )
            
            # Parsear dados para extrair estatísticas
            dados = json.loads(self.json_consolidado)
            estatisticas = dados.get('estatisticas', {})
            
            return {
                'status': 'SUCESSO',
                'total_colaboradores': estatisticas.get('total_colaboradores', 0),
                'estatisticas': estatisticas
            }
            
        except Exception as e:
            return {
                'status': 'ERRO',
                'erro': str(e)
            }
    
    def extrair_dados_para_llm(self) -> Dict[str, Any]:
        """
        Extrai dados consolidados no formato específico para LLM.
        
        Returns:
            Dict com dados estruturados para análise LLM
        """
        if not self.json_consolidado:
            raise ValueError("Dados consolidados não disponíveis. Execute o processo primeiro.")
        
        dados = json.loads(self.json_consolidado)
        
        # Extrair cargos únicos para análise LLM
        colaboradores_dict = dados.get('colaboradores', {})
        cargos_consolidados = {}
        
        # Iterar sobre os valores do dicionário de colaboradores
        for matricula, colab in colaboradores_dict.items():
            cargo = colab.get('cargo', '').strip()
            if cargo and cargo not in cargos_consolidados:
                cargos_consolidados[cargo] = {
                    'cargo': cargo,
                    'colaboradores': []
                }
            
            if cargo:
                cargos_consolidados[cargo]['colaboradores'].append({
                    'nome': colab.get('nome', matricula),  # usar matrícula se nome não existir
                    'sindicato': colab.get('sindicato', ''),
                    'status': colab.get('status', ''),
                    'salario': colab.get('salario', 0)
                })
        
        return {
            'cargos_consolidados': list(cargos_consolidados.values()),
            'total_cargos': len(cargos_consolidados),
            'gerado_em': datetime.now().isoformat()
        }
