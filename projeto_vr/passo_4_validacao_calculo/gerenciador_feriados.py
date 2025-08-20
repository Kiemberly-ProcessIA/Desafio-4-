#!/usr/bin/env python3
"""
Módulo de Feriados - Passo 4
Responsável por gerenciar feriados estaduais e municipais para cálculo correto de dias úteis.
Usa consultor LLM para obter informações dinâmicas de feriados.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Set, Optional
import logging
import json
import os
import sys
from pathlib import Path

# Adicionar o diretório do projeto ao path
projeto_root = Path(__file__).parent.parent.parent
sys.path.append(str(projeto_root))

# Importar configurações da raiz do projeto
from config import GOOGLE_API_KEY, NOME_MODELO_LLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GerenciadorFeriados:
    """Classe para gerenciar feriados nacionais, estaduais e municipais usando LLM."""
    
    def __init__(self, usar_llm: bool = True, api_key: str = None, model: str = None):
        """
        Inicializa o gerenciador de feriados.
        
        Args:
            usar_llm: Se deve usar consultor LLM ou dados estáticos
            api_key: Chave da API Gemini (opcional, usa GOOGLE_API_KEY se não fornecida)
            model: Modelo Gemini (opcional, usa NOME_MODELO_LLM se não fornecido)
        """
        self.usar_llm = usar_llm
        self.api_key = api_key or GOOGLE_API_KEY
        self.model = model or NOME_MODELO_LLM
        self.cache_informacoes = {}
        
        # Inicializar consultor LLM se disponível
        if self.usar_llm:
            try:
                from .consultor_feriados_llm import criar_consultor_feriados
                self.consultor_llm = criar_consultor_feriados(self.api_key, self.model)
                logger.info(f"Consultor LLM inicializado com sucesso ({self.model})")
            except ImportError as e:
                logger.warning(f"Não foi possível importar consultor LLM: {e}")
                self.usar_llm = False
                self.consultor_llm = None
            except Exception as e:
                logger.warning(f"Erro ao inicializar consultor LLM: {e}")
                self.usar_llm = False
                self.consultor_llm = None
        else:
            self.consultor_llm = None
        
        # Fallback para dados estáticos
        if not self.usar_llm:
            self.feriados_nacionais = self._definir_feriados_nacionais_2025()
            self.feriados_estaduais = self._definir_feriados_estaduais_2025()
            self.feriados_municipais = self._definir_feriados_municipais_2025()
            logger.info("Usando dados estáticos de feriados")
    
    def _definir_feriados_nacionais_2025(self) -> Set[date]:
        """Define feriados nacionais para 2025."""
        feriados = {
            date(2025, 1, 1),   # Confraternização Universal
            date(2025, 4, 18),  # Paixão de Cristo (Sexta-feira Santa)
            date(2025, 4, 21),  # Tiradentes
            date(2025, 5, 1),   # Dia do Trabalhador
            date(2025, 9, 7),   # Independência do Brasil
            date(2025, 10, 12), # Nossa Senhora Aparecida
            date(2025, 11, 2),  # Finados
            date(2025, 11, 15), # Proclamação da República
            date(2025, 12, 25), # Natal
        }
        
        # Adicionar feriados móveis de 2025
        feriados.add(date(2025, 3, 3))   # Carnaval (Segunda-feira)
        feriados.add(date(2025, 3, 4))   # Carnaval (Terça-feira)
        feriados.add(date(2025, 6, 19))  # Corpus Christi
        
        return feriados
    
    def _definir_feriados_estaduais_2025(self) -> Dict[str, Set[date]]:
        """Define feriados estaduais específicos para 2025."""
        return {
            'São Paulo': {
                date(2025, 2, 13),  # Carnaval (data específica SP)
                date(2025, 7, 9),   # Revolução Constitucionalista
            },
            'Rio de Janeiro': {
                date(2025, 4, 23),  # São Jorge
                date(2025, 10, 28), # Dia do Funcionário Público (RJ)
                date(2025, 11, 20), # Zumbi dos Palmares
            },
            'Rio Grande do Sul': {
                date(2025, 9, 20),  # Revolução Farroupilha
            },
            'Paraná': {
                date(2025, 12, 19), # Emancipação do Paraná
            }
        }
    
    def _definir_feriados_municipais_2025(self) -> Dict[str, Set[date]]:
        """Define feriados municipais principais para 2025."""
        return {
            'São Paulo': {
                date(2025, 1, 25),  # Aniversário de São Paulo
            },
            'Rio de Janeiro': {
                date(2025, 3, 1),   # Aniversário do Rio de Janeiro
            },
            'Porto Alegre': {
                date(2025, 3, 26),  # Aniversário de Porto Alegre
            },
            'Curitiba': {
                date(2025, 3, 29),  # Aniversário de Curitiba
            }
        }
    
    def obter_informacoes_estado_llm(self, estado: str) -> Dict:
        """
        Obtém informações completas do estado usando LLM.
        
        Args:
            estado: Nome do estado
            
        Returns:
            Dicionário com informações de feriados, dias úteis e valores
        """
        if estado in self.cache_informacoes:
            logger.info(f"Usando cache para {estado}")
            return self.cache_informacoes[estado]
        
        if self.usar_llm and self.consultor_llm:
            try:
                logger.info(f"Consultando LLM para informações de {estado}")
                info = self.consultor_llm.obter_informacoes_estado(estado)
                self.cache_informacoes[estado] = info
                return info
            except Exception as e:
                logger.error(f"Erro ao consultar LLM para {estado}: {e}")
                return self._obter_informacoes_fallback(estado)
        else:
            return self._obter_informacoes_fallback(estado)
    
    def _obter_informacoes_fallback(self, estado: str) -> Dict:
        """Obtém informações usando dados estáticos como fallback."""
        feriados_nacionais = [
            {"data": f.strftime('%Y-%m-%d'), "nome": self._obter_nome_feriado(f), "tipo": "nacional"}
            for f in self.feriados_nacionais
        ]
        
        feriados_estaduais = [
            {"data": f.strftime('%Y-%m-%d'), "nome": self._obter_nome_feriado(f), "tipo": "estadual"}
            for f in self.feriados_estaduais.get(estado, set())
        ]
        
        feriados_municipais = [
            {"data": f.strftime('%Y-%m-%d'), "nome": self._obter_nome_feriado(f), "tipo": "municipal"}
            for f in self.feriados_municipais.get(self._obter_capital_estado(estado), set())
        ]
        
        # Calcular dias úteis usando método existente
        todos_feriados = self.feriados_nacionais.copy()
        todos_feriados.update(self.feriados_estaduais.get(estado, set()))
        capital = self._obter_capital_estado(estado)
        todos_feriados.update(self.feriados_municipais.get(capital, set()))
        
        periodo_inicio = date(2025, 4, 15)
        periodo_fim = date(2025, 5, 15)
        dias_uteis = self._calcular_dias_uteis_com_feriados(periodo_inicio, periodo_fim, todos_feriados)
        
        # Feriados no período
        feriados_periodo = []
        for feriado_date in todos_feriados:
            if periodo_inicio <= feriado_date <= periodo_fim:
                nome_feriado = self._obter_nome_feriado(feriado_date)
                tipo = "nacional"
                if feriado_date in self.feriados_estaduais.get(estado, set()):
                    tipo = "estadual"
                elif feriado_date in self.feriados_municipais.get(capital, set()):
                    tipo = "municipal"
                
                feriados_periodo.append({
                    "data": feriado_date.strftime('%Y-%m-%d'),
                    "nome": nome_feriado,
                    "tipo": tipo
                })
        
        # Valores conhecidos por estado
        valores_vr = {
            'São Paulo': 37.5,
            'Rio de Janeiro': 35.0,
            'Rio Grande do Sul': 35.0,
            'Paraná': 35.0
        }
        
        return {
            "estado": estado,
            "ano": 2025,
            "feriados_nacionais": feriados_nacionais,
            "feriados_estaduais": feriados_estaduais,
            "feriados_municipais": feriados_municipais,
            "dias_uteis_periodo": {
                "inicio": periodo_inicio.strftime('%Y-%m-%d'),
                "fim": periodo_fim.strftime('%Y-%m-%d'),
                "total_dias_uteis": dias_uteis,
                "feriados_no_periodo": feriados_periodo
            },
            "valor_vr_vigente": {
                "valor": valores_vr.get(estado, 35.0),
                "moeda": "BRL",
                "base_legal": f"Convenção Coletiva {estado}",
                "vigencia": "2025-01-01"
            }
        }
    
    def _calcular_dias_uteis_com_feriados(self, data_inicio: date, data_fim: date, feriados: Set[date]) -> int:
        """Calcula dias úteis considerando conjunto de feriados."""
        if data_fim < data_inicio:
            return 0
        
        dias_uteis = 0
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # Verificar se é dia útil (segunda a sexta) e não é feriado
            if data_atual.weekday() < 5 and data_atual not in feriados:
                dias_uteis += 1
            data_atual += timedelta(days=1)
        
        return dias_uteis
    
    def obter_feriados_estado(self, estado: str) -> Set[date]:
        """
        Obtém todos os feriados para um estado específico.
        
        Args:
            estado: Nome do estado
            
        Returns:
            Conjunto de datas de feriados
        """
        if self.usar_llm:
            try:
                info = self.obter_informacoes_estado_llm(estado)
                feriados = set()
                
                # Converter datas string para objetos date
                for categoria in ['feriados_nacionais', 'feriados_estaduais', 'feriados_municipais']:
                    for feriado in info.get(categoria, []):
                        try:
                            data_feriado = datetime.strptime(feriado['data'], '%Y-%m-%d').date()
                            feriados.add(data_feriado)
                        except (ValueError, KeyError):
                            continue
                
                return feriados
            except Exception as e:
                logger.error(f"Erro ao obter feriados via LLM: {e}")
        
        # Fallback para dados estáticos
        feriados = self.feriados_nacionais.copy()
        
        # Adicionar feriados estaduais
        if estado in self.feriados_estaduais:
            feriados.update(self.feriados_estaduais[estado])
        
        return feriados
        """
        Obtém todos os feriados para um município específico.
        
        Args:
            estado: Nome do estado
            municipio: Nome do município (opcional, padrão para capital)
            
        Returns:
            Conjunto de datas de feriados
        """
    def obter_feriados_municipio(self, estado: str, municipio: str = None) -> Set[date]:
        """
        Obtém todos os feriados para um município específico.
        
        Args:
            estado: Nome do estado
            municipio: Nome do município (opcional, padrão para capital)
            
        Returns:
            Conjunto de datas de feriados
        """
        if self.usar_llm:
            try:
                info = self.obter_informacoes_estado_llm(estado)
                feriados = set()
                
                # Incluir todos os tipos de feriados
                for categoria in ['feriados_nacionais', 'feriados_estaduais', 'feriados_municipais']:
                    for feriado in info.get(categoria, []):
                        try:
                            data_feriado = datetime.strptime(feriado['data'], '%Y-%m-%d').date()
                            feriados.add(data_feriado)
                        except (ValueError, KeyError):
                            continue
                
                return feriados
            except Exception as e:
                logger.error(f"Erro ao obter feriados municipais via LLM: {e}")
        
        # Fallback para dados estáticos
        feriados = self.obter_feriados_estado(estado)
        
        # Se não especificou município, usar capital do estado
        if not municipio:
            municipio = self._obter_capital_estado(estado)
        
        # Adicionar feriados municipais
        if municipio in self.feriados_municipais:
            feriados.update(self.feriados_municipais[municipio])
        
        return feriados
    
    def _obter_capital_estado(self, estado: str) -> str:
        """Obtém a capital do estado."""
        capitais = {
            'São Paulo': 'São Paulo',
            'Rio de Janeiro': 'Rio de Janeiro',
            'Rio Grande do Sul': 'Porto Alegre',
            'Paraná': 'Curitiba'
        }
        return capitais.get(estado, '')
    
    def calcular_dias_uteis(self, data_inicio: date, data_fim: date, estado: str, municipio: str = None) -> int:
        """
        Calcula o número de dias úteis entre duas datas, considerando feriados.
        
        Args:
            data_inicio: Data de início (inclusiva)
            data_fim: Data de fim (inclusiva)
            estado: Estado para considerar feriados
            municipio: Município para considerar feriados (opcional)
            
        Returns:
            Número de dias úteis
        """
        if data_fim < data_inicio:
            return 0
        
        if self.usar_llm:
            try:
                # Usar informações do LLM para o período específico
                info = self.obter_informacoes_estado_llm(estado)
                periodo_info = info.get('dias_uteis_periodo', {})
                
                # Verificar se o período bate com o solicitado
                if (periodo_info.get('inicio') == data_inicio.strftime('%Y-%m-%d') and
                    periodo_info.get('fim') == data_fim.strftime('%Y-%m-%d')):
                    return periodo_info.get('total_dias_uteis', 0)
                else:
                    # Período diferente, calcular manualmente com feriados do LLM
                    feriados = self.obter_feriados_municipio(estado, municipio)
                    return self._calcular_dias_uteis_com_feriados(data_inicio, data_fim, feriados)
            except Exception as e:
                logger.error(f"Erro ao calcular dias úteis via LLM: {e}")
        
        # Fallback para cálculo estático
        feriados = self.obter_feriados_municipio(estado, municipio)
        return self._calcular_dias_uteis_com_feriados(data_inicio, data_fim, feriados)
    
    def listar_feriados_periodo(self, data_inicio: date, data_fim: date, estado: str, municipio: str = None) -> List[Dict]:
        """
        Lista todos os feriados em um período específico.
        
        Args:
            data_inicio: Data de início
            data_fim: Data de fim
            estado: Estado
            municipio: Município (opcional)
            
        Returns:
            Lista de feriados no período
        """
        feriados = self.obter_feriados_municipio(estado, municipio)
        feriados_periodo = []
        
        for feriado in sorted(feriados):
            if data_inicio <= feriado <= data_fim:
                tipo = 'Nacional'
                if feriado in self.feriados_estaduais.get(estado, set()):
                    tipo = 'Estadual'
                elif municipio and feriado in self.feriados_municipais.get(municipio, set()):
                    tipo = 'Municipal'
                
                feriados_periodo.append({
                    'data': feriado,
                    'tipo': tipo,
                    'nome': self._obter_nome_feriado(feriado)
                })
        
        return feriados_periodo
    
    def _obter_nome_feriado(self, data_feriado: date) -> str:
        """Obtém o nome do feriado baseado na data."""
        nomes_feriados = {
            date(2025, 1, 1): 'Confraternização Universal',
            date(2025, 1, 25): 'Aniversário de São Paulo',
            date(2025, 2, 13): 'Carnaval (SP)',
            date(2025, 3, 1): 'Aniversário do Rio de Janeiro',
            date(2025, 3, 3): 'Carnaval',
            date(2025, 3, 4): 'Carnaval',
            date(2025, 3, 26): 'Aniversário de Porto Alegre',
            date(2025, 3, 29): 'Aniversário de Curitiba',
            date(2025, 4, 18): 'Paixão de Cristo',
            date(2025, 4, 21): 'Tiradentes',
            date(2025, 4, 23): 'São Jorge',
            date(2025, 5, 1): 'Dia do Trabalhador',
            date(2025, 6, 19): 'Corpus Christi',
            date(2025, 7, 9): 'Revolução Constitucionalista',
            date(2025, 9, 7): 'Independência do Brasil',
            date(2025, 9, 20): 'Revolução Farroupilha',
            date(2025, 10, 12): 'Nossa Senhora Aparecida',
            date(2025, 10, 28): 'Dia do Funcionário Público (RJ)',
            date(2025, 11, 2): 'Finados',
            date(2025, 11, 15): 'Proclamação da República',
            date(2025, 11, 20): 'Zumbi dos Palmares',
            date(2025, 12, 19): 'Emancipação do Paraná',
            date(2025, 12, 25): 'Natal',
        }
        return nomes_feriados.get(data_feriado, 'Feriado')
    
    def gerar_relatorio_feriados(self, estado: str, municipio: str = None, arquivo_saida: str = None) -> str:
        """
        Gera relatório de feriados para o estado/município.
        
        Args:
            estado: Estado
            municipio: Município (opcional)
            arquivo_saida: Arquivo de saída (opcional)
            
        Returns:
            Conteúdo do relatório
        """
        periodo_inicio = date(2025, 4, 15)
        periodo_fim = date(2025, 5, 15)
        
        feriados_periodo = self.listar_feriados_periodo(periodo_inicio, periodo_fim, estado, municipio)
        dias_uteis = self.calcular_dias_uteis(periodo_inicio, periodo_fim, estado, municipio)
        
        relatorio = []
        relatorio.append(f"RELATÓRIO DE FERIADOS - {estado}")
        if municipio:
            relatorio.append(f"Município: {municipio}")
        relatorio.append("=" * 50)
        relatorio.append(f"Período: {periodo_inicio} a {periodo_fim}")
        relatorio.append(f"Dias úteis no período: {dias_uteis}")
        relatorio.append("")
        
        if feriados_periodo:
            relatorio.append("FERIADOS NO PERÍODO:")
            relatorio.append("-" * 25)
            for feriado in feriados_periodo:
                relatorio.append(f"{feriado['data'].strftime('%d/%m/%Y')} - {feriado['nome']} ({feriado['tipo']})")
        else:
            relatorio.append("Nenhum feriado no período de referência.")
        
        relatorio.append("")
        relatorio.append("RESUMO POR TIPO:")
        relatorio.append("-" * 18)
        tipos = {}
        for feriado in feriados_periodo:
            tipos[feriado['tipo']] = tipos.get(feriado['tipo'], 0) + 1
        
        for tipo, count in tipos.items():
            relatorio.append(f"{tipo}: {count} feriado(s)")
        
        conteudo = "\n".join(relatorio)
        
        if arquivo_saida:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            logger.info(f"Relatório de feriados salvo em: {arquivo_saida}")
        
        return conteudo


# Instância global para uso em outros módulos
gerenciador_feriados = GerenciadorFeriados(usar_llm=True)


def obter_dias_uteis_estado(estado: str, data_inicio: date = None, data_fim: date = None) -> int:
    """
    Função utilitária para obter dias úteis de um estado usando LLM.
    
    Args:
        estado: Nome do estado
        data_inicio: Data de início (padrão: 15/04/2025)
        data_fim: Data de fim (padrão: 15/05/2025)
        
    Returns:
        Número de dias úteis
    """
    if not data_inicio:
        data_inicio = date(2025, 4, 15)
    if not data_fim:
        data_fim = date(2025, 5, 15)
    
    return gerenciador_feriados.calcular_dias_uteis(data_inicio, data_fim, estado)


def obter_valor_vr_estado(estado: str) -> float:
    """
    Função utilitária para obter valor de VR de um estado usando LLM.
    
    Args:
        estado: Nome do estado
        
    Returns:
        Valor de VR em reais
    """
    try:
        info = gerenciador_feriados.obter_informacoes_estado_llm(estado)
        return info.get('valor_vr_vigente', {}).get('valor', 35.0)
    except Exception as e:
        logger.error(f"Erro ao obter valor VR para {estado}: {e}")
        # Fallback para valores conhecidos
        valores_fallback = {
            'São Paulo': 37.5,
            'Rio de Janeiro': 35.0,
            'Rio Grande do Sul': 35.0,
            'Paraná': 35.0
        }
        return valores_fallback.get(estado, 35.0)


def salvar_cache_feriados(arquivo: str = "cache_feriados.json"):
    """Salva cache de informações de feriados."""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(gerenciador_feriados.cache_informacoes, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Cache de feriados salvo em: {arquivo}")
    except Exception as e:
        logger.error(f"Erro ao salvar cache: {e}")


def carregar_cache_feriados(arquivo: str = "cache_feriados.json"):
    """Carrega cache de informações de feriados."""
    try:
        import os
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                gerenciador_feriados.cache_informacoes = json.load(f)
            logger.info(f"Cache de feriados carregado de: {arquivo}")
    except Exception as e:
        logger.error(f"Erro ao carregar cache: {e}")


if __name__ == "__main__":
    # Teste das funcionalidades com LLM
    print("🧪 TESTANDO GERENCIADOR DE FERIADOS COM LLM")
    print("=" * 60)
    
    # Carregar cache existente
    carregar_cache_feriados()
    
    estados = ['São Paulo', 'Rio de Janeiro', 'Rio Grande do Sul', 'Paraná']
    periodo_inicio = date(2025, 4, 15)
    periodo_fim = date(2025, 5, 15)
    
    print("🔍 Consultando informações via LLM...")
    
    for estado in estados:
        print(f"\n📍 {estado}:")
        try:
            # Obter informações completas via LLM
            info = gerenciador_feriados.obter_informacoes_estado_llm(estado)
            
            dias_uteis = info['dias_uteis_periodo']['total_dias_uteis']
            valor_vr = info['valor_vr_vigente']['valor']
            
            print(f"  Dias úteis: {dias_uteis}")
            print(f"  Valor VR: R$ {valor_vr:.2f}")
            print(f"  Base legal: {info['valor_vr_vigente']['base_legal']}")
            
            feriados_periodo = info['dias_uteis_periodo']['feriados_no_periodo']
            if feriados_periodo:
                print("  Feriados no período:")
                for feriado in feriados_periodo:
                    print(f"    - {feriado['data']}: {feriado['nome']} ({feriado['tipo']})")
            else:
                print("  Nenhum feriado no período.")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            
            # Testar fallback
            try:
                dias_uteis_fallback = gerenciador_feriados.calcular_dias_uteis(periodo_inicio, periodo_fim, estado)
                print(f"  Fallback - Dias úteis: {dias_uteis_fallback}")
            except Exception as e2:
                print(f"  ❌ Erro no fallback: {e2}")
    
    # Salvar cache
    salvar_cache_feriados()
    print(f"\n✅ Teste concluído. Cache salvo.")
