# Identidade oficial NOW Assistant

A fonte de verdade é a imagem oficial enviada pelo usuário: N em magenta/roxo/azul/ciano com órbita sobre fundo preto. Não redesenhar ou substituir por ícone genérico de IA.

Nesta sessão a imagem foi visível na conversa, mas nenhum arquivo de imagem ficou disponível nos anexos da máquina. O manifest registra essa pendência. A GUI usa o nome NOW Assistant e a paleta de referência; não apresenta um desenho substituto como logo oficial.

Assim que o PNG/JPG/WebP original estiver disponível, importar com `python tools/import_branding.py caminho/da/logo.png`, com `requirements-desktop.txt` instalado. O original é copiado sem mudar bytes, com SHA-256 registrado. Derivados só redimensionam e acomodam a imagem, mantendo proporção e fundo original, sem apagar detalhes escuros. O ICO contém os PNGs derivados; não é vetor. SVG exige um renderizador e revisão separados e é recusado por esta ferramenta. Fazer revisão visual dos ícones antes de release. Os mesmos pixels podem ser usados em superfícies claras/escuras; não existe variante redesenhada, transparência por remoção do preto nem launcher Android validado.
