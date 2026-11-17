# Continuar em uma nova tarefa Codex

## Direção atual — plataforma própria, 17/11/2026

A solicitação mais recente substitui Ollama como destino obrigatório por uma
plataforma independente. Ler primeiro
`docs/NOW_BRAIN_PLATFORM_ARCHITECTURE.md`, `docs/MODEL_ROADMAP.md` e
`docs/DATA_POLICY.md`. Arquitetura, hardware e custos foram preparados para
revisão; treinamento e hospedagem não estão autorizados por essa proposta.
Usar o HEAD mais recente de `work`, preservando o candidato Fase 6 abaixo.

Próximo incremento: catálogo/adaptadores neutros e inferência direta com pesos
abertos via llama.cpp; vLLM como opção de servidor próprio. Hoje API, contratos
e GUI ainda fixam Ollama em pontos auditados. Preservar esse caminho como
compatibilidade e rollback; não afirmar que novos runtimes já foram testados.
A avaliação dos 20 casos e das tags instaladas continua necessária, sem impedir
a preparação da independência solicitada na nova direção.

NOW Dataset/Training Lab: 36 exemplos sem licença/aprovação, 12 casos de teste;
19 testes do pipeline aprovados nesta revisão e dry-run sem treino/GPU.
Evidência: `validation/platform-direction-20261117/audit.json`. Antes de alterar
pesos, implementar controles por execução e obter aprovação do dataset,
modelo-base, manifesto do experimento e orçamento. Aprovação para promover ou
implantar é separada. Não usar chats/memória/saídas GPT ou Gemini no treino sem
as autorizações e direitos específicos; memória armazenada não é aprendizado
dos pesos. Preços cloud não puderam ser consultados (CONNECT 403); números da
proposta são premissas orçamentárias, não cotações.

Nenhum runtime, modelo, cofre, teste, workflow ou build Windows foi modificado
nesta revisão documental; nenhum treino, provisionamento ou deploy foi executado.
As seções abaixo preservam os resultados anteriores, não prevalecem sobre essa
direção mais recente. Release/deploy/Something Gamer continuam exigindo
autorização explícita.

## Estado atual — Fase 6 / Brain na interface

Código Fase 6 em `dec954030215a262ac2f77bcfebffa4b846fafed`, `work`; usar o HEAD
mais recente sem resetar. Desktop usa v1/SSE, modelo escolhido nas Preferências,
TTFT/recepção/tokens/s reportados com origem clara, cancelamento por socket e
rollback `/v2`. Dados cifrados e logo foram preservados. `Avaliar-Modelos.cmd`
abre o avaliador empacotado; nenhuma instalação manual de Python ou envio de
conversas privadas é necessário. Ler `docs/PHASE6_WINDOWS.md` e o topo de
`VALIDACAO.md` para artefato, hashes, provas e limitações.

Candidato Alpha 0.3.0-alpha.2: run **44186126526**, código `dec9540`, Success,
51,1 MB. CI **44186126472** também Success. Windows Server 2022: 139 casos,
138 aprovados e um POSIX não aplicável; EXE, logo, GUI/Engine v1 e avaliador
empacotado passaram. Não são inferência ou Windows 10 do usuário. Download e
hashes no topo de `VALIDACAO.md`; nenhum Release publicado.

Linux: 139 aprovados/zero skips. Testes de protocolo e self-check sem modelo não
são inferência. Nuvem continua sem Ollama/403: 0 gerações Qwen, 20 NOT_RUN por tag.
Próximo gate: executar o utilitário no Windows 10/Athlon/8 GB com 0.5B e 1.5B já
instalados, revisar respostas/latência/licença e escolher o próximo incremento
com esses dados. Não promover modelo nem declarar qualidade por tamanho.
Não iniciar módulos futuros antes dessa avaliação. Nenhuma GitHub Release,
deploy ou alteração SG está autorizada. As seções abaixo são históricas.


## Continuação prioritária — NOW Brain API V5, 17/11/2026

Implementação local independente em `e015f349d58ac0c125338e2761ba7b9965c05bf3`
na `work`, sem recriar projeto, alterar SG ou publicar release. Use o HEAD mais
recente sem resetar. As notas Alpha abaixo são históricas e não aprovam o código
V5. Ler primeiro `docs/NOW_BRAIN_API_V1.md` e a seção V5 de `VALIDACAO.md`.

