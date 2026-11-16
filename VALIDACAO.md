# NOW Assistant — validação incremental

## Distribuição GitHub — preparação de 0.3.0-alpha.1 (16/11/2026)

Base `work`, commit inicial `15e03a7dbbe73a817a831d3f27858d7387b6e0e2`, árvore inicialmente limpa e remoto correspondente; backup de fontes versionadas em `/workspace/.now-ai-backups/distribution-before-15e03a7.zip`. Nenhum reset/recriação. Baseline: 86 testes aprovados em 25,538 s.

Implementados workflows Windows CI, Prepare Windows Alpha e publicação exclusivamente manual, com permissões separadas e actions fixadas por SHA. SemVer inicial `0.3.0-alpha.1`, notas/guia para usuário sem Python/VS Code, build/Engine/smoke reais exigidos e ZIP com hashes, licenças e inspeção de arquivos privados. O CI diagnóstico é identificado como não publicável; Alpha exige logo original/revisão e ícone PE/GUI reais. Não foi autorizada/executada publicação de release.

Validação local após implementação: **95 testes aprovados** em Linux, 0 ignorados, em 28,996 s. São os 86 anteriores mais nove testes de gates com fixtures sintéticos de metadados/ZIP; esses fixtures não são builds Windows e não validam inferência. Testes GUI existentes receberam apenas ajustes para operar o seletor Qt de forma portável; nenhum caso foi removido. `actionlint 1.7.11` validou os três workflows sem erros; binário oficial com checksum `900919a84f2229bac68ca9cd4103ea297abc35e9689ebb842c6e34a3d1b01b0a` verificado. Compilação de módulos e `git diff --check` aprovados.

**Estado antes do primeiro push da pipeline:** build Windows ainda não executado, Alpha não aprovada. A logo foi enviada novamente como imagem inline, mas nenhum arquivo binário apareceu nos anexos locais; não foi redesenhada. `gh api .../actions/workflows` falhou no CONNECT 403 porque `api.github.com` não consta na política aplicada. Git e site GitHub respondem. O estado/resultados do runner serão registrados depois da tentativa real, sem substituir execução por simulação.

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
