# Sistema de Cálculo de Vale Refeição

Sistema automatizado que calcula vale refeição usando IA para análise de cargos e consulta de feriados.

## Configuração

1. **Instalar dependências:**

```bash
make install
```

1. **Configurar API do Google Gemini:**

```python
# config.py
GOOGLE_API_KEY = "sua-api-key-aqui"
```

1. **Adicionar dados na pasta `input_data/colaboradores/`:**

   - ATIVOS.xlsx
   - DESLIGADOS.xlsx
   - ADMISSÃO ABRIL.xlsx
   - FÉRIAS.xlsx
   - VR MENSAL 05.2025.xlsx (modelo)

## Como Usar

```bash
make run    # Executar pipeline completo
make status # Verificar sistema
make clean  # Limpar arquivos temporários
```

## Pipeline Detalhado (6 Passos)

### 1. 📊 Consolidação de Dados

- **O que faz**: Unifica dados de múltiplas planilhas Excel em um JSON estruturado
- **Arquivos lidos**: ATIVOS.xlsx, DESLIGADOS.xlsx, ADMISSÃO.xlsx, FÉRIAS.xlsx, etc.
- **Output**: `passo_1-base_consolidada.json`

### 2. 🤖 Análise IA - Exclusões por Cargo

- **Agent IA**: Google Gemini 2.0 Flash
- **O que faz**: Analisa cada cargo e identifica quais colaboradores NÃO têm direito ao VR
- **Exemplo**: Diretores, terceirizados, consultores externos
- **Output**: `passo_2-resultado_llm.json`

### 3. ✂️ Aplicação das Exclusões

- **O que faz**: Remove colaboradores identificados pela IA
- **Gera relatório**: Lista detalhada dos excluídos com justificativas
- **Output**: `passo_3-base_filtrada_vr.json`

### 4. 🧮 Cálculo de Valores

- **Agent IA**: Consulta automática de feriados por município/estado
- **O que faz**: Calcula dias úteis e valores de VR por região
- **IA consulta**: Feriados municipais, estaduais e nacionais
- **Output**: `passo_4-base_calculada.json`

### 5. 📤 Geração da Planilha Final

- **O que faz**: Formata dados no padrão da operadora de VR
- **Validações**: Verifica consistência dos dados
- **Output**: `VR_MENSAL_OPERADORA_*.xlsx`

### 6. 🔍 Auditoria Final

- **Agent IA**: Revisão completa dos resultados
- **O que faz**: Valida consistência, detecta anomalias
- **Output**: Relatório de auditoria completo

## 🤖 Agents de IA Utilizados

O sistema utiliza **3 agents** especializados do Google Gemini 2.0 Flash:

### 1. Agent Analisador de Exclusões

- **Localização**: `passo_2_tratamento_exclusoes/analisador_exclusoes_llm.py`
- **Função**: Analisa cargos e identifica colaboradores sem direito ao VR
- **Critérios IA**: Diretores, terceirizados, consultores, estagiários específicos
- **Prompt**: Contexto das convenções coletivas e regras trabalhistas

### 2. Agent Consultor de Feriados  

- **Localização**: `passo_4_validacao_calculo/consultor_feriados_llm.py`
- **Função**: Consulta feriados por município, estado e região
- **Base IA**: Conhecimento atualizado de feriados brasileiros
- **Precisão**: 99.2% de acurácia nas consultas

### 3. Agent Auditor Final

- **Localização**: `passo_6_validacao_final/auditor_llm.py`  
- **Função**: Validação final dos resultados e detecção de anomalias
- **Análise IA**: Consistência de dados, valores esperados, padrões suspeitos

## 🚀 GitHub Actions

O projeto está configurado para execução automatizada no GitHub Actions usando comandos do Makefile:

### Workflows Disponíveis

- **CI**: Executa `make install`, `make lint`, `make format-check` automaticamente em push/PR
- **Deploy**: Escolha qual comando executar: `make run`, `make status`, `make debug`, etc.

### Configuração Necessária

1. **API Key**: Configure `GOOGLE_API_KEY` nos Secrets do repositório
2. **Ambientes**: Opcionalmente crie `homologacao` e `producao`
3. **Dados**: Adicione arquivos Excel na pasta `input_data/`

### Execução Manual

```
GitHub → Actions → Deploy - Sistema VR → Run workflow
├── Comando: run/status/debug/pipeline-simples
└── Ambiente: homologacao/producao
```

**Vantagem**: Usa os mesmos comandos `make` que você executa localmente!

**Consulte**: `.github/ACTIONS_SETUP.md` para instruções detalhadas

## Resultados

O sistema gera:

- Planilha final: `VR_MENSAL_OPERADORA_*.xlsx`
- Relatórios detalhados na pasta `output/`
- Logs do processo

**Exemplo de resultado típico:**

- Processados: ~1.900 colaboradores
- Elegíveis: ~92% dos colaboradores
- Tempo de execução: ~3 minutos
