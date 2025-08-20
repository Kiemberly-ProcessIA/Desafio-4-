# =============================================================================
# SISTEMA DE PROCESSAMENTO DE VALE REFEIÇÃO COM IA (LLM)
# =============================================================================

.PHONY: help setup install clean run pipeline test debug

# Variáveis
PYTHON = python3
UV = uv
PROJECT_DIR = projeto_vr
OUTPUT_DIR = output
VENV_DIR = .venv

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
BLUE = \033[0;34m
NC = \033[0m # No Color

# =============================================================================
# COMANDOS PRINCIPAIS
# =============================================================================

help: ## 📋 Mostrar esta ajuda
	@echo "$(BLUE)🚀 SISTEMA DE PROCESSAMENTO VR COM IA$(NC)"
	@echo "$(BLUE)================================================$(NC)"
	@echo ""
	@echo "$(GREEN)COMANDOS PRINCIPAIS:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(YELLOW)%-12s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(GREEN)EXEMPLOS:$(NC)"
	@echo "  make setup      # Configurar ambiente"
	@echo "  make run        # Executar pipeline completo"
	@echo "  make clean      # Limpar arquivos temporários"
	@echo ""
	@echo "$(BLUE)📁 ESTRUTURA:$(NC)"
	@echo "  • input_data/   - Dados de entrada (colaboradores, configurações)"
	@echo "  • output/       - Resultados finais (Excel, relatórios)"
	@echo "  • config.py     - Configurações do LLM (Gemini)"
	@echo ""
	@echo "$(BLUE)🤖 IA INTEGRADA:$(NC)"
	@echo "  • Análise inteligente de cargos"
	@echo "  • Consulta dinâmica de feriados"
	@echo "  • Valores de VR atualizados por estado"

setup: ## 🔧 Configurar ambiente virtual e dependências
	@echo "$(BLUE)🔧 Configurando ambiente...$(NC)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "$(YELLOW)Criando ambiente virtual...$(NC)"; \
		$(UV) venv $(VENV_DIR); \
	else \
		echo "$(GREEN)✅ Ambiente virtual já existe$(NC)"; \
	fi
	@echo "$(YELLOW)Instalando dependências...$(NC)"
	@$(UV) pip install -r requirements.txt
	@echo "$(GREEN)✅ Ambiente configurado com sucesso!$(NC)"

install: setup ## 📦 Alias para setup (compatibilidade)

run: setup ## 🚀 Executar pipeline completo com IA e auditoria
	@echo "$(BLUE)🚀 INICIANDO PIPELINE COMPLETO COM AUDITORIA...$(NC)"
	@echo "$(BLUE)=====================================================$(NC)"
	@echo "$(YELLOW)🧹 Limpando arquivos anteriores...$(NC)"
	@rm -rf $(OUTPUT_DIR)/*
	@mkdir -p $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Diretório output limpo$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py all --incluir-auditoria
	@echo ""
	@echo "$(GREEN)🎉 PIPELINE DE 6 PASSOS CONCLUÍDO COM AUDITORIA!$(NC)"
	@echo "$(YELLOW)📄 Verifique o relatório final em: output/RELATORIO_FINAL_PROJETO_VR_*.txt$(NC)"
	@echo "$(YELLOW)📄 Verifique o arquivo Excel final em: output/VR_MENSAL_OPERADORA_*.xlsx$(NC)"

pipeline: run ## 🔄 Alias para run (compatibilidade)

pipeline-simples: setup ## 📋 Executar pipeline de 5 passos (sem auditoria)
	@echo "$(BLUE)🚀 INICIANDO PIPELINE SIMPLES (5 PASSOS)...$(NC)"
	@echo "$(BLUE)================================================$(NC)"
	@echo "$(YELLOW)🧹 Limpando arquivos anteriores...$(NC)"
	@rm -rf $(OUTPUT_DIR)/*
	@mkdir -p $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Diretório output limpo$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py all
	@echo ""
	@echo "$(GREEN)🎉 PIPELINE DE 5 PASSOS CONCLUÍDO!$(NC)"
	@echo "$(YELLOW)📄 Verifique o arquivo Excel final em: output/VR_MENSAL_OPERADORA_*.xlsx$(NC)"

lint: setup ## 📝 Análise de código (flake8)
	@echo "$(BLUE)📝 Executando análise de código...$(NC)"
	@$(UV) pip install flake8
	@$(UV) run python -m flake8 $(PROJECT_DIR)/ --max-line-length=100 --ignore=E203,W503 || echo "$(YELLOW)⚠️ Lint com problemas$(NC)"

format: setup ## ✨ Formatar código (black)
	@echo "$(BLUE)✨ Formatando código...$(NC)"
	@$(UV) pip install black isort
	@$(UV) run python -m black $(PROJECT_DIR)/
	@$(UV) run python -m isort $(PROJECT_DIR)/
	@echo "$(GREEN)✅ Código formatado$(NC)"

format-check: setup ## 🔍 Verificar formatação (sem alterar)
	@echo "$(BLUE)🔍 Verificando formatação...$(NC)"
	@$(UV) pip install black isort
	@$(UV) run python -m black --check --diff $(PROJECT_DIR)/ || echo "$(YELLOW)⚠️ Black: Formatação precisa de ajustes$(NC)"
	@$(UV) run python -m isort --check-only --diff $(PROJECT_DIR)/ || echo "$(YELLOW)⚠️ Isort: Formatação precisa de ajustes$(NC)"

debug: setup ## 🐛 Executar pipeline em modo DEBUG (gera JSONs intermediários)
	@echo "$(BLUE)🐛 Executando em modo DEBUG...$(NC)"
	@mkdir -p $(OUTPUT_DIR)
	@DEBUG=true cd $(PROJECT_DIR) && $(UV) run main.py pipeline
	@echo "$(YELLOW)📊 Arquivos de debug salvos em: output/$(NC)"

clean: ## 🧹 Limpar arquivos temporários e cache
	@echo "$(BLUE)🧹 Limpando arquivos temporários...$(NC)"
	@rm -rf $(VENV_DIR)/ || true
	@rm -rf $(OUTPUT_DIR)/ || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Limpeza completa realizada$(NC)"

clean-output: ## 🗑️ Limpar apenas arquivos de output
	@echo "$(BLUE)🗑️ Limpando apenas arquivos de output...$(NC)"
	@rm -rf $(OUTPUT_DIR)/*
	@mkdir -p $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Diretório output limpo$(NC)"
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name "*Zone.Identifier" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Limpeza concluída!$(NC)"

# =============================================================================
# COMANDOS AVANÇADOS (PASSOS INDIVIDUAIS)
# =============================================================================

step1: setup ## 📂 Executar apenas Passo 1 (Consolidação)
	@echo "$(BLUE)📂 Executando Passo 1: Consolidação...$(NC)"
	@mkdir -p $(OUTPUT_DIR)
	@cd $(PROJECT_DIR) && $(UV) run main.py passo1

step2: setup ## 🤖 Executar apenas Passo 2 (Análise IA)
	@echo "$(BLUE)🤖 Executando Passo 2: Análise com IA...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py passo2-llm

step3: setup ## 🔄 Executar apenas Passo 3 (Aplicar Exclusões)
	@echo "$(BLUE)🔄 Executando Passo 3: Aplicar Exclusões...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py passo3

step4: setup ## 🧮 Executar apenas Passo 4 (Cálculos)
	@echo "$(BLUE)🧮 Executando Passo 4: Cálculos...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py passo4

step5: setup ## 📊 Executar apenas Passo 5 (Excel Final)
	@echo "$(BLUE)📊 Executando Passo 5: Excel Final...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py passo5

step6: setup ## 🔍 Executar apenas Passo 6 (Auditoria LLM)
	@echo "$(BLUE)🔍 Executando Passo 6: Auditoria Final com LLM...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py passo6

pipeline6: setup ## 🚀 Executar pipeline completo com 6 passos (incluindo auditoria)
	@echo "$(BLUE)🚀 INICIANDO PIPELINE COMPLETO COM AUDITORIA...$(NC)"
	@echo "$(BLUE)=====================================================$(NC)"
	@echo "$(YELLOW)🧹 Limpando arquivos anteriores...$(NC)"
	@rm -rf $(OUTPUT_DIR)/*
	@mkdir -p $(OUTPUT_DIR)
	@echo "$(GREEN)✓ Diretório output limpo$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run main.py all --incluir-auditoria
	@echo ""
	@echo "$(GREEN)🎉 PIPELINE DE 6 PASSOS CONCLUÍDO!$(NC)"
	@echo "$(YELLOW)📄 Verifique o relatório final em: output/RELATORIO_FINAL_PROJETO_VR_*.txt$(NC)"

# =============================================================================
# INFORMAÇÕES DO SISTEMA
# =============================================================================

status: ## ℹ️ Mostrar status do projeto
	@echo "$(BLUE)ℹ️ STATUS DO PROJETO$(NC)"
	@echo "$(BLUE)===================$(NC)"
	@echo "$(YELLOW)📁 Diretório:$(NC) $(shell pwd)"
	@echo "$(YELLOW)🐍 Python:$(NC) $(shell python3 --version 2>/dev/null || echo 'Não encontrado')"
	@echo "$(YELLOW)📦 UV:$(NC) $(shell uv --version 2>/dev/null || echo 'Não encontrado')"
	@echo "$(YELLOW)🌐 Ambiente:$(NC) $(if $(wildcard $(VENV_DIR)),✅ Configurado,❌ Não configurado)"
	@echo "$(YELLOW)📄 Dados:$(NC) $(if $(wildcard input_data/),✅ Presentes,❌ Ausentes)"
	@echo "$(YELLOW)⚙️ Config:$(NC) $(if $(wildcard config.py),✅ Presente,❌ Ausente)"
	@if [ -f config.py ]; then \
		echo "$(YELLOW)🤖 LLM:$(NC) Gemini $(shell grep NOME_MODELO_LLM config.py | cut -d'"' -f2 2>/dev/null || echo 'Não configurado')"; \
	fi

config: ## ⚙️ Verificar configuração do LLM
	@echo "$(BLUE)⚙️ CONFIGURAÇÃO DO LLM$(NC)"
	@echo "$(BLUE)=====================$(NC)"
	@if [ -f config.py ]; then \
		echo "$(GREEN)✅ Arquivo config.py encontrado$(NC)"; \
		echo "$(YELLOW)🤖 Modelo:$(NC) $$(grep NOME_MODELO_LLM config.py | cut -d'"' -f2)"; \
		echo "$(YELLOW)🔑 API Key:$(NC) $$(grep GOOGLE_API_KEY config.py | cut -d'"' -f2 | sed 's/.*\(.\{8\}\)/...\1/')"; \
	else \
		echo "$(RED)❌ Arquivo config.py não encontrado!$(NC)"; \
		echo "$(YELLOW)💡 Crie o arquivo com suas credenciais do Google Gemini$(NC)"; \
	fi
	@echo "$(YELLOW)🔑 Verificando variável de ambiente...$(NC)"
	@if [ -z "$$GOOGLE_API_KEY" ]; then \
		echo "$(RED)❌ GOOGLE_API_KEY não definida como variável de ambiente$(NC)"; \
	else \
		if echo "$$GOOGLE_API_KEY" | grep -q "^AIza"; then \
			echo "$(GREEN)✓ Formato da API key parece correto (AIza...)$(NC)"; \
		else \
			echo "$(YELLOW)⚠️ API key não segue o formato padrão do Gemini (deve começar com AIza...)$(NC)"; \
			echo "$(YELLOW)🔗 Obtenha uma nova em: https://aistudio.google.com/app/apikey$(NC)"; \
		fi; \
	fi

test-api: setup ## 🔑 Testar conexão com a API do Google Gemini
	@echo "$(BLUE)🔑 TESTANDO API DO GOOGLE GEMINI$(NC)"
	@echo "$(BLUE)================================$(NC)"
	@if [ -z "$$GOOGLE_API_KEY" ]; then \
		echo "$(RED)❌ GOOGLE_API_KEY não definida$(NC)"; \
		echo "$(YELLOW)💡 Configure a variável de ambiente GOOGLE_API_KEY$(NC)"; \
		echo "$(YELLOW)🔗 Obtenha em: https://aistudio.google.com/app/apikey$(NC)"; \
		echo ""; \
		echo "$(BLUE)📋 Exemplo de uso:$(NC)"; \
		echo "$(YELLOW)export GOOGLE_API_KEY=\"AIza...sua_chave_aqui\"$(NC)"; \
		echo "$(YELLOW)make test-api$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Validando formato da API key...$(NC)"
	@if echo "$$GOOGLE_API_KEY" | grep -q "^AIza"; then \
		echo "$(GREEN)✓ Formato correto (AIza...)$(NC)"; \
	else \
		echo "$(RED)❌ Formato incorreto! Deve começar com 'AIza'$(NC)"; \
		echo "$(YELLOW)🔗 Obtenha uma nova em: https://aistudio.google.com/app/apikey$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Testando conexão com a API...$(NC)"
	@cd $(PROJECT_DIR) && $(UV) run python -c "import google.generativeai as genai; import os; genai.configure(api_key=os.getenv('GOOGLE_API_KEY')); model = genai.GenerativeModel('gemini-2.0-flash-001'); response = model.generate_content('Teste de conexão. Responda apenas: API funcionando.'); print('✅ API conectada com sucesso!'); print(f'📝 Resposta: {response.text.strip()}'); print('🎉 Sistema pronto para executar!')" && echo "$(GREEN)✅ Teste concluído com sucesso!$(NC)" || (echo "$(RED)❌ Erro ao conectar com a API$(NC)" && echo "$(YELLOW)💡 Verifique se a API key está correta e ativa$(NC)" && echo "$(YELLOW)🔗 Obtenha uma nova em: https://aistudio.google.com/app/apikey$(NC)")

check-api: ## 🔍 Verificar apenas o formato da API key (sem testar conexão)
	@echo "$(BLUE)🔍 VERIFICANDO API KEY$(NC)"
	@echo "$(BLUE)=====================$(NC)"
	@if [ -z "$$GOOGLE_API_KEY" ]; then \
		echo "$(RED)❌ GOOGLE_API_KEY não definida$(NC)"; \
		echo "$(YELLOW)💡 Defina: export GOOGLE_API_KEY=\"sua_chave\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Chave atual: $$(echo $$GOOGLE_API_KEY | sed 's/\(.\{10\}\).*/\1.../')$(NC)"
	@if echo "$$GOOGLE_API_KEY" | grep -q "^AIza"; then \
		echo "$(GREEN)✅ Formato correto para Google Gemini$(NC)"; \
		echo "$(YELLOW)📏 Tamanho: $$(echo $$GOOGLE_API_KEY | wc -c) caracteres$(NC)"; \
	else \
		echo "$(RED)❌ Formato incorreto!$(NC)"; \
		echo "$(YELLOW)Expected: AIza... (Google AI Studio)$(NC)"; \
		echo "$(YELLOW)Current:  $$(echo $$GOOGLE_API_KEY | cut -c1-4)... $(NC)"; \
	fi

# Comando padrão
.DEFAULT_GOAL := help
