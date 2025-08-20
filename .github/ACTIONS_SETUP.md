# Configuração do GitHub Actions - Sistema VR

Este documento explica como configurar o GitHub Actions para executar o sistema usando os comandos do Makefile.

## 🔧 Configuração Inicial

### 1. Secrets Necessários

Configure os seguintes secrets no seu repositório GitHub:
`Settings → Secrets and variables → Actions → New repository secret`

- **`GOOGLE_API_KEY`**: Sua chave de API do Google Gemini 2.0 Flash

### 2. Environments (Opcional)

Para maior controle, crie os environments:
`Settings → Environments → New environment`

- **`homologacao`**: Para testes
- **`producao`**: Para execução real

## 🚀 Workflows Disponíveis

### CI - Sistema VR (`ci.yml`)

- **Trigger**: Push/PR para main/develop
- **Executa**: 
  - `make install` - Configura ambiente
  - `make status` - Verifica sistema
  - `make format-check` - Verifica formatação
  - `make lint` - Análise de código
- **Não precisa**: API key real ou dados

### Deploy - Sistema VR (`deploy.yml`)

- **Trigger**: Manual (workflow_dispatch)
- **Executa**: Comando do Makefile escolhido
- **Comandos disponíveis**:
  - `make status` - Verificar sistema
  - `make run` - Pipeline completo com auditoria
  - `make pipeline-simples` - Pipeline sem auditoria
  - `make debug` - Modo debug com JSONs intermediários
- **Precisa**: API key e dados no repositório

## 📋 Como Executar

### 1. Execução Manual (Deploy)

```
GitHub → Actions → Deploy - Sistema VR → Run workflow
├── Comando: Escolha qual make executar
└── Ambiente: homologacao/producao
```

### 2. Execução Automática (CI)

- Push ou Pull Request para `main` ou `develop`
- Executa validações automaticamente usando comandos do Makefile

## 📊 Resultados

### Artifacts Gerados

- **`resultado-{comando}-{ambiente}`**: Planilhas e relatórios finais
- **`logs-{comando}-{ambiente}`**: Logs de execução

### Relatórios

- Summary automático no GitHub Actions
- Upload de arquivos por 30 dias (resultados) / 7 dias (logs)

## ⚠️ Considerações Importantes

1. **API Key**: Nunca commite a API key no código
2. **Dados**: Arquivos Excel não são commitados (ver .gitignore)
3. **Custos**: Cada execução consome créditos da API Gemini
4. **Tempo**: Pipeline completo demora ~3-5 minutos
5. **Consistência**: Usa os mesmos comandos `make` do desenvolvimento local

## 🔒 Segurança

- ✅ API keys protegidas por GitHub Secrets
- ✅ Verificação automática de vazamento de secrets
- ✅ Arquivos sensíveis no .gitignore
- ✅ Ambientes separados (homolog/prod)

## 🐛 Troubleshooting

### CI falhando?

```bash
# Localmente
make lint
make format-check
```

### Deploy falhando?

- Verificar se `GOOGLE_API_KEY` está configurada
- Verificar se dados estão na pasta `input_data/`
- Conferir logs no Actions

### Sem dados para testar?

- Use ambiente `homologacao` 
- Execute comando `status` (não precisa de dados reais)
- Faz apenas validação do sistema

## 🎯 Vantagem da Abordagem

**Consistência Total**: Os mesmos comandos que você usa localmente funcionam no GitHub Actions!

```bash
# Local
make run

# GitHub Actions  
make run
```
