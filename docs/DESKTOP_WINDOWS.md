# NOW Assistant no Windows / VS Code

## O que está disponível

Código executável da interface Qt, chat ligado à Engine local, comandos de texto em português/inglês, histórico criptografado opcional e preferências NOW Memory. Executados e testados em Linux offscreen. **O build e a execução Windows ainda não foram realizados.** Não há áudio real, wake word, bandeja ou APK nesta entrega. A logo oficial aguarda seu arquivo original; nenhum desenho substituto foi criado.

## Instalar e abrir sem alterar o projeto existente

Instale Python **3.12 x64**, VS Code e a extensão Python da Microsoft. Windows 10 x64 é o alvo prioritário, pendente de validação real. Abra a pasta do checkout `Now-assistant`; não recrie, não faça reset/clean e não extraia ZIP por cima de alterações locais. Para continuar a branch existente, confira antes:

```powershell
git status --short
git branch --show-current
git log -1 --oneline
```

Use o checkout `work`; se houver alterações ou outra branch, preserve-as antes de mudar. Terminal do VS Code em PowerShell, na raiz:

```powershell
py -3.12 -m venv .venv-desktop
.\.venv-desktop\Scripts\python.exe -m pip install pip==26.3
.\.venv-desktop\Scripts\python.exe -m pip install -r requirements-desktop.txt
.\.venv-desktop\Scripts\python.exe -m pip check
$env:ENABLE_GEMINI_FALLBACK = 'false'
.\.venv-desktop\Scripts\python.exe -m now_desktop
```

Não é necessário ativar venv, alterar ExecutionPolicy, instalar Google SDK, fornecer chave ou abrir portas. Se existir `.venv-desktop`, reutilize-o sem apagar seu ambiente anterior. **Python: Select Interpreter** deve apontar para `.venv-desktop\Scripts\python.exe`. A GUI inicia/encerra sua própria Engine em porta privada aleatória; não é necessário iniciar uvicorn manualmente. API legada na porta 8000 pode continuar separada.

## Usar hoje

1. Digite `oi`, `horas`, `data` ou `ajuda`. Enter envia; Shift+Enter insere nova linha. A interface indica o provedor real. Sem modelo, perguntas livres mostram indisponibilidade, sem mensagem fictícia de assistente.
2. Preferências → idioma English → Aplicar muda a interface e os comandos: `hello`, `time`, `date`, `help`. Persona/humor/extensão serão enviados ao modelo quando disponível; sua qualidade não foi validada sem Qwen.
3. A abertura é temporária. Para guardar **novas** conversas, Ativar histórico → senha ≥12 caracteres, confirmação, consentimento e prazo (padrão 30 dias). Guarde a senha fora do aplicativo; não há recuperação. Chats temporários anteriores permanecem temporários.
4. Use busca, lista e menu `•••` para retomar, renomear, exportar ou excluir a conversa. Exportação exige confirmação e arquivo novo; contém texto aberto. No botão Histórico protegido: bloquear, deixar de salvar novas conversas, reativar, mudar retenção ou apagar tudo. Prazo conta desde última atividade; a limpeza só opera com cofre desbloqueado.
5. Em Preferências, Aplicar vale para a sessão. Guardar na NOW Memory exige consentimento e senha de um cofre separado. Carregar exige desbloqueio explícito após cada abertura; desativar/apagar remove o uso na sessão. Essas ações não autorizam microfone, tela, ferramentas ou nuvem.
6. Cancelar descarta a resposta da janela; uma geração que já começou pode continuar no Ollama. Fechar encerra a aplicação e sua Engine; não a mantém na bandeja.

Dados ficam por padrão em `%LOCALAPPDATA%\NOWAssistant`, separados em `history` e `preferences`. Não mova bancos/exports para o repositório, OneDrive compartilhado ou pastas públicas. Faça backups privados dos cofres cifrados com o app fechado; mantenha senha separada. A segurança Windows/ACL e o comportamento de backup precisam de validação no seu perfil. Não há sincronização automática.

