# 📚 Exemplos de Uso - RAGAS Text Comparison

Este documento apresenta exemplos práticos para utilizar a ferramenta de comparação de textos com RAGAS.

## 🚀 Configuração Inicial

### 1. Configuração da API
- **OpenAI API Key**: Insira sua chave da API OpenAI na sidebar
- **Base URL**: Configure o endpoint da API (padrão: `https://api.openai.com/v1`)
- **Modelo**: Clique em "🔄 Buscar Modelos" para carregar modelos disponíveis

### 2. Parâmetros de Avaliação
- **Mode**: Escolha entre F1, Precision ou Recall
- **Atomicity**: Configure como None, High ou Low

---

## 📖 Exemplos Práticos

### Exemplo 1: Avaliação Simples - Informações Factuais

**Texto de Referência:**
```
A Amazônia é a maior floresta tropical do mundo, cobrindo aproximadamente 5,5 milhões de km². 
Ela está localizada principalmente no Brasil, mas também se estende por outros 8 países sul-americanos.
```

**Texto Gerado:**
```
A floresta amazônica é a maior floresta tropical global, com cerca de 5,5 milhões de quilômetros quadrados. 
Localiza-se principalmente no território brasileiro.
```

**Resultado Esperado:** Score alto (0.8-1.0) pois as informações principais são mantidas.

---

### Exemplo 2: Avaliação Simples - Dados Históricos

**Texto de Referência:**
```
A Segunda Guerra Mundial ocorreu de 1939 a 1945. O conflito envolveu mais de 30 países e 
resultou em aproximadamente 70-85 milhões de mortes.
```

**Texto Gerado:**
```
A Segunda Guerra Mundial durou de 1940 a 1945, envolvendo dezenas de países e causando 
milhões de mortes em todo o mundo.
```

**Resultado Esperado:** Score médio (0.6-0.8) devido à data incorreta de início (1940 vs 1939).

---

### Exemplo 3: Avaliação Múltipla - Comparação de Modelos

Use a aba "Avaliação Múltipla" para comparar diferentes versões de respostas:

#### Comparação 1: "GPT-4 vs Referência"
**Referência:** 
```
Python foi criado por Guido van Rossum e lançado pela primeira vez em 1991.
```
**Gerado:** 
```
Python é uma linguagem de programação desenvolvida por Guido van Rossum em 1991.
```

#### Comparação 2: "GPT-3.5 vs Referência"  
**Referência:**
```
Python foi criado por Guido van Rossum e lançado pela primeira vez em 1991.
```
**Gerado:**
```
Python foi inventado em 1990 por Guido van Rossum na Holanda.
```

#### Comparação 3: "Claude vs Referência"
**Referência:**
```
Python foi criado por Guido van Rossum e lançado pela primeira vez em 1991.
```
**Gerado:**
```
A linguagem Python foi desenvolvida por Guido van Rossum, sendo lançada inicialmente em 1991.
```

**Resultado Esperado:** 
- GPT-4: Score alto (~0.95)
- Claude: Score alto (~0.90)  
- GPT-3.5: Score baixo (~0.5) devido ao ano incorreto

---

## 🎯 Casos de Uso Recomendados

### 1. **Avaliação de Chatbots**
Compare respostas de diferentes modelos de IA para a mesma pergunta.

### 2. **Validação de Conteúdo**
Verifique se textos gerados mantêm a precisão factual do conteúdo original.

### 3. **Análise de Resumos**
Avalie se resumos preservam informações factuais importantes.

### 4. **Comparação de Traduções**
Compare diferentes traduções mantendo a precisão factual.

### 5. **Teste A/B de Prompts**
Compare resultados de diferentes prompts para o mesmo modelo.

---

## ⚙️ Configurações Avançadas

### Modo de Avaliação

- **F1**: Balanceamento entre precision e recall
- **Precision**: Foco na precisão das informações geradas
- **Recall**: Foco na cobertura das informações de referência

### Atomicidade

- **None**: Avaliação em nível de documento
- **High**: Avaliação granular, cada claim individual
- **Low**: Avaliação em nível de sentença

---

## 📊 Interpretação dos Resultados

### Scores de Qualidade
- **0.8 - 1.0**: ✅ Alta correção factual
- **0.6 - 0.8**: ⚠️ Correção factual moderada  
- **0.0 - 0.6**: ❌ Baixa correção factual

### Visualizações Gráficas
- **Gráfico de Barras**: Comparação visual dos scores
- **Código de Cores**: Verde (alto), Laranja (médio), Vermelho (baixo)
- **Estatísticas**: Média, máximo, mínimo e total de avaliações

---

## 🔧 Resolução de Problemas

### Erros Comuns

1. **"OPENAI_API_KEY não encontrada"**
   - Verifique se inseriu a API key na sidebar
   - Confirme se a chave está válida

2. **"Erro ao buscar modelos"**
   - Verifique a Base URL
   - Confirme conectividade com a API

3. **Scores muito baixos inesperados**
   - Revise os textos de entrada
   - Ajuste os parâmetros de Mode e Atomicity
   - Teste com modelo diferente

### Dicas de Performance

- Use **gpt-4o-mini** para avaliações rápidas
- Use **gpt-4o** para máxima precisão
- Agrupe avaliações similares em lotes
- Configure Atomicity baseado no nível de granularidade desejado

---

## 📈 Exemplos de Resultados Visuais

Após executar avaliações múltiplas, você verá:

1. **Gráfico Interativo**: Barras coloridas com scores
2. **Métricas Individuais**: Cards com score de cada comparação  
3. **Estatísticas Agregadas**: Resumo estatístico dos resultados
4. **Barra de Progresso**: Acompanhamento em tempo real

---

## 🎉 Próximos Passos

Experimente diferentes combinações de:
- Modelos (GPT-4, GPT-3.5, modelos locais)
- Modos de avaliação (F1, Precision, Recall)  
- Níveis de atomicidade (None, High, Low)
- Tipos de conteúdo (técnico, criativo, factual)

Para suporte adicional, consulte a documentação do RAGAS ou entre em contato com o suporte técnico.
