# Bibliotecas e avisos de terceiros

A pasta LICENSES acompanha o aplicativo. Python, PySide6/shiboken6/Qt, PyInstaller e as dependências mantêm seus direitos e licenças próprios; esses textos não alteram a licença do código da NOW Assistant.

Qt/PySide são distribuídos como bibliotecas dinâmicas. A opção LGPL-3.0 inclui seus termos e os termos GPL referenciados, além de avisos de terceiros coletados dos fontes oficiais. As DLLs não são fundidas em um executável estático. Preserve os avisos e permita substituir/depurar versões modificadas dessas bibliotecas conforme os termos aplicáveis. Os fontes correspondentes upstream, commits e SHA-256 estão em DEPENDENCIES.json. O código-fonte da aplicação está em https://github.com/Gabomgames/Now-assistant na revisão indicada em BUILD-VALIDACAO.json.

Os textos de Qtbase, QtSvg e PySide são obtidos de arquivos de fonte oficiais, com revisão e hash fixados. A coleta inclui avisos de componentes opcionais que podem não estar no pacote. O inventário SHA-256 em BUILD-VALIDACAO.json identifica os arquivos realmente distribuídos. As licenças das distribuições Python são copiadas dos pacotes instalados no ambiente isolado, e a licença do interpretador vem da instalação usada no build.

O bootloader do PyInstaller possui exceção própria; consulte o texto copiado do pacote. Não há Ollama ou pesos Qwen neste ZIP. A instalação separada desses produtos tem seus próprios requisitos/licenças. Não há licença comercial Qt ou assinatura Authenticode da NOW nesta Alpha.
