# Identidade oficial NOW Assistant

A fonte de verdade é a imagem oficial enviada pelo usuário: N em magenta/roxo/azul/ciano com órbita sobre fundo preto. Não redesenhar ou substituir por ícone genérico de IA.

O original definitivo foi recebido em `NOW_Assistant_Logo_Oficial_PARA_CODEX.zip`, validado por CRC/assinatura PNG e decodificado em Qt. `original.png` preserva exatamente os 943.589 bytes do PNG recebido, com SHA-256 `9bf499258d4b298fa410142452ccf0443039e6c76e709c540c6d22db204935dc`, dimensões 1301 × 1209. Não foi redesenhado, recortado nem teve cores/fundo alterados.

Importação usada: `python tools/import_branding.py <PNG-original> --padding black`, com `requirements-desktop.txt`. A imagem foi somente reduzida proporcionalmente e acomodada em canvas preto. O fundo original, inclusive seus detalhes quase pretos, permaneceu intacto. Tamanhos PNG: 16, 24, 32, 48, 64, 128, 192, 256 e 512; ICO contém oito PNGs até 256. Em tamanhos pequenos, o raster perde detalhe por redução, sem simplificação/redesenho da marca.

A GUI usa PNG no cabeçalho e ICO multi-resolução no ícone da janela/Windows. O PyInstaller recebe o mesmo ICO como recurso do EXE. Fonte e ícones foram inspecionados visualmente; o smoke exige imagem visível e ícone carregado também no aplicativo empacotado. A validação Windows final fica no relatório do candidato, não é presumida pela criação desses arquivos.

O ICO não é vetor. SVG exige renderizador/revisão separados e é recusado pelo importador. Não há remoção do preto, variante redesenhada, ícone de bandeja ativo ou launcher Android validado. Uma troca futura do original exige revisão explícita e atualização das verificações de identidade; o importador recusa sobrescrever a marca já importada com bytes diferentes.
