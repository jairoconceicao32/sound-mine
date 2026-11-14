# Sound Mine

Mini editor de áudio projetado para ser simples e intuitivo.

Inspirado no MiniGrave, do DOSVOX, o Sound Mine tem como objetivo oferecer uma solução mais simples para edição de áudio, sem exigir que o usuário recorra a ferramentas robustas e complexas.

O projeto não visa competir com os editores disponíveis no mercado, mas oferecer uma alternativa para quem busca praticidade e agilidade na realização de edições simples de áudio.

## Sobre o projeto

O Sound Mine está sendo desenvolvido com foco na simplicidade de utilização, priorizando uma navegação intuitiva por teclado e uma experiência acessível.

## Compatibilidade com leitores de tela

O Sound Mine buscará oferecer compatibilidade com NVDA, JAWS e outras tecnologias assistivas disponíveis no mercado.

## Funcionalidades previstas

- **Abertura de arquivos:** seleção de arquivos por meio do Explorador de Arquivos do Windows.
- **Formatos suportados:** MP3, M4A, WAV e OGG.
- **Reprodução de áudio:** reprodução e pausa utilizando a tecla Espaço.
- **Edição de áudio:** operações básicas, como cortes e adição de músicas.
- **Navegação por teclado:** acesso às opções por meio de letras e setas do teclado.
- **Ajuda integrada:** consulta aos comandos disponíveis utilizando a tecla F1.
- **Configurações:** seleção de idioma, formato de saída e qualidade de áudio.
- **Sons de interface:** efeitos sonoros para inicialização, encerramento e navegação pelos menus.

## Registro de erros

Quando ocorre um erro, o Sound Mine grava um registro técnico no arquivo `sound_mine.log`, na pasta `logs`, dentro da própria pasta do Sound Mine.

Se a pasta do programa não permitir gravação (por exemplo, quando ele estiver instalado em `C:\Program Files`), o registro é gravado automaticamente em:

```
%LOCALAPPDATA%\Sound Mine\logs\sound_mine.log
```

Para abrir essa pasta, pressione `Windows + R`, digite `%LOCALAPPDATA%\Sound Mine\logs` e pressione Enter. O arquivo só é criado depois do primeiro erro.

O registro ajuda a investigar problemas e pode ser enviado a quem desenvolve o programa. Ele fica apenas no seu computador e não guarda nomes de arquivos, nomes de pastas pessoais, o conteúdo dos áudios, os textos falados pelo programa nem o nome dos dispositivos de som. Do arquivo de áudio, registra apenas a extensão e o tamanho. O arquivo é limitado a 1 MB, com até 3 cópias anteriores.

## Status do projeto

O Sound Mine está em fase de planejamento e desenvolvimento. As funcionalidades serão implementadas gradualmente, conforme a evolução das regras de negócio.
## Licença

O Sound Mine é software livre, distribuído sob a **GNU General Public License, versão 3 ou posterior** (GPL-3.0-or-later). O texto completo está no arquivo [`LICENSE`](LICENSE).

Você pode usar, estudar, modificar e redistribuir o programa. Versões modificadas que forem distribuídas também precisam ser distribuídas sob a GPL, com o código-fonte disponível.

O Sound Mine usa bibliotecas de terceiros, cada uma com a própria licença: wxPython (wxWindows Library Licence), accessible_output2 (MIT), PyAV (BSD-3, com o FFmpeg em LGPL/GPL), soundfile (BSD-3, com a libsndfile em LGPL), sounddevice (MIT, com o PortAudio) e NumPy (BSD-3). As licenças acompanham cada pacote instalado pelo `pip`.
