# Plano: Migrar Backend para Funções Python Vercel (Opção A)

TL;DR: Converter endpoints Flask (/api/chat, /api/model-status, /api/health) em funções Python stateless na pasta `api/` (raiz do projeto Vercel), centralizar lógica de entrevista usando `ConversationState` no cliente (ou enviar estado completo a cada requisição), encapsular fallback Gemini em módulo reutilizável puro, adicionar testes (Vitest/RTL para frontend, pytest para backend), configurar variáveis (`GEMINI_API_KEY`) e ajustar root deploy para `frontend/` mantendo funções na raiz.

## Objetivos
1. Deploy do frontend React/Vite no Vercel (Root Directory: `frontend/`).
2. Substituir Flask por funções serverless Python compatíveis com Vercel (`api/*.py`).
3. Tornar o backend stateless eliminando armazenamento em memória de conversas; estado fica no cliente.
4. Extrair fallback de modelos Gemini para módulo independente testável.
5. Introduzir TDD (Vitest + React Testing Library no frontend; pytest no backend).
6. Configurar variáveis de ambiente seguras (não commitar `.env`).
7. Documentar fluxo de build, testes e deploy.

## Escopo de Refatoração
- Remover dependência direta de Flask (`backend/api.py` será substituído por funções em `api/`).
- Unificar lógica de fases usando apenas `ConversationState` em frontend; servidor recebe lista completa de mensagens + fase.
- Criar módulo `api/ai_fallback.py` com função pura `run_gemini_fallback(models: list[str], system_instruction: str, messages: list[dict]) -> dict`.
- Reescrever endpoint `chat` para: validar payload → chamar fallback → retornar resposta e metadados (modelo escolhido, tentativas).
- Reescrever endpoints `model-status` e `health` como funções simples.

## Estrutura Proposta
```
/ (root Vercel project)
  api/
    chat.py
    model_status.py
    health.py
    ai_fallback.py
  frontend/  (Root Directory configurado no Vercel)
    package.json
    vite.config.js
    src/
      ... (App.jsx, main.jsx, etc.)
  src/ (Python util, poderá ser parcialmente movido ou mantido para testes)
    conversation.py
  tests/
    python/
      test_ai_fallback.py
      test_conversation_state.py
    frontend/ (Vitest auto-descoberta em `frontend/src/__tests__`)
  .env.example
  README.md (atualizado)
```

## Detalhes de Implementação
### 1. Funções Serverless Python (Vercel)
Cada arquivo em `api/` exportará um `handler(request)` que retorna dict: `{"status": int, "headers": {...}, "body": string}`.
- `chat.py`: parse JSON (mensagens, fase, modelos opcionais), valida, chama `run_gemini_fallback`, formata resposta.
- `model_status.py`: retorna lista de modelos disponíveis com ordem de fallback.
- `health.py`: retorna `{ ok: true, timestamp }`.

### 2. Stateless Conversa
Frontend mantém `ConversationState`. A cada envio: envia payload `{ messages, phase }`. Backend não persiste nada.

### 3. Fallback Gemini
Implementar tentativa sequencial com tempo máximo por chamada e captura de exceções; retorna primeiro sucesso.
Pseudo:
```
for model in models:
  try:
    resp = call_model(model, system_instruction, messages)
    if valido(resp): return { model, content }
  except Exception as e:
    registrar erro
return { model: None, error: "All models failed" }
```

### 4. Tests
Frontend:
- Instalar `vitest`, `@testing-library/react`, `@testing-library/user-event`.
- Testar componente principal: avanço de fases, renderização de pergunta, envio de mensagem.
Backend:
- `pytest` + `requests` (ou httpx) simulando chamadas ao `handler` (chamada direta em vez de HTTP real).
- Testar: sucesso no primeiro modelo, fallback ao segundo, erro geral.
- Testar `ConversationState` (avançar fases, rota customizada).

### 5. Variáveis de Ambiente
- `GEMINI_API_KEY` (chave única).
- `GEMINI_MODELS` (ex: `gemini-2.0-flash-exp,gmini-1.5-flash,gmini-1.5-pro`).
- `SYSTEM_INSTRUCTION` (texto base opcional; senão incorporar diretamente no código).
- Declarar no Vercel (Production / Preview / Development). No código: `os.getenv()`.

### 6. Segurança & Validação
- Limitar tamanho máximo de mensagens (ex: soma chars < 20k).
- Filtrar campos obrigatórios: cada mensagem `{ role: user|assistant|system, content: str }`.
- Timeout por modelo (ex: 10s) para evitar exceder limite serverless.
- Retornar status 400 em payload inválido.

### 7. Build & Deploy
Frontend:
- `npm run build` → output `dist/`.
Vercel Settings:
- Root Directory: `frontend`.
- Build Command: `npm run build`.
- Output: `dist`.
- Serverless functions: Diretório `api/` na raiz.
- Node version: 18+.
- Python version: usar default; validar compatibilidade libs.

### 8. Observabilidade Inicial
- Logging mínimo via `print(f"[chat] model={model} success")`.
- Retornar no JSON: `{ model_used, attempts }`.

### 9. README Atualizado
Seções:
- Arquitetura.
- Fluxo de conversa (estado no cliente).
- Endpoint contract.
- Variáveis Ambiente.
- Testes e scripts.
- Deploy Vercel.

### 10. Scripts
Frontend `package.json`:
```
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview",
  "test": "vitest",
  "test:ui": "vitest --ui"
}
```
Backend (pytest) no root ou em `tests/python`: comando `pytest -q`.

## Cronograma Sugerido
1. Extrair fallback (módulo puro) e criar testes de unidade.
2. Criar funções `api/*.py` substituindo Flask.
3. Adaptar frontend para enviar `phase` e lista completa de `messages`.
4. Introduzir Vitest & primeiros testes UI.
5. Variáveis de ambiente & README atualizado.
6. Teste local integrado (`vercel dev`).
7. Deploy inicial (Preview) → ajustar.
8. Harden (validações, limites) → Deploy produção.

## Riscos & Mitigações
- Timeout fallback → reduzir número de modelos ou tempo por chamada.
- Erro de compatibilidade Python no Vercel → simplificar dependências ou migrar AI call para Node.
- Crescimento tamanho de conversa → paginar ou resumir no cliente antes de enviar.

## Próximos Passos (Execução)
1. Implementar `api/ai_fallback.py`.
2. Criar `api/chat.py`, `api/model_status.py`, `api/health.py`.
3. Ajustar frontend para novo contrato stateless.
4. Adicionar suites de teste.

(Arquivo criado para refinamento antes da execução.)
