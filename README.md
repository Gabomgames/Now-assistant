# NOW Assistant

Assistente pessoal de uso geral, com especialidade gamer. A primeira interface desktop está integrada à NOW Engine existente: chat por texto, comandos locais em português/inglês, sessões temporárias e histórico opcional criptografado. O terminal, a API 0.2, a preparação de treinamento, o NOW Memory e os contratos do NOW Voice continuam no projeto.

## Baixar para Windows

A primeira Alpha oficial ainda aguarda o arquivo original da logo e autorização de publicação. O [artefato Windows de diagnóstico](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793#artifacts) foi construído/testado no GitHub Actions e está disponível para revisão; é identificado como não publicável. O download de artifacts pode exigir login no GitHub.

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

## Modelo local

Instale o Ollama de [sua página oficial](https://ollama.com/download), inicie-o localmente e execute:

```powershell
ollama pull qwen2.5:0.5b
ollama list
$env:OLLAMA_MODEL = 'qwen2.5:0.5b'
```

Reabra a NOW Assistant após configurar o ambiente. Perguntas livres usam `/api/chat` do Ollama local com contexto limitado da conversa. Essa integração tem código e tratamento real de indisponibilidade; **as oito gerações Qwen ainda não foram executadas**, pois `registry.ollama.ai` continua bloqueado nesta máquina. Não há fallback comercial na interface nova.

## Validação e limites desta entrega

Distribuição pelo GitHub: [pipeline Windows, candidatos e aprovação manual](docs/GITHUB_DISTRIBUTION.md). Versão preparada `0.3.0-alpha.1`; CI e preparo de candidato não publicam Releases. O [run Windows de diagnóstico](https://github.com/Gabomgames/Now-assistant/actions/runs/43950853793) passou com EXE, Engine, seis comandos offline e ZIP verificado. A Alpha oficial continua bloqueada pela ausência do arquivo original da logo. Nenhuma Release foi publicada. Python/Qt acompanham o pacote; Ollama/modelos são instalações separadas.

GUI, API autenticada e armazenamento foram executados em **Linux com Qt offscreen** e **Windows Server 2022 no GitHub Actions**. A suíte atual tem 95 casos: 95 aprovados em Linux; 94 aprovados e um teste POSIX não aplicável em Windows. O smoke do EXE usa comandos determinísticos reais, sem Gemini ou inferência simulada. [VALIDACAO.md](VALIDACAO.md) contém escopo dos fixtures/doubles e evidências. Para repetir toda a suíte, incluindo treinamento:

```powershell
.\.venv-desktop\Scripts\python.exe -m unittest discover -v
```

A imagem oficial foi visível na conversa, mas seu arquivo não ficou acessível ao ambiente. [O manifest](assets/branding/manifest.json) registra a pendência; não foi criada outra logo. Há importação fiel de raster e geração de ícones pronta para receber o original. A interface usa nome e paleta até esse arquivo chegar.

O [build Windows GUI](tools/build_desktop_windows.py) exige Windows real e logo oficial para gerar um candidato publicável. O CI gerou/testou um **EXE de diagnóstico não publicável**, sem logo substituta. Windows 10/hardware alvo e a Alpha com identidade oficial ainda precisam de validação; APK não foi construído. Microfone, STT/TTS audíveis, wake word, bandeja, inicialização automática, visão, sincronização e NOW Cloud são próximas fases.

## Compatibilidade e continuação

Os comandos `python main.py` e `python -m uvicorn now_engine.api:app --host 127.0.0.1 --port 8000` mantêm a interface legada 0.2 e seus nomes públicos. Essa API antiga não tem autenticação; mantenha-a em loopback e não exponha portas. A GUI usa uma API separada autenticada, sem rotas de dados privados. O SDK Gemini permanece opcional no legado via `requirements.txt`.

Consulte [o guia legado](docs/WINDOWS_VSCODE.md), [NOW Memory](docs/NOW_MEMORY.md), [NOW Voice Engine](docs/NOW_VOICE_ENGINE.md), [treinamento](training/README.md) e [a próxima tarefa](docs/NEXT_TASK.md). Nenhum modelo foi treinado nesta entrega.
