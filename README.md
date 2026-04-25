# rllm — Roteamento Inteligente de LLMs

CLI que roteia automaticamente seus prompts para o modelo de linguagem mais adequado, usando um **direcionador** de baixo custo como orquestrador.

## Como funciona

```
Prompt do usuário
       │
       ▼
  ┌─────────────┐
  │ Direcionador │  ← modelo barato (Groq, Gemini Flash, Ollama...)
  └─────────────┘
       │
       │  classifica: low / medium / high
       ▼
  ┌─────────────────────────────────────┐
  │            Arsenal do usuário        │
  │  fast (low)  │ balanced │ smart (high)│
  └─────────────────────────────────────┘
       │
       ▼
   Resposta
```

O **direcionador** avalia a complexidade do prompt e roteia para o LLM com melhor custo-benefício para aquela tarefa.

## Instalação

```bash
pip install roteamento-llm
# ou em modo desenvolvimento:
pip install -e ".[dev]"
```

## Início rápido

### 1. Configure o direcionador (orquestrador)

```bash
rllm direcionador set
```

Recomendamos modelos gratuitos ou de baixo custo:
- **Groq** `llama-3.1-8b-instant` (gratuito com limite)
- **Google Gemini Flash** (gratuito com limite)
- **Ollama** (local, totalmente gratuito)

### 2. Adicione LLMs ao arsenal

```bash
rllm add
```

Exemplo de arsenal:
| Alias | Provider | Modelo | Nível |
|-------|----------|--------|-------|
| fast | groq | llama-3.1-8b-instant | low |
| balanced | openai | gpt-4o-mini | medium |
| smart | anthropic | claude-sonnet-4-6 | high |

### 3. Envie prompts

```bash
rllm chat "Qual é a capital do Brasil?"
# → direcionador detecta: low → roteia para 'fast'

rllm chat "Explique o algoritmo de Dijkstra com exemplos em Python"
# → direcionador detecta: medium → roteia para 'balanced'

rllm chat "Projete uma arquitetura de microsserviços para e-commerce com alta disponibilidade"
# → direcionador detecta: high → roteia para 'smart'
```

## Comandos

```
rllm chat "<prompt>"          Envia prompt com roteamento automático
rllm chat "<prompt>" --use fast  Força um LLM específico

rllm add [alias]              Adiciona LLM ao arsenal (interativo)
rllm list                     Lista LLMs configurados
rllm remove <alias>           Remove um LLM

rllm direcionador set         Configura o orquestrador
rllm direcionador show        Mostra configuração atual
rllm direcionador test "<prompt>"  Testa avaliação sem chamar LLM

rllm config show              Mostra configuração completa (YAML)
rllm config path              Mostra caminho do arquivo de config
rllm version                  Versão instalada
```

## API Keys via variável de ambiente

Ao adicionar um modelo, você pode informar `env:NOME_DA_VAR` como API key:

```bash
# Ao adicionar:
API Key: env:OPENAI_API_KEY

# E depois export no shell:
export OPENAI_API_KEY="sk-..."
```

## Provedores suportados

| Provider | Chave |
|----------|-------|
| OpenAI | `openai` |
| Anthropic | `anthropic` |
| Google Gemini | `google` |
| Groq | `groq` |
| Ollama (local) | `ollama` |
| OpenRouter | `openrouter` |
| Mistral | `mistral` |
| DeepSeek | `deepseek` |
| xAI (Grok) | `xai` |
| Together AI | `together` |
| Perplexity | `perplexity` |

Qualquer provedor compatível com a interface OpenAI também funciona via `openrouter` ou configurando `extra_params` manualmente no YAML.

## Arquivo de configuração

O arquivo fica em `~/.rllm/config.yaml`:

```yaml
direcionador:
  api_key: env:GROQ_API_KEY
  model: llama-3.1-8b-instant
  provider: groq

arsenal:
  - alias: fast
    provider: groq
    model: llama-3.1-8b-instant
    api_key: env:GROQ_API_KEY
    complexity_levels: [low]
    description: Respostas rápidas e baratas

  - alias: balanced
    provider: openai
    model: gpt-4o-mini
    api_key: env:OPENAI_API_KEY
    complexity_levels: [medium]
    description: Equilíbrio custo/qualidade

  - alias: smart
    provider: anthropic
    model: claude-sonnet-4-6
    api_key: env:ANTHROPIC_API_KEY
    complexity_levels: [high]
    description: Tarefas complexas
```
