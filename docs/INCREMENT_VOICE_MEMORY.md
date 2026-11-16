# Entrega incremental: fundação de voz e preferências

Base: commit `5caadce`, branch `work`. A aplicação original, os testes anteriores e o kit Qwen foram preservados. A rede desta instância ainda não permite o manifesto Qwen, portanto a entrega avança em código independente dos pesos.

- `now_memory`: preferências opt-in, SQLite criptografado/autenticado, senha não persistida, CLI e controles de privacidade. [Guia](NOW_MEMORY.md).
- `now_voice`: contratos de áudio, controlador com permissões/estados/cancelamento, planejamento de pausas/estilo e CLI de texto. [Arquitetura](NOW_VOICE_ENGINE.md).
- `now_engine.assistant`: novo adaptador local, com comandos PT-BR/EN e instruções gerais Casual. A API e o terminal originais continuam preservados. O caminho gerativo novo precisa de teste real após o modelo instalado.
- [Plano de GUI](GUI_PLAN.md): Windows/Android, acessibilidade, estados reais, integração e autenticação antes de APIs privadas.

Não há STT/TTS, detector “Now”, memória de conversas, sincronização, GUI ou qualidade vocal aprovados. Os testes com doubles de áudio validam apenas a orquestração. Resultados executados e bloqueios constam em `../VALIDACAO.md`.

```bash
.venv/bin/python -m pip install -r requirements-memory.txt
.venv/bin/python -m unittest discover -v
.venv/bin/python -m now_voice --capabilities
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory status
```

Status não cria armazenamento; `init --consent` é uma ação separada. Não crie cofres, senhas ou autorizações de microfone automaticamente ao instalar o ambiente. Retomada: [NEXT_TASK.md](NEXT_TASK.md).
