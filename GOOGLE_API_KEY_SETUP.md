# 🔑 Configuração da API Key do Google Gemini

## ❌ Problema Identificado
A API key atual não é válida para o Google Gemini:
- **Chave atual**: `IzaSyCqhTMK23vm04zwLAYjE4awzVcwFVOeP2o`
- **Problema**: Formato incorreto (parece ser do Google Maps API)

## ✅ Como Obter a API Key Correta

### 1. **Acessar o Google AI Studio**
🔗 [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 2. **Fazer Login**
- Use sua conta Google
- Aceite os termos de uso se solicitado

### 3. **Criar Nova API Key**
- Clique em **"Create API Key"**
- Escolha **"Create API key in new project"** (recomendado)
- Copie a chave gerada

### 4. **Identificar o Formato Correto**
✅ **Formato válido**: `AIzaSy...` (sempre começa com "AIza")
❌ **Formato inválido**: `IzaSy...` (sem o "A" inicial)

## 🔧 Como Configurar no GitHub

### 1. **Atualizar o Secret no GitHub:**
1. Vá para **Settings** → **Secrets and variables** → **Actions**
2. Clique em **GOOGLE_API_KEY**
3. Clique **"Update secret"**
4. Cole a nova chave (formato `AIza...`)
5. Salve

### 2. **Testar a Configuração:**
Execute o comando de teste:
```bash
make test-api
```

## 🚨 Pontos Importantes

### **Diferenças entre APIs Google:**
- **Google AI Studio (Gemini)**: `AIza...` ✅ 
- **Google Cloud Console**: Formato diferente
- **Google Maps API**: `IzaSy...` ❌

### **Verificações de Segurança:**
- ✅ API Key ativa no Google AI Studio
- ✅ Projeto com billing habilitado (se necessário)
- ✅ API Generative Language habilitada

### **Limites Gratuitos:**
- Google Gemini oferece cota gratuita generosa
- Monitor o uso em: [Google AI Studio → Usage](https://aistudio.google.com/app/usage)

## 🧪 Testar Localmente

```bash
# Definir a variável
export GOOGLE_API_KEY="sua_chave_aqui"

# Testar a API
make test-api

# Se funcionar, executar o sistema
make run
```

## 📞 Suporte

Se continuar com problemas:
1. ✅ Verificar se a chave está no formato `AIza...`
2. ✅ Confirmar que foi copiada completamente
3. ✅ Testar em uma requisição simples
4. ✅ Verificar logs de quota no Google AI Studio

---

**Após atualizar a API key, re-execute o workflow no GitHub Actions!** 🚀
