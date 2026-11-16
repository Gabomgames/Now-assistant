# NOW Assistant — incremento desktop V3

## Decisão: PySide6 para o primeiro desktop

A especificação permite outra tecnologia mediante justificativa. PySide6 reutiliza o Python 3.12 existente, entrega widgets nativos e acessíveis por teclado, HTTP assíncrono, distribuição Windows com PyInstaller e execução/testes reais nesta máquina. Isso evita acrescentar uma toolchain Flutter/Dart e um segundo empacotador antes de validar o produto desktop. Qt 6.8.3 possui wheel oficial Windows x64 e declara suporte à geração Windows 10; compatibilidade real no hardware alvo ainda está pendente. Não é uma promessa de suporte irrestrito a todo Windows 10.

Android continua uma aplicação futura, possivelmente Flutter, consumindo contratos versionados. O Python/Qt desktop não é apresentado como APK nem como um backend móvel pronto. Essa escolha não remove os componentes existentes.

## Camadas executáveis

`now_desktop.window` exibe estado e usa `EngineClient` → HTTP autenticado `/v2` → `now_engine.desktop_api` → `LocalAssistant` → comandos locais ou Ollama. Widgets não importam implementações de modelo. `controller` contém o estado de conversas em RAM. `StorageService` mantém SQLite e scrypt em um único worker fora da thread gráfica. `now_history` não conhece Qt; `now_memory.security` compartilha apenas os primitivos criptográficos.

O launcher cria um processo próprio de Engine, token aleatório e identificador de instância por abertura. Porta efêmera, bind exclusivo em `127.0.0.1`, credencial em variável de ambiente do filho, nunca em argv/arquivo. A janela confirma o identificador via health antes de habilitar envio. Ao sair, encerra somente seu processo filho. Uma pequena corrida entre selecionar a porta e vinculá-la pode causar falha de startup; a autenticação/identidade impede aceitar outro serviço como a Engine correta. Não há serviço externo público.

`/v2/health`, `/v2/capabilities` e `/v2/chat` exigem Bearer. Origem de navegador é recusada, Host é restrito, corpo limitado a 64 KiB, texto a 4.000 caracteres e taxa a 60 requisições/minuto por processo. Uma geração por vez. Sem docs públicas, CORS permissivo ou endpoints de senha/cofre. A API legada `/v1` permanece compatível e separada, sem a segurança nova; não a expor.

O contexto envia apenas falas user/assistant da conversa selecionada, excluindo tentativas falhas/canceladas, com até 12 mensagens e orçamento de 6.000 caracteres. O sistema e suas instruções não são aceitos como papéis enviados pelo cliente. Nome de exibição é dado serializado, não comando. Nenhuma saída de modelo pode executar shell, abrir programas, captar microfone/tela ou conceder permissões. Resistência linguística do Qwen a prompt injection e qualidade de personalidade ainda exigem avaliação do modelo real.

O adaptador usa apenas Ollama em loopback, exige tag instalada e recusa tags/metadata remotas. Verificar presença não significa ter aprovado a qualidade da inferência. A GUI informa erro 503 quando o modelo falta; não acrescenta resposta de assistente nesse caso. Não depende de Gemini, OpenAI ou outro provedor comercial.

Cancelar aborta a requisição da janela e impede inserir sua resposta tardia. Uma geração já iniciada no Ollama pode continuar até concluir/timeout; este incremento não implementa interrupção garantida do cálculo remoto ao processo. Timeout do cliente 95 s; pré-verificação do modelo 5 s e geração até 90 s. Fechar encerra a Engine própria. Streaming está planejado.

## Dados e consentimento

