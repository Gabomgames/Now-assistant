# NOW Brain API v1 — primeiro incremento V5

Perfil entregue: **local, uma geração por processo, loopback autenticado**.
É uma API independente do Qt, do histórico e dos cofres. Reutiliza os contratos
internos de contexto/persona e limites de extensão do Engine existente. Não é um
servidor público/multiusuário; não disponibiliza rotas de senha, memória, arquivos
ou ferramentas. Não há treinamento, coleta privada, fallback comercial nem API
que receba URLs de provedores. vLLM/llama.cpp remotos, quotas distribuídas e OIDC
pertencem a uma fase posterior com infraestrutura e autorização próprias.

A GUI atual continua no `/v2` e conserva seu cancelamento anterior. O novo
streaming/cancelamento é entregue na **API v1 e no cliente nativo de validação**;
não se afirma que a janela atual já consome SSE. A distribuição Alpha anterior,
logo, bancos e workflows não foram substituídos. O módulo de autenticação local
foi extraído sem mudar o contrato `/v2`.

## Instalar sem Qt ou SDK proprietário

No checkout existente `work`, Python 3.12 x64, PowerShell:

```powershell
git status --short
git log -3 --oneline
py -3.12 -m venv .venv-brain
.\.venv-brain\Scripts\python.exe -m pip install -r requirements-brain.txt
.\.venv-brain\Scripts\python.exe -m pip check
```

Reutilize o venv existente se já preparado. Não faça reset/clean nem sobreponha
cofres. Linux: `python -m venv .venv-brain` e `.venv-brain/bin/python`.
Ollama e pesos continuam separados. O validador abaixo usa o Ollama **já ativo**;
não instala, baixa pesos, inicia ou encerra o serviço do usuário.

## Validação real no Windows 10 com o Ollama já instalado

Confirme as tags disponíveis, sem novo download:

```powershell
ollama list
.\.venv-brain\Scripts\python.exe tools\validate_brain_api.py --models qwen2.5:0.5b qwen2.5:1.5b --timeout 300 --output "$env:TEMP\now-brain-v5-check-01"
```

Escolha uma pasta de saída **nova**. Alternativa, sem alterar ExecutionPolicy:

```powershell
& .\tools\validate_brain_windows.ps1 -Models 'qwen2.5:0.5b','qwen2.5:1.5b' -GenerationTimeout 300
```

Se a política local não permitir scripts PowerShell, use o comando Python.
Em máquinas lentas, execute uma tag por vez em diretórios novos. São 20 casos
por modelo, alternando resposta JSON completa e SSE, mais um teste de cancelamento.
Eles incluem cinco turnos encadeados, Minecraft, programação, física, gírias,
mudança de idioma, ambiguidade, limites de memória e permissões e profundidade.
Um resultado ruim no 0.5B não altera o baseline nem promove automaticamente 1.5B.

O validador cria/fecha **só sua API filha**, com token aleatório em ambiente e
porta efêmera em loopback. Não abre cofres ou conversa do usuário. As respostas
são aos prompts sintéticos versionados em `validation/brain-v5-cases.json`; as
saídas são apenas avaliação, **não dados de treinamento**. Nada é enviado ao Git,
SG ou a outro serviço. Não copie histórico pessoal para os relatórios.

`evaluation.json` contém sistema, hashes de código/casos, tag/digest/tamanho/
quantização observados, licença para revisão, respostas, status de truncamento,
tempos totais, tempo ao primeiro token e tokens/s reportados pelo Ollama. JSON
completo usa tempo do servidor ao primeiro token; SSE também mede recepção no
cliente. p50/p95/p99 usam nearest-rank e mostram o tamanho da amostra. Não são
SLOs ou benchmark sob carga; com 20 amostras, p95/p99 são pouco estáveis. Não há
medição de VRAM, FPS, RAM do modelo ou CPU do Athlon nesta entrega.

Saídas do processo:

