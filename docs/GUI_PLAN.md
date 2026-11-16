# Interface NOW Assistant — plano e implementação

## Atualização V3 — 16/11/2026

A primeira GUI executável está em `now_desktop`, com PySide6, API autenticada `/v2`, texto, estado real do modelo, configurações, histórico opt-in criptografado e NOW Memory separado. Foi executada com API/SQLite reais em Linux/Qt offscreen e no Windows Server 2022 do GitHub Actions. O EXE de diagnóstico passou no smoke offline; Alpha oficial, arquivo da logo, Qwen, áudio e hardware Windows 10 permanecem pendentes. A decisão por PySide6 está em [DESKTOP_ARCHITECTURE.md](DESKTOP_ARCHITECTURE.md); execução no VS Code em [DESKTOP_WINDOWS.md](DESKTOP_WINDOWS.md) e distribuição em [GITHUB_DISTRIBUTION.md](GITHUB_DISTRIBUTION.md).

O plano anterior abaixo fica preservado como referência para as fases futuras. Sua preferência por Flutter/ARB não é a implementação atual: o desktop usa traduções Python PT-BR/EN e worker de armazenamento testado. Flutter/Android, permissões móveis, voz real e sincronização ainda não foram construídos.

## Plano anterior preservado

## Estrutura e visual

Preferência por Flutter para compartilhar componentes e traduções. Windows usa navegação lateral e dois painéis em telas largas; Android usa navegação inferior e páginas individuais. Tema escuro/claro sóbrio, contraste AA, fonte escalável, foco visível, navegação por teclado, leitores de tela e animações leves. Especialização gamer não domina a navegação ou todas as conversas.

| Área | Conteúdo | Requisito para habilitar ações |
| --- | --- | --- |
| Conversa | Texto, resposta, fonte offline/local, erro recuperável, cancelar | Chat disponível; não mostrar resposta gerada quando o provedor está indisponível. |
| Voz | Estado do microfone, push-to-talk, saída, idioma, voz e velocidade | Adaptadores e permissões presentes. Hoje captura/fala/wake word aparecem como não disponíveis. |
| Memória | Cofre bloqueado/habilitado, preferências, exportar/excluir/desabilitar | Desbloqueio explícito. Exportação informa que produz texto aberto e pede destino novo. |
| Configurações | Persona, humor, idioma, tamanho da resposta, privacidade | Preferências distinguem estilo de permissão. Nenhuma configuração de estilo autoriza ferramentas ou microfone. |

A faixa de status reflete estados reais: offline, modelo indisponível, escutando, transcrevendo, pensando, sintetizando, falando, desabilitado ou erro. “Now” não recebe botão funcional antes de existir detector validado; usar indicação de recurso planejado. Não exibir “voz natural” ou “modelo treinado” como aprovação automática.

## Limites de arquitetura

- ViewModels traduzem capacidades/estados para a interface; regras de dados e permissões ficam nos serviços testados, não em widgets.
- `VoiceSession` roda em worker, com uma requisição ativa, eventos de estado e cancelamento cooperativo. Nunca bloquear a thread de renderização durante modelo, KDF ou áudio.
- `MemoryStore` é o armazenamento atual; carregar senha por entrada nativa oculta, manter chave só na sessão e limpar snapshots da UI ao bloquear. Conversas não são memorizadas por padrão.
- O adaptador `LocalAssistant` novo é local e geral; a API original fica preservada para compatibilidade. Antes de expor memória/voz por HTTP, criar autenticação, autorização por usuário e contratos versionados. Não reutilizar endpoints legados sem proteção para dados privados.
- No Windows, avaliar IPC por named pipes com controle do usuário ou uma API local autenticada. Não passar senha em argv. Nenhum desses transportes novos está implementado ainda.
- O backend Python atual não é automaticamente um backend Android. Avaliar portas nativas/modelos pequenos locais ou servidor autenticado e opcional por HTTPS. Sincronização exige consentimento separado e política de conflitos/exclusão; não foi implementada.

## Fluxos de privacidade

Primeira abertura mantém memória e microfone desligados. Criar um cofre exige escolha consciente de armazenamento e senha; desabilitar nunca é interpretado como apagar. Preferências de voz podem ser persistidas, mas permissão para captar/reproduzir precisa ser concedida ao runtime e revogada imediatamente pela UI. Captura em andamento só é considerada parada após o driver confirmar; exibir cancelando enquanto necessário.

No Android, microfone requer permissões de plataforma e, quando permitido, foreground service com notificação. Não prometer escuta permanente em background/tela bloqueada. Push-to-talk é o primeiro alvo; wake word, echo cancellation e barge-in são etapas posteriores.

## Idiomas e testes futuros

Todos os textos futuros da UI devem usar recursos ARB versionados em pt-BR/en-US; códigos de erro dos serviços viram mensagens localizadas. Não inferir idade ou idioma com certeza a partir de uma palavra. Aplicar formatação regional e respeitar troca explícita de idioma.

Antes de release: testes de widgets/acessibilidade, contrato dos serviços, memória criptografada, revogação real, falha de dispositivo/rede, teclado/atalhos em jogos, permissões Android e consumo/latência em Windows 10 e hardware alvo. O build nativo, a qualidade vocal e a interface só recebem aprovação após execução nas plataformas correspondentes.
