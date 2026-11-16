# NOW Memory — preferências locais criptografadas

O módulo `now_memory` armazena somente preferências explícitas. Importar o módulo ou consultar status não cria banco. Não há coleta de histórico, memórias inferidas, sincronização ou acesso pela API HTTP original.

## Segurança implementada

- SQLite local com valores AES-256-GCM autenticados; cada gravação recebe nonce aleatório e associa a cifra ao nome da preferência. Trocar cifras de campo ou alterar conteúdo é detectado.
- A chave é derivada da senha com scrypt (`N=131072, r=8, p=1`, salt aleatório de 16 bytes). Não há senha ou chave persistida junto do banco.
- O estado de habilitação também é autenticado. Sem desbloquear, status informa `enabled=null`, não uma confirmação de consentimento.
- Pastas/arquivos novos recebem 0700/0600 no POSIX. Caminhos de cofre que sejam symlinks ou tenham acesso de grupo/outros no POSIX são recusados; diretórios existentes do usuário não têm permissões alteradas silenciosamente.
- Atualizações múltiplas são validadas antes da transação. Uma gravação inválida não altera os valores anteriores. Não são aceitas preferências que concedam microfone ou execução de ferramentas.
- Não se sobrescrevem cofres ou arquivos de exportação existentes. Desabilitar bloqueia uso/gravação automáticos; exportar, excluir e limpar continuam disponíveis ao proprietário desbloqueado.

O formato guarda nomes de campos, salt, versão e horários de atualização como metadados legíveis. O conteúdo das preferências e o estado habilitado são cifrados. Isso não é uma auditoria de segurança nem proteção contra malware no processo desbloqueado/conta comprometida. A senha forte precisa ser guardada pelo usuário; não existe recuperação implementada. O KDF usa aproximadamente 128 MiB por desbloqueio; desempenho no Athlon/Windows ainda precisa de medição.

Excluir/limpar usa `secure_delete` e compactação do SQLite. Isso não apaga cópias externas, snapshots ou garante eliminação forense em SSD. A exportação é JSON em texto aberto, criada apenas por comando explícito e com modo privado no POSIX. Guarde dados, backups e exportações fora do repositório.

## Instalação e comandos

```bash
.venv/bin/python -m pip install -r requirements-memory.txt
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory status
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory init --consent
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory set language en-US
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory set persona casual
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory set humor 2
.venv/bin/python -m now_memory --directory /workspace/.now-ai-environment/user-memory get
```

A senha é solicitada por entrada oculta no terminal. `--password-env NOME_DA_VARIAVEL` é alternativa explícita para automação local; passa-se o nome, nunca o valor como argumento. Não coloque senhas em chat, comandos salvos, `.env.example` ou configuração reutilizável. Não reutilize placeholders de segredos de proxy como chaves locais.

As demais operações são `disable`, `enable --consent`, `delete NOME`, `clear` e `export --output CAMINHO_NOVO.json`. Exportação é texto aberto. Um cofre desabilitado não é desbloqueado automaticamente pela camada de voz para usar seus valores.

Campos aceitos: `display_name`, `language` (pt-BR/en-US), `persona` (classic/casual/gamer/focus/creative), `humor` (0–3), `reply_length`, `voice_style`, `voice_rate` e `proactive_comments`. Armazenar `proactive_comments=true` não inicia comentários; a funcionalidade ainda não foi implementada.

## Integração efetiva com o novo fluxo de texto

```bash
.venv/bin/python -m now_voice --memory-directory /workspace/.now-ai-environment/user-memory --text hello
```

O cliente desbloqueia o cofre por solicitação do usuário e obtém um snapshot das preferências. Idioma/nome personalizam os comandos determinísticos; velocidade/estilo entram no plano de fala e persona/humor entram na instrução do novo adaptador local. Não existe histórico conversacional persistente, e a CLI/API originais não foram modificadas para coletar dados.

No Windows, executar os mesmos módulos com `.\.venv\Scripts\python.exe`. O caminho padrão é `%LOCALAPPDATA%\NOWAI\memory`; no Linux, `$XDG_DATA_HOME/now-ai/memory` ou `~/.local/share/now-ai/memory`. No ambiente Codex com home somente leitura, use o diretório explícito de `/workspace` mostrado acima. Nenhum cofre real de usuário foi criado automaticamente por esta entrega.

Criptografia, permissões POSIX e fluxo de CLI foram testados no Linux. ACLs, distribuição nativa e comportamento em Windows/Android ainda não foram validados. Migrações futuras devem manter cópias e recusar formatos desconhecidos; esta versão só abre `now-memory-v1` e nunca sobrescreve uma base incompatível.
