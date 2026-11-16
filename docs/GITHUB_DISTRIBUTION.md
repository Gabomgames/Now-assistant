# Distribuição Windows pelo GitHub

## Fluxos separados

| Workflow | Disparo | Permissões | Resultado |
| --- | --- | --- | --- |
| Windows CI | Push na work com código/build, PR para work ou manual | contents:read | Testes + build Windows **diagnóstico**, nunca publicável |
| Prepare Windows Alpha | Manual ou push de solicitação explícita; proprietário, work e confirmação da logo | contents:read | Candidato com logo, testes e smoke empacotado; artifact para revisão |
| Publish approved Windows Release | Somente manual, proprietário, versão/SHA/run exatos e frase de aprovação | contents:write/actions:read apenas no job de publicação | Publica exatamente o ZIP revisado após verificar sua origem/hashes |

Não há publicação em push, tag, conclusão de CI ou cron. Não foi solicitada/executada publicação nesta preparação. GitHub pode precisar que o proprietário habilite Actions em **Settings → Actions → General**; a preferência de workflow pode permanecer read-only, pois só o job manual de publicação solicita contents:write. Não é necessário criar PAT ou guardar uma credencial pessoal: usa o GITHUB_TOKEN efêmero do próprio workflow. As actions estão fixadas por SHA completo.

`work` foi confirmada como branch padrão do repositório. Workflows `workflow_dispatch` precisam existir na branch padrão para aparecer no painel. Caso a branch padrão mude, mantenha os workflows nela mediante revisão; não modifique `main` automaticamente para resolver isso. Fonte/testes/desenvolvimento continuam na `work`.

## O que o Windows runner executa

Windows Server 2022 x64 hospedado pelo GitHub, Python 3.12 x64, venv de build isolado, dependências fixadas em `packaging/desktop/requirements-build.txt`. O build:

1. Exige fonte versionada limpa e versão SemVer de `now_desktop/version.py`.
2. Executa `pip check` e **toda** a suíte via `tools/run_tests.py`, gerando JSON. GUI/API não podem ser ignoradas por falta de Qt. A única exclusão prevista em Windows é o teste de permissões POSIX, registrado explicitamente.
3. Usa PyInstaller `onedir/windowed`, sem UPX; inclui Python/Qt, recursos da marca e versão no PE. O código da Engine é o existente no repositório.
4. Abre o **EXE empacotado**. Ele inicia sua própria Engine via o mesmo EXE, confirma autenticação/identidade e executa oi/horas/data + hello/time/date por HTTP real. Verifica Windows, Python 3.12 x64, `sys.frozen`, plugin Qt `windows`, ausência de banco em sessão temporária e captura widgets reais. Não são respostas Qwen simuladas.
5. Coleta licenças/avisos, inclusive fontes Qt/PySide fixados por commit/SHA-256, cria inventário SHA-256 de arquivos e rejeita `.env`, chaves, credenciais reconhecíveis e bancos privados. Não coleta env dump nem cofres do usuário.
6. Cria ZIP, verifica CRC, caminhos seguros, conteúdo e hashes antes de disponibilizar o artifact. `BUILD-VALIDACAO.json`, `SHA256SUMS.txt`, notas, testes e capturas acompanham a evidência. Qualquer falha impede aprovação.

Smoke no runner não comprova Windows 10, hardware de 8 GB, leitor de tela, DPI, ACLs de perfis de usuários, áudio físico ou naturalidade Qwen. A suíte inclui doubles antigos e novos fixtures de metadados/ZIP; eles são testes de contratos/validação, separados do smoke nativo. A janela empacotada é realmente executada no Windows runner; não afirmar interação humana ou áudio onde não houve.

## Logo oficial e primeiro candidato

