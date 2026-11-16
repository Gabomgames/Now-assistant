# Continuar em uma nova tarefa Codex

Use o checkout existente em `/workspace/Now-assistant`; a tarefa já está isolada. Não crie worktree, não substitua o checkout nem use reset/clean sobre arquivos locais. Os arquivos originais da NOW AI 0.2 e todo o histórico de relatórios devem permanecer preservados.

## Confirmar a versão e o estado

```bash
cd /workspace/Now-assistant
git status --short
git log -1 --format='%H %s'
git branch --show-current
```

O commit desta entrega inclui a base antes sem commits, a preparação Windows anterior e o módulo `training/`. O resultado do envio remoto deve ser conferido no retorno da tarefa e com uma operação Git de leitura; não assuma push ou restauração sem evidência. O destino previsto para envio é a branch `work`, preservando `main`.

No painel do ambiente, revisar e salvar as instruções e a seleção de repositório atualizadas e publicar o snapshot quando desejado. Uma nova tarefa deve selecionar essa versão publicada. Salvar um rascunho não executa instalação nem atualiza outras tarefas já abertas. Publicação e restauração devem ser verificadas na nova tarefa, não presumidas a partir do teste nesta máquina.

## Retomar primeiro o que funciona offline

Se a `.venv` e as dependências não tiverem sido restauradas, usar o script de instalação salvo nas configurações do ambiente. A cópia local está em `/workspace/.now-ai-environment/install.sh`. Alternativa para um checkout fora desse snapshot: Python 3.12, `python3 -m venv .venv` e `.venv/bin/python -m pip install -r requirements.txt -c packaging/windows/constraints-python312.txt`.

```bash
cd /workspace/Now-assistant
.venv/bin/python -m unittest discover -v
.venv/bin/python training/scripts/validate_dataset.py
.venv/bin/python training/scripts/train_lora_gpu.py --dry-run
.venv/bin/python training/scripts/run_ollama_eval.py --dry-run
```

Nenhum desses comandos de preparação precisa de Ollama, GPU ou dependências de ML. A suíte completa também usa as dependências FastAPI já instaladas e inicia processos temporários de API/CLI com saída de rede negada. Não classificar dry-run como treino ou inferência.

## Quando a tarefa exigir modelos reais

1. Consultar a política **aplicada** da instância. O rascunho já solicita `registry.ollama.ai`, mas a última observação do runtime continuava sem essa regra. Não regravar a mesma regra nem contornar o proxy.
2. Se o acesso estiver aplicado, iniciar Ollama em loopback com `OLLAMA_NO_CLOUD=1` e modelos em `/workspace/.now-ai-environment/models`; as instruções completas estão no `start_skill` salvo.
3. Executar o pull normal de `qwen2.5:0.5b` e conferir inventário. Se houver novo bloqueio de blob, registrar o hostname exato observado; não adivinhar nem liberar destinos amplos.
4. Iniciar a API original com Gemini desligado: `ENABLE_GEMINI_FALLBACK=false .venv/bin/python -m uvicorn now_engine.api:app --env-file .env --host 127.0.0.1 --port 8000`.
5. Executar `tools/validate_local.py --output <arquivo-novo.json>` para oito gerações pelos caminhos existentes, e `training/scripts/run_ollama_eval.py --model qwen2.5:0.5b` para os 12 casos de persona. Ler as respostas e registrar revisão humana. São avaliações distintas.

Não importar outputs sintéticos como evidência de inferência. Não iniciar treino com o piloto de 36 registros. A procedência/licença permanece pendente e o treinamento real está bloqueado por essas condições, além de corpus/validação/GPU.

Para a próxima fase, seguir `MODEL_ROADMAP.md`. Windows, memória e voz continuam pendentes; não foram validados por estes testes offline. Os nove arquivos originais podem ser verificados usando os hashes e a origem registrados em `VALIDACAO.md` e `training/data/PROVENANCE.json`.
