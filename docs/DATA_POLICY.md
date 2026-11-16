# Política inicial de dados — NOW AI

- Somente exemplos autorais ou com licença comprovada e registro de procedência. Os 36 exemplos do pacote foram escritos especificamente para este protótipo.
- Não usar saídas da API OpenAI ou Gemini como corpus de treinamento para modelo concorrente sem autorização expressa aplicável; conferir termos atualizados.
- Não usar conversas privadas de usuários, áudios, arquivos, nomes, e-mails ou dados pessoais sem base legal, permissões e controles apropriados.
- Separar treino de avaliação: nunca incluir `eval_cases.jsonl` no fine-tuning.
- Limpar, revisar e versionar o dataset; documentar licença, origem, idioma, problemas e mudanças.
- Criar política de exclusão, direitos do usuário e salvaguardas adequadas a idade antes de coletar dados reais.
- Manter relatórios de avaliação sem dados sensíveis, evitar expor prompts privados em logs.
- Não treinar com o dataset piloto de 36 exemplos: é uma amostra para testar o pipeline, não um corpus suficiente.
- O treino não ensina o modelo a executar ações diretamente: ações devem ser implementadas e confirmadas pelo software sob permissões explícitas.
