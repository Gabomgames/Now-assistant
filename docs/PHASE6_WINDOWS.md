# NOW Assistant — testar Brain na interface, 0.3.0-alpha.2

Este candidato mantém a GUI, logo, cofres e NOW Memory. O cliente padrão usa
`/api/now/v1` por SSE. `/v2` permanece disponível no mesmo processo para rollback.
Ollama/modelos são externos ao ZIP e não são instalados nem baixados pelo app.
Não há publicação de Release, treinamento ou envio automático de relatórios.

## Abrir e escolher modelo sem variáveis de ambiente

1. Baixe o artifact **Prepare Windows Alpha** indicado em `VALIDACAO.md` e extraia
   a pasta inteira do ZIP. Mantenha `_internal` junto de `NOW-Assistant.exe`.
2. Com o Ollama já ativo, abra `NOW-Assistant.exe`, depois **Preferências**.
3. Em **Modelo local**, escolha `qwen2.5:0.5b` ou `qwen2.5:1.5b` se aparecerem.
   **Verificar modelo** consulta o inventário real e filtra entradas cloud/remotas.
   Nenhum modelo é escolhido como vencedor automaticamente. Sem seleção,
   comandos básicos funcionam e perguntas livres pedem a escolha nas Preferências.
4. Selecione Casual, Português brasileiro e Curta/Equilibrada/Detalhada. Aplicar.
   A escolha técnica de modelo/conexão fica em `client.json` no diretório do app;
   nomes, personalidade e outras preferências pessoais continuam sujeitos ao
   fluxo de consentimento e senha existente da NOW Memory.
5. Converse normalmente: o texto aparece progressivamente. Hora/data/ajuda
   continuam identificados como comandos locais. Com modelo selecionado,
   saudações e perguntas livres usam inferência; erros não viram respostas falsas.

Os deltas são recebidos por HTTP assíncrono e a pintura da GUI é limitada a 20
atualizações/s, sem recriar o histórico a cada token. Texto parcial fica na RAM;
só o resultado terminal validado é anexado/salvo conforme o consentimento de
histórico. Cancelar, trocar de conversa, bloquear ou fechar interrompe a conexão
atual e impede inserir texto tardio. Não é garantido que o Ollama devolva CPU/GPU
imediatamente após o fechamento do socket — isso exige medição no serviço real.

O indicador mostra tempo decorrido, tempo até o primeiro texto recebido (TTFT)
e taxa de **caracteres recebidos/s** durante o stream. No fim, mostra tokens/s
somente quando o Ollama fornecer contagem e duração reais. `—` significa sem
medição. Comandos determinísticos não têm taxa de inferência. Streaming melhora
o tempo percebido de leitura; não aumenta por si só a velocidade do modelo.

## Avaliar sem instalar Python

Dê dois cliques em **`Avaliar-Modelos.cmd`**, incluído ao lado do EXE. Ele abre o
utilitário gráfico empacotado no mesmo runtime Python/Qt. Não precisa instalar
Python, SDK, configurar PATH ou credenciais. O utilitário:

- consulta o Ollama local e mostra as tags realmente disponíveis;
- permite selecionar os modelos para comparação; 0.5B e 1.5B vêm marcados se
  instalados, sem declarar um vencedor;
- executa os mesmos 20 prompts sintéticos por modelo (contexto, PT-BR/EN,
  Minecraft, programação, cotidiano, humor e limites de memória/permissões);
- usa uma única API própria durante toda a avaliação, sem reiniciar o Ollama;
- salva `evaluation.json`, `report.html` e OpenAPI numa pasta nova escolhida por
  você, sem abrir seus cofres ou chats;
- permite parar o worker e sua API, conservando relatório parcial com estado de
  cancelamento; fechar encerra apenas os processos criados pelo utilitário.

Clique **Abrir relatório legível** para comparar respostas lado a lado com
latência/TTFT/tokens/s observados e critérios de revisão. HTML escapa o texto do
modelo e não executa scripts. Não há upload, treinamento, vencedor ou aprovação
automática de qualidade. Licença e digest observados continuam exigindo revisão.
Sem Ollama/modelos, você pode gerar um diagnóstico: os casos ficam NOT_RUN.
Parar uma avaliação não autoriza considerar os casos restantes executados.

A avaliação pode levar vários minutos no Athlon 3000G/8 GB. O prazo por geração
no utilitário é 300 segundos. O app usa o Ollama já instalado, não faz `pull`,
não inicia/reinicia seu serviço e não descarrega pesos entre os prompts. Modelos
podem ter cold start e usar recursos diferentes; compare os mesmos casos, sem
tratar o primeiro token como velocidade total de inferência. CPU/RAM/FPS do
hardware alvo não são medidos por este utilitário.

## Rollback

Nas Preferências, **Conexão → Legado /v2**, ou abra **`Modo-Legado.cmd`**. Isso
mantém os cofres e usa a API anterior, sem reiniciar a Engine. O modelo selecionado
na interface v1 não é aplicado ao adaptador legado; ele mantém sua configuração
anterior. O legado não fornece SSE nem garante parada do cálculo ao cancelar.
Para voltar, escolha NOW Brain v1 e seu modelo nas Preferências. `client.json`
contém só escolhas técnicas; apagar esse arquivo com o app fechado restaura v1
sem seleção e não altera histórico ou NOW Memory.

## Escopo da evidência

Os testes de GUI usam widgets, HTTP e sockets reais contra uma fixture explícita
do protocolo Ollama; não aprovam inteligência. O build Windows abre a GUI nativa,
verifica logo/ícone e comandos offline pela v1. Também abre o utilitário empacotado
com uma tag deliberadamente não instalada para provar recursos/imports/worker e
tratamento de indisponibilidade; esse self-check não é avaliação de Qwen.

Na nuvem, o registro Ollama continua CONNECT 403 e não há pesos. As 20 respostas
por modelo, naturalidade Casual e desempenho no Windows 10/Athlon ainda dependem
da execução local. As instruções de personalidade foram enxugadas e localizadas,
com honestidade sobre contexto/memória e sem respostas de jogos pré-fabricadas;
a melhoria linguística não é declarada antes de revisar gerações reais.

Este é candidato de testes, não versão comercial aprovada: sem Authenticode,
com validação de hardware/DPI/acessibilidade pendente. Nenhuma mudança no SG ou
serviço público foi feita. Os resultados observados estão em `VALIDACAO.md`.