## Habilitar o modelo local por download autorizado

Instale [Ollama oficial](https://ollama.com/download), abra-o ou use `ollama serve` se não houver instância rodando. Em outro terminal:

```powershell
ollama pull qwen2.5:0.5b
ollama list
$env:OLLAMA_MODEL = 'qwen2.5:0.5b'
$env:ENABLE_GEMINI_FALLBACK = 'false'
.\.venv-desktop\Scripts\python.exe -m now_desktop
```

Espere o download concluir e confirme a tag em `ollama list`. O status da GUI verifica presença do modelo; não é selo de qualidade. Teste perguntas novas em PT-BR/EN e referências à conversa. No ambiente remoto desta tarefa, o pull continuou `Forbidden` no manifesto de `registry.ollama.ai`; não há pesos nem oito gerações reais aprovadas. Em rede corporativa, peça a liberação legítima do host e dos hosts de blobs que o download realmente indicar; não desative TLS, não mude proxies para contornar regras.

## Testar e registrar a execução real

```powershell
.\.venv-desktop\Scripts\python.exe -m unittest discover -v
.\.venv-desktop\Scripts\python.exe -m now_desktop --smoke-output "$env:TEMP\NOW-Assistant-check-01"
```

A pasta de smoke precisa ser **nova**. O smoke abre janela e Engine reais, usa armazenamento temporário, executa seis comandos determinísticos (três por idioma), salva capturas e `REAL-GUI-VALIDACAO.json`. Não testa inferência, áudio ou Windows 10 por si só; registre plataforma e limites. Não execute com dados privados para produzir capturas compartilháveis. Na nuvem Linux, Qt usa `QT_QPA_PLATFORM=offscreen`; isso não prova renderização nativa Windows.

Para o validador legado de oito gerações, após instalar o modelo e iniciar API legada, consulte `python tools/validate_local.py --help` e o guia `WINDOWS_VSCODE.md`. Não conte os seis comandos offline do smoke como gerações Qwen.

## Importar a logo oficial e preparar `.exe`

O anexo visual desta sessão não tinha arquivo acessível. Recebendo o PNG/JPG/WebP original, execute:

```powershell
.\.venv-desktop\Scripts\python.exe tools\import_branding.py 'C:\caminho\logo-oficial.png'
```

Confira `assets\branding\original.*`, SHA no manifest e todos os ícones. O processo apenas escala, acomoda proporcionalmente e preserva o fundo; não desenha, não remove preto e não produz vetor. SVG é recusado até haver renderizador revisado. Os testes usam retângulos artificiais temporários, que não são assets da marca.

Depois de revisar visualmente os derivados, **em Windows x64/Python 3.12 real**:

```powershell
.\.venv-desktop\Scripts\python.exe -m pip install -r packaging\desktop\requirements-build.txt
.\.venv-desktop\Scripts\python.exe tools\build_desktop_windows.py --branding-reviewed --output "$env:TEMP\NOW-Assistant-builds"
```

O script verifica plataforma/logo, executa suíte, gera pasta `NOW-Assistant` com `NOW-Assistant.exe` e dependências dinâmicas, abre a GUI empacotada com Engine real e registra smoke/capturas antes de compactar. Sem a logo ele recusa release; em Linux recusa o build. Uma falha interrompe a entrega, sem aprovar o executável. Copie a pasta inteira para executar; não apenas o EXE. Ollama/modelos são instalados separadamente e não entram no bundle. Nenhum banco do usuário ou `.env` é adicionado.

Antes de distribuir, conferir licenças/avisos de todas as bibliotecas Qt/terceiros, assinatura/instalador, DPI 100/125/150%, teclado/leitor de tela, erros de permissão/disco, abrir/fechar, cofres, reabertura sem Ollama e consumo no Windows 10/8 GB. O build automático não aprova esses itens. Não há instalador assinado nesta entrega. A ferramenta antiga `tools/build_windows.py` continua sendo um build **de terminal legado**, não da GUI.
