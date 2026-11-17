# Política de dados — NOW Dataset e NOW Brain

- Somente exemplos autorais verificáveis ou com licença comprovada e registro de procedência. Conteúdo público não é automaticamente licenciado para treinamento ou uso comercial.
- Os 36 exemplos do pacote são um piloto recebido. A autoria sintética é uma declaração do material, ainda não verificada; licença e base de direitos continuam ausentes em `training/data/PROVENANCE.json`. Não apresentá-los como corpus autoral aprovado nem alterar sua aprovação por suposição.
- Saídas de GPT/OpenAI ou Gemini não entram no treino por padrão. Qualquer exceção exige autorização expressa dos titulares/provedores aplicáveis e do projeto, com termos e licença compatíveis com a finalidade. Permissão para usar uma API não concede automaticamente direito de treinar modelos concorrentes.
- Não usar conversas privadas de usuários, áudios, arquivos, nomes, e-mails ou dados pessoais sem base legal, permissões e controles apropriados.
- Consentimento para histórico e NOW Memory não autoriza contribuição ao dataset. Não coletar chats automaticamente para treinamento. Armazenar uma preferência ou recuperar uma conversa não demonstra aprendizado dos pesos.
- Separar treino, validação e teste por conversa/origem; revisar duplicatas e sobreposição semântica. Nunca incluir `eval_cases.jsonl`, os 20 casos de `validation/brain-v5-cases.json` ou seus relatórios de avaliação no fine-tuning.
- Limpar, revisar e versionar o dataset; documentar licença/versão, origem, autoria, direitos de uso/redistribuição, revisão de privacidade, idioma, hashes, problemas e mudanças.
- Criar política de exclusão, direitos do usuário e salvaguardas adequadas a idade antes de coletar dados reais.
- Manter relatórios de avaliação sem dados sensíveis, evitar expor prompts privados em logs.
- Não treinar com o dataset piloto de 36 exemplos: é uma amostra para testar o pipeline, não um corpus suficiente.
- Aprovação de dados não autoriza uma execução de treino nem a promoção/implantação de pesos. Exigir aprovações separadas vinculadas aos artefatos, configuração e orçamento exatos; esses controles por execução ainda precisam ser implementados no laboratório experimental.
- O treino não ensina o modelo a executar ações diretamente: ações devem ser implementadas e confirmadas pelo software sob permissões explícitas.

Arquitetura, separação de memória/treino e gates propostos:
[NOW Brain Platform](NOW_BRAIN_PLATFORM_ARCHITECTURE.md).
