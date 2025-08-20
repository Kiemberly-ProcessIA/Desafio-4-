# 🚀 Configuração do GitHub Actions

## 📋 Resumo

Este documento explica como configurar o GitHub Actions para executar o Sistema VR com a API do Google Gemini.

## 🔑 Configurando Secrets

### 1. API Key do Google Gemini

Para que o sistema funcione no GitHub Actions, você precisa adicionar a API key como um **secret**:

1. **Acesse seu repositório no GitHub**
2. **Vá em `Settings` → `Secrets and variables` → `Actions`**
3. **Clique em `New repository secret`**
4. **Configure:**
   - **Name**: `GOOGLE_API_KEY`
   - **Value**: Sua chave da API do Google Gemini (começa com `AIza...`)

### 2. Onde obter a API Key

- **Google AI Studio**: https://aistudio.google.com/app/apikey
- **Documentação**: https://ai.google.dev/gemini-api/docs/api-key

## 🔄 Workflows Disponíveis

### CI - Sistema VR (`ci.yml`)
- **Trigger**: Push para `main/develop`, Pull Requests
- **Funcionalidades**:
  - ✅ Testes básicos (sempre executados)
  - 🔑 Teste da API (só se secret configurado)
  - 🚀 Execução completa (só se secret configurado)

### Executar Sistema VR (`run-sistema.yml`)
- **Trigger**: Manual (`workflow_dispatch`)
- **Funcionalidades**:
  - Execução completa com diferentes ambientes
  - Upload de resultados e logs
  - Requer API key configurada

## 🛡️ Segurança

- ✅ API keys são armazenadas como secrets (criptografados)
- ✅ Secrets não aparecem nos logs
- ✅ Workflows continuam funcionando mesmo sem API key (modo básico)

## 🔍 Verificação Local

Para testar localmente antes de fazer push:

```bash
# Definir a API key temporariamente
export GOOGLE_API_KEY="sua_chave_aqui"

# Testar a API
make test-api

# Executar testes básicos
make test-ci

# Executar sistema completo
make run
```

## 🚨 Troubleshooting

### Erro: "API key not valid"
- ✅ Verifique se o secret `GOOGLE_API_KEY` está configurado
- ✅ Confirme que a API key é válida no Google AI Studio
- ✅ Verifique se a API key começa com `AIza`

### Workflow falha sem secret
- ✅ Workflows agora têm `continue-on-error: true`
- ✅ Testes básicos sempre executam
- ✅ Execução com API é opcional

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs do GitHub Actions
2. Execute `make test-api` localmente
3. Consulte a documentação da API do Google Gemini
