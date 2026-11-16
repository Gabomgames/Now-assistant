# NOW AI 0.2 — Windows x64 / VS Code

> Guia legado preservado. Para a marca NOW Assistant, a GUI Qt e os comandos atuais de instalação/build, use [DESKTOP_WINDOWS.md](DESKTOP_WINDOWS.md). A interface nova foi executada em Linux; nenhum build Windows foi aprovado. As afirmações de preservação dos nove arquivos neste guia descrevem a etapa anterior: na V3, README e `.gitignore` foram atualizados intencionalmente, mantendo os sete arquivos originais restantes e o histórico Git.

## Estado desta entrega

Os nove arquivos da base original foram preservados. Foram acrescentadas ferramentas de validação real e de empacotamento, sem recriar o projeto. A máquina de desenvolvimento atual é Linux: o `.exe` ainda não foi gerado ou testado em Windows. O modelo local também aguarda liberação de rede no ambiente em nuvem. Consulte `VALIDACAO.md`; não considere os passos abaixo como testes já concluídos.

O executável legado será um aplicativo de terminal com opção de iniciar a API local. Não há GUI, áudio real, ativação por palavra ou aplicativo Android. O incremento opcional oferece preferências criptografadas persistentes e controlador de voz em código-fonte; o build legado não os anuncia como modos empacotados.

## Pré-requisitos no Windows

- Windows x64. Windows 10 é o alvo do projeto; a compatibilidade ainda precisa de teste nessa plataforma.
- Python 3.12 x64, instalado do site oficial, para desenvolvimento e build.
- VS Code e a extensão Python da Microsoft.
- Ollama para Windows, obtido em https://ollama.com/download. O Ollama e o modelo são dependências separadas do futuro `.exe`.
- Internet para a instalação inicial de pacotes e do modelo. A geração usa o modelo local, sem Gemini.

Abra a pasta que contém `main.py`, `requirements.txt` e `now_engine` no VS Code. Escolha **Terminal > New Terminal**, usando PowerShell. Nos comandos abaixo, mantenha-se nessa pasta.

## Instalação e configuração

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -c packaging\windows\constraints-python312.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

No VS Code, use **Python: Select Interpreter** e selecione `.venv\Scripts\python.exe`. Não é necessário ativar o virtualenv nem alterar a política de execução do PowerShell.

No `.env`, mantenha `OLLAMA_MODEL=qwen2.5:0.5b` e `ENABLE_GEMINI_FALLBACK=false`. Nenhuma chave Gemini é necessária. Não sobrescreva configurações existentes e não compartilhe `.env`.

Abra o aplicativo Ollama. Se ele não estiver executando, use `ollama serve` em um terminal dedicado. Não inicie uma segunda instância se a porta 11434 já estiver ocupada pelo Ollama. Em outro terminal:

```powershell
$env:ENABLE_GEMINI_FALLBACK = 'false'
$env:OLLAMA_MODEL = 'qwen2.5:0.5b'
ollama pull qwen2.5:0.5b
ollama list
```

O download só termina quando o Ollama informar sucesso e listar o modelo. Preserve a validação TLS e a verificação de blobs feitas pelo Ollama. Falhas de rede, disco ou modelo precisam ser resolvidas antes de afirmar que o chat funciona.

## API e terminal pelo código-fonte

Terminal do chat:

```powershell
.\.venv\Scripts\python.exe main.py
```

Digite `ajuda`, uma pergunta livre ou `sair`. Perguntas livres precisam retornar `NOW [local]`; `NOW [unavailable]` indica uma falha real de disponibilidade.

Em outro terminal:

```powershell
$env:ENABLE_GEMINI_FALLBACK = 'false'
.\.venv\Scripts\python.exe -m uvicorn now_engine.api:app --env-file .env --host 127.0.0.1 --port 8000
```

A API carrega `.env` por `--env-file`; o CLI já faz esse carregamento. O serviço existente não tem autenticação: mantenha-o em `127.0.0.1` conforme o README original.

## Testes reais e automatizados

