# Evolução incremental da NOW AI

O estado desta entrega está em `../VALIDACAO.md`. Este documento descreve próximos passos, não funcionalidades prontas.

## Estado preservado

A NOW Engine 0.2 continua com terminal, FastAPI e comandos determinísticos. O padrão local é `qwen2.5:0.5b`; Gemini permanece opcional e desligado por padrão. A persona original da aplicação ainda é gamer/pt-BR. O novo perfil Casual geral/PT-BR/EN está preparado no avaliador e ainda não foi avaliado com pesos reais.

## Corpus e avaliação

1. Confirmar autoria/permissões e registrar licença dos exemplos. Os 36 exemplos recebidos são piloto e sua procedência ainda exige revisão.
2. Ampliar o corpus autoral com cotidiano, estudo, programação, humor, jogos e troca de idioma, incluindo respostas honestas sobre funções ausentes. Revisar idade, privacidade, qualidade e regionalismos. Não incorporar conversas privadas ou saídas de provedores fechados sem direitos aplicáveis.
3. Separar treino, validação e teste antes de experimentar; revisar também sobreposição semântica que o detector textual não identifica. Versionar dados e checksums.
4. Avaliar Qwen2.5 e, separadamente, Qwen3-0.6B com a mesma persona e casos. Registrar revisão humana e tempos reais. O candidato não substitui o baseline automaticamente.
5. Só depois testar LoRA em CUDA, com versões travadas no executor e medições de recursos. Comparar o adaptador com baseline e reprovar regressões em honestidade, privacidade e idioma.
6. Exportar o candidato aprovado e validar os oito caminhos reais de `tools/validate_local.py`, além dos 12 casos de avaliação. Integrar por adaptador/configuração versionada, mantendo rollback e sem remover o fluxo existente.

Adaptar pesos Qwen pode produzir um modelo personalizado da NOW, sujeito à licença do modelo-base. Não equivale a treinar um modelo fundacional próprio do zero.

## Memória — preferências implementadas, histórico/sync pendentes

O módulo `now_memory` já oferece SQLite criptografado por senha, preferências explícitas, consentimento, leitura/edição/exportação/exclusão e desabilitação. Foi testado em Linux. A integração opcional com o novo cliente de texto usa snapshots de preferências. O terminal/API legados não foram alterados para coletar dados. Históricos de conversa, memórias inferidas, contas e sincronização continuam pendentes; precisam de retenção e isolamento explícitos. A linguagem do modelo nunca deve afirmar salvamento sem confirmação do armazenamento.

## Voz — controlador/contratos implementados, áudio pendente

`now_voice` já prepara estados, permissões, cancelamento cooperativo, segmentação/pausas e estilo com fallback neutro. Ainda não há adaptadores STT/TTS/microfone/saída ou detector “Now”. O próximo incremento deve entregar push-to-talk real e medir o indicador/encerramento de captura, antes de wake word. Escolher motores após conferir licenças e desempenho pt-BR/EN e validar em hardware Windows; Android exige testes próprios. Qualidade natural/expressiva, conversa contínua e barge-in continuam sem validação.

## Windows

O launcher e o build PyInstaller estão preparados em `packaging/windows` e `tools/build_windows.py`. A geração/teste de `.exe` ainda exige Windows x64. O guia é `WINDOWS_VSCODE.md`; nenhum executável é considerado concluído nesta entrega Linux.