API `/api/now/v1`, OpenAPI protegida, modelos locais observados, chat JSON/SSE,
cancelamento/desconexão e limites estão implementados. GUI mantém `/v2`, cofres e
marca; ela ainda não usa SSE novo. Linux: 129 testes aprovados, zero skips/falhas,
GUI/Engine offline reais e execução mínima da API sem Qt. Fixtures de protocolo
não são inferência. Registro/downloads Ollama retornam CONNECT 403 nesta nuvem.

Próximo gate: executar `tools/validate_brain_api.py` no Windows 10 com os Qwen
0.5B/1.5B já instalados, 20 casos por modelo e licença/quantização/digest/timing
observados. Não publicar relatórios privados, não baixar pesos por vias não
autorizadas e não promover modelo antes da revisão de qualidade. Não reaproveitar
respostas de GPT/Gemini para treinamento. A avaliação cloud está BLOCKED/0
respostas/NOT_SCORED; o wrapper PowerShell e Windows 10 do usuário ainda não foram executados.

CI Windows Server 2022 passou no run 44159954202, fonte `d4b4408…`: 129 casos,
128 aprovados e um POSIX não aplicável; EXE/Qt/Engine/logo e seis comandos offline
reais. Artifact de diagnóstico, sem inferência, assinatura ou autorização de
Release. Metadados em `validation/brain-api-v5-20261117/windows-ci.json`.

Depois dos resultados reais, escolher o próximo incremento de qualidade e
migração da GUI para SSE. Multiusuário/infraestrutura SG, memória de fatos,
voz/visão/ações seguem fora deste primeiro incremento. Autorizações de release
e produção continuam ausentes; não usar a existência da API como permissão.


## Ponto atual — candidato Alpha Windows disponível