Versão preparada: **0.3.0-alpha.1**. O ZIP definitivo da logo foi recebido e seu PNG original foi preservado em `assets/branding/original.png`, SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`. O manifest registra `imported_official_asset`, proporção original 1301 × 1209 e padding preto externo. Há nove PNGs derivados e ICO com oito resoluções; não houve redesenho ou remoção de fundo. O modo Alpha usa esses assets verificados. O CI de diagnóstico permanece não publicável por definição.

Recebendo o arquivo original, com o ambiente desktop instalado:

```powershell
python tools/import_branding.py 'C:\caminho\logo-oficial.png' --padding black
```

Confira o original intacto, SHA do manifest e ícones derivados. Commit/push dos assets na work são necessários para o runner receber os mesmos bytes. **Actions → Prepare Windows Alpha → Run workflow**: branch work, version `0.3.0-alpha.1`, marcar `branding_reviewed` somente após inspeção. O modo Alpha recusa logo ausente/alterada e verifica recurso de ícone no PE e imagem carregada na GUI. Ele não cria tag nem release.

Também é possível preparar pelo evento nativo **push**, alterando `packaging/releases/alpha-request.json` na work. Essa solicitação contém UUID v4 novo, versão exata, SHA-256 do original revisado, `branding_reviewed: true`, `prepare_artifact: true` e obrigatoriamente `publish_release: false`. Preserve o schema e os demais campos do arquivo. Commit/push pelo proprietário solicita somente o artifact; mudanças comuns de código não repetem essa preparação. O workflow valida autor original e de rerun, branch, versão e logo antes de instalar dependências. O builder vincula o SHA-256 dos bytes da solicitação ao relatório e ao ZIP.

Esse disparo usa Git e o evento padrão do Actions, com token somente de leitura. Não faz chamadas à API em nome do ambiente cloud, não altera sua política de rede e não publica versões. A opção manual continua disponível. Para preparar outro candidato pela solicitação, atualize a versão se necessário e gere um novo UUID com `python -c "import uuid; print(uuid.uuid4())"`; revise, faça commit e push na work.

## Revisar antes de autorizar publicação

No run de Prepare Windows Alpha, leia o Summary, a conclusão de todos os passos e baixe o artifact `now-assistant-windows-<VERSION>-<SHA>-attempt-<N>`. O artifact do GitHub é um invólucro: dentro há o ZIP portátil da NOW, relatório, hashes e capturas. Confira versão, SHA completo, assinatura ausente, proveniência e limitações. Execute a aplicação no Windows alvo, mantendo a pasta `_internal`. Preserve os dados privados; os testes do runner usam somente fixtures temporários.

Após autorização explícita para **aquele** candidato, o proprietário pode executar **Publish approved Windows Release** com:

- `version`: SemVer exato, por exemplo `0.3.0-alpha.1`.
- `source_sha`: 40 caracteres do commit **testado**, não o HEAD presumido.
- `candidate_run_id`: ID numérico do run Alpha aprovado, não o run Windows CI.
- `authorization`: `PUBLICAR v0.3.0-alpha.1 @ <SHA_COMPLETO>`.

Não executar esse workflow apenas porque um build terminou. A autorização desta tarefa cobre preparar/testar, **não** publicar a primeira Alpha. O assistente deve apresentar o candidato/resultados e aguardar autorização posterior antes de disparar publicação.

O publicador confere proprietário/evento/branch, repo/workflow/run/attempt, conclusão, SHA, artifact imutável, ZIP/relatório/notas e hashes. Recusa CI de diagnóstico, forks, commit diferente, original da logo ausente e release existente. Não recompila durante publicação. Só após validar cria/reutiliza uma tag do mesmo commit, cria um **draft**, envia assets e por último torna público. Falhas de upload deixam draft, sem release pública. Reruns de publicação não sobrescrevem uma versão existente.

Para candidatos preparados por push, o publicador também lê a solicitação no **commit aprovado**, confere seus bytes/SHA contra o relatório e exige a mesma versão e logo. Um push comum ou um artifact de Windows CI não atende a esses critérios. A aceitação dessa origem não substitui a autorização manual de publicação para versão/SHA/run.

Versões com sufixos alpha/beta/rc e versões 0.x são marcadas **Pre-release** e não substituem Latest estável. Uma versão estável futura precisa de SemVer próprio, notas e nova aprovação manual. Não mover tags já publicadas para outro commit.

## Usuário final e conteúdo público

O usuário baixa o ZIP em Releases, verifica SHA-256, extrai a pasta inteira e abre NOW-Assistant.exe. Não precisa de VS Code ou Python manualmente. `LEIA-ME.md` e as notas de cada versão incluem instalação, requisitos, novidades, privacidade e limitações. Sem assinatura digital nesta Alpha.

**Ollama e Qwen não acompanham o ZIP.** Para perguntas livres: instalar Ollama oficial e baixar `qwen2.5:0.5b` por rede autorizada. Comandos locais básicos funcionam sem modelo. Nenhuma inferência, qualidade vocal, wake word ou visão é aprovada pelo smoke offline. Não incluir `.env`, senhas, bancos ou exportações pessoais ao relatar problemas.

## Acesso desta tarefa ao GitHub

Git HTTPS para work funciona. O acesso à API `api.github.com` foi recusado pelo proxy (CONNECT 403) e esse host está ausente da política aplicada da instância. O site normal `github.com` permitiu observar status/anotações dos runs, incluindo sucesso final e hashes. Logs autenticados e download do ZIP não foram acessados nesta máquina. Não extrair tokens nem trocar proxy para contornar a regra.

O domínio `api.github.com` foi acrescentado ao **rascunho de rede do ambiente**, mantendo `registry.ollama.ai`. Para habilitá-lo: painel do Codex → configurações deste ambiente → Internet/rede restrita → revisar domínios permitidos → `api.github.com` sem esquema/caminho → salvar/aplicar pela ação disponível. Publicar a configuração e selecionar a versão em nova tarefa quando necessário. Confirmar o host na política efetiva antes de repetir `gh api`. Salvar rascunho não aplica a rede nem publica o ambiente; **isso não é uma GitHub Release**. O Windows runner usa a rede/token normais do Actions, separado desta instância cloud. Não é necessário fornecer PAT em chat.

## Resultados históricos de diagnóstico

O [run 43950853793](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793), fonte `c97f9d1fd8ce152f3d2261c750c5d8739e69c88f`, terminou **Success** em 2m58s. Windows/Python 3.12.10: 95 casos, 94 aprovados, um POSIX não aplicável, zero falhas/erros. O EXE congelado abriu Qt `windows`, iniciou Engine e executou seis comandos offline reais. ZIP, licenças, inventário/CRC/SHA e upload passaram no runner. Artifact de cerca de 50 MB em **Artifacts**, no mesmo run.

Esse artifact é **diagnóstico** (`release_eligible:false`), sem o original da logo e sem ícone substituto. Não pode ser usado pelo publicador como Alpha aprovada. O ZIP Windows não foi baixado/inspecionado localmente por bloqueio da API; os resultados/hashes foram observados nas anotações públicas. Nenhuma tag ou Release foi criada; o fluxo de publicação permanece configurado, não executado. O original definitivo foi posteriormente integrado e testado no [Windows CI 43961691647](https://github.com/Gabomgames/Now-assistant/actions/runs/43961691647), com 97 aprovados/um POSIX não aplicável e ZIP de diagnóstico com a marca. A tentativa anterior de disparo manual via gh recebeu Forbidden no GET da API; não foi tratada como execução bem-sucedida. A preparação agora admite também a solicitação explícita por push descrita acima; os resultados mais recentes de Prepare Windows Alpha ficam no início de `VALIDACAO.md`.

Resultados reais, SHA testado e bloqueios finais ficam em `VALIDACAO.md` e `validation/distribution-20261116.json`. Arquivos de fixture não são evidência de um build Windows. Nenhuma publicação é presumida a partir da existência dos workflows.
