# NOW Assistant — validação incremental

## NOW Brain API V5 — primeiro incremento local — 17/11/2026

**Código executável:** `e015f349d58ac0c125338e2761ba7b9965c05bf3`, branch `work`.
Baseline auditada `e80fb8a25d9f4b40c480cdb072880ae3d6f561df`, árvore limpa;
`201fe4cab058bf7e7da41523b47404ba7c02c76f` e `e80fb8a…` existiam somente
localmente naquele momento. `git ls-remote origin refs/heads/work` confirmou a
referência remota inicial `32220c92d22c7eba13f81fb7c1ef47b3b9d54fba`.
O anexo `NOW_BRAIN_API_SUPERPROMPT_ENTERPRISE_V5.txt` foi lido integralmente antes
das alterações; hash e inventário de arquivos estão no relatório de auditoria.

A API nova é independente de Qt, dos bancos e de SDKs comerciais. Implementa
`/api/now/v1/{health,capabilities,models,chat,chat/stream,chat/cancel,openapi.json}`,
autenticação de processo, schemas estritos, seleção de tag local observada,
contexto/persona, extensões de 192/512/1024 tokens, SSE incremental, fechamento
do socket upstream ao cancelar/desconectar, limite de uma geração, quota local
e métricas sem conteúdo privado. Não é um NOW Server público/multiusuário.
A GUI continua no `/v2`; seu contrato foi preservado. Foi extraído somente o
middleware compartilhado de autenticação/limite de corpo, com formato legado
mantido por default. Novas rotas não acessam cofres nem executam ferramentas.