**Prepare Windows Alpha [43969485511](https://github.com/Gabomgames/Now-assistant/actions/runs/43969485511)** concluiu Success; fonte **`cb5204041907139a8fb862e7ff6a557dec53df24`**, branch work. Usar HEAD mais recente sem resetar: commits posteriores de relatório não alteram o código desse build. Windows Server 2022/Python 3.12.10: **102 casos, 101 aprovados, um POSIX não aplicável**, zero falhas/erros. EXE PyInstaller abriu Qt `windows`, logo/ICO, Engine própria e seis comandos offline PT-BR/EN reais. ZIP/CRC/SHA/inventário/licenças/inspeção de arquivos privados passaram no runner.

Artifact de revisão, ~51 MB/30 dias: `now-assistant-windows-0.3.0-alpha.1-cb5204041907139a8fb862e7ff6a557dec53df24-attempt-1`. ZIP `NOW-Assistant-0.3.0-alpha.1-Windows-x64.zip`, SHA-256 `33de53c1235504e5dc125b44a13ee13bc9ecb77fb22b2d0f8b2755fd6c33efe7`. É candidato Alpha real, `release_eligible:true`, `diagnostic_only:false`; a autorização de Release continua **ausente**. Nenhuma tag/draft/Release foi criada. Não invocar o publicador sem aprovação explícita posterior para versão/SHA/run.

A nova entrada de build por push é limitada à alteração de `packaging/releases/alpha-request.json`, proprietário e work. Não muda rede nem usa Actions como proxy de API. Conferência de versão, logo e SHA exato da solicitação: `732f882054badc1077e59b83c6c026c7126251f6ca8d24a6a05c7ee5e6e81518`, igual no commit e no relatório Windows. `.gitattributes` evita LF/CRLF; o primeiro run 43969162346 foi substituído por essa correção, sem relaxar a conferência. O modo manual de preparação permanece. Publicação continua manual com frase exata e verifica a solicitação no commit aprovado.

Ler `VALIDACAO.md`, `validation/alpha-candidate-20261116.json`, `docs/GITHUB_DISTRIBUTION.md` e notas/guia em `packaging/releases`. Linux: 102 aprovados/zero skips; os quatro novos casos são fixtures de gates, separados da execução Windows. O Git/site público funcionam, mas `api.github.com` segue bloqueado nesta instância: os artifacts/capturas Windows não foram baixados ou inspecionados localmente. O usuário pode baixá-los com login no site GitHub.

O consumidor extrai a pasta completa e executa sem Python/VS Code. Ollama/Qwen separados; oito gerações e naturalidade não executadas. Authenticode, Windows 10/hardware alvo/DPI/acessibilidade/ACLs manuais, voz física/wake/background/Android continuam pendentes. Próximo passo: revisão do candidato pelo usuário; somente depois de autorização concreta publicar como Pre-release pelo fluxo manual. As seções abaixo são históricas.

## Preparação por solicitação explícita — 16/11/2026

Foi acrescentada uma entrada de **build**, sem publicação: push na work alterando `packaging/releases/alpha-request.json` executa Prepare Windows Alpha, com validação de proprietário, revisão da logo, versão e SHA dos bytes da solicitação. O modo manual permanece disponível. Git/Actions são usados normalmente; a instância cloud não recebe acesso à API por esse fluxo. O publicador continua manual e exige autorização exata para versão/SHA/run, além de conferir a solicitação no commit de origem quando o candidato veio de push.

Estado antes do primeiro push desta entrada: **102 testes locais aprovados**, zero falhas/erros/skips, incluindo os 98 anteriores; actionlint passou. O novo candidato Windows ainda precisa executar e ter seu resultado registrado. Não promover o diagnóstico anterior nem inferir sucesso. Acompanhar Prepare Windows Alpha e atualizar `VALIDACAO.md` com o run real, fonte, ZIP/hashes e limitações antes de apresentar. Não executar publicação nem criar tag/draft/Release nesta tarefa.

As seções seguintes preservam os estados anteriores. O início de `VALIDACAO.md` é a referência para o resultado atual.

## Etapa anterior — logo definitiva integrada

Logo recebida em `NOW_Assistant_Logo_Oficial_PARA_CODEX.zip`, PNG intacto em `assets/branding/original.png`, SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`. Não solicitar novamente a imagem. Commit da implementação **`856723ef1fccb6d86cdc3fbffdd374663f717974`**, branch work; usar HEAD mais recente sem resetar para a referência. Nove PNGs e ICO com oito tamanhos, somente escala proporcional e padding preto externo; manifest/provenance e testes preservam a identidade.

**Prova Windows com logo:** [run 43961691647](https://github.com/Gabomgames/Now-assistant/actions/runs/43961691647), Success em 3m8s, Windows Server 2022/Python 3.12.10, 97 aprovados e um POSIX não aplicável (98 casos). EXE abriu, marca/ícone e Engine empacotada carregaram e seis comandos offline PT-BR/EN passaram; ZIP/inventário/CRC/SHA/licenças verificados no runner. Artifact CI de ~51 MB com fonte 856723e. Continua `diagnostic_only:true`, `release_eligible:false`; não apresentar como run Prepare Windows Alpha.

**Próximo passo exato:** executar `gh workflow run windows-alpha.yml --repo Gabomgames/Now-assistant --ref work -f version=0.3.0-alpha.1 -f branding_reviewed=true` após confirmar acesso legítimo à API. A tentativa desta tarefa falhou (código 1) no GET de `api.github.com`; runtime revisão 1 não aplica o domínio, embora esteja no rascunho. Não repetir antes de mudança efetiva nem alterar as regras do workflow/publicador para driblar o bloqueio. O proprietário pode disparar pelo painel GitHub, work, versão 0.3.0-alpha.1 e branding_reviewed=true. Original, ícones e GUI foram realmente inspecionados.

O usuário já autorizou **gerar e testar o candidato**, sem autorização de Release. Depois do disparo legítimo, acompanhar Prepare Windows Alpha até o fim, corrigir falhas, registrar SHA/run/ZIP/hashes e apresentar artifact e limitações. Não publicar tag/draft/Release. A pipeline de publicação e suas barreiras permanecem intactas. Usar cliente `gh` normal se a rede permitir, sem extrair credenciais. ZIP/screenshots Windows ainda não foram baixados/inspecionados localmente.

Local: 98 testes aprovados (95 anteriores + 3 de branding), Qt/API reais em Linux offscreen com venv mínimo sem SDK Gemini, ícone com oito tamanhos e seis comandos offline. Não há inferência/áudio novo. Evidências: `validation/official-logo-alpha-20261116.json`, `assets/branding/PROVENANCE.json`, `VALIDACAO.md`. Os estados anteriores de logo ausente abaixo são históricos.

## Etapa anterior — distribuição Windows 0.3.0-alpha.1

Continuar do HEAD mais recente de `work`, preservando todos os commits. Implementação inicial da pipeline: `a130ba3`; correções Windows incrementais até **`c97f9d1fd8ce152f3d2261c750c5d8739e69c88f`**, que foi o código testado no [run 43950853793](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793). Commits posteriores de documentação/relatórios não mudam essa identidade de teste.

O CI Windows Server 2022/Python 3.12.10 passou: **94 testes aprovados, um teste POSIX não aplicável**, GUI/API/SQLite reais, EXE PyInstaller, Engine empacotada e seis comandos determinísticos PT-BR/EN. Artefato Windows de diagnóstico (~50 MB), ZIP/SHA/evidências em Artifacts do run. Não declarar esse diagnóstico como Alpha oficial: `release_eligible:false`, original da logo ainda ausente. Publicação configurada, **não executada e não autorizada** nesta preparação.

O que desbloqueia a Alpha:

1. Receber o PNG/JPG/WebP original **como arquivo**; a imagem inline não foi exposta no filesystem. Não redesenhar, não usar fixtures, não afirmar que foi incorporada. Importar com `tools/import_branding.py`, conferir original/SHA/ícones e commitar assets na work.
2. Executar **Prepare Windows Alpha** pelo proprietário (work, SemVer do `now_desktop/version.py`, revisão visual verdadeira), aguardar todo o build/smoke e apresentar o artifact/resultados. Se o assistente não puder usar a API, o proprietário pode disparar pelo painel Actions; não usar push de tag como substituto.
3. Somente após autorização explícita para o candidato revisado, usar **Publish approved Windows Release** com versão, SHA completo, ID do run Alpha e frase exata. Não invocar agora com base no pedido de preparar. Nenhuma tag/release existente deve ser sobrescrita.

API `api.github.com` está bloqueada no runtime revisão 1; Git/site público funcionam e permitiram ler status/anotações. Rascunho de rede já contém esse domínio e registry.ollama.ai, mas não está aplicado. Revisar/salvar/aplicar no painel, publicar configuração para tarefas novas e confirmar política efetiva antes de tentar `gh`. Não extrair credenciais ou contornar proxy. Mesmo sem isso, os workflows rodam no GitHub e o proprietário pode revisar os artifacts pelo navegador autenticado.

Suíte local: 95 testes em Linux, todos aprovados; `actionlint 1.7.11` passou. Fixtures sintéticos de gates ZIP/metadados não validam Windows/inferência; o smoke Windows é separado e real. Correções preservaram casos/asserts: fechamento de SQLite, cofre ausente portátil, encerramento da árvore de processo própria, bootstrap IPC do loop antes do audit de aplicação, caminhos Windows 8.3 e espera por widget real. `.gitattributes` preserva hashes dos dados originais em checkout Windows.

Guias atuais: `docs/GITHUB_DISTRIBUTION.md`, `packaging/releases/INSTALL-WINDOWS.md`, `VALIDACAO.md`, `validation/distribution-20261116.json`. Ollama/pesos não acompanham ZIP. Qwen/inferência, áudio físico/“Now”, Windows 10/hardware alvo e Android continuam pendentes. Não recriar o projeto nem reduzir testes para aprovar pacote.

## Etapa anterior preservada — NOW Assistant V3 desktop

Continuar do HEAD mais recente de `work`, descendente de `6cdb0c72fd2b70af118df1f41dda6f9e260db047`; não voltar a esse SHA nem a `5caadce`. O SHA da entrega e confirmação de push ficam na resposta da tarefa e em `git log`/`git ls-remote`. A especificação integral está em `docs/specs/NOW_ASSISTANT_V3.txt`. Os relatórios anteriores abaixo são históricos.

Entrega de texto: `python -m now_desktop` abre GUI PySide6, inicia uma Engine autenticada própria e usa comandos reais offline PT-BR/EN. `now_history` guarda conversas com senha/consentimento; `now_memory` continua separado. Instalar `requirements-desktop.txt` além das dependências antigas, ou usar o ambiente mínimo sem Google. A suíte atual executou **86 testes**: 55 anteriores e 31 novos. GUI/API/SQLite reais em Linux offscreen; doubles antigos de áudio/modelo continuam identificados e não aprovam inferência/áudio.

```bash
cd /workspace/Now-assistant
git status --short
git branch --show-current
git log -1 --oneline
.venv/bin/python -m pip install -r requirements-desktop.txt
QT_QPA_PLATFORM=offscreen XDG_CACHE_HOME=/workspace/.cache .venv/bin/python -m unittest discover -v
```

Não criar cofres, senhas, gravações ou permissões no setup. A GUI padrão não cria banco; não abrir dados privados para fazer screenshots. Instalação do ambiente salva deve incluir Qt e sua suíte, sem modelo/ML obrigatório. `pip==26.3` corrige os alertas do pip originalmente fornecido. Os constraints existentes continuam aplicados. Os testes Windows precisam de Python 3.12 x64 real; Linux offscreen não é equivalente.

Próximas dependências e entregas:

1. **Logo:** imagem inline foi visível, porém seu arquivo não estava entre os anexos locais. Solicitar o PNG/JPG/WebP original como arquivo. Manifest segue `awaiting_original_file`; não usar imagem sintética da suíte. Importar com `tools/import_branding.py`, preservar bytes/SHA e revisar tamanhos visualmente. Sem esse arquivo, o build de release recusa prosseguir.
2. **Windows:** seguir `docs/DESKTOP_WINDOWS.md`. A ferramenta `tools/build_desktop_windows.py` está preparada; apenas sua recusa correta em Linux foi executada. Realizar build, smoke empacotado, revisão de licenças Qt, GUI/cofres/ACL/DPI/acessibilidade e consumo em Windows 10/8 GB. Não existe EXE validado nesta máquina.
3. **Qwen:** runtime revisão 1 com rede restrita aplicada ainda exclui `registry.ollama.ai`; GET do manifesto e pull real continuam 403/Forbidden. O rascunho contém a regra, sem aplicação comprovada. Ferramentas não oferecem aplicação direta. Revisar/salvar/publicar configuração no painel, selecionar versão em nova tarefa e confirmar política efetiva antes de tentar novo download. Não contornar proxy/TLS nem repetir pulls sem mudança. Zero pesos instalados, zero das oito gerações reais executadas.
4. **Voz:** reutilizar contratos `now_voice`, depois implementar e testar microfone → STT → Engine → TTS → saída real. Sem botões de fachada. Wake “Now”, bandeja e startup opt-in vêm depois; falsa ativação/eco exigem hardware real.

Relatórios e limites: `VALIDACAO.md`, `validation/desktop-v3-20261116.json`, `validation/desktop-dependencies-20261116.json`, `docs/DESKTOP_ARCHITECTURE.md`. Capturas compartilháveis só dos comandos artificiais de teste sem dados privados. A publicação/restauração do ambiente em nova tarefa não está comprovada por um rascunho salvo.

## Incremento de voz e memória

O projeto agora inclui `now_memory` (preferências criptografadas opt-in), `now_voice` (controlador/contratos/plano de fala) e `now_engine.assistant` (adaptador local adicional). Instalar também `requirements-memory.txt` antes da suíte completa. A referência de origem deste incremento é `5caadce`; obter a revisão atual com Git, sem resetar para a referência de origem.

```bash
cd /workspace/Now-assistant
.venv/bin/python -m pip install -r requirements-memory.txt -c packaging/windows/constraints-python312.txt
.venv/bin/python -m unittest discover -v
.venv/bin/python -m now_voice --capabilities
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory status
```

Status não cria banco. Não criar cofre, senha, permissão de microfone ou sessão de escuta durante setup. `docs/INCREMENT_VOICE_MEMORY.md` detalha o escopo. Este incremento não possui STT/TTS/detector, e os testes de contrato com doubles não validam áudio. Captura, fala física e “Now” continuam indisponíveis até implementar/adicionar e testar adaptadores reais.

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

Para a próxima fase, seguir `MODEL_ROADMAP.md` e os guias `NOW_MEMORY.md`, `NOW_VOICE_ENGINE.md` e `GUI_PLAN.md`. Preferências criptografadas e controle/planejamento de voz foram testados em Linux; memória de conversas, STT/TTS, hardware, wake word e builds Windows/Android continuam pendentes. Os nove arquivos originais podem ser verificados pelos hashes de `validation/training-integration-20261116.json`.
