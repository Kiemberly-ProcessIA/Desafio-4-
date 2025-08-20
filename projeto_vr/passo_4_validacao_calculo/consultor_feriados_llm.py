#!/usr/bin/env python3
"""
Consultor de Feriados via LLM - Passo 4
Usa LLM para obter informações dinâmicas sobre feriados e dias úteis por estado.
"""

import json
import logging
import sys
from datetime import date, datetime
from typing import Dict, List, Set, Optional
import requests
from pathlib import Path

# Adicionar o diretório do projeto ao path
projeto_root = Path(__file__).parent.parent.parent
sys.path.append(str(projeto_root))

# Importar configurações da raiz do projeto
from config import GOOGLE_API_KEY, NOME_MODELO_LLM

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultorFeriadosLLM:
    """Classe para consultar feriados usando LLM."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Inicializa o consultor de feriados via LLM.
        
        Args:
            api_key: Chave da API do LLM (usa GOOGLE_API_KEY se não fornecida)
            model: Modelo do LLM a usar (usa NOME_MODELO_LLM se não fornecido)
        """
        self.api_key = api_key or GOOGLE_API_KEY
        self.model_name = model or NOME_MODELO_LLM
        self.cache_feriados = {}
        
        # Configurar cliente Gemini
        if genai is not None:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Cliente Gemini inicializado: {self.model_name}")
            except Exception as e:
                logger.error(f"Erro ao inicializar Gemini: {e}")
                self.model = None
        else:
            logger.warning("Pacote google-generativeai não encontrado. Usando modo fallback.")
            self.model = None
        
        # URLs de APIs públicas de feriados como fallback
        self.apis_feriados = {
            'brasil': 'https://date.nager.at/api/v3/publicholidays/2025/BR',
            'brasilapi': 'https://brasilapi.com.br/api/feriados/v1/2025'
        }
    
    def consultar_feriados_llm(self, estado: str, ano: int = 2025) -> Dict:
        """
        Consulta o LLM para obter feriados específicos do estado.
        
        Args:
            estado: Nome do estado
            ano: Ano de referência
            
        Returns:
            Dicionário com informações de feriados
        """
        cache_key = f"{estado}_{ano}"
        if cache_key in self.cache_feriados:
            return self.cache_feriados[cache_key]
        
        prompt = f"""
        Como especialista em legislação trabalhista brasileira, forneça informações sobre feriados para o estado de {estado} em {ano}.

        Preciso das seguintes informações:
        1. Lista completa de feriados NACIONAIS que se aplicam ao estado
        2. Lista de feriados ESTADUAIS específicos do {estado}
        3. Lista de feriados MUNICIPAIS da capital do {estado}
        4. Número total de dias úteis no período de 15 de abril de {ano} a 15 de maio de {ano}
        5. Valor atual do vale-refeição/alimentação por convenção coletiva no {estado}

        Considere:
        - Feriados que caem em fins de semana
        - Pontes e emendas oficiais
        - Convenções coletivas vigentes
        - Calendário de dias úteis comerciais

        Formato da resposta em JSON:
        {{
            "estado": "{estado}",
            "ano": {ano},
            "feriados_nacionais": [
                {{"data": "YYYY-MM-DD", "nome": "Nome do Feriado", "tipo": "nacional"}}
            ],
            "feriados_estaduais": [
                {{"data": "YYYY-MM-DD", "nome": "Nome do Feriado", "tipo": "estadual"}}
            ],
            "feriados_municipais": [
                {{"data": "YYYY-MM-DD", "nome": "Nome do Feriado", "tipo": "municipal"}}
            ],
            "dias_uteis_periodo": {{
                "inicio": "2025-04-15",
                "fim": "2025-05-15",
                "total_dias_uteis": 0,
                "feriados_no_periodo": []
            }},
            "valor_vr_vigente": {{
                "valor": 0.0,
                "moeda": "BRL",
                "base_legal": "Convenção Coletiva ou Lei",
                "vigencia": "YYYY-MM-DD"
            }}
        }}
        """
        
        try:
            # Tentar usar LLM real se disponível
            if self.model:
                resultado = self._consultar_gemini(prompt)
            else:
                # Fallback: usar APIs públicas + heurísticas
                resultado = self._consultar_apis_publicas(estado, ano)
            
            self.cache_feriados[cache_key] = resultado
            return resultado
            
        except Exception as e:
            logger.error(f"Erro ao consultar feriados para {estado}: {e}")
            return self._obter_feriados_padrao(estado, ano)
    
    def _consultar_gemini(self, prompt: str) -> Dict:
        """Consulta o Google Gemini."""
        try:
            logger.info(f"Consultando Gemini ({self.model_name})...")
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Tentar extrair JSON da resposta
                content = response.text
                try:
                    # Procurar JSON na resposta
                    start_json = content.find('{')
                    end_json = content.rfind('}') + 1
                    if start_json >= 0 and end_json > start_json:
                        json_content = content[start_json:end_json]
                        resultado = json.loads(json_content)
                        logger.info("JSON extraído com sucesso do Gemini")
                        return resultado
                except json.JSONDecodeError as e:
                    logger.warning(f"Erro ao parsear JSON do Gemini: {e}")
                
                # Se não conseguiu parsear JSON, usar fallback
                logger.warning("Gemini não retornou JSON válido, processando resposta texto")
                return self._processar_resposta_texto(content)
            else:
                raise Exception("Gemini não retornou resposta válida")
                
        except Exception as e:
            logger.error(f"Erro na consulta Gemini: {e}")
            raise
    
    def _processar_resposta_texto(self, texto: str) -> Dict:
        """Processa resposta em texto quando não consegue extrair JSON."""
        logger.info("Processando resposta em texto...")
        # Implementação básica - retorna dados padrão
        return self._obter_feriados_padrao("São Paulo", 2025)
    
    def _consultar_apis_publicas(self, estado: str, ano: int) -> Dict:
        """Consulta APIs públicas de feriados como fallback."""
        feriados_nacionais = []
        
        # Tentar APIs públicas
        for api_name, url in self.apis_feriados.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for feriado in data:
                        if api_name == 'brasil':
                            feriados_nacionais.append({
                                "data": feriado.get('date', ''),
                                "nome": feriado.get('name', ''),
                                "tipo": "nacional"
                            })
                        elif api_name == 'brasilapi':
                            feriados_nacionais.append({
                                "data": feriado.get('date', ''),
                                "nome": feriado.get('name', ''),
                                "tipo": "nacional"
                            })
                    break
            except Exception as e:
                logger.warning(f"Erro ao consultar API {api_name}: {e}")
                continue
        
        # Complementar com dados conhecidos específicos do estado
        feriados_estaduais = self._obter_feriados_estaduais_conhecidos(estado)
        feriados_municipais = self._obter_feriados_municipais_conhecidos(estado)
        
        # Calcular dias úteis usando lógica própria
        dias_uteis_info = self._calcular_dias_uteis_periodo(
            date(2025, 4, 15), 
            date(2025, 5, 15), 
            feriados_nacionais + feriados_estaduais + feriados_municipais
        )
        
        # Obter valor VR conhecido
        valor_vr = self._obter_valor_vr_conhecido(estado)
        
        return {
            "estado": estado,
            "ano": ano,
            "feriados_nacionais": feriados_nacionais,
            "feriados_estaduais": feriados_estaduais,
            "feriados_municipais": feriados_municipais,
            "dias_uteis_periodo": dias_uteis_info,
            "valor_vr_vigente": valor_vr
        }
    
    def _obter_feriados_estaduais_conhecidos(self, estado: str) -> List[Dict]:
        """Retorna feriados estaduais conhecidos."""
        feriados_por_estado = {
            'São Paulo': [
                {"data": "2025-07-09", "nome": "Revolução Constitucionalista", "tipo": "estadual"}
            ],
            'Rio de Janeiro': [
                {"data": "2025-04-23", "nome": "São Jorge", "tipo": "estadual"},
                {"data": "2025-10-28", "nome": "Dia do Funcionário Público", "tipo": "estadual"},
                {"data": "2025-11-20", "nome": "Zumbi dos Palmares", "tipo": "estadual"}
            ],
            'Rio Grande do Sul': [
                {"data": "2025-09-20", "nome": "Revolução Farroupilha", "tipo": "estadual"}
            ],
            'Paraná': [
                {"data": "2025-12-19", "nome": "Emancipação do Paraná", "tipo": "estadual"}
            ]
        }
        return feriados_por_estado.get(estado, [])
    
    def _obter_feriados_municipais_conhecidos(self, estado: str) -> List[Dict]:
        """Retorna feriados municipais das capitais."""
        feriados_municipais = {
            'São Paulo': [
                {"data": "2025-01-25", "nome": "Aniversário de São Paulo", "tipo": "municipal"}
            ],
            'Rio de Janeiro': [
                {"data": "2025-03-01", "nome": "Aniversário do Rio de Janeiro", "tipo": "municipal"}
            ],
            'Rio Grande do Sul': [
                {"data": "2025-03-26", "nome": "Aniversário de Porto Alegre", "tipo": "municipal"}
            ],
            'Paraná': [
                {"data": "2025-03-29", "nome": "Aniversário de Curitiba", "tipo": "municipal"}
            ]
        }
        return feriados_municipais.get(estado, [])
    
    def _calcular_dias_uteis_periodo(self, data_inicio: date, data_fim: date, feriados: List[Dict]) -> Dict:
        """Calcula dias úteis no período considerando feriados."""
        from datetime import timedelta
        
        # Converter feriados para set de datas
        datas_feriados = set()
        for feriado in feriados:
            try:
                data_feriado = datetime.strptime(feriado['data'], '%Y-%m-%d').date()
                if data_inicio <= data_feriado <= data_fim:
                    datas_feriados.add(data_feriado)
            except (ValueError, KeyError):
                continue
        
        # Contar dias úteis
        dias_uteis = 0
        data_atual = data_inicio
        feriados_no_periodo = []
        
        while data_atual <= data_fim:
            # Verificar se é dia da semana (seg-sex) e não é feriado
            if data_atual.weekday() < 5:  # 0-4 = segunda a sexta
                if data_atual not in datas_feriados:
                    dias_uteis += 1
                else:
                    # Encontrar o feriado
                    for feriado in feriados:
                        try:
                            if datetime.strptime(feriado['data'], '%Y-%m-%d').date() == data_atual:
                                feriados_no_periodo.append(feriado)
                                break
                        except (ValueError, KeyError):
                            continue
            
            data_atual += timedelta(days=1)
        
        return {
            "inicio": data_inicio.strftime('%Y-%m-%d'),
            "fim": data_fim.strftime('%Y-%m-%d'),
            "total_dias_uteis": dias_uteis,
            "feriados_no_periodo": feriados_no_periodo
        }
    
    def _obter_valor_vr_conhecido(self, estado: str) -> Dict:
        """Retorna valores de VR conhecidos por estado."""
        valores_conhecidos = {
            'São Paulo': {"valor": 37.5, "moeda": "BRL", "base_legal": "Convenção Coletiva SINDPD-SP", "vigencia": "2025-01-01"},
            'Rio de Janeiro': {"valor": 35.0, "moeda": "BRL", "base_legal": "Convenção Coletiva SINDPD-RJ", "vigencia": "2025-01-01"},
            'Rio Grande do Sul': {"valor": 35.0, "moeda": "BRL", "base_legal": "Convenção Coletiva SINDPPD-RS", "vigencia": "2025-01-01"},
            'Paraná': {"valor": 35.0, "moeda": "BRL", "base_legal": "Convenção Coletiva SITEPD-PR", "vigencia": "2025-01-01"}
        }
        return valores_conhecidos.get(estado, {"valor": 35.0, "moeda": "BRL", "base_legal": "Padrão Nacional", "vigencia": "2025-01-01"})
    
    def _obter_feriados_padrao(self, estado: str, ano: int) -> Dict:
        """Retorna feriados padrão quando não consegue consultar APIs."""
        logger.warning(f"Usando feriados padrão para {estado}")
        
        # Feriados nacionais básicos de 2025
        feriados_nacionais = [
            {"data": "2025-01-01", "nome": "Confraternização Universal", "tipo": "nacional"},
            {"data": "2025-03-03", "nome": "Carnaval", "tipo": "nacional"},
            {"data": "2025-03-04", "nome": "Carnaval", "tipo": "nacional"},
            {"data": "2025-04-18", "nome": "Paixão de Cristo", "tipo": "nacional"},
            {"data": "2025-04-21", "nome": "Tiradentes", "tipo": "nacional"},
            {"data": "2025-05-01", "nome": "Dia do Trabalhador", "tipo": "nacional"},
            {"data": "2025-06-19", "nome": "Corpus Christi", "tipo": "nacional"},
            {"data": "2025-09-07", "nome": "Independência do Brasil", "tipo": "nacional"},
            {"data": "2025-10-12", "nome": "Nossa Senhora Aparecida", "tipo": "nacional"},
            {"data": "2025-11-02", "nome": "Finados", "tipo": "nacional"},
            {"data": "2025-11-15", "nome": "Proclamação da República", "tipo": "nacional"},
            {"data": "2025-12-25", "nome": "Natal", "tipo": "nacional"}
        ]
        
        feriados_estaduais = self._obter_feriados_estaduais_conhecidos(estado)
        feriados_municipais = self._obter_feriados_municipais_conhecidos(estado)
        
        todos_feriados = feriados_nacionais + feriados_estaduais + feriados_municipais
        
        dias_uteis_info = self._calcular_dias_uteis_periodo(
            date(2025, 4, 15),
            date(2025, 5, 15),
            todos_feriados
        )
        
        valor_vr = self._obter_valor_vr_conhecido(estado)
        
        return {
            "estado": estado,
            "ano": ano,
            "feriados_nacionais": feriados_nacionais,
            "feriados_estaduais": feriados_estaduais,
            "feriados_municipais": feriados_municipais,
            "dias_uteis_periodo": dias_uteis_info,
            "valor_vr_vigente": valor_vr
        }
    
    def obter_informacoes_estado(self, estado: str) -> Dict:
        """
        Método principal para obter todas as informações de um estado.
        
        Args:
            estado: Nome do estado
            
        Returns:
            Dicionário com todas as informações necessárias
        """
        logger.info(f"Consultando informações para o estado: {estado}")
        return self.consultar_feriados_llm(estado, 2025)
    
    def salvar_cache(self, arquivo: str = "cache_feriados_llm.json"):
        """Salva o cache de consultas em arquivo."""
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(self.cache_feriados, f, indent=2, ensure_ascii=False)
            logger.info(f"Cache salvo em: {arquivo}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def carregar_cache(self, arquivo: str = "cache_feriados_llm.json"):
        """Carrega cache de consultas anteriores."""
        try:
            if Path(arquivo).exists():
                with open(arquivo, 'r', encoding='utf-8') as f:
                    self.cache_feriados = json.load(f)
                logger.info(f"Cache carregado de: {arquivo}")
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")


def criar_consultor_feriados(api_key: str = None, model: str = None) -> ConsultorFeriadosLLM:
    """
    Factory function para criar consultor de feriados.
    
    Args:
        api_key: Chave da API Gemini (opcional, usa GOOGLE_API_KEY se não fornecida)
        model: Modelo Gemini (opcional, usa NOME_MODELO_LLM se não fornecido)
        
    Returns:
        Instância do ConsultorFeriadosLLM
    """
    consultor = ConsultorFeriadosLLM(api_key, model)
    consultor.carregar_cache()  # Carregar cache existente
    
    return consultor


if __name__ == "__main__":
    # Teste do sistema
    print("🧪 TESTANDO CONSULTOR DE FERIADOS VIA LLM")
    print("=" * 50)
    
    consultor = criar_consultor_feriados()
    
    estados_teste = ['São Paulo', 'Rio de Janeiro', 'Rio Grande do Sul', 'Paraná']
    
    for estado in estados_teste:
        print(f"\n📍 {estado}:")
        try:
            info = consultor.obter_informacoes_estado(estado)
            
            print(f"  Dias úteis (15/04 a 15/05): {info['dias_uteis_periodo']['total_dias_uteis']}")
            print(f"  Valor VR: R$ {info['valor_vr_vigente']['valor']:.2f}")
            print(f"  Feriados estaduais: {len(info['feriados_estaduais'])}")
            
            feriados_periodo = info['dias_uteis_periodo']['feriados_no_periodo']
            if feriados_periodo:
                print(f"  Feriados no período:")
                for feriado in feriados_periodo:
                    print(f"    - {feriado['data']}: {feriado['nome']}")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")
    
    # Salvar cache
    consultor.salvar_cache()
    print(f"\n✅ Teste concluído. Cache salvo.")
