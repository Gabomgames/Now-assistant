# NOW Assistant

Assistente pessoal de uso geral, com especialidade gamer. A primeira interface desktop está integrada à NOW Engine existente: chat por texto, comandos locais em português/inglês, sessões temporárias e histórico opcional criptografado. O terminal, a API 0.2, a preparação de treinamento, o NOW Memory e os contratos do NOW Voice continuam no projeto.

## Direção — plataforma NOW Brain independente

API, dataset com direitos verificáveis, Training Lab supervisionado e memória
autorizada sob controle da NOW. [Arquitetura proposta, hardware, custos e gates
de aprovação](docs/NOW_BRAIN_PLATFORM_ARCHITECTURE.md). Ollama permanece uma
integração de compatibilidade; llama.cpp direto e vLLM em servidor próprio são
próximos adaptadores propostos, ainda não implementados/testados. A inferência
atual continua acoplada ao Ollama. Nenhum treino, provisionamento ou deploy foi
executado nesta revisão. Armazenar conversas/preferências não altera pesos.

## Fase 6 — Brain na interface Windows

Cliente desktop por SSE, seleção de modelo nas Preferências, indicadores e
rollback `/v2`. O candidato `0.3.0-alpha.2` inclui `Avaliar-Modelos.cmd`, sem
instalar Python manualmente. [Como usar e avaliar](docs/PHASE6_WINDOWS.md).
Resultados e link do build em [VALIDACAO.md](VALIDACAO.md). Qualidade Qwen e
Windows 10/Athlon continuam exigindo avaliação real; não há Release publicada.

## NOW Brain API — desenvolvimento V5

API local própria em `/api/now/v1`, com inventário, chat, SSE e cancelamento.
A GUI usa v1 por padrão e mantém rollback compatível para `/v2`. [Instalação, contrato e validação real no Windows](docs/NOW_BRAIN_API_V1.md).
A avaliação de inferência neste ambiente de desenvolvimento continua bloqueada;
a API não foi aprovada como serviço público ou multiusuário.

## Baixar para Windows — Fase 6