| Item | Estado e evidência observada |
| --- | --- |
| Auditoria/base Linux/Python 3.12.14 | **112 testes aprovados em 26,044 s**, sem falhas/erros/skips. |
| Suíte no commit de código acima, árvore limpa | **129 aprovados em 30,208 s**, sem falhas/erros/skips; preserva os 112 anteriores. |
| 17 novos testes | **12 integrações HTTP/SSE/socket reais** com fixture Ollama explícita e cinco testes de cliente/validador/casos. Não são inferência de modelo. |
| Streaming/cancelamento | Deltas, UTF-8, truncamento, EOF quebrado, timeout e saída inválida testados; cancelamento autenticado e desconexão em JSON/SSE fecham upstream e liberam slot. Não foi medida liberação de CPU/GPU pelo Ollama real. |
| API mínima independente | Instalada e iniciada em `.venv-brain`, sem Qt/cryptography/google; `pip check` passou. OpenAPI protegida e erros sem echo de inputs testados. |
| Modelo ausente/segurança | HTTP 503 sem reply fabricado; inventário remoto/cloud recusado, URL externa recusada, Origin/Host/token/payload/esquema/quota testados. |
| GUI legada | Qt offscreen e HTTP autenticado reais; seis comandos offline PT-BR/EN, marca/ícone oficiais e nenhuma base privada criada no smoke. |
| Marca/dados/distribuição | `assets/branding`, `now_history`, `now_memory`, `now_voice`, `.github`, `packaging` e dependências desktop sem alterações contra a base. |
| Inferência real na nuvem | **BLOQUEADA**, exit 2: Ollama ausente; CONNECT 403 no registro e download oficiais. **Zero gerações; 20 casos NOT_RUN para cada uma das tags 0.5B e 1.5B.** |
| CI Windows Server 2022 | [Run 44159954202](https://github.com/Gabomgames/Now-assistant/actions/runs/44159954202), **Success em 2m59s**; Python 3.12.10, 129 casos: **128 aprovados e um POSIX não aplicável**, zero falhas/erros. EXE Qt nativo, logo/ícone, Engine própria e seis comandos offline passaram. |
| Validador Windows 10/Ollama | Entregue Python executável + wrapper PowerShell, sem download/treino/upload; o caminho bloqueado foi executado no Linux. **Windows 10 do usuário/PowerShell/qualidade real ainda NOT_RUN.** |

A execução nativa acima foi disparada pelo push normal de
`d4b4408c6fb400c9f8dcc8b08d858332f6af9d2c` (código e evidências V5), sem
alterar workflows. A anotação pública informa `actual_windows_smoke_passed`,
`qt_platform:windows`, `frozen_executable:true`, logo oficial verificada,
`diagnostic_only:true`, `release_eligible:false`, `release_published:false` e
`model_inference_tested:false`. O artifact real
`now-assistant-ci-d4b4408c6fb400c9f8dcc8b08d858332f6af9d2c-attempt-1`, **51 MB**,
está no run. Hash do ZIP diagnóstico observado no runner:
`ec34676d695333d3774b99e665392705288a58e664fbd9492bf42e2cf3e49e38`.
Anotações, digest e metadados foram observados no GitHub e registrados em
`windows-ci.json`; **ZIP/EXE/capturas Windows não foram baixados nem inspecionados
localmente**. É diagnóstico, sem assinatura e sem pesos, não novo candidato
Alpha publicável. Não testa Qwen nem o Athlon/8 GB do usuário.

**Métricas disponíveis:** 10 amostras do chat explicitamente **determinístico**
da API independente: p50 **8,691 ms**, p95/p99 **15,638 ms** (nearest-rank).
Amostragem executada junto da suíte/GUI nesta máquina Linux, sem isolamento de
carga. Não é latência de inferência, benchmark do Athlon, throughput ou SLO.
Tokens/s, TTFT de modelo, uso de RAM/CPU/VRAM e FPS do Windows não foram medidos.
Qualidade permanece **NOT_SCORED**; nenhuma conversa gerada pode ser apresentada
como exemplo aprovado. Resultados do usuário sobre Qwen não foram tratados como
execuções desta instância.

**Arquivos/justificativas:** `now_brain/` separa contratos, transporte Ollama,
orquestração, API, cliente e ciclo de vida; `now_engine/security.py` evita duplicar
o guard legado; `requirements-brain.txt` permite instalação mínima; testes novos
cobrem contratos/erros/streaming; `validation/brain-v5-cases.json` e
`tools/validate_brain_api.py` executam a avaliação real comparável;
`tools/validate_brain_windows.ps1` facilita a execução local; `.gitignore` ignora
apenas o venv novo. README/guia documentam comandos, contrato e limitações.
Lista completa dos 19 arquivos da implementação em `audit.json`.

Evidências em [brain-api-v5-20261117](validation/brain-api-v5-20261117/audit.json):
relatórios base/final, log da suíte, OpenAPI obtida por HTTP, avaliação real
bloqueada e captura/relatório do desktop. Os hashes de arquivos no relatório de
avaliação identificam o código executado. O snapshot de evidência é do commit de
implementação acima; o commit posterior altera somente relatórios/documentação.

**Próxima ação útil:** no Windows com Ollama já ativo e as tags instaladas, seguir
[guia executável](docs/NOW_BRAIN_API_V1.md) e comparar as respostas reais. O
validador abre/fecha somente sua API filha, usa prompts sintéticos de avaliação,
registra tag/digest/quantização/licença e mede TTFT/latência/tokens/s observados.
Não instala modelos, não toca no serviço do usuário, não lê cofres e não envia
relatórios. Saída 0 ainda requer revisão humana de correção/naturalidade; não
aprova licença ou qualidade automaticamente.

**Limites/gates:** perfil local funcional/testado no escopo de protocolo;
inferência comercialmente aceitável ainda não aprovada. Migração visual da GUI
para SSE, memória de fatos consentida, RAG, providers próprios remotos, tenants,
OIDC, quotas distribuídas, carga e Windows 10/8 GB são incrementos posteriores.
Sem treinamento, uso comercial de GPT/Gemini, alteração SG, release ou deploy.
Rollback por reversão dos commits V5; nenhum banco exige migração. As evidências
Windows Alpha anteriores abaixo mantêm seu SHA/escopo; não validam este código.


## NOW Brain V4 — incremento 1, aceite generativo BLOQUEADO — 17/11/2026

Ambiente operacional, checkout `Gabomgames/Now-assistant`, branch `work`, base
`32220c92d22c7eba13f81fb7c1ef47b3b9d54fba`, inicialmente limpa e igual à referência
remota verificada por `git ls-remote`. Anexo Master V4.0 disponível, 10.000 linhas,
SHA-256 `be5811f706bce8efb002823010519df17331ccb9d002214b11fee159917bec42`.
O cabeçalho contém o prompt de execução e a especificação mestre; não foi
localizado outro prompt inicial separado no workspace ou nesta conversa.

Código do incremento: **`201fe4cab058bf7e7da41523b47404ba7c02c76f`**. O provedor
Ollama foi separado da preparação de contexto/personalidade; geração continua
local, sem proxy, redirecionamentos ou Gemini. As preferências existentes Curta,
Equilibrada e Detalhada agora controlam 192/512/1024 tokens, substituindo o limite
único 220. API v2 acrescenta modelo/encerramento/truncamento; a GUI mostra aviso
quando o modelo encerra por limite. Nenhuma mudança nos formatos dos cofres.

| Verificação real | Resultado |
| --- | --- |
| Base antes das mudanças | 102 testes aprovados, zero falhas/erros/skips. |
| Suíte no commit de implementação acima | **112 aprovados em 24,456 s**, zero falhas/erros/skips; 10 testes GUI anteriores e seis testes HTTP anteriores continuam aprovados. |
| Novos testes | Nove casos de transporte/contrato/contexto/preferências e um caso de renderização Qt com fixtures sintéticas; **não representam inferência**. Incluem redirecionamento HTTP real recusado. |
| GUI + Engine autenticada, Linux Qt offscreen | Seis comandos offline reais PT-BR/EN aprovados; capturas reais salvas, captura PT-BR inspecionada visualmente. Nenhum banco criado pela sessão temporária. |
| Dependências | `pip check`: sem dependências quebradas. |
| Marca, workflows, histórico e NOW Memory | Diretórios sem diferenças contra a base; PNG original mantém SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`. |
| Ollama / pesos | Executável ausente, serviço loopback recusou conexão. Downloads oficiais e registro retornaram CONNECT 403 no proxy. |
| Avaliação generativa pela GUI no commit limpo | **BLOCKED**, saída 2, **0 gerações, 20 casos não executados, qualidade NOT_SCORED**. Nenhuma resposta de modelo inventada ou aprovada. |

Evidências versionadas em `validation/brain-v4-increment-20261117/`: relatórios
base/pós-alteração, preflight generativo, smoke offline, capturas e proveniência.
Guia e comando real: [NOW Brain](docs/NOW_BRAIN.md). A avaliação preparada usa a
GUI e sua Engine, com cinco turnos encadeados, mudança de idioma e casos de
profundidade, personalidade, incerteza e limites de memória/permissão. Ela exige
revisão das respostas reais; sucesso de transporte não aprova qualidade.

A política ativa era restrita/enforced, sem domínios customizados. Adições
`ollama.com` e `registry.ollama.ai` foram salvas no rascunho do ambiente,
preservando o preset. Isso **não aplicou nem publicou** a configuração. É preciso
revisar/salvar nas configurações do ambiente e publicar essa configuração para
retestar os downloads por via oficial. Nenhuma credencial adicional foi pedida.

**Entrega parcial:** não se afirma que a NOW já conversa melhor. Faltam pesos
reais, gerações e avaliação de naturalidade/coerência/qualidade e latência por
modelo. Streaming visual, cancelamento no servidor, memória permanente de fatos
com consentimento granular e integração SG ficam para incrementos posteriores.
As preferências autorizadas e o histórico existentes foram preservados/testados.
Nenhum SG, release, deploy, push ou workflow remoto foi executado. Windows nativo
não foi revalidado para este incremento. Rollback: reverter o commit de código;
não há migrações de dados nem mudança na versão do candidato Alpha anterior.


## Candidato Windows 0.3.0-alpha.1 executado — 16/11/2026

**Prepare Windows Alpha concluiu Success:** [run 43969485511](https://github.com/Gabomgames/Now-assistant/actions/runs/43969485511), commit **`cb5204041907139a8fb862e7ff6a557dec53df24`**, branch work. Duração total **3m57s**, incluindo espera; job Windows **2m44s**. Windows Server 2022 x64/Python **3.12.10**, PyInstaller e dependências fixadas. Base `25efee4` preservada, com commits incrementais; nenhum arquivo original ou teste anterior removido.

| Verificação executada | Resultado |
| --- | --- |
| Suíte completa no Windows | **102 casos, 101 aprovados, um POSIX não aplicável**, zero falhas/erros. Os 98 anteriores foram mantidos. |
| EXE empacotado | Abriu janela Qt nativa `windows`, `sys.frozen=true`, carregou logo e ícone multi-resolução e iniciou a Engine empacotada. |
| Engine/GUI/HTTP reais | Seis respostas offline: `oi`, `horas`, `data`, `hello`, `time`, `date`. Não são gerações Qwen nem respostas simuladas. |
| Marca oficial | PNG original SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`; ICO `a6f4af3370d657e14df8b685176c512980a3549640a0408c8542d26a2db73d59`; recurso PE e imagem/ícone na GUI verificados. |
| Pacote | Python/Qt embutidos, licenças, inventário SHA-256, CRC e caminhos ZIP verificados; inspeção de arquivos privados passou. Sessão de teste temporária sem cofre pessoal. |
| Origem da solicitação | Hash observado no Windows **igual aos bytes do commit**: `732f882054badc1077e59b83c6c026c7126251f6ca8d24a6a05c7ee5e6e81518`. `publish_release:false`. |

### Download do candidato para revisão

[Abrir Artifacts do build](https://github.com/Gabomgames/Now-assistant/actions/runs/43969485511#artifacts), entrar no GitHub se necessário e baixar **`now-assistant-windows-0.3.0-alpha.1-cb5204041907139a8fb862e7ff6a557dec53df24-attempt-1`**, aproximadamente **51 MB**, retenção configurada de **30 dias**. O invólucro contém o ZIP portátil, relatório, testes, hashes, notas e capturas reais da janela.

- ZIP portátil: **`NOW-Assistant-0.3.0-alpha.1-Windows-x64.zip`**.
- SHA-256 do ZIP: **`33de53c1235504e5dc125b44a13ee13bc9ecb77fb22b2d0f8b2755fd6c33efe7`**.
- SHA-256 do EXE: `de6a4d90dfb8362c0a0a7111dc58a7b3485ed10d1afd792109324dc726072f30`.
- Digest do invólucro GitHub: `26ede53d4ed3a6970fda2dd7c10b6cae54d4fc6c331a9c1d7c1f9fec8f6ef006`.

Extraia o artifact e depois **toda a pasta do ZIP portátil**; abra `NOW-Assistant.exe`, mantendo `_internal`. O usuário não precisa instalar Python nem VS Code. Leia `LEIA-ME.md` e `CHANGELOG.md` incluídos. Ollama e pesos Qwen não estão incluídos. Para perguntas livres, instale Ollama oficial e execute `ollama pull qwen2.5:0.5b` por rede autorizada; confirme com `ollama list`. Sem modelo, os comandos locais continuam disponíveis.

### Escopo, correção e publicação

O primeiro Prepare Windows Alpha, [43969162346](https://github.com/Gabomgames/Now-assistant/actions/runs/43969162346), também executou os testes/EXE, mas foi **substituído**: a conversão Git LF/CRLF mudou o hash da solicitação. A diferença foi medida tanto pelo filtro Git quanto pelo relatório real do runner. `.gitattributes` passou a preservar os bytes; o candidato acima foi reconstruído e seu hash de origem coincide. A comparação de proveniência não foi relaxada. Ambos os resultados estão em `validation/alpha-candidate-20261116.json`.

Linux/Python 3.12.14: **102 testes aprovados em 23,254 s**, zero falhas/erros/skips, na árvore imediatamente antes do commit final de código; actionlint passou. Os quatro novos casos usam fixtures de solicitação/proveniência e não representam inferência ou aprovação Windows. A prova Windows é o run nativo separado acima.

Status, contagens e hashes foram observados na página pública e nas anotações estruturadas do GitHub. O runner executou CRC/SHA/inventário/renderização nativa; **ZIP/EXE/capturas Windows não foram baixados ou inspecionados localmente**, pois `api.github.com` continua bloqueado nesta instância. Não se afirma revisão visual humana no Windows. O evento nativo de push solicita apenas o build, sem relay de API ou mudança da política cloud.

**Candidato pronto para revisão, não publicado.** `release_eligible:true` e `diagnostic_only:false` são resultados do builder, não autorização de publicação. Publish approved Windows Release permanece exclusivamente manual, exige proprietário e versão/SHA/run/frase exatos e verifica a solicitação no commit de origem. A versão será **Pre-release** se posteriormente autorizada. Nenhuma tag, draft ou GitHub Release foi criada nesta tarefa; o fluxo de publicação está configurado/testado por contratos, **não executado**.

Limitações: sem Authenticode; Windows 10/hardware de 8 GB, acessibilidade, DPI e ACLs manuais pendentes. Inferência Qwen/oito gerações, voz física/STT/TTS, ativação “Now”, bandeja/background, visão e Android não foram aprovados. O modelo continua separado e nenhuma chamada Gemini foi usada na validação desktop/Engine. Instruções: `docs/GITHUB_DISTRIBUTION.md` e `packaging/releases/INSTALL-WINDOWS.md`.

As seções seguintes preservam a cronologia; bloqueios antigos não substituem o resultado atual acima.

## Preparação explícita do primeiro candidato Windows — 16/11/2026

Base preservada: `25efee4c39f88e8ed72f287ed61092ec3e53a643`, branch work, backup versionado local antes das alterações. A entrada nativa de push de `packaging/releases/alpha-request.json` foi adicionada a Prepare Windows Alpha; a entrada manual permanece. A solicitação vincula versão, revisão da logo e SHA do PNG original e proíbe publicação. O workflow permanece somente de leitura. O publicador manual mantém a aprovação exata por versão/SHA/run e passa a conferir a solicitação no commit de origem de candidatos preparados por push. Não há relay de API, alteração da política de rede, publicação por push ou extração de credenciais.

**Executado antes do push:** Python 3.12.14/Linux, suíte completa com **102 aprovados em 24,404 s**, zero falhas/erros/skips; todos os 98 casos anteriores preservados. Os quatro casos adicionais validam solicitações/proveniência com fixtures, sem representar um build Windows. `actionlint 1.7.11` aprovou os três workflows. A logo original mantém SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`.

**Pendente neste ponto:** execução real de Prepare Windows Alpha com este commit, resultado do EXE/GUI/Engine/comandos offline e artifact final. Os resultados serão acrescentados somente após o runner concluir. Nenhuma tag, draft ou GitHub Release foi criada. Os diagnósticos abaixo permanecem históricos e não substituem esse candidato.

**Correção durante a preparação:** a prova de filtros Git com `core.autocrlf=true` detectou conversão LF/CRLF da solicitação (SHA do blob `ce35f814e2b47143a2c9bc545312a29f38ad99b19d30c1b00703b34b5a6e362d`, checkout convertido `4a96ae6811fbac7cfdc93164f613e7e97b17274507565b6297bf923920644bab`). A regra `-text` foi acrescentada para esse arquivo; uma nova solicitação será a fonte do candidato final. A conferência de origem não foi relaxada para aceitar bytes diferentes.

## Logo oficial e candidato 0.3.0-alpha.1 — 16/11/2026

Continuação da `work` a partir de `fcff45f8f6bf868d08ff0639c93e445f72299393`, árvore limpa e remoto correspondente. Backup das fontes versionadas: `/workspace/.now-ai-backups/before-official-branding-fcff45f.zip`. Fonte/pipeline anteriores preservadas; publicação de GitHub Release continua proibida nesta preparação.

O ZIP `NOW_Assistant_Logo_Oficial_PARA_CODEX.zip` passou no CRC, contém somente `NOW_Assistant_Logo_Oficial.png` (943.589 bytes, 1301 × 1209), assinatura/decodificação PNG válidas. SHA-256 ZIP: `aae376b0251529e51c7f7ec91b3841f2030e6d78db99a85cf8e2c4f33e04636b`. O original em `assets/branding/original.png` foi comparado **byte a byte** com o membro do ZIP; SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`.

Gerados PNGs 16/24/32/48/64/128/192/256/512 e ICO com oito resoluções até 256. Somente redução proporcional e acomodação externa preta: sem redesenho, recorte, troca de cores, remoção de preto ou vetorização. Original, ícones 512/128/32 e a GUI real foram inspecionados. O importador manteve o comportamento anterior de padding transparente como default e ganhou a opção explícita preta, testada sem eliminar casos anteriores.

Integração: PNG no cabeçalho, ICO multi-resolução para janela/Windows e o mesmo ICO para o recurso PE do EXE. O smoke agora exige logo visível e ícone real com resolução 256 quando a marca oficial existe. O CI passou a observar mudanças em `assets/branding/**`. O workflow Alpha e todas as barreiras de publicação manual continuam preservados.

**Resultados locais executados:** 98 testes aprovados, 0 ignorados, 0 falhas/erros (24,016 s): os 95 anteriores mais três de padding/identidade oficial/ícone e GUI. `actionlint` passou nos três workflows. Smoke Qt/API real em Linux offscreen, venv mínimo **sem SDK Gemini**, seis comandos offline PT-BR/EN, imagem oficial e ICO carregados com oito tamanhos; nenhum banco criado. Não são inferência, áudio físico ou build Windows. Evidência: `validation/official-logo-alpha-20261116.json` e `assets/branding/PROVENANCE.json`.

**Estado antes de executar o candidato Windows:** a API `api.github.com` ainda retorna Forbidden no CONNECT, ausente da política aplicada revisão 1. O domínio já consta no rascunho 8, mas não foi aplicado. O disparo via `gh` de Prepare Windows Alpha está pendente dessa configuração ou de ação do proprietário no painel Actions. A execução e o link do candidato serão registrados quando realmente ocorrerem; não considerar o diagnóstico anterior como o novo candidato com logo. Nenhuma tag, draft ou Release foi criada.

### Windows com a marca oficial: execução real concluída

O [Windows CI 43961691647](https://github.com/Gabomgames/Now-assistant/actions/runs/43961691647), fonte **`856723ef1fccb6d86cdc3fbffdd374663f717974`**, terminou **Success em 3m8s**: **98 casos, 97 aprovados, um POSIX não aplicável, zero falhas/erros**, Windows Server 2022 x64/Python 3.12.10. Os 95 casos anteriores foram mantidos. O builder verificou o ícone PE, abriu o EXE congelado com Qt `windows`, renderizou logo e ICO, iniciou a Engine empacotada e executou seis comandos offline reais. O smoke exige imagem visível, ícone não nulo e resolução 256, além de respostas HTTP reais.

PNG original conferido no runner: SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`; ICO `a6f4af3370d657e14df8b685176c512980a3549640a0408c8542d26a2db73d59`. ZIP com Python/Qt, licenças, CRC, inventário e inspeção de arquivos privados passou. A pasta extraída dispensa Python/VS Code externos. Ollama/pesos Qwen são separados; não houve inferência simulada.

- Artifact: **`now-assistant-ci-856723ef1fccb6d86cdc3fbffdd374663f717974-attempt-1`**, ~**51 MB**, em [Artifacts](https://github.com/Gabomgames/Now-assistant/actions/runs/43961691647#artifacts).
- ZIP: `NOW-Assistant-0.3.0-alpha.1-diagnostic-Windows-x64.zip`, SHA-256 `ba874cd4734b36cdc6866ab563df20e33a24ac34898eab4aec3042c836e1e5db`.
- EXE: SHA-256 `7fce2c1ea849566fd3e4a919537a4ccc7461cfa08fa15dcf6babb3f1f061d4fa`.
- Digest do invólucro artifact GitHub: `16987ab23e41db67b2283600e48483867597b7232b3e2d53628d901264b534ef`.

Status/hashes observados nas anotações públicas do GitHub. CRC/SHA/renderização foram executados pelo builder Windows; ZIP/EXE/screenshots Windows não foram baixados/inspecionados nesta máquina por bloqueio da API. A inspeção visual local foi da GUI Linux offscreen e ícones reais. Evidência: `validation/official-logo-alpha-20261116.json`.

### Prepare Windows Alpha: tentativa bloqueada, não executado

Após enviar o commit, foi tentado `gh workflow run windows-alpha.yml --repo Gabomgames/Now-assistant --ref work -f version=0.3.0-alpha.1 -f branding_reviewed=true`. Encerrou com **código 1**: `Get "https://api.github.com/repos/Gabomgames/Now-assistant/actions/workflows/windows-alpha.yml": Forbidden`. Política aplicada observada: revisão **1**, sem esse domínio. A tentativa não disparou o workflow. Nenhuma credencial foi extraída/pedida e nenhuma barreira da pipeline foi removida.

O pacote acima é **CI diagnóstico**, `release_eligible:false`, mesmo com a marca. Não equivale ao candidato final de Prepare Windows Alpha. Para concluir: aplicar legitimamente a regra já salva no rascunho ou acessar [Prepare Windows Alpha](https://github.com/Gabomgames/Now-assistant/actions/workflows/windows-alpha.yml) → Run workflow → **work** → version **0.3.0-alpha.1** → **branding_reviewed=true**. Acompanhar o novo run e apresentar candidato/resultados antes de publicar. Nenhuma tag, draft ou GitHub Release foi criada.

Persistem limites: Windows 10/hardware de 8 GB, DPI/leitor de tela/ACLs manuais, Authenticode, inferência Qwen, áudio físico/wake word e Android não recebem aprovação por esse smoke. A marca deixou de ser bloqueio; o bloqueio atual é disparar o workflow pela API restrita desta instância.

Os relatórios abaixo são históricos das etapas anteriores, inclusive quando o arquivo da logo ainda não estava disponível.

## Distribuição GitHub — preparação de 0.3.0-alpha.1 (16/11/2026)

Base `work`, commit inicial `15e03a7dbbe73a817a831d3f27858d7387b6e0e2`, árvore inicialmente limpa e remoto correspondente; backup de fontes versionadas em `/workspace/.now-ai-backups/distribution-before-15e03a7.zip`. Nenhum reset/recriação. Baseline: 86 testes aprovados em 25,538 s.

Implementados workflows Windows CI, Prepare Windows Alpha e publicação exclusivamente manual, com permissões separadas e actions fixadas por SHA. SemVer inicial `0.3.0-alpha.1`, notas/guia para usuário sem Python/VS Code, build/Engine/smoke reais exigidos e ZIP com hashes, licenças e inspeção de arquivos privados. O CI diagnóstico é identificado como não publicável; Alpha exige logo original/revisão e ícone PE/GUI reais. Não foi autorizada/executada publicação de release.

Validação local após implementação: **95 testes aprovados** em Linux, 0 ignorados, em 28,996 s. São os 86 anteriores mais nove testes de gates com fixtures sintéticos de metadados/ZIP; esses fixtures não são builds Windows e não validam inferência. Testes GUI existentes receberam apenas ajustes para operar o seletor Qt de forma portável; nenhum caso foi removido. `actionlint 1.7.11` validou os três workflows sem erros; binário oficial com checksum `900919a84f2229bac68ca9cd4103ea297abc35e9689ebb842c6e34a3d1b01b0a` verificado. Compilação de módulos e `git diff --check` aprovados.

**Estado antes do primeiro push da pipeline (histórico):** build Windows ainda não executado, Alpha não aprovada. A logo foi enviada novamente como imagem inline, mas nenhum arquivo binário apareceu nos anexos locais; não foi redesenhada. `gh api .../actions/workflows` falhou no CONNECT 403 porque `api.github.com` não consta na política aplicada. Git e site GitHub respondem.

### Resultado final: build Windows real de diagnóstico aprovado

O [run 43950853793](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793), fonte **`c97f9d1fd8ce152f3d2261c750c5d8739e69c88f`**, terminou **Success** em **2m58s**. Runner **Windows Server 2022 x64**, Python **3.12.10**, PyInstaller **6.22.3** e dependências fixadas. Não foi build Linux, Wine ou compilação simulada.

| Verificação no runner | Resultado real |
| --- | --- |
| Suíte completa | 95 casos: **94 aprovados**, **1 POSIX não aplicável ao Windows**, 0 falhas e 0 erros. Nenhum caso foi removido para obter aprovação. |
| GUI, API e SQLite da fonte | Nove testes GUI e seis HTTP reais exigidos pelo gate; cofres, histórico/preferências e compatibilidade de formato incluídos na suíte. |
| Executável | PyInstaller `onedir/windowed`, Windows x64/Python embutido; EXE executado de verdade com `sys.frozen=true`. |
| Qt empacotado | Plugin **windows**, janela real e capturas dos widgets no runner. Não houve validação humana de acessibilidade/DPI. |
| NOW Engine empacotada | A mesma aplicação iniciou sua Engine filha, com Bearer e identidade de instância confirmados via cliente HTTP real. |
| Comandos reais | **6**: oi/horas/data e hello/time/date. Provider offline, conteúdo não vazio e nenhum banco criado pela sessão temporária. Não são gerações Qwen. |
| ZIP | Criado com EXE, dependências Python/Qt, instalação/notas, licenças, capturas e evidência. CRC, caminhos, inventário, tamanho e SHA-256 verificados pelo builder Windows. |
| Arquivos privados | Inspeção no builder aprovada: nenhum `.env`, banco privado ou padrão reconhecido de credencial incluído. Pacote construído de entradas controladas, sem diretórios de usuário. |
| Artifact GitHub | Aproximadamente **50 MB**, `now-assistant-ci-c97f9d1fd8ce152f3d2261c750c5d8739e69c88f-attempt-1`, disponível em Artifacts do run. |
| Publicação | **Não executada**. Nenhuma tag, draft ou Release criada por esta preparação. Workflow de publicação configurado/testado em seus gates unitários, sem execução da operação pública. |

ZIP gerado: `NOW-Assistant-0.3.0-alpha.1-diagnostic-Windows-x64.zip`.

- SHA-256 do ZIP informado pelo runner: `8cfa2d45fc21e635f66594e5967087b9ded53fd8cf9926439a84ee4df1842785`.
- SHA-256 do EXE informado pelo runner: `443b63989b4ec62a0825ab4dc70c7b3a896adc04e217b448bb4a00a822a5e5bd`.
- Digest do invólucro artifact GitHub (diferente do ZIP interno): `ee103621b88dce97f04daf2a91ccfd0805d374f409679270490b2ded10731841`.

Os resultados/hashes foram observados nas anotações estruturadas e no status públicos do run. A API continua bloqueada nesta instância; **ZIP/EXE e screenshots Windows não foram baixados/inspecionados localmente**. As verificações de CRC/SHA/inventário citadas foram executadas pelo builder Windows, não uma segunda verificação nesta máquina Linux. Evidência registrada em `validation/distribution-20261116.json`.

### Falhas encontradas e correções executadas

| Run | Fonte | Resultado |
| --- | --- | --- |
| [43947946896](https://github.com/Gabomgames/Now-assistant/actions/runs/43947946896) | `a130ba3` | Falhou antes do ZIP; logs autenticados indisponíveis nesta instância. Não aprovado. |
| [43948920266](https://github.com/Gabomgames/Now-assistant/actions/runs/43948920266) | `e5ee9bc` | Falhou; anotações identificaram arquivos SQLite abertos, erro de cofre ausente, Engine filha, bootstrap API e caminho Qt. Não aprovado. |
| [43950337802](https://github.com/Gabomgames/Now-assistant/actions/runs/43950337802) | `aa8dd86` | 93 aprovados, uma falha de espera por widget nativo, um POSIX não aplicável; erros de recursos eliminados. Não aprovado. |
| [43950853793](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793) | `c97f9d1` | **Sucesso**, 94 aprovados/um POSIX não aplicável; build/EXE/Engine/ZIP reais completos. |

Correções mantiveram as verificações: fechamento explícito de conexões SQLite de status/fixtures (context manager SQLite faz commit, mas não fecha), cofre ausente com erro portátil, encerramento apenas da árvore da Engine própria no Windows e espera curta por liberação de handles. O teste de API cria o socketpair de controle interno do loop Windows antes de instalar o audit que continua negando toda conexão da aplicação, inclusive imports/modelo. Caminhos Qt são comparados após resolver aliases Windows 8.3 e o teste aguarda a visibilidade real após resposta HTTP. Nenhum teste de rede foi trocado por resposta simulada.

Uma prova separada de checkout `core.autocrlf=true` reproduziu alteração dos 36 finais de linha do dataset, quebrando o hash original. `.gitattributes` mantém os bytes dos dados/originais; o checkout conferido voltou ao SHA-256 original `dd4c28950cd930fc009164bb82f5dc10bccf2f7898e9818478355b375ed07e72`. Não houve substituição do hash para aceitar dados alterados. Linux: 95 testes passaram após correções de recursos (25,957 s); API/GUI portáveis passaram em execução direcionada de 11 testes (12,180 s).

### O que impede a Alpha oficial/publicação

O pacote atual é **diagnóstico, `release_eligible:false`**: falta o PNG/JPG/WebP original da logo acessível como arquivo. Foi usado `--icon NONE`, sem logo redesenhada ou genérica apresentada como oficial. O importador/uso de PNG/ICO está implementado e o modo Alpha exige logo verificada, confirmação de revisão, ícone PE e imagem carregada na GUI. **Esses testes com a marca oficial ainda não foram executados.** Enviar o original em ZIP evita a indisponibilidade do anexo inline.

Após receber/importar/revisar/commitar os assets, executar Prepare Windows Alpha, apresentar seu ZIP/resultados e só publicar mediante autorização posterior do proprietário para versão/SHA/run específicos. A publicação manual recusa diagnóstico, forks, SHA/versão diferentes, hashes inválidos e versão já existente. Não dispara automaticamente por push/tag/CI concluído. Versões experimentais são Pre-release.

Windows 10/hardware alvo de 8 GB, revisão humana de DPI/leitor de tela/ACLs e assinatura digital permanecem pendentes. Ollama e Qwen não estão incluídos; nenhuma inferência, voz física, wake word ou APK foi validado nesta pipeline. A execução automática Windows não altera esses limites.

Para `gh`/download de logs nesta instância: painel do ambiente Codex → Internet/rede restrita → confirmar **`api.github.com`** nos hosts permitidos, sem esquema/caminho → revisar/salvar/aplicar e publicar configuração para novas tarefas quando necessário → verificar política efetiva. O domínio já foi salvo no rascunho, preservando `registry.ollama.ai`, mas o runtime ainda observa revisão **1**, sem a regra. Não foi pedido PAT/chave nem contornado proxy. Essa publicação de configuração de ambiente é diferente de GitHub Releases.

Detalhes: `docs/GITHUB_DISTRIBUTION.md`. Relatórios anteriores abaixo continuam históricos, não são aprovação da distribuição Alpha.

## Entrega desktop V3 — 16/11/2026

Especificação V3 lida integralmente (235 linhas), preservada em `docs/specs/NOW_ASSISTANT_V3.txt`, SHA-256 `7195a17c6e9da500d8873c90d42f8fe684de9da8375dc862a3a2a5f993ebb280`. O plano foi apresentado antes das alterações: GUI PySide6 ligada à Engine, texto assíncrono, estados reais, histórico opt-in e preferências separadas. Justificativa da tecnologia em `docs/DESKTOP_ARCHITECTURE.md`.

### Preservação e baseline

Branch `work`, HEAD inicial `6cdb0c72fd2b70af118df1f41dda6f9e260db047`, árvore inicialmente limpa e remoto correspondente. Backup dos arquivos versionados, sem `.env`/cofres privados: `/workspace/.now-ai-backups/desktop-v3-20261116T141403Z/tracked-source.zip`. Nenhum reset, clean, recriação ou remoção da base. Todos os arquivos de testes anteriores permanecem byte a byte iguais ao commit inicial.

Dos nove arquivos originais do ZIP 0.2, **sete continuam byte a byte iguais**. README foi atualizado conforme pedido explícito V3, e `.gitignore` recebeu venv desktop, releases e bancos privados. Ambas as versões originais permanecem no histórico Git e no backup; os sete arquivos de código/configuração restantes não foram reescritos. `now_engine.assistant` evoluiu de forma compatível para contexto e nome atual; os primitivos de criptografia foram compartilhados sem mudar o formato Memory v1. A compatibilidade do formato antigo foi testada com um banco montado independentemente.

### Resultados executados

| Verificação | Resultado real e limite |
| --- | --- |
| Baseline antes da implementação | **55 testes**, todos aprovados em 9,100 s. |
| Suíte final completa em venv mínimo sem Google SDK | **86 testes**, 86 aprovados, 0 ignorados, em 23,972 s. Inclui treinamento e os 55 anteriores. |
| Reuso do install_script atualizado | Executado integralmente, código 0; **86 testes** aprovados em 26,236 s, `pip check`, validação de dados e dry-runs. Não são outros 86 testes distintos. |
| Testes novos | 8 de histórico/compatibilidade Memory v1; 6 da API HTTP real; 9 de Qt + API/SQLite reais; 5 de estado/privacidade do controller; 3 do importador raster. |
| GUI + API | Widgets reais via QTest: envio, idioma/nome, erro real de modelo ausente, cancelamento, limite, texto HTML não interpretado, renderização e scroll. Sem doubles de resposta nos novos testes da GUI/API. |
| Histórico na janela | Consentimento, senha, persistir, buscar conteúdo, renomear, exportar JSON, bloquear, reabrir, erro de senha sem substituir banco, retomar, excluir e manutenção de retenção realmente executados. |
| NOW Memory na janela | Guardar/carregar preferências, desativar, impedir carga desativada, apagar e confirmar estado real do cofre; histórico não foi criado por salvar preferências. |
| Launcher normal | `now_desktop.__main__.main` executou seu event loop Qt, iniciou API própria, respondeu `horas` e encerrou; nenhum banco temporário criado. |
| Smoke e capturas | Janela real **Linux/Qt offscreen**, seis comandos determinísticos: oi/horas/data e hello/time/date. Provider `offline`; nenhuma resposta generativa. Pasta local `/workspace/artifacts/NOW-Assistant-V3-FINAL-GUI`. |
| RAM/latência observadas no smoke | Valores da execução em `validation/desktop-v3-20261116.json`: RSS de GUI/Engine e latência por comando. Não medem pico de scrypt/modelo, CPU em repouso, FPS ou Windows 10/8 GB. |
| Dependências | Ambiente desktop mínimo instalado com versões fixadas; `pip check` aprovado. Consulta PyPI das 21 distribuições não indicou alertas após atualizar pip 25.0.1 para 26.3. Escopo não inclui auditoria completa das bibliotecas nativas Qt/OpenSSL. Licenças Qt/terceiros requerem revisão para redistribuição. |
| Build Windows | Apenas a proteção de plataforma foi executada: recusa correta em Linux, código 2. **Nenhum `.exe` construído ou validado**. Ferramenta preparada exige logo original e revisão de ícones. |
| Treinamento | Fontes/dados preservados; validação e dry-runs executados pelo setup. Nenhum treino, LoRA ou avaliação de respostas de modelo realizada. |

Durante a implementação, o teste de exportação inicialmente selecionava o nome padrão em vez do nome solicitado; o diagnóstico confirmou exportação real para aquele nome. A automação passou a preencher o campo de arquivo e validar o destino. A inspeção das capturas também encontrou sobreposição de widgets antigos e scroll fora da última mensagem: o código foi corrigido e ganhou teste de renderização. Os resultados iniciais com falhas não foram declarados aprovados; os números acima são das execuções finais.

Os testes antigos com modelos/áudio substitutos continuam sendo **TESTADO COM DOUBLE**; fixtures do controller e retângulos do importador não representam conversas/identidade visual reais. Os novos fluxos Qt/API/cofres são **TESTADO REALMENTE**, na plataforma Linux indicada. Fonte e ferramentas estão **IMPLEMENTADO**, sem aprovação automática de Windows.

### Bloqueios observados

- **Qwen — BLOQUEADO:** política aplicada observada atual, revisão 1, `restricted/enforced`, sem `registry.ollama.ai`. GET real falhou no túnel com `403 Forbidden`; pull real com o binário Ollama 0.40.16 retornou `Forbidden` no manifesto `https://registry.ollama.ai/v2/library/qwen2.5/manifests/0.5b`, código 1. `/api/tags` responde com lista vazia. **Zero das oito gerações reais executadas**. Nenhuma chamada Gemini, contorno de rede ou desativação de TLS.
- **Logo — BLOQUEADO PELO ARQUIVO:** a imagem foi visível na conversa, mas não chegou como arquivo acessível nos anexos da máquina. Manifest `awaiting_original_file`; não há logo desenhada ou genérica substituta. Importador gera PNGs/ICO proporcionais preservando bytes do original quando o arquivo for fornecido. Seus testes usaram apenas retângulos temporários, não a marca oficial. A GUI usa texto NOW Assistant e paleta enquanto aguarda.
- **Windows — PENDENTE DE PLATAFORMA:** código/build preparados, instalação e roteiro VS Code em `docs/DESKTOP_WINDOWS.md`; execução Windows, ACLs, DPI, leitor de tela, hardware alvo, licença final do bundle e EXE/instalador precisam de validação nativa.

Para resolver a rede: no painel do ambiente, revisar a configuração Internet/rede restrita e confirmar o domínio **já presente no rascunho**, `registry.ollama.ai` (sem esquema/caminho), preservando os outros domínios. Salvar/aplicar a configuração pela ação disponível; publicar a versão para novas tarefas. Confirmar depois que o host aparece na política efetiva da instância. As ferramentas desta tarefa salvam rascunho e leem estado, mas não aplicam a política ao runtime. Outros hosts de blobs só podem ser identificados após liberar o manifesto. Salvar rascunho não comprova aplicação, publicação ou restauração. Não pedir chave Gemini para resolver esse bloqueio.

### Próximas fases

Voz real push-to-talk, STT/TTS audíveis, “Now” em segundo plano, bandeja/startup opt-in, visão, ferramentas permitidas, modos de linguagem por idade, Android/sincronização e NOW Cloud estão **PLANEJADO**, aproveitando os contratos anteriores sem anunciar captura/fala ativas. Naturalidade bilíngue, humor/entonação e contexto generativo precisam de modelo/áudio reais. Não há proatividade, microfone, tela ou nuvem habilitados pela GUI.

Evidências compartilháveis (somente dados artificiais dos testes): `validation/desktop-v3-20261116.json`, `validation/desktop-dependencies-20261116.json` e `validation/desktop-v3-evidence/`. O install_script com Qt foi executado; a revisão exata salva no rascunho e o SHA enviado ao GitHub são informados na entrega final. Publicação/restauração de outra tarefa não foram realizadas nesta máquina.

---

## Relatórios anteriores preservados — NOW AI 0.2, 16/11/2026

## Base e preservação

Importados nove arquivos originais de `NOW-AI-0.2-ENGINE.zip` para o checkout vazio `/workspace/Now-assistant`. Código, README, requisitos e seis testes foram preservados. O GitHub continua sem commits/branches; a base importada está sem commit. O TXT V2 é uma especificação futura, não uma implementação.

## Verificado nesta máquina Linux x86_64 / CPU

- Python 3.12.14, virtualenv, instalação dos requisitos e `pip check`: sucesso.
- Seis testes existentes com unittest: 6 executados, 6 aprovados; alguns usam mocks.
- CLI real: ajuda, hora, data, encerramento e erro de provedor indisponível: sucesso.
- Dez verificações de HTTP contra Uvicorn real: saúde, Swagger, OpenAPI, três comandos offline, três entradas inválidas e indisponibilidade explícita do modelo: sucesso.
- Ollama 0.40.16: pacote oficial com SHA-256 `87bfafb2acbc89b2e6a1be0a9043de6aa75fb450696f86bc426e65fc448f788d` verificado; somente binários/bibliotecas CPU e licenças extraídos. `/api/version` e `/api/tags` responderam; lista de modelos vazia.
- Script de instalação executado e repetido com sucesso, reutilizando dependências e binários verificados. Servidores encerrados e reiniciados pelos comandos registrados; as mesmas dez verificações de HTTP passaram após o reinício. A configuração local `.env` permaneceu igual aos defaults fornecidos.
- Comparação final byte a byte: todos os nove arquivos fornecidos continuam idênticos ao ZIP. Nenhum commit ou push realizado. O arquivo de instalação de 1,44 GB foi removido após verificação e extração; os componentes CPU retidos ocupam aproximadamente 77 MB.

## Pendência externa

O download real de `qwen2.5:0.5b` falhou no manifesto de `https://registry.ollama.ai/v2/library/qwen2.5/manifests/0.5b`: proxy Forbidden. A requisição direta também falhou com Tunnel connection failed: 403 Forbidden. Inferência com modelo local permanece não validada. A inclusão de `registry.ollama.ai` foi salva no rascunho da rede; aplicar nas configurações e repetir o pull. A consulta final do runtime confirmou que esse domínio ainda não está liberado na política aplicada. Domínios de blobs adicionais só poderão ser identificados se o registro redirecionar o download.

Gemini não foi configurado nem testado, pois é opcional. Windows, Android, voz, GPU, memória persistente, internacionalização e fases V2 não foram testados ou implementados. A API atual já existia no ZIP e não tem autenticação, conforme o README; permanece em loopback.

## Reutilização

Instruções completas: `install.sh` e `start_skill.md` neste diretório, salvas nos campos `install_script` e `start_skill` da configuração, junto com a adição de rede `registry.ollama.ai`. A ferramenta confirmou `status=saved` e `requires_publish=true`. Dependências e binários são arquivos retidos; processos devem ser reiniciados. Salvar rascunho não aplica a rede nem publica o ambiente. Revise e salve as alterações nas configurações; após resolver o download e validar o modelo, publique o ambiente. Publicação e restauração em uma nova tarefa ainda não foram verificadas.

## Continuação do desenvolvimento — 16/11/2026

### Preservação

Antes desta continuação foi criado o backup local `/workspace/.now-ai-backups/20261116T105318Z/before.tar.gz`, com 4.341 entradas do checkout e do estado de configuração, incluindo arquivos locais. Ele é um backup privado de trabalho e não faz parte do ZIP de entrega. Há também um manifesto SHA-256 no mesmo diretório. A comparação final confirmou que os nove arquivos originais continuam idênticos, byte a byte, ao ZIP enviado. Nenhum arquivo original foi removido, reescrito ou recriado; nenhum commit/push foi realizado.

### Rede e modelo: bloqueio confirmado

A consulta do ambiente retornou observações atuais, rede restrita aplicada (`state=enforced`) e revisão de runtime `1`, sem `registry.ollama.ai` entre os domínios efetivos. O rascunho, revisão `2`, já contém o domínio nos destinos personalizados. O GET real do manifesto continuou falhando com `Tunnel connection failed: 403 Forbidden`. Isso é uma diferença entre rascunho salvo e política aplicada, não uma necessidade de chave Gemini.

As ferramentas disponíveis permitem consultar o runtime e salvar o rascunho, mas não oferecem `request_changes` nem outra ação para aplicar a rede diretamente à máquina. Não houve tentativa de contornar o proxy. O Ollama local responde com versão `0.40.16`; `/api/tags` continua retornando lista vazia. O modelo `qwen2.5:0.5b` não foi baixado ou instalado, e nenhuma conversa gerada foi validada.

Para prosseguir: abrir as configurações deste ambiente no painel do Codex, acessar a configuração de rede/Internet, manter acesso restrito e confirmar `registry.ollama.ai` nos domínios permitidos, sem esquema, porta ou caminho. Preservar as demais permissões. Salvar/aplicar as alterações ao ambiente em execução; quando oferecida, a ação **Save draft** pode atualizar o ambiente de configuração. O domínio já está no rascunho, portanto não é necessário declará-lo de novo. Depois, confirmar a política aplicada e repetir o pull. Caso um blob redirecione a um novo host bloqueado, registrar o hostname observado para liberação adicional. Publicar a configuração reutilizável após concluir a validação.

### Resultados desta continuação

| Verificação | Resultado real |
| --- | --- |
| `pip check` | Aprovado: nenhuma dependência quebrada. |
| `python -m unittest discover -s tests -v` | 6 testes executados e aprovados. Os mocks existentes não comprovam geração real. |
| Validador `tools/validate_local.py` | 7 checks básicos aprovados: saúde da API, 3 comandos offline, terminal offline, versão e inventário Ollama. |
| Gerações pt-BR/en-US, em Ollama/Engine/API/terminal | 8 checks **não executados** por ausência do modelo. O validador encerrou com código 2 e status `blocked`, preservando essa distinção. |
| Caminho real de erro por falta do modelo | Ollama retornou HTTP 404; Engine, API FastAPI e terminal retornaram `unavailable`. Nenhuma resposta de modelo foi simulada. |
| Gemini no teste integrado de erro | A API temporária e o terminal foram iniciados explicitamente com `ENABLE_GEMINI_FALLBACK=false`; o Engine foi chamado com a mesma variável. Nenhuma chave foi solicitada. |
| Launcher novo, em código-fonte Linux | CLI com ajuda/hora/data/saída aprovado. API com saúde, comando offline, entrada inválida HTTP 422 e modelo ausente aprovada. Não é um teste de executável Windows. |
| Sintaxe dos três scripts adicionados | `py_compile` aprovado; ajuda de linha de comando verificada. |
| Build nativo Windows | Não executado: esta máquina é Linux. O comando de build recusou a plataforma com código 2, conforme projetado. Nenhum `.exe` foi gerado ou declarado validado. |

Os testes temporários de API foram encerrados; os serviços originais de desenvolvimento foram preservados. As evidências estruturadas estão em `validation/local-validation-20261116.json` e `validation/failure-paths-20261116.json` no checkout. As mesmas evidências foram retidas em `/workspace/.now-ai-environment`. Elas contêm apenas prompts de teste fixos e resultados observados.

### Preparação Windows e VS Code

Arquivos novos, sem modificar a base:

- `tools/validate_local.py`: gera oito respostas reais por quatro caminhos e dois idiomas quando o modelo existe. Sem o modelo, registra `not_run`; não substitui respostas por mocks. Mesmo com transporte aprovado, exige leitura das respostas para avaliar idioma e qualidade.
- `packaging/windows/entry.py`: launcher adicional para o terminal original ou API em loopback, com `.env` externo ao futuro executável e saída UTF-8.
- `tools/build_windows.py`: build com PyInstaller em Windows x64/Python 3.12. Executa testes existentes, testa CLI/API offline do executável e gera ZIP e relatório somente após esses checks. Não faz cross-compilação nem comprova conversas com modelo.
- `packaging/windows/requirements-build.txt` e `constraints-python312.txt`: dependências de build declaradas; PyInstaller `6.22.3` consultado no PyPI oficial. As versões de runtime foram copiadas da instalação Linux validada. A instalação dessas dependências no Windows ainda não foi executada.
- `docs/WINDOWS_VSCODE.md`: instruções completas em PowerShell para VS Code, instalação, modelo, API, terminal, validação real, build e uso do futuro `.exe`.

A sequência restante é: aplicar a rede; baixar e verificar o modelo via Ollama; executar o validador e revisar as respostas pt-BR/en-US sem Gemini; gerar o `.exe` em executor Windows; validar o executável também com modelo real e registrar a versão do Windows. O prompt original pede pt-BR, portanto o comportamento em inglês precisa de evidência específica. Não há validação de Windows 10, nem comprovação de voz, interface ou Android.

O pacote de fonte e ferramentas será denominado `NOW-AI-0.2-FONTE-E-BUILD-WINDOWS.zip`; esse nome não representa um executável já construído. O pacote exclui `.env`, credenciais, `.git`, ambientes virtuais, caches e modelos.


## Rechecagem após a liberação informada — 16/11/2026 08:11:54 (America/Sao_Paulo)

A alteração informada pelo usuário foi investigada com uma nova conexão ao registro, uma tentativa real de download pelo cliente Ollama e consulta da política viva do proxy. Os arquivos e resultados anteriores foram preservados; esta seção acrescenta as evidências da nova tentativa.

| Item observado | Resultado desta tentativa |
| --- | --- |
| Estado da instância | Observações atuais; revisão desejada e observada `1`; política restrita `enforced`. |
| Rascunho | Revisão `2`; contém a regra `registry.ollama.ai`. |
| Política viva do proxy | Modo `allowlist`; o campo `policy.http.allowed_domains` tem zero entradas e não permite `registry.ollama.ai`. |
| GET novo do manifesto | `Tunnel connection failed: 403 Forbidden`. |
| `ollama pull qwen2.5:0.5b` | Executado, falhou com código 1 em `https://registry.ollama.ai/v2/library/qwen2.5/manifests/0.5b`: `Forbidden`. |
| Ollama e inventário | `/api/version`: HTTP 200, versão 0.40.16; `/api/tags`: HTTP 200, lista de modelos vazia. |
| API existente | `/health`: HTTP 200, NOW AI 0.2.0. Isso não demonstra inferência. |
| Oito gerações pt-BR/en-US | **Não executadas**: o modelo não foi baixado ou instalado. Nenhuma resposta de modelo foi simulada. |
| Executável Windows | Não gerado ou testado nesta máquina Linux; fonte, launcher, script de build e guia existentes foram preservados. |

O bloqueio exato é a ausência de `registry.ollama.ai` na lista ativa `policy.http.allowed_domains` do proxy desta instância. A regra está persistida no rascunho, mas não está aplicada à máquina desta conversa. O bloqueio acontece antes de obter o manifesto; nenhum redirecionamento de blob foi alcançado. Portanto, não há evidência de outro hostname de download faltando neste momento.

A configuração necessária é aplicar a regra de rede à **instância em execução desta conversa**, preservando as outras permissões e o modo restrito. Uma alteração salva apenas no rascunho ou destinada a futuras tarefas não comprova atualização desta máquina. As ferramentas disponíveis não oferecem uma ação `request_changes`/aplicação ao runtime; repetir a gravação do mesmo rascunho não resolveria essa diferença. Não foi solicitada uma nova autorização genérica: falta a aplicação da configuração à instância atual.

Os seis testes unitários e os checks anteriores mantêm seus resultados históricos; não foram reexecutados nesta rechecagem, que se limitou ao diagnóstico de rede e aos endpoints de estado. Não há nova aprovação de geração, idiomas ou executável. Gemini não foi usado nesta tentativa.

Evidência estruturada: `validation/network-recheck-20261116T111154Z.json`. Os relatórios anteriores foram copiados para `/workspace/.now-ai-backups/network-recheck-20261116T111154Z/` antes desta atualização. Os nove arquivos originais continuam idênticos ao ZIP; as demais fontes e configurações locais foram conferidas por SHA-256. A entrega Windows continua sendo um kit de fonte e build, sem `.exe`.


## Integração do kit Qwen — 16/11/2026 08:43 (America/Sao_Paulo)

Integração aditiva de `NOW_AI_TREINAMENTO.zip` à base existente, após backup em `/workspace/.now-ai-backups/training-integration-20261116T112912Z/`. O checkpoint preserva código, Git e arquivos locais; dependências/cache não foram alterados. Os nove arquivos originais da aplicação continuam byte a byte idênticos ao ZIP da Engine. Os datasets recebidos, os quatro testes originais do kit e `docs/DATA_POLICY.md` também foram preservados sem alterações.

| Área | Estado | Evidência/limite |
| --- | --- | --- |
| Kit integrado | CONCLUÍDO | `training/`, procedência, persona de avaliação, configurações, testes e documentação adicionados. Scripts do add-on adaptados; Engine original preservada. |
| Dados | TESTADO | 36 registros de treino piloto, 12 casos independentes, zero erro estrutural e zero sobreposição de prompts normalizados. A verificação não cobre toda similaridade semântica. |
| Suíte completa | TESTADO | 27 executados, 27 aprovados: 8 da aplicação e 19 de preparação/dados. Os testes unitários originais com mocks não demonstram inferência. |
| API/terminal sem provedor | TESTADO | Processos reais com saída de rede negada por audit hook: comandos offline funcionam e perguntas livres retornam indisponibilidade. Gemini foi explicitamente desativado. Nenhuma resposta de modelo foi simulada. |
| Instalação reproduzível | TESTADO | `bash /workspace/.now-ai-environment/install.sh` completou, reutilizando dependências/binários verificados e executando os 27 testes e os três comandos de preparação. |
| Planejamento LoRA | TESTADO | `--dry-run` validou dados e listou bloqueios sem importar bibliotecas GPU ou baixar pesos. Não iniciou treinamento. |
| Planejamento da avaliação | TESTADO | `--dry-run`: 12 casos, zero gerações, 12 não executados, qualidade `NOT_SCORED`. |
| Gerações com modelo | IMPEDIDO | Modelo não instalado; última política aplicada continua sem `registry.ollama.ai`. Não houve nova tentativa de contornar ou repetir downloads nesta integração offline. Os oito checks anteriores da aplicação e os 12 novos casos reais continuam não executados. |
| Fine-tuning real | PENDENTE | Piloto insuficiente, validação separada ausente, licença/permissão dos dados ainda não confirmadas e executor CUDA não preparado/validado. Dependências GPU não foram instaladas. |
| Perfil Casual/PT-BR/EN | CONCLUÍDO como preparação | Texto versionado no avaliador, com limites de ferramentas, memória e áudio. A persona da Engine original não foi alterada e o comportamento de nenhum modelo foi aprovado. |
| Memória e voz | PENDENTE | Roadmap documentado; nenhuma persistência, transcrição, síntese ou ativação por voz foi implementada. |
| Executável Windows | IMPEDIDO nesta máquina | Build/guia anteriores preservados e ampliados com preparação de dados. Build e execução nativa Windows continuam não executados. |
| Retomada | CONCLUÍDO como documentação | `docs/NEXT_TASK.md`, `training/README.md`, `docs/MODEL_ROADMAP.md` e guia Windows descrevem comandos e pré-requisitos. Publicação/restauração em nova tarefa ainda não verificadas. |

Comandos efetivamente executados com sucesso:

```bash
.venv/bin/python -m pip check
.venv/bin/python training/scripts/validate_dataset.py
.venv/bin/python -m unittest discover -s training/tests -v  # quatro testes do kit antes das adaptações
.venv/bin/python training/scripts/train_lora_gpu.py --dry-run
.venv/bin/python training/scripts/run_ollama_eval.py --dry-run
.venv/bin/python -m unittest discover -v                  # suíte final: 27 testes
bash /workspace/.now-ai-environment/install.sh           # reprodução final, também 27 testes
```

A procedência está em `training/data/PROVENANCE.json`, vinculada por SHA-256 ao arquivo piloto e ao ZIP. A declaração de autoria sintética veio no material recebido; não foi transformada em comprovação de autoria/licença. A execução real exige uma revisão explícita vinculada ao checksum, novo corpus e validação independente. A recusa de treino com o piloto foi testada.

Qwen2.5 permanece baseline; Qwen3-0.6B é apenas candidato registrado, sem troca automática. Documentações oficiais Qwen foram consultadas por HTTPS e declaram licenças abertas Apache 2.0; a licença/revisão dos artefatos não baixados ainda deve ser conferida. Os ranges de dependências de treino permanecem experimentais e não tiveram compatibilidade GPU comprovada.

O avaliador foi preparado para manter progresso/metadados, arquivos anteriores e revisão humana. O caminho que recebe/salva gerações reais ainda precisa ser exercitado com Ollama e pesos locais. Nenhum adaptador foi treinado e nenhum modelo próprio foi declarado pronto. Personalizar Qwen não equivale a treinar um modelo fundacional do zero.

Evidência estruturada e hashes dos nove originais: `validation/training-integration-20261116.json`. Para identificar o commit desta entrega, consultar `git log -1 --format='%H %s'`; o resultado do envio remoto deve ser conferido no retorno desta tarefa e com Git de leitura, sem presumir autorização ou push bem-sucedido.


## Incremento NOW Memory / NOW Voice Engine — 16/11/2026 09:57 (America/Sao_Paulo)

Origem confirmada em `5caadced232697430af32d0cb30a564901c0c25a`, branch `work`, com árvore limpa e remoto igual. Backup anterior à edição: `/workspace/.now-ai-backups/voice-memory-20261116T123125Z/`. Os nove arquivos originais da aplicação e todos os arquivos-fonte dos 27 testes anteriores foram preservados. Não houve recriação da Engine, remoção de funcionalidades ou alteração dos dados de treinamento.

| Entrega/check | Estado | Resultado executado e limite |
| --- | --- | --- |
| Regressão da base | TESTADO | Os 27 testes existentes foram executados inicialmente e novamente na suíte completa; continuaram aprovados. |
| Suíte completa | TESTADO | 55 executados, 55 aprovados, zero falhas/skip no Linux: 27 anteriores + 14 de memória + 14 de voz. Reproduzidos também pelo instalador atualizado. |
| NOW Memory: preferências | FUNCIONAL/TESTADO | SQLite real, AES-256-GCM, scrypt e senha/chave não persistidas. Opt-in, leitura, atualização atômica, desabilitação, exportação explícita, exclusão e limpeza. Estado de consentimento autenticado e cifra vinculada ao campo. |
| Integridade/privacidade | TESTADO | Senha incorreta preserva banco; alteração/troca de cifras é detectada; dados inválidos não alteram preferências; diretório/arquivo 0700/0600 no POSIX. Abertura repetida nunca sobrescreve cofre. Exportação é texto aberto e não substitui arquivo existente. |
| CLI de memória e novo cliente | TESTADO | 15 verificações reais de subprocesso, incluindo preferências persistentes, saudação personalizada em inglês, recusa de memória desabilitada, exportação/limpeza e erros explícitos de modelo/áudio ausentes. Cofre de teste e exportação removidos; nenhum cofre real de usuário criado automaticamente. |
| NOW Voice Engine: infraestrutura | IMPLEMENTADO/TESTADO | Contratos PCM16, estados, uma requisição ativa, permissões independentes, cancelamento cooperativo e plano de segmentos/pausas/estilo. Não abre microfone no import ou setup. |
| Texto PT-BR/EN independente de modelo | FUNCIONAL/TESTADO | Novo `LocalAssistant` responde comandos determinísticos em ambos os idiomas e usa preferências explícitas. Testes impedem chamadas a modelo nesses comandos. |
| Persona geral Casual | PREPARADA EM CÓDIGO | Novo adaptador monta instruções versionadas de persona/humor/idioma; caminho generativo só aceita modelo local instalado, sem Gemini. Qualidade de conversação e humor continua não validada com modelo real. API/CLI originais preservadas. |
| Áudio/STT/TTS/“Now” | PENDENTE | Nenhum adaptador físico ou detector foi instalado. Capacidades reais padrão: capture=false, speech_output=false, wake_word=false, voice_quality_validated=false. `--speak` retorna erro de capacidade ausente. |
| Testes de contrato de áudio | TESTADO COM DOUBLES | Fixtures explicitamente identificadas, com PCM silencioso apenas para fluxo/estado; não são provas de transcrição, síntese, reprodução física ou qualidade vocal. |
| GUI Windows/Android | PLANEJADO | `docs/GUI_PLAN.md`: navegação, estados reais, acessibilidade, privacidade, transporte/autenticação e separação ViewModel/serviços. Nenhuma GUI/APK construída. |
| Modelo Qwen/inferência real | BLOQUEADO | GET novo e `ollama pull qwen2.5:0.5b` falharam no manifesto de registry.ollama.ai com Forbidden. Inventário Ollama vazio. Zero gerações novas; oito checks legados, 12 casos de persona e conversas do novo adaptador continuam sem execução real. |
| Fine-tuning, histórico e voz natural | PENDENTE | Nenhum peso treinado, histórico conversacional, sincronização, STT/TTS audível ou teste em hardware-alvo. Perfis/planos não comprovam voz natural ou expressividade. |
| Windows nativo | NÃO EXECUTADO | Guias/dependência opcional preparados. ACLs, dispositivos, GUI e `.exe` Windows/Android não foram validados nesta máquina Linux. |

### Rede publicada versus esta instância

A instância permaneceu na revisão desejada/observada `1`, ligada à mesma versão de origem anterior; a regra registry.ollama.ai consta no rascunho. O primeiro status desta rodada indicava política restrita aplicada (`enforced`); o último indicou estado de rede `unknown`, ainda sem a regra no conjunto informado. Esse estado desconhecido não prova prontidão. Uma conexão nova ao registro continuou recebendo `Tunnel connection failed: 403 Forbidden` após a reconsulta. Portanto, não foi possível confirmar que a configuração publicada se aplicou a esta máquina. O cliente Ollama também falhou com código 1 no domínio exato do manifesto; nenhum redirecionamento de blob foi alcançado. Não se contornou a política nem se inventaram respostas.

### Comandos efetivamente executados

```bash
.venv/bin/python -m unittest discover -v                 # base inicial: 27; suíte final: 55
.venv/bin/python -m pip install -r requirements-memory.txt -c packaging/windows/constraints-python312.txt
.venv/bin/python -m unittest tests.test_memory tests.test_voice -v  # 26 antes das duas últimas regressões
.venv/bin/python -m now_voice --capabilities
TZ=America/Sao_Paulo .venv/bin/python -m now_voice --text horas --language pt-BR
TZ=America/Sao_Paulo .venv/bin/python -m now_voice --text time --language en-US
bash /workspace/.now-ai-environment/install.sh           # suíte final 55 + preparação e status sem criar cofre
```

Também foram executados 15 comandos de smoke pela CLI com senha aleatória só no ambiente temporário do processo, sem imprimi-la ou persistir esse valor na evidência. O arquivo `validation/voice-memory-20261116.json` registra contagens e limites reais. O retorno `mode=text` e `playback_completed=false` foi conferido; não representa fala audível.

### Segurança e próximos passos

O cofre protege preferências em repouso, sem armazenar senha/chave; metadados como nomes de campos e horários são legíveis. Não é proteção contra um processo/conta já comprometido. Exclusão SQLite não apaga backups externos ou garante eliminação forense em SSD. A senha precisa ser fornecida pelo usuário no terminal, e os dados permanecem fora do Git. Permissões de microfone nunca são carregadas de preferências persistidas. Não há endpoints HTTP novos para dados privados.

O cancelamento de voz é cooperativo: drivers reais devem respeitar o token; a requisição HTTP local ainda pode aguardar até 90 segundos e não tem interrupção ativa da geração. Próximos incrementos: aplicar rede à instância e revisar conversas reais PT-BR/EN; implementar push-to-talk com adaptadores STT/TTS licenciados e medir em hardware; só então detector “Now”, eco e barge-in. Memória de conversas, migrações futuras, sincronização e transporte autenticado para a GUI requerem escopo/testes próprios.

Documentação: `docs/INCREMENT_VOICE_MEMORY.md`, `docs/NOW_MEMORY.md`, `docs/NOW_VOICE_ENGINE.md`, `docs/GUI_PLAN.md` e `docs/NEXT_TASK.md`. A revisão a usar na nova tarefa deve ser obtida com `git log -1`; confirmação do envio remoto e do rascunho fica no retorno desta tarefa. Publicação e restauração numa nova instância não são comprovadas pelos testes nesta máquina.