- **0:** todas as gerações de avaliação concluíram; qualidade ainda exige revisão.
- **1:** falha de contrato/execução; veja o caso FAILED e os NOT_RUN restantes.
- **2:** provedor/modelo indisponível; casos não executados permanecem NOT_RUN.

Cancelamento tem resultado próprio DEMONSTRATED/NOT_DEMONSTRATED. Uma geração
muito rápida pode terminar antes do pedido de parada. Fechar o socket upstream
é verificável; liberação imediata de CPU/GPU pelo serviço externo Ollama **não**
é presumida. Mesmo com saída 0, `quality` continua NOT_SCORED até revisão humana.
Compare idiomas, correção, naturalidade, continuidade, persona, comprimento,
alucinações e honestidade sobre acesso/memória usando o campo `review` de cada caso.
Licença observada não equivale a aprovação jurídica/comercial.

## Iniciar a API independente manualmente

Gere um segredo **de processo** sem imprimi-lo. Não o salve no código ou no Git:

```powershell
$env:NOW_BRAIN_TOKEN = (& .\.venv-brain\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
$env:ENABLE_GEMINI_FALLBACK = 'false'
$env:OLLAMA_MODEL = 'qwen2.5:1.5b' # somente se instalado; não é recomendação de qualidade
.\.venv-brain\Scripts\python.exe -m now_brain --port 8765 --timeout 300
```

Linux: exporte um token aleatório gerado com `secrets.token_urlsafe(32)` sem
registrar seu valor, depois execute `.venv-brain/bin/python -m now_brain`.
O comando vincula exclusivamente `127.0.0.1`; não oferece `--host` público.
Clientes nativos usam `Authorization: Bearer <token>`; a API recusa `Origin` de
navegador, Host externo, segredo errado e corpo acima de 64 KiB. Não configure
CORS permissivo, port forwarding nem exponha o serviço local para SG/Android.
O perfil NOW Server com identidade/tenant real ainda não existe.

## Contrato HTTP

Prefixo `/api/now/v1`. Todas as rotas, incluindo OpenAPI, exigem Bearer. Não há
Swagger público. A especificação pode ser obtida por um cliente nativo autorizado
em `/openapi.json`; o validador salva uma cópia. Os erros de validação são
reduzidos e não devolvem prompts/inputs. `X-Request-ID` é gerado pelo servidor,
e as respostas usam `Cache-Control: no-store`. Sem logs de acesso/conversas.

| Rota | Comportamento |
| --- | --- |
| `GET /health` | Liveness 200 e prontidão separada do modelo padrão; `ready:false` não é falha de processo. |
| `GET /capabilities` | Recursos implementados versus modelo pronto; counters sem conteúdo e limites do processo. |
| `GET /models` | Tags locais observadas, digest e quantização; filtra entradas remotas/cloud. 503 se Ollama não responder. |
| `POST /chat` | Geração completa, mesmas políticas do streaming, cancelável por desconexão. |
| `POST /chat/stream` | SSE real com eventos `state`, `delta`, `done` ou erro terminal `error`. |
| `POST /chat/cancel` | Para o request_id ativo deste processo; autorização pelo Bearer, nunca por user_id enviado pelo cliente. |

Exemplo de corpo:

```json
{
  "model_id": "qwen2.5:1.5b",
  "mode": "model",
  "messages": [{"role": "user", "content": "Achei uma vila no Minecraft. O que faço primeiro?"}],
  "options": {"language": "pt-BR", "persona": "casual", "humor": 1, "reply_length": "balanced"}
}
```

`model_id` omitido usa `OLLAMA_MODEL` ou o padrão legado `qwen2.5:0.5b`; nenhuma
tag é promovida sem benchmark/revisão. `mode:model` sempre tenta inferência,
inclusive em saudações. `mode:offline` só aceita comandos locais reconhecidos,
com `provider_id:offline`; não faz fallback silencioso.

