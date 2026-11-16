# NOW AI 0.2 — NOW Engine

Evolução da NOW AI 0.1: mantém terminal e comandos offline, acrescenta FastAPI, Ollama local e fallback opcional para Gemini.

## Windows / VS Code (PowerShell)

1. Instale Python 3.11+ e abra esta pasta no VS Code.
2. `py -m venv .venv`
3. `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
4. `Copy-Item .env.example .env`
5. Instale Ollama no Windows pelo site oficial https://ollama.com/download e abra o aplicativo.
6. No terminal: `ollama pull qwen2.5:0.5b` (precisa de internet apenas para baixar o modelo).
7. Execute o terminal NOW: `.\.venv\Scripts\python.exe main.py`
8. Em outro terminal, inicie a API: `.\.venv\Scripts\python.exe -m uvicorn now_engine.api:app --host 127.0.0.1 --port 8000`
9. Abra http://127.0.0.1:8000/docs para testar `POST /v1/chat` com `{"message":"Oi Now"}`.
10. Testes: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

Para permitir Gemini como alternativa, altere `ENABLE_GEMINI_FALLBACK=true` e configure `GEMINI_API_KEY` no `.env`. O Gemini não é necessário para comandos offline ou modelo local.

**Segurança:** a API escuta apenas 127.0.0.1; não abra portas nem exponha o servidor na internet. Antes de publicar, implementar autenticação, HTTPS, limitação de requisições e políticas de privacidade. Não compartilhe o `.env`.

**Limitações:** sem memória persistente, voz, ativação por palavra-chave, Android ou GPU remota. O Ollama precisa estar rodando. O modelo pequeno tem qualidade limitada. O histórico de conversas do Gemini 0.1 não foi preservado, pois era somente memória temporária do processo.