Com Ollama e API em execução:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools\validate_local.py --output resultados\conversas-locais.json
```

O último comando envia perguntas reais em português e inglês diretamente ao Ollama, ao NOW Engine, à API e ao terminal. Não usa respostas simuladas. Código de saída 2 significa modelo ausente; 1 significa falha; 0 significa que os caminhos de geração passaram e as respostas precisam de leitura para avaliar idioma e qualidade. O relatório distingue checks aprovados, falhos e não executados. A revisão de idioma é humana: uma resposta não vazia não prova inglês ou português corretos.

O prompt original do Engine pede português brasileiro. Os testes em inglês pedem explicitamente inglês; o comportamento ainda precisa de validação real. O modelo de 0,5 bilhão de parâmetros tem limites de qualidade. A base processa cada pergunta separadamente e não preserva contexto de conversa.

## Gerar o executável, após validar o modelo

O PyInstaller exige build no sistema de destino; este script aceita Windows x64 e Python 3.12. Execute:

```powershell
.\.venv\Scripts\python.exe -m pip install -r packaging\windows\requirements-build.txt
.\.venv\Scripts\python.exe tools\build_windows.py
```

O script executa os seis testes existentes, empacota com PyInstaller e testa o terminal e a API do `.exe` com comandos offline. Cada build usa uma pasta datada para preservar builds anteriores. A saída fica em `release\windows\<data>\NOW-AI\NOW-AI.exe`, com um ZIP ao lado. Erros interrompem o processo; o script não declara um build aprovado se esses checks falharem.

Preserve a pasta inteira `NOW-AI`, inclusive `_internal`. Extraia o ZIP inteiro antes de executar. A distribuição não inclui dados pessoais, `.env`, modelos ou o instalador Ollama. Ela inclui `.env.example`: copie-o para `.env` ao lado do `.exe` se ainda não existir. O launcher carrega essa configuração externa. O Python de desenvolvimento deixa de ser necessário para executar o pacote gerado; o Ollama e o modelo continuam necessários para perguntas livres.

```powershell
# Use o caminho real que o build imprimir.
$exe = '.\release\windows\<data>\NOW-AI\NOW-AI.exe'
& $exe
# Em outro terminal:
& $exe --api
```

Para validar também as perguntas livres do executável, encerre a API Python que você iniciou, inicie a API do `.exe` e, em outro terminal, execute:

```powershell
.\.venv\Scripts\python.exe tools\validate_local.py --cli-executable $exe --output resultados\conversas-executavel.json
```

Nesse segundo terminal, defina `$exe` novamente com o caminho real do build. Leia as oito respostas produzidas antes de marcar idiomas como validados. Registre versão do Windows, modelo, tempos medidos, erros e resultado em `VALIDACAO.md`. Os testes offline do build não substituem essa validação com modelo.

## Problemas comuns

- `unavailable`: confirme `ollama list`, o modelo exato e se o Ollama responde em 127.0.0.1:11434. A API leva até 90 segundos para aguardar o provedor.
- Porta 8000 ocupada: encerre somente a instância que você iniciou ou escolha outra porta com `--port`. Passe a mesma porta ao validador com `--api-port`.
- `403 Forbidden` na nuvem: nas configurações do ambiente Codex, mantenha acesso restrito, inclua `registry.ollama.ai` nos domínios permitidos e salve/aplique a alteração ao ambiente em execução. Esse domínio já consta no rascunho. Um redirecionamento de blob pode exigir outro hostname, a ser identificado pela falha real.
- O build não roda no Linux: execute no Windows; não renomeie um binário Linux como `.exe`.
- Falha ao instalar uma versão de dependência: preserve o erro e confirme Python 3.12 x64. As constraints registram a instalação Linux validada; a instalação Windows ainda precisa ser executada e verificada.

## Kit Qwen integrado: preparação sem Ollama

Na pasta do projeto, estes comandos adicionais validam dados, separação e planejamento sem baixar modelos:

```powershell
.\.venv\Scripts\python.exe training\scripts\validate_dataset.py
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe training\scripts\train_lora_gpu.py --dry-run
.\.venv\Scripts\python.exe training\scripts\run_ollama_eval.py --dry-run
```

O dry-run não é um treinamento ou teste de inferência. Os 36 exemplos piloto não estão aprovados para fine-tuning. O novo perfil Casual/PT-BR/EN está no avaliador; a persona da Engine original foi preservada. Consulte `training/README.md`, `docs/MODEL_ROADMAP.md` e `docs/NEXT_TASK.md` antes de continuar. O pipeline GPU é experimental e não foi executado em Windows ou nesta máquina Linux.

## Novo código de memória e controle de voz

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-memory.txt
.\.venv\Scripts\python.exe -m now_voice --capabilities
.\.venv\Scripts\python.exe -m now_voice --text "time" --language en-US
.\.venv\Scripts\python.exe -m now_memory status
```

São comandos de código-fonte, não um novo `.exe` aprovado. Memória só é criada por `init --consent`, com senha no terminal; consulte `docs/NOW_MEMORY.md`. Estados, permissões, pausas e estilo estão em `docs/NOW_VOICE_ENGINE.md`. A GUI é apenas planejada em `docs/GUI_PLAN.md`. Segurança de ACL, drivers, áudio e builds Windows/Android ainda exigem execução nativa.
