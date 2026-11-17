# Instalar NOW Assistant no Windows

1. Baixe o ZIP Windows x64 e SHA256SUMS.txt da mesma versão em https://github.com/Gabomgames/Now-assistant/releases.
2. Confira o hash no PowerShell com `Get-FileHash .\NOW-Assistant-*.zip -Algorithm SHA256`, comparando-o ao arquivo da release.
3. Extraia **toda** a pasta NOW-Assistant para uma pasta privada do seu usuário. Não execute dentro do ZIP nem copie só o EXE.
4. Abra NOW-Assistant.exe. Não precisa de VS Code, Python ou instalação de pacotes Python.

Requisitos: Windows x64 (Windows 10 é alvo; Windows Server 2022 é o runner automático), cerca de 8 GB RAM e espaço para extrair o pacote. Comandos básicos não exigem GPU, internet, conta ou modelo. Bibliotecas Python/Qt necessárias acompanham a pasta `_internal`; preserve-a. A Alpha não é assinada digitalmente: Windows/antivírus podem apresentar avisos. Confira origem/hash e siga a política do seu computador; não desative proteções para contornar um bloqueio.

## Usar sem modelo

Digite `oi`, `horas`, `data` ou `ajuda`. Em Preferências, escolha English para `hello`, `time`, `date`, `help`. São comandos locais determinísticos. Histórico é temporário por padrão; guardar novas conversas exige consentimento e senha. Preferências NOW Memory são um cofre separado. Dados ficam em `%LOCALAPPDATA%\NOWAssistant`, sem entrar neste ZIP. Guarde sua senha: não há recuperação automática.

## Conversas livres com Ollama, instalação separada

Ollama **não está incluído** no executável. Pesos Qwen também **não estão incluídos**.

Instale o Ollama pelo site oficial https://ollama.com/download/windows, abra-o e use PowerShell:

```powershell
ollama pull qwen2.5:0.5b
ollama list
```

Espere o download concluir e confirme a tag. Reabra a NOW. O modelo usa CPU/RAM próprios e pode afetar jogos. A interface informa quando o modelo não está disponível; não habilita Gemini. NATURALIDADE E QUALIDADE DO QWEN NÃO FORAM APROVADAS nesta Alpha. A validação automática de distribuição testa comandos offline reais, não oito gerações Qwen. Rede para baixar o modelo deve ser liberada legitimamente; preserve TLS e políticas do ambiente.

## Limitações e desinstalação

Sem voz audível, microfone/STT/TTS, wake “Now”, bandeja, iniciar com Windows, análise de tela, sincronização ou Android. Fechar a janela encerra a Engine própria. Cancelar descarta a resposta da janela; uma geração já iniciada pode continuar no Ollama. É uma versão experimental; compatibilidade Windows 10, DPI, leitor de tela, ACLs e hardware de 8 GB ainda exigem validação manual no alvo. Um teste no runner Windows Server não comprova todos esses cenários.

Para remover, feche o aplicativo e apague a pasta extraída. Dados pessoais permanecem em `%LOCALAPPDATA%\NOWAssistant`; exporte/apague explicitamente pelo app conforme sua preferência. Desinstalar o Ollama/modelo é uma operação separada. Não envie bancos, senhas ou exports pessoais em relatos de erro.


## Candidato 0.3.0-alpha.2 / Fase 6

No pacote novo, escolha o modelo instalado em Preferências. Não é necessário
configurar variáveis para o Brain v1. `Avaliar-Modelos.cmd` abre o utilitário
empacotado com relatório local e `Modo-Legado.cmd` permite rollback.
Leia `AVALIACAO-E-MODELOS.md` incluído no ZIP. Ollama/pesos não acompanham o
candidato; nenhuma avaliação é enviada automaticamente e nenhuma Release foi
publicada por essa mudança.