- **Sessão temporária:** RAM, sem SQLite e sem conversão retroativa ao ativar histórico. Clipboard/exportação só por ação do usuário; clipboard é recurso do sistema e pode ser observado por outros aplicativos.
- **Histórico:** `%LOCALAPPDATA%\NOWAssistant\history\history.sqlite3`, senha independente e consentimento para novas conversas. Persistência entre aberturas; sempre bloqueado ao abrir. Listar/buscar requer desbloqueio. Exportar é JSON claro, confirmado, arquivo novo. Bloquear remove cópias persistentes e temporárias derivadas delas do estado da janela.
- **Preferências:** `%LOCALAPPDATA%\NOWAssistant\preferences\preferences.sqlite3`, NOW Memory separado. Carregar por senha é explícito; nada é aplicado entre sessões sem essa ação. Editar em Preferências e guardar permite corrigir os cinco campos; limpar o nome remove o campo salvo. Desativar/apagar restauram defaults da sessão.
- **Retenção:** padrão 30 dias desde a última atividade autenticada da conversa; `0` desliga a exclusão automática. Aplicada ao desbloquear, mudar prazo, salvar e em manutenção a cada hora enquanto desbloqueado e ocioso. Não existe serviço de limpeza de cofre bloqueado ou app fechado. Até 200 conversas persistentes, 200 mensagens e 200.000 caracteres por conversa; inicie outra conversa ao atingir o limite.

AES-256-GCM com nonce aleatório e autenticação por identificador; scrypt N=131072, r=8, p=1 e salt aleatório de 16 bytes. Senha com ao menos 12 caracteres não vazios e até 1.024 bytes UTF-8. A chave não fica ao lado do banco. Títulos, mensagens, preferências e consentimento são cifrados; formato, salt, IDs e quantidade de registros ficam visíveis. O formato Memory v1 permanece legível; um teste monta independentemente um banco com o formato anterior. Histórico tem formato próprio v1, sem migração destrutiva automática.

POSIX usa 0700/0600; no Windows o arquivo fica no perfil local e herda suas ACLs. Não há integração DPAPI/Credential Manager nem ACLs Windows verificadas. Encryption em repouso não protege contra senha fraca, sessão desbloqueada, administrador/malware, swap/crash dump ou backup externo. Python não garante zeragem de strings/chaves na RAM. Apagar registros não assegura apagamento físico em SSD e não apaga exportações/backups. Sem recuperação de senha. Não publicar cofres, senhas ou exports no Git.

## Segurança de dependências e distribuição

`requirements-desktop.txt` fixa as dependências diretas e usa os constraints Python 3.12 existentes; PySide6-Essentials fixa shiboken6 na mesma versão. O ambiente mínimo foi instalado do PyPI sem SDK Gemini. O pip fornecido no venv tinha alertas e foi atualizado para 26.3; o resultado atual da consulta de metadados PyPI está em `validation/desktop-dependencies-20261116.json`. Isso não é auditoria completa de Qt/OpenSSL/bibliotecas nativas nem garantia de ausência de vulnerabilidades. Não houve revisão independente de segurança.

PySide6/shiboken6 têm opções LGPL-3.0/GPL/comercial. FastAPI é MIT; uvicorn BSD-3-Clause; cryptography Apache-2.0 ou BSD-3-Clause; demais declarações estão no relatório. O build é `onedir`, com bibliotecas dinâmicas e metadata, sem UPX, para permitir inspeção/substituição de bibliotecas. Antes de redistribuir, coletar/revisar textos de licença, fontes/referências e avisos de terceiros de **cada** DLL/plugin Qt e demais componentes incluídos; metadata PyPI sozinha não cumpre essas obrigações. Nenhum instalador assinado ou licença comercial foi obtido nesta etapa.

## Próximas fases com critérios reais

1. Receber arquivo binário da logo, importar sem alterar original, revisar ícones; executar build e validação de GUI/cofre no Windows 10 x64 real, com teclado, escalas DPI e permissões do perfil. Medir CPU/RAM/FPS no hardware alvo.
2. Voz push-to-talk: adaptadores reais STT/TTS licenciados, permissões de dispositivos e reprodução audível PT-BR/EN. Só aprovar após microfone/alto-falantes reais, cancelamento e medidas de qualidade/latência. O contrato existente é reutilizado, sem botão de microfone de fachada.
3. Wake word local “Now”, bandeja, mute e inicialização opt-in; validar eco, falsos positivos, consumo em repouso/jogos e revogação.
4. Rede aplicada liberada: baixar Qwen legitimamente, executar oito gerações reais nas integrações existentes e contexto da GUI; avaliar português, inglês, segurança, limites e personalidade. ModelProvider/streaming/NOW Cloud seguem extensíveis, sem exigir API paga.
5. Visão/ferramentas sob permissão; Android/sincronização autenticada opt-in; LoRA somente com dados licenciados, GPU e avaliação independente. Não estão implementados nesta GUI.