Candidato **0.3.0-alpha.2** disponível no [build Alpha 44186126526](https://github.com/Gabomgames/Now-assistant/actions/runs/44186126526#artifacts),
artifact de **51,1 MB** com fonte `dec9540`. Baixe o artifact, extraia-o e depois
extraia todo o ZIP `NOW-Assistant-0.3.0-alpha.2-Windows-x64.zip` em uma pasta nova.
Abra `NOW-Assistant.exe`, mantendo `_internal`. Não precisa instalar Python.

Em **Preferências**, selecione o modelo local instalado. `Avaliar-Modelos.cmd`
compara os modelos com 20 casos por tag e salva relatório local. **Nenhuma GitHub
Release foi publicada.** Qualidade Qwen e desempenho no Windows 10/Athlon ainda
precisam da avaliação local. [Guia](docs/PHASE6_WINDOWS.md) e [evidências/hashes](VALIDACAO.md).

### Candidato anterior — 0.3.0-alpha.1

A versão **`0.3.0-alpha.1`** está disponível para revisão nos [Artifacts do build Windows 43969485511](https://github.com/Gabomgames/Now-assistant/actions/runs/43969485511#artifacts), aproximadamente 51 MB. Windows Server 2022/Python 3.12: 101 testes aprovados, um POSIX não aplicável, EXE/GUI/Engine e seis comandos offline reais aprovados. A logo oficial preserva bytes, cores, proporções e fundo preto. [Resultados, hashes e limitações](VALIDACAO.md). **Nenhuma GitHub Release foi publicada.** O download de artifacts pode exigir login no GitHub e tem retenção de 30 dias.

Baixe o artifact `now-assistant-windows-0.3.0-alpha.1-cb5204041907139a8fb862e7ff6a557dec53df24-attempt-1`, extraia-o e depois extraia toda a pasta de `NOW-Assistant-0.3.0-alpha.1-Windows-x64.zip`. Abra `NOW-Assistant.exe` mantendo `_internal`. Não precisa instalar Python nem VS Code.

Quando uma versão for aprovada, o ZIP ficará em [GitHub Releases](https://github.com/Gabomgames/Now-assistant/releases): extrair a pasta inteira e abrir `NOW-Assistant.exe`, **sem instalar Python ou VS Code**. Python/Qt acompanham a pasta; Ollama/pesos Qwen são separados. [Instalação e requisitos para usuários](packaging/releases/INSTALL-WINDOWS.md).

## Executar a interface no VS Code / Windows

Use Python **3.12 x64** e PowerShell na raiz do repositório:

```powershell
py -3.12 -m venv .venv-desktop
.\.venv-desktop\Scripts\python.exe -m pip install pip==26.3
.\.venv-desktop\Scripts\python.exe -m pip install -r requirements-desktop.txt
$env:ENABLE_GEMINI_FALLBACK = 'false'
.\.venv-desktop\Scripts\python.exe -m now_desktop
```

A janela inicia sua própria API autenticada em loopback. Sem Ollama, experimente `oi`, `horas`, `data` e `ajuda`; em Preferências, escolha English para usar `hello`, `time`, `date` e `help`. Esses são comandos determinísticos, não respostas geradas por Qwen. A interface e seu ambiente mínimo não precisam do SDK ou de chave Gemini.

Guia completo: [Windows e VS Code](docs/DESKTOP_WINDOWS.md). Decisão de tecnologia e segurança: [arquitetura desktop](docs/DESKTOP_ARCHITECTURE.md). [Especificação V3](docs/specs/NOW_ASSISTANT_V3.txt).

## Privacidade e histórico

A abertura padrão é temporária, sem criar bancos. “Ativar histórico” exige consentimento e senha; inicia novas conversas persistentes, sem converter chats temporários anteriores. Buscar, retomar, renomear, exportar, excluir, bloquear e configurar retenção estão implementados. Exportações são JSON em texto aberto, com confirmação, e nunca sobrescrevem arquivos existentes.

Preferências são um cofre separado no NOW Memory: idioma, personalidade, humor, extensão e nome. Aplicar configurações vale somente para a sessão; guardar/carregar exige ação e senha explícitas. Microfone, tela, execução de programas e processamento remoto não são autorizados por essas preferências.

## Modelo local — caminho compatível atual

O candidato Windows atual usa Ollama. Ele não é requisito definitivo da
arquitetura futura. Se já possui modelos instalados, escolha-os em
**Preferências** sem configurar variáveis de ambiente. Para instalar um modelo
nesse caminho compatível, use o Ollama de
[sua página oficial](https://ollama.com/download), inicie-o localmente e execute:

```powershell
ollama pull qwen2.5:0.5b
ollama list
```

Selecione o modelo nas Preferências. Perguntas livres chegam à NOW Brain API,
que hoje usa `/api/chat` do Ollama local com contexto limitado da conversa.
Essa integração tem código e tratamento de indisponibilidade; inferência real
dos Qwen continua pendente nesta nuvem, sem pesos disponíveis. Não há fallback
comercial na interface nova. [Avaliação de 20 casos no Windows](docs/PHASE6_WINDOWS.md).

## Validação e limites desta entrega

Distribuição pelo GitHub: [pipeline Windows, candidatos e aprovação manual](docs/GITHUB_DISTRIBUTION.md).
O candidato atual é `0.3.0-alpha.2`, fonte `dec9540`, run Alpha `44186126526`.
CI e preparo de candidato não publicam Releases. Python/Qt acompanham o pacote;
o runtime de inferência e os pesos continuam separados.

GUI, API autenticada e armazenamento foram executados em **Linux com Qt offscreen**
e **Windows Server 2022 no GitHub Actions**. A Fase 6 registrou 139 casos:
139 aprovados em Linux; 138 aprovados e um POSIX não aplicável em Windows.
EXE, logo, GUI/Engine v1 e avaliador empacotado passaram. Fixtures de protocolo e
utilitário sem modelo não são inferência. [VALIDACAO.md](VALIDACAO.md) contém
resultados, hashes e limitações. A revisão de arquitetura posterior executou
somente os 19 testes do pipeline de dados e dry-run, sem treino. Para repetir
toda a suíte, incluindo os testes de preparação de treinamento:

```powershell
.\.venv-desktop\Scripts\python.exe -m unittest discover -v
```

O PNG original recebido em ZIP está intacto em [assets/branding/original.png](assets/branding/original.png), com SHA-256 no [manifest](assets/branding/manifest.json) e comprovante em [PROVENANCE.json](assets/branding/PROVENANCE.json). A interface usa a imagem oficial; o ícone da janela e do EXE usa ICO com oito resoluções. A marca não foi redesenhada, recortada ou convertida em vetor.

O [build Windows GUI](tools/build_desktop_windows.py) exige Windows real e logo
oficial. O candidato Alpha acima foi gerado/testado com essa identidade, sem
assinatura Authenticode. Windows 10/hardware alvo e qualidade de inferência
continuam pendentes; APK não foi construído. Microfone, STT/TTS audíveis, wake
word, bandeja, inicialização automática, visão, sincronização e hospedagem são
fases futuras; a independência e a qualidade da NOW Brain têm prioridade.

## Compatibilidade e continuação

Os comandos `python main.py` e `python -m uvicorn now_engine.api:app --host 127.0.0.1 --port 8000` mantêm a interface legada 0.2 e seus nomes públicos. Essa API antiga não tem autenticação; mantenha-a em loopback e não exponha portas. A GUI usa uma API separada autenticada, sem rotas de dados privados. O SDK Gemini permanece opcional no legado via `requirements.txt`.

Consulte [o guia legado](docs/WINDOWS_VSCODE.md), [NOW Memory](docs/NOW_MEMORY.md), [NOW Voice Engine](docs/NOW_VOICE_ENGINE.md), [treinamento](training/README.md) e [a próxima tarefa](docs/NEXT_TASK.md). Nenhum modelo foi treinado nesta entrega.
