# NOW Training Lab — preparação experimental

A direção atual é independente de Ollama. A
[arquitetura proposta](../docs/NOW_BRAIN_PLATFORM_ARCHITECTURE.md) apresenta
hardware, custos estimados e aprovações antes de qualquer treino. Este diretório
é a base experimental, não um laboratório GPU validado. O avaliador Ollama abaixo
é compatibilidade existente; futuros backends não devem depender dele.

Este módulo é aditivo à NOW AI 0.2. Os nove arquivos originais da aplicação e os quatro testes recebidos no kit foram preservados. Os scripts do kit foram adaptados para validar separação de dados, proteger relatórios e bloquear treinamento prematuro. Não há pesos treinados ou modelo baixado neste módulo.

## O que funciona sem Ollama, GPU ou bibliotecas de ML

Na raiz do projeto, com Python 3.12:

~~~powershell
python training/scripts/validate_dataset.py
python -m unittest discover -s training/tests -v
python training/scripts/train_lora_gpu.py --dry-run
python training/scripts/run_ollama_eval.py --dry-run
~~~

Os comandos usam somente a biblioteca padrão. O dry-run do treino valida os dados e registra bloqueios; ele não importa PyTorch, não inicia treino e não baixa modelos. O dry-run da avaliação valida os 12 casos, mas registra zero gerações e qualidade NOT_SCORED.

Para executar também as regressões reais da API/terminal, use o ambiente da aplicação:

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -v
~~~

As regressões de API/terminal iniciam processos com conexões de saída negadas e Gemini desligado. Testam comandos offline e indisponibilidade real do provedor. Os testes unitários originais com mocks continuam separados de qualquer alegação de inferência.

## Dados e procedência

- data/now_seed.jsonl: 36 exemplos piloto, preservados byte a byte.
- data/eval_cases.jsonl: 12 casos independentes, preservados; nunca usar como dados de treino.
- data/PROVENANCE.json: checksum do ZIP e dos dados. A autoria sintética é uma declaração do material recebido, não uma autoria independentemente comprovada.
- A licença e a aprovação de treino permanecem pendentes. A integração do kit não concede direitos novos nem certifica o conteúdo.
- Consulte ../docs/DATA_POLICY.md. O validador verifica formato, duplicatas e sobreposição de prompts; não substitui revisão humana nem detecta toda paráfrase ou dado pessoal.

O corpus piloto não deve ser usado para fine-tuning. O script recusa execução real com menos de 100 exemplos; esse mínimo herdado do protótipo não garante qualidade. Antes de treinar, expandir o corpus revisado, reservar validação separada no mesmo formato prompt/completion, manter testes independentes e atualizar a procedência vinculada ao SHA-256 do novo arquivo.

## Persona de avaliação e modelos

prompts/now-casual-v1.txt define uma persona geral Casual, com PT-BR/EN, limites explícitos de memória, voz e ferramentas. É um perfil de avaliação experimental; a persona de produção da NOW Engine original não foi alterada. Escrever uma instrução não comprova que o modelo a segue.

config/models.json registra Qwen2.5-0.5B-Instruct como baseline e Qwen3-0.6B como candidato futuro. Não troca o modelo de produção automaticamente. As documentações oficiais declaram licenças abertas Apache 2.0; a licença da revisão exata do artefato ainda deve ser conferida antes de usar os pesos.

config/evaluation.json fixa persona, parâmetros e idiomas esperados. O caso en-langswitch pede explicitamente português; esse resultado esperado foi anotado na configuração sem alterar o dataset original.

## Avaliação com geração real, quando o modelo estiver disponível

Somente depois de instalar um modelo local em ambiente com rede autorizada:

~~~powershell
python training/scripts/run_ollama_eval.py --model qwen2.5:0.5b
~~~

O comando consulta somente o Ollama local, sem Gemini/OpenAI. Confere inventário antes de gerar, recusa entradas cloud/remotas, salva cada resposta efetivamente recebida e mantém metadados de progresso/erro. Arquivos existentes não são sobrescritos. As saídas ficam em training/reports/, ignorado pelo Git, com um .meta.json ao lado.

- COMPLETED_UNSCORED significa gerações concluídas, com revisão humana ainda necessária.
- BLOCKED significa preflight impedido; não há respostas geradas.
- PARTIAL/FAILED distingue respostas obtidas de falhas e casos não executados.
- Todas as respostas começam como NOT_SCORED. Avaliar idioma, utilidade, tom, honestidade, privacidade, memória e alegações de execução; registrar PASS/FAIL e notas separadas para cada caso.

Para A/B, repetir explicitamente com o candidato local, usando os mesmos casos, persona, opções e hardware. Comparar os hashes da configuração antes de comparar qualidade. Não combinar os resultados com os oito checks de tools/validate_local.py: esses verificam outros caminhos do aplicativo e usam o prompt original da Engine.

Não foi executada geração real deste avaliador nesta entrega. A persistência de respostas reais, qualidade, latência e comportamento de cada modelo ainda precisam ser exercitados com o modelo instalado.

## Fine-tuning GPU futuro — experimental, não executado

Usar ambiente GPU dedicado e autorizado. Não instalar as dependências pesadas no ambiente comum apenas para validar dados. A seleção da distribuição CUDA e das versões compatíveis precisa ser verificada nesse executor.

~~~powershell
py -3.12 -m venv training\.venv
.\training\.venv\Scripts\python.exe -m pip install -r training\requirements-train.txt
~~~

Antes de qualquer execução real:

1. Obter aprovação humana para o experimento exato: modelo/revisão, hashes dos
   datasets, configuração/código, hardware, horas e teto de custo. A aprovação
   de procedência sozinha não autoriza treino. O script atual ainda não aplica
   esse gate por execução; não iniciar treino antes de implementá-lo e revisá-lo.
2. Concluir revisão de dados, licença e permissão; registrar license, rights_basis, reviewed_by, reviewed_at e approved_for_training no manifesto correspondente ao checksum exato.
3. Preparar treino e validação sem sobreposição, preservando os 12 casos de teste independentes.
4. Fazer avaliação baseline real e revisão manual; conferir licença dos pesos e capacidade da GPU.
5. Verificar a API das versões instaladas de Transformers/TRL/PEFT e registrar um lockfile daquele ambiente. Os ranges do kit são experimentais e não foram instalados/testados em GPU.
6. Escolher uma pasta de saída nova e testar --dry-run com os caminhos reais.

O script aceita --dataset, --validation-dataset, --provenance e --output. O padrão local_files_only evita download implícito de pesos. --allow-model-download só deve ser usado quando o download normal estiver permitido pela política de rede; essa opção não contorna restrições.

Treino bem-sucedido salvaria um adaptador LoRA, tokenizer e plano de execução.
Ainda seriam necessários avaliação independente, comparação com baseline,
aprovação separada de promoção/implantação, export compatível e validação no
runtime de destino e na NOW Brain API. Ollama não é destino obrigatório. Nada
disso foi executado nesta entrega; QLoRA e gates comerciais não estão implementados.

Memória persistente, voz e controle de ferramentas são implementações de software separadas; fine-tuning não as cria. Próximas fases: ../docs/MODEL_ROADMAP.md. Retomada no ambiente: ../docs/NEXT_TASK.md.
