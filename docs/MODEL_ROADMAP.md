# Evolução da NOW Brain — direção independente

Direção atualizada em 17/11/2026. A [arquitetura proposta](NOW_BRAIN_PLATFORM_ARCHITECTURE.md)
detalha hardware, estimativas de custo, dependências e aprovações. Não constitui
autorização para treinar, implantar ou comprar infraestrutura.

## Base preservada

Windows e NOW Brain v1 já estão integrados, com SSE, seleção explícita de modelo,
indicadores, cancelamento e rollback `/v2`. Logo, cofres separados de histórico
e NOW Memory, testes e pipeline Windows permanecem preservados. O código atual
de inferência ainda é acoplado ao Ollama; não chamar a independência de concluída.
Estado e provas do candidato: [VALIDACAO.md](../VALIDACAO.md).

## Ordem dos incrementos

1. Tornar catálogo, contratos, configuração e adaptadores de inferência neutros.
   Manter compatibilidade com Ollama sem torná-lo requisito definitivo.
2. Validar llama.cpp direto para pesos abertos no Windows e preparar integração
   vLLM em servidor GPU sob controle da NOW. Exigir artefatos com licença e
   integridade verificadas e testes de inferência reais. Comparar os 20 casos
   com os modelos já instalados, medindo qualidade, TTFT, tempo total e memória.
3. Estruturar NOW Dataset com autoria/direitos verificáveis e NOW Training Lab
   com ambientes reproduzíveis, versões, aprovações por execução e orçamento.
   Os 36 exemplos atuais continuam sem licença e sem aprovação para treino.
4. Somente com autorização do experimento exato: piloto supervisionado LoRA/QLoRA,
   comparação baseline/candidato e revisão humana. O script atual de LoRA é
   experimental e não foi validado em GPU. Exportar/promover/implantar requer
   aprovação separada; queda de loss não basta.
5. Após autorização específica de hospedagem: autenticação, isolamento, TLS,
   quotas, fila, métricas e rollback em servidor GPU. Android/Something Gamer
   serão clientes futuros da mesma API, sem alteração desses produtos agora.

## Memória, personalidade e propriedade

Preferências e histórico criptografados não modificam pesos. Ampliar memória
somente com confirmação, edição e exclusão; consentimento para guardar dados
não autoriza treinamento. Medir naturalidade PT-BR/EN e contexto com respostas
reais, sem assumir qualidade por nome/tamanho de modelo ou presença de prompt.

A tecnologia da NOW compreende API, orquestração, dados, memória, avaliação e
ciclo de modelos sob seu controle. Pesos-base continuam sujeitos às respectivas
licenças; fine-tuning não equivale a criar um modelo fundacional do zero.
GPT/Gemini podem ser adaptadores externos futuros autorizados, sem uso de suas
saídas no treino salvo autorização expressa e termos/licenças compatíveis.
Ver [política de dados](DATA_POLICY.md).

Voz/visão, ações, sincronização e módulos de produto futuros não devem desviar
o próximo incremento da independência e da qualidade de inferência. Não publicar
Release, implantar produção ou alterar Something Gamer sem autorização explícita.
