# 🤖 GitHub Actions - Sistema VR

Este diretório contém os workflows automatizados do GitHub Actions para o Sistema de Vale Refeição.

## 📋 Workflows Disponíveis

### 1. `ci.yml` - Integração Contínua
- **Quando executa**: Push/PR na branch main
- **O que faz**: 
  - ✅ Validações de código
  - ✅ Testes de formatação
  - ✅ Análise de lint
  - ✅ Executa o sistema completo
  - 📦 Gera artefatos com outputs

### 2. `deploy.yml` - Deploy Manual
- **Quando executa**: Execução manual via interface
- **O que faz**: Deploy personalizado com opções

### 3. `run-sistema.yml` - Execução do Sistema VR
- **Quando executa**: Execução manual via interface
- **O que faz**: 
  - 🚀 Executa o sistema VR com diferentes ambientes
  - 📊 Gera relatórios completos
  - 📦 Disponibiliza todos os outputs como artefatos

## 🚀 Como Executar o Sistema VR

### Execução Manual:
1. Acesse: **Actions** → **Executar Sistema VR**
2. Clique em **Run workflow**
3. Escolha o ambiente:
   - **producao**: Execução completa com auditoria
   - **desenvolvimento**: Execução padrão
   - **debug**: Execução com logs detalhados

### Automática:
- Push ou PR na branch `main` executa automaticamente

## 📦 Artefatos Gerados

Após a execução, você encontrará os seguintes artefatos:

### 🎯 Resultados Principais
- **Nome**: `vr-resultados-[ambiente]-[numero]`
- **Contém**: 
  - `*.json` - Dados processados
  - `*.xlsx` - Planilhas finais
  - `*.txt` - Relatórios textuais
- **Retenção**: 90 dias

### 📝 Logs Detalhados  
- **Nome**: `vr-logs-[ambiente]-[numero]`
- **Contém**: Logs de execução completos
- **Retenção**: 30 dias

### 📊 Relatórios Específicos
- **Nome**: `vr-relatorios-[ambiente]-[numero]`
- **Contém**: 
  - Relatórios de auditoria
  - Resumos executivos
  - Relatórios de cálculo
- **Retenção**: 60 dias

## 📥 Como Baixar os Artefatos

1. Vá para **Actions**
2. Clique na execução desejada
3. Role até **Artifacts** (final da página)
4. Clique para baixar o ZIP desejado

## 🔧 Configuração Necessária

### Secrets Obrigatórios:
- `GOOGLE_API_KEY`: Chave da API do Google Gemini

### Para configurar:
1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Nome: `GOOGLE_API_KEY`
4. Valor: Sua chave da API

## 📊 Estrutura dos Outputs

```
output/
├── agrupamentos_consolidados.json
├── passo_1-base_consolidada.json
├── passo_2-resultado_llm.json
├── passo_3-base_filtrada_vr.json
├── passo_3-relatorio_exclusoes.txt
├── passo_4-base_calculada.json
├── passo_4-base_final_vr.json
├── passo_4-base_validada.json
├── passo_4-relatorio_calculo_vr.txt
├── passo_4-relatorio_consolidado.txt
├── passo_4-relatorio_validacao.txt
├── passo_4-resumo_executivo.json
├── passo_6-auditoria_completa_*.json
├── passo_6-relatorio_auditoria_*.txt
├── RELATORIO_FINAL_PROJETO_VR_*.txt
├── VR_MENSAL_OPERADORA_*.xlsx
└── logs/
    └── vr_system_*.log
```

## 🏃‍♂️ Comandos Make Utilizados

- `make run`: Pipeline completo com auditoria (6 passos)
- `make debug`: Execução com logs detalhados
- `make status`: Verificação do ambiente

## 🔍 Monitoramento

Cada execução gera um **resumo detalhado** visível diretamente na interface do GitHub Actions, incluindo:

- 📈 **Estatísticas** da execução
- 📁 **Lista de arquivos** gerados  
- ✅ **Status** de cada etapa
- ⏱️ **Tempo** de execução

---

Para mais informações, consulte a [documentação principal](../README.md) do projeto.
