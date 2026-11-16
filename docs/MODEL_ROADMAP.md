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

## Memória — fase ainda não implementada

Implementar SQLite separado do modelo, com preferências explícitas, consentimento, retenção e isolamento por usuário. Entregar visualizar, editar, exportar e excluir antes de habilitar persistência. Testar exclusão e modo sem memória. A linguagem do modelo nunca deve afirmar que algo foi salvo sem confirmação do armazenamento.

## Voz — fase ainda não implementada

Começar com push-to-talk, indicador de microfone, permissões revogáveis e transcrição/síntese local. Escolher STT/TTS após conferir licenças e desempenho real em pt-BR/EN. Validar primeiro em hardware Windows; Android tem requisitos próprios. Wake word, conversa contínua e expressividade dependem de medições e testes posteriores.

## Windows

O launcher e o build PyInstaller estão preparados em `packaging/windows` e `tools/build_windows.py`. A geração/teste de `.exe` ainda exige Windows x64. O guia é `WINDOWS_VSCODE.md`; nenhum executável é considerado concluído nesta entrega Linux.
