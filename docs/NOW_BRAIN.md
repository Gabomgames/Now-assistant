# NOW Brain — incremento 1 da V4

O desktop continua usando sua Engine autenticada em loopback e a API `/v2/chat`.
`LocalAssistant` prepara contexto e personalidade; `ModelProvider` separa isso do
transporte `OllamaProvider`. Nenhum texto é enviado a um provedor comercial.
O transporte usa somente o Ollama local, sem proxy HTTP nem redirecionamentos.
Tags cloud e entradas de inventário remoto são recusadas antes do envio do chat.

As preferências existentes da GUI agora controlam `num_predict`: Curta 192,
Equilibrada 512, Detalhada 1024. São limites iniciais para avaliação, não uma
promessa de qualidade ou de desempenho. O teto de 12.000 caracteres do histórico
continua valendo. Respostas vazias, incompletas ou incompatíveis com esse teto
falham sem criar uma mensagem de assistente. Um encerramento Ollama `length`
retorna o texto parcial com aviso visível em PT-BR/EN; `stop` indica encerramento
normal, não aprovação da qualidade da resposta.

Os campos `model`, `finish_reason` e `output_truncated` são aditivos na API v2.
Clientes anteriores podem continuar lendo `reply` e `provider`. O formato do
histórico criptografado não mudou; o aviso de truncamento pertence ao resultado
atual e não é persistido como metadado de histórico nesta etapa.

O contexto é o da conversa selecionada, dentro dos limites já existentes.
Preferências pessoais continuam exigindo as ações explícitas da NOW Memory.
Este incremento não extrai fatos pessoais do chat nem cria memória permanente
automática. A personalidade pede continuidade, naturalidade e honestidade, mas
a aderência dessas instruções depende de avaliação com pesos reais.

## Executar a avaliação real

Pré-requisitos: Python 3.12, `requirements-desktop.txt`, Ollama oficial local
em loopback e um modelo local instalado por rede autorizada. A seleção continua
em `OLLAMA_MODEL`; o padrão legado `qwen2.5:0.5b` foi preservado, sem promovê-lo
a modelo aprovado para qualidade. Não há download automático ou API paga.

Na raiz do repositório, depois de confirmar `ollama list`:

```bash
export ENABLE_GEMINI_FALLBACK=false
export XDG_CACHE_HOME=/workspace/.cache/now-assistant
mkdir -p "$XDG_CACHE_HOME"
# Em Linux sem display, usar QT_QPA_PLATFORM=offscreen.
.venv-desktop/bin/python tools/evaluate_brain.py --output /tmp/now-brain-evaluation-new
```

Escolha um diretório de saída novo. A ferramenta abre a GUI real e sua Engine,
checa o inventário local, envia 20 prompts sintéticos, registra respostas reais,
latência, preferência de extensão e capturas da janela. Usa uma conversa de cinco
turnos com mudança de idioma, seguida de casos independentes. Não lê conversas
ou cofres do usuário. Fecha os processos que iniciou. Saídas: 0 = gerações
concluídas, ainda exigindo revisão; 1 = falha; 2 = modelo indisponível, BLOQUEADO.
Nenhuma saída equivale a aprovação automática da qualidade.

Revise cada resposta em `evaluation.json`: idioma, naturalidade, correção,
continuidade dos cinco turnos, mudanças de assunto, personalidade, diferenças
entre extensões e honestidade sobre memória/permissões. Marque problemas de
truncamento. Compare modelos com os mesmos casos; não publique conversas privadas.

## Limites verificados nesta entrega

Inferência e qualidade: **BLOQUEADAS** nesta instância, por ausência de Ollama e
403 do proxy nos downloads oficiais e no registro de modelos. O relatório real
da tentativa registra zero gerações e 20 casos não executados. Testes de
transporte com fixtures não são inferência. Resultados detalhados em `VALIDACAO.md`.
Streaming visual, cancelamento da geração no servidor, memória de fatos com
consentimento granular e benchmark entre modelos são incrementos posteriores.
Nenhuma integração ou produção Something Gamer foi alterada. Não há build ou
publicação Windows desta implementação. Rollback: reverter apenas o commit do
incremento; não há migração de bancos, alteração da marca ou de workflows.
