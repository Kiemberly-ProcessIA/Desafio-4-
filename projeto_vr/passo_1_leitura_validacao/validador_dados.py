#!/usr/bin/env python3
# validador_dados.py - Validações específicas e regras de negócio

import pandas as pd
import re
from typing import List, Dict, Set, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidadorDados:
    """
    Classe para validações específicas e regras de negócio dos dados Excel.
    """
    
    def __init__(self):
        self.erros_criticos = []
        self.avisos = []
        self.matriculas_processadas = set()
    
    def validar_matricula(self, matricula: any) -> bool:
        """Valida se uma matrícula está em formato válido."""
        if pd.isna(matricula):
            return False
        
        matricula_str = str(matricula)
        # Matrícula deve ser numérica e ter pelo menos 4 dígitos
        return matricula_str.isdigit() and len(matricula_str) >= 4
    
    def validar_duplicatas_matricula(self, df: pd.DataFrame, nome_arquivo: str) -> List[str]:
        """Identifica matrículas duplicadas em um arquivo."""
        if 'matricula' not in df.columns:
            return [f"{nome_arquivo}: Coluna 'matricula' não encontrada"]
        
        duplicatas = df[df['matricula'].duplicated(keep=False)]
        problemas = []
        
        if not duplicatas.empty:
            matriculas_dup = duplicatas['matricula'].unique()
            for matricula in matriculas_dup:
                count = len(duplicatas[duplicatas['matricula'] == matricula])
                problemas.append(f"{nome_arquivo}: Matrícula {matricula} aparece {count} vezes")
        
        return problemas
    
    def validar_consistencia_matriculas(self, dados: Dict[str, pd.DataFrame]) -> List[str]:
        """Valida consistência de matrículas entre arquivos."""
        problemas = []
        
        # Obter matrículas de cada arquivo
        matriculas_por_arquivo = {}
        for nome, df in dados.items():
            if 'matricula' in df.columns:
                matriculas_por_arquivo[nome] = set(df['matricula'].dropna().astype(str))
        
        # Verificar se matrículas de DESLIGADOS estão em ATIVOS
        if 'desligados' in matriculas_por_arquivo and 'ativos' in matriculas_por_arquivo:
            matriculas_desligados = matriculas_por_arquivo['desligados']
            matriculas_ativos = matriculas_por_arquivo['ativos']
            
            desligados_nao_encontrados = matriculas_desligados - matriculas_ativos
            if desligados_nao_encontrados:
                problemas.append(f"Matrículas em DESLIGADOS mas não em ATIVOS: {desligados_nao_encontrados}")
        
        # Verificar se matrículas de FÉRIAS estão em ATIVOS
        if 'ferias' in matriculas_por_arquivo and 'ativos' in matriculas_por_arquivo:
            matriculas_ferias = matriculas_por_arquivo['ferias']
            matriculas_ativos = matriculas_por_arquivo['ativos']
            
            ferias_nao_encontrados = matriculas_ferias - matriculas_ativos
            if ferias_nao_encontrados:
                problemas.append(f"Matrículas em FÉRIAS mas não em ATIVOS: {ferias_nao_encontrados}")
        
        return problemas
    
    def validar_sindicatos_consistencia(self, dados: Dict[str, pd.DataFrame]) -> List[str]:
        """Valida consistência dos sindicatos entre arquivos."""
        problemas = []
        
        # Obter sindicatos de ATIVOS
        if 'ativos' in dados and 'sindicato' in dados['ativos'].columns:
            sindicatos_ativos = set(dados['ativos']['sindicato'].dropna().unique())
            
            # Obter sindicatos de dias úteis
            if 'dias_uteis' in dados and 'sindicato' in dados['dias_uteis'].columns:
                sindicatos_dias = set(dados['dias_uteis']['sindicato'].dropna().unique())
                
                # Sindicatos em ATIVOS que não têm dias úteis definidos
                sem_dias_uteis = sindicatos_ativos - sindicatos_dias
                if sem_dias_uteis:
                    problemas.append(f"Sindicatos sem dias úteis definidos: {sem_dias_uteis}")
                
                # Sindicatos com dias úteis que não estão em ATIVOS
                dias_sem_ativos = sindicatos_dias - sindicatos_ativos
                if dias_sem_ativos:
                    problemas.append(f"Sindicatos com dias úteis mas sem funcionários ativos: {dias_sem_ativos}")
        
        return problemas
    
    def validar_valores_numericos(self, df: pd.DataFrame, coluna: str, nome_arquivo: str) -> List[str]:
        """Valida se uma coluna contém apenas valores numéricos válidos."""
        problemas = []
        
        if coluna not in df.columns:
            return [f"{nome_arquivo}: Coluna '{coluna}' não encontrada"]
        
        # Verificar valores não numéricos
        nao_numericos = df[~pd.to_numeric(df[coluna], errors='coerce').notna()]
        if not nao_numericos.empty:
            valores_invalidos = nao_numericos[coluna].unique()[:5]  # Mostrar até 5 exemplos
            problemas.append(f"{nome_arquivo}: Valores não numéricos em '{coluna}': {valores_invalidos}")
        
        # Verificar valores negativos onde não deveriam existir
        if coluna in ['dias uteis', 'valor', 'dias de férias']:
            numericos = pd.to_numeric(df[coluna], errors='coerce')
            negativos = df[numericos < 0]
            if not negativos.empty:
                problemas.append(f"{nome_arquivo}: Valores negativos encontrados em '{coluna}': {len(negativos)} registros")
        
        return problemas
    
    def validar_datas(self, df: pd.DataFrame, coluna: str, nome_arquivo: str) -> List[str]:
        """Valida formato e consistência de datas."""
        problemas = []
        
        if coluna not in df.columns:
            return [f"{nome_arquivo}: Coluna '{coluna}' não encontrada"]
        
        # Tentar converter para datetime
        try:
            datas = pd.to_datetime(df[coluna], errors='coerce')
            datas_invalidas = df[datas.isna() & df[coluna].notna()]
            
            if not datas_invalidas.empty:
                problemas.append(f"{nome_arquivo}: {len(datas_invalidas)} datas inválidas em '{coluna}'")
            
            # Verificar datas no futuro (se for demissão)
            if 'demissao' in coluna.lower():
                hoje = datetime.now()
                futuro = datas[datas > hoje]
                if not futuro.empty:
                    problemas.append(f"{nome_arquivo}: {len(futuro)} datas de demissão no futuro")
        
        except Exception as e:
            problemas.append(f"{nome_arquivo}: Erro ao validar datas em '{coluna}': {e}")
        
        return problemas
    
    def validar_completude_dados(self, df: pd.DataFrame, colunas_obrigatorias: List[str], nome_arquivo: str) -> List[str]:
        """Valida se colunas obrigatórias estão preenchidas."""
        problemas = []
        
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                problemas.append(f"{nome_arquivo}: Coluna obrigatória '{coluna}' ausente")
                continue
            
            nulos = df[coluna].isnull().sum()
            vazios = df[coluna].astype(str).str.strip().eq('').sum()
            total_problemas = nulos + vazios
            
            if total_problemas > 0:
                percentual = (total_problemas / len(df)) * 100
                problemas.append(f"{nome_arquivo}: '{coluna}' tem {total_problemas} valores vazios ({percentual:.1f}%)")
        
        return problemas
    
    def executar_validacao_completa(self, dados: Dict[str, pd.DataFrame]) -> Dict[str, any]:
        """Executa todas as validações nos dados carregados."""
        logger.info("🔍 INICIANDO VALIDAÇÃO DETALHADA DOS DADOS")
        
        todos_problemas = []
        
        # 1. Validar duplicatas de matrícula em cada arquivo
        for nome, df in dados.items():
            if 'matricula' in df.columns:
                problemas_dup = self.validar_duplicatas_matricula(df, nome.upper())
                todos_problemas.extend(problemas_dup)
        
        # 2. Validar consistência entre arquivos
        problemas_consistencia = self.validar_consistencia_matriculas(dados)
        todos_problemas.extend(problemas_consistencia)
        
        # 3. Validar sindicatos
        problemas_sindicatos = self.validar_sindicatos_consistencia(dados)
        todos_problemas.extend(problemas_sindicatos)
        
        # 4. Validações específicas por arquivo
        if 'ativos' in dados:
            df_ativos = dados['ativos']
            colunas_obrig = ['matricula', 'empresa', 'cargo', 'situacao', 'sindicato']
            problemas_ativos = self.validar_completude_dados(df_ativos, colunas_obrig, 'ATIVOS')
            todos_problemas.extend(problemas_ativos)
        
        if 'valores' in dados:
            df_valores = dados['valores']
            problemas_valores = self.validar_valores_numericos(df_valores, 'valor', 'BASE SINDICATO X VALOR')
            todos_problemas.extend(problemas_valores)
        
        if 'dias_uteis' in dados:
            df_dias = dados['dias_uteis']
            problemas_dias = self.validar_valores_numericos(df_dias, 'dias uteis', 'BASE DIAS UTEIS')
            todos_problemas.extend(problemas_dias)
        
        if 'desligados' in dados:
            df_desligados = dados['desligados']
            if 'demissao data' in df_desligados.columns:
                problemas_datas = self.validar_datas(df_desligados, 'demissao data', 'DESLIGADOS')
                todos_problemas.extend(problemas_datas)
        
        # 5. Compilar resultado final
        resultado = {
            'timestamp': datetime.now().isoformat(),
            'total_problemas': len(todos_problemas),
            'problemas_criticos': [p for p in todos_problemas if any(palavra in p.lower() for palavra in ['ausente', 'não encontrada', 'duplicada'])],
            'avisos': [p for p in todos_problemas if p not in [p for p in todos_problemas if any(palavra in p.lower() for palavra in ['ausente', 'não encontrada', 'duplicada'])]],
            'todos_problemas': todos_problemas,
            'status_validacao': 'APROVADO' if len(todos_problemas) == 0 else 'COM_PROBLEMAS' if len([p for p in todos_problemas if any(palavra in p.lower() for palavra in ['ausente', 'não encontrada'])]) == 0 else 'CRITICO'
        }
        
        # Log dos resultados
        if resultado['status_validacao'] == 'APROVADO':
            logger.info("✅ VALIDAÇÃO CONCLUÍDA: Todos os dados estão íntegros")
        elif resultado['status_validacao'] == 'COM_PROBLEMAS':
            logger.warning(f"⚠️ VALIDAÇÃO CONCLUÍDA: {len(resultado['avisos'])} avisos encontrados")
        else:
            logger.error(f"❌ VALIDAÇÃO CONCLUÍDA: {len(resultado['problemas_criticos'])} problemas críticos encontrados")
        
        return resultado
    
    def imprimir_relatorio_validacao(self, resultado: Dict[str, any]):
        """Imprime relatório detalhado da validação."""
        print("\n" + "="*80)
        print("🔍 RELATÓRIO DETALHADO DE VALIDAÇÃO")
        print("="*80)
        
        print(f"🏷️ Status: {resultado['status_validacao']}")
        print(f"📊 Total de problemas: {resultado['total_problemas']}")
        print(f"❌ Problemas críticos: {len(resultado['problemas_criticos'])}")
        print(f"⚠️ Avisos: {len(resultado['avisos'])}")
        
        if resultado['problemas_criticos']:
            print(f"\n❌ PROBLEMAS CRÍTICOS:")
            for problema in resultado['problemas_criticos']:
                print(f"   • {problema}")
        
        if resultado['avisos']:
            print(f"\n⚠️ AVISOS:")
            for aviso in resultado['avisos'][:10]:  # Mostrar até 10 avisos
                print(f"   • {aviso}")
            
            if len(resultado['avisos']) > 10:
                print(f"   ... e mais {len(resultado['avisos']) - 10} avisos")
        
        print("\n" + "="*80)