Até 20 mensagens user/assistant, última user até 4.000 caracteres, anteriores
até 12.000; contexto efetivo até 12 mensagens/6.000 caracteres, com sinalização
`context_trimmed`. Opções são validadas estritamente: PT-BR/EN, cinco personas,
humor 0–3 e short/balanced/detailed (192/512/1024 tokens). Teto de saída 12.000
caracteres, deadline configurável 1–900 s (padrão 180). `conversation_id`, quando
fornecido, é UUID canônico de correlação: **não** dá acesso a dados persistidos.
O servidor não lembra conversas; envie o contexto autorizado a cada requisição.
Preferências explícitas de sessão não significam memória permanente.

O resultado inclui api_version, request_id, conversation_id, model_id,
provider_id, status, reply, finish_reason, context_messages, context_trimmed e
metrics. `truncated` indica encerramento `length`; nunca é qualidade aprovada.
Não use respostas canceladas/interrompidas como turnos completos no contexto.

SSE: cada evento tem `event: nome`, `data: JSON` e linha vazia. `state` informa
request_id; `delta` traz apenas texto novo; `done` contém o resultado completo
para confirmação. Em erro após os headers, `error` é terminal, **sem `done` de
sucesso**. Exija terminal válido, não interprete EOF abrupto como conclusão.
O cliente nativo `now_brain.client.Client` demonstra leitura incremental e
fechamento seguro. Cancelamento: `{"request_id":"UUID da state"}` no endpoint
`/chat/cancel`; resulta em done/cancelled quando o cliente ainda está conectado.
Desconectar também fecha o socket Ollama e libera o slot local.

Não há fila: uma geração ativa por processo, segunda recebe 409/busy. Até 60
admissões de chat/minuto por processo; excesso recebe 429/quota_exceeded.
Cancelamento não é bloqueado por quota. O leitor faz uma leitura limitada por
vez, sem fila de tokens ilimitada; o próximo chunk só é puxado após o consumo
anterior. Limites por linha NDJSON e deadline limitam o fornecedor malformado.

Erros estáveis: `invalid_request` 422, `model_not_allowed` 422,
`offline_command_unknown` 422, `unavailable`/`model_not_installed` 503,
`timeout` 504, `interrupted`/`provider_error`/`output_limit`, `busy` 409,
`quota_exceeded` 429, `request_not_found` 404. Corpo de erro v1 tem api_version
e error com code/request_id/retryable, sem texto privado. Em SSE, o erro
terminal contém o mesmo detalhe, pois o HTTP 200 já foi enviado.

## Validar regressões e limitações

No venv desktop existente:

```powershell
.\.venv-desktop\Scripts\python.exe tools\run_tests.py --report "$env:TEMP\now-v5-tests.json"
.\.venv-desktop\Scripts\python.exe -m now_desktop --smoke-output "$env:TEMP\now-v5-desktop-new"
```

`tests.test_brain_api_v1` executa Uvicorn, HTTP/SSE e sockets reais contra uma
**fixture de protocolo**, incluindo timeout, stream quebrado, cancelamento,
autenticação, payload, quota e isolamento de contexto. Isso não gera tokens de
um modelo. `tools/validate_brain_api.py` é a avaliação independente com Ollama
real; não deve ser substituída por fixtures para declarar inferência aprovada.

Na nuvem desta tarefa: Ollama ausente e downloads/registro oficiais com CONNECT
403. Portanto inferência e qualidade ficam BLOQUEADAS/NOT_RUN. Testes Linux não
aprovam Windows 10/8 GB, licenças, desempenho do Athlon, SG ou produção. Resultados
observados e commits são registrados em `VALIDACAO.md`.

Próximo incremento: executar o validador no Windows, revisar respostas e comparar
modelos antes de escolher um padrão; depois migrar a GUI para SSE sob testes de
compatibilidade. Memória de fatos, RAG, voz, visão, ações e NOW Server continuam
fora deste escopo. Rollback: reverter os commits deste incremento; não há
migração de banco. Produção SG, releases, Alpha e deploy não são acionados pelo
validador nem pelo serviço.
