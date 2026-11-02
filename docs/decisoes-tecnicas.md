# Sound Mine — Decisões Técnicas

Este documento registra as decisões técnicas relevantes do Sound Mine e os motivos de cada uma.

---

## DT01 — Estrutura do projeto

- `sound_mine.py` na raiz é o ponto de entrada e apenas chama `src/main.py`.
- Todo o código fica em `src/`:
  - `src/controllers`: modelo e definições dos menus (`menu_model.py`, `menu_navigator.py`, `main_menu.py`, `editor_menu.py`) e o formulário de configurações (`settings.py`).
  - `src/models`: gerenciamento das telas (`screen_manager.py`), os valores das configurações (`settings.py`), o player (`audio_player.py`) e as operações de edição (`audio_edit.py`).
  - `src/view`: telas, exibição, teclado, fala e mensagens.
- Testes em `tests/`, com `unittest` da biblioteca padrão.
- A versão do programa fica na variável global `SOUND_MINE_VER`, no ponto de entrada `sound_mine.py`, e é passada para `main(version)`. Nenhum arquivo de `src/` define a versão. Valor atual: `Sound Mine 0.1.0 DEV`.
- O código não leva comentários nem docstrings.

**Execução:** `python sound_mine.py`
**Testes:** `python -m unittest`

## DT02 — Sistema próprio de menus

O Sound Mine não utiliza barra de menus, menus suspensos, submenus nem listas nativas do Windows.

**Motivo:** listas e menus nativos fazem o leitor de tela anunciar "lista", "painel" ou o menu do sistema, e podem gerar leituras duplicadas. A mesma abordagem já foi validada no Over Drive.

**Como funciona:**

- O foco fica em um ponto de foco invisível dentro da janela (`FocusSink`, em `src/view/screen.py`), e não na própria janela. Os painéis não aceitam foco (`NoFocusPanel`).
- Todas as teclas chegam pelo `EVT_CHAR_HOOK` da janela e são traduzidas em comandos em um único lugar (`src/view/keys.py`). Isso garante a mesma navegação em todas as telas.
- O foco é devolvido com `wx.CallAfter` sempre que a janela é exibida ou reativada. Cada tela pode indicar outro destino para o foco (`focus_target`).

**Ponto de foco invisível:** se o foco ficasse na janela, o NVDA falaria o título sempre que o foco voltasse para ela (por exemplo, ao sair de uma caixa de edição). O título deve ser falado apenas quando a janela ganha o foco e no NVDA+T. O ponto de foco tem como nome um caractere invisível (U+200B), porque o NVDA ignora nomes formados só por espaços e, para um objeto sem nome, fala o tipo ("desconhecido").

**Exceção — controles nativos nas configurações:** a tela de configurações usa controles nativos do Windows nos campos em que o anúncio do próprio leitor de tela é necessário:

| Campo | Controle | Anúncio do NVDA |
|---|---|---|
| Valor digitado | `wx.TextCtrl` | "editável" |
| Percentual | `wx.Slider` | "controle deslizante" |
| Ativar ou desativar | `wx.CheckBox` | "caixa de seleção, marcada / não marcada" |

- Cada campo tem o seu próprio controle, com um rótulo (`wx.StaticText`) logo antes dele, para o NVDA ler o nome do campo.
- O foco passa para o controle novo antes de o anterior ser escondido. Reaproveitar o mesmo controle, ou escondê-lo com o foco ainda nele, faz o NVDA não anunciar o campo ou cortar a fala.
- Enquanto um controle nativo tem o foco, as teclas de edição passam direto para ele (`passes_key`). Tab, Ctrl+Tab, Enter e Esc continuam com o programa.
- Ao sair de um controle nativo para um campo do programa, a fala desse campo espera 150 ms (`ANNOUNCE_DELAY_MS`), para não ser cortada pela troca de foco.
- Listas, seletor de guias e botões continuam no sistema próprio, falados pelo programa.
- O mesmo formulário é usado nos volumes do Fundo sonoro (DT07), com a opção `show_tab_selector=False`: sem seletor de guias, o primeiro campo já é um controle nativo, que recebe o foco ao abrir e é anunciado pelo próprio NVDA.
- Para quem enxerga, o item atual aparece em texto, com a posição (por exemplo, "Abrir arquivo (1 de 3)").

**Expansão:** um menu é uma lista de `MenuItem` dentro de um `Menu`. Para adicionar, remover ou reordenar opções, basta editar essa lista. A lógica de navegação não muda.

## DT03 — Regras de navegação

| Tecla | Comportamento |
|---|---|
| Setas para cima e para baixo | Navegam entre as opções, com o som de navegação. Não há navegação circular: nas pontas, toca o som de borda (`border`), como no DOSVOX, sem fala. Vale para todos os menus, inclusive a lista do editor. |
| Enter | Executa a opção selecionada. |
| Letra | Nos menus comuns, apenas seleciona a opção (`LetterMode.SELECT`). No editor, executa a opção diretamente (`LetterMode.ACTIVATE`), e a lista de opções só aparece pelas setas (DT07). |
| Esc | Volta à tela anterior. No menu principal, fecha o programa sem confirmação. |
| F1 | Disponível apenas nos menus que declaram `has_help=True` (menus do editor). |
| F2, F3 e F4 | Controles do player (ver DT07). Nas outras telas, não fazem nada. |
| Alt, Aplicativos e Alt+Espaço | Bloqueadas, para não abrir o menu do sistema do Windows. Alt+F4 continua fechando o programa. |
| Tab e Shift+Tab | Nas configurações, passam pelos campos. Nos menus, não fazem nada. |
| Ctrl+Tab e Ctrl+Shift+Tab | Nas configurações, trocam de guia. Nos menus, não fazem nada. |
| Setas para os lados, Home, End, Page Up, Page Down, Backspace e Espaço | Usadas pelos controles nativos das configurações. Nos menus, não fazem nada. No player, Espaço, setas para os lados, Home e End controlam a reprodução (DT07). |
| Números | Nos menus, funcionam como letras. Nas caixas de edição, são digitados. O teclado numérico também funciona. |

- Letras repetidas em um mesmo menu são recusadas ao montar o menu.
- Opções indisponíveis ficam ocultas (por exemplo, opções de edição sem arquivo aberto). Se a verificação de disponibilidade falhar, a opção também fica oculta.
- A opção Sair existe no menu principal e fecha o programa sem confirmação. A única confirmação de saída é a do editor com alterações não salvas (DT07).

## DT04 — Exibição das opções

- Nos menus comuns, a opção é exibida e falada sem o prefixo da letra (por exemplo, "Abrir arquivo").
- No editor, a opção é exibida e falada com o prefixo (por exemplo, "T - Tocar arquivo").

## DT05 — Fala e mensagens

**Fala:** feita pela biblioteca `accessible_output2` (versão 0.17), que fala pelo NVDA, pelo JAWS ou, na falta deles, pela voz do Windows (SAPI).

- Motivo da escolha: suporte a vários leitores de tela, licença MIT e uso já validado no Over Drive.
- Riscos: a biblioteca recebe poucas atualizações e carrega DLLs próprias.
- Proteções: a versão está fixada em `requirements.txt`. Se a fala não iniciar, o programa continua funcionando e avisa o usuário ao abrir.

**Mensagem de abertura:** ao abrir um menu, o programa fala e mostra a mensagem de abertura do menu (`intro`, ou o título quando não houver). Depois de 3 segundos (`MESSAGE_TIME_MS`), o texto sai da janela e o item atual é falado sem interromper a mensagem. Uma seta ou letra interrompe a mensagem imediatamente. Com a opção **Desativar dicas do programa** marcada, a mensagem de abertura é apenas o título do menu.

**Sons da interface:** abertura (`startup`), fechamento (`close`), navegação (`navigation`), confirmação (`confirme`) e borda do menu (`border`). Com a opção **Desativar sons da interface** marcada, `InterfaceSounds.enabled` fica falso e os sons deixam de tocar.

**Configurações em memória:** os valores ficam em um objeto `Settings` (`src/models/settings.py`), criado ao abrir o programa e guardado no `ScreenManager`. A tela de configurações altera apenas uma cópia (o formulário), que só é aplicada ao salvar. Ainda não há arquivo de configurações.

**Título da janela:** é sempre `SOUND_MINE_VER`, para que NVDA+T leia o nome e a versão do programa.

**Tipos de mensagem (`Announcer`):**

| Tipo | Uso | Exibição |
|---|---|---|
| `info` | Avisos comuns | Apenas falado |
| `error` | Erros | Caixa de diálogo |
| `done` | Operação de edição concluída (por exemplo, arquivo salvo) | Caixa de diálogo |

Erros em ações de menu são registrados no console e anunciados ao usuário, sem fechar o programa.

## DT06 — Dependências

| Dependência | Versão | Uso |
|---|---|---|
| wxPython | 4.3.2 | Interface gráfica |
| accessible_output2 | 0.17 | Fala pelo leitor de tela |
| soundfile | 0.13.1 (libsndfile 1.2.2) | Leitura dos sons da interface |
| sounddevice | 0.5.2 (PortAudio V19.7) | Saída de áudio (sons da interface e player) |
| av (PyAV) | 19.0.2 (FFmpeg 9.0.2) | Leitura dos arquivos de áudio no player, em todos os formatos previstos |

O numpy é instalado junto com a soundfile e é usado para guardar as amostras de áudio.

Instalação: `python -m pip install -r requirements.txt`

## DT07 — Editor

O editor (RN02, RN02.1 a RN02.4 e RN03) foi desenvolvido primeiro como um protótipo isolado e, depois de validado, integrado ao menu principal.

**Integração ao menu principal:**

- A opção **Abrir arquivo** abre o Explorador de Arquivos do Windows (`src/view/file_dialog.py`), filtrado para MP3, M4A, WAV e OGG (RN01).
- O arquivo escolhido é carregado pelo `AudioPlayer` (DT08). Se for inválido, o programa mostra o erro e continua no menu principal. Se for válido, abre o menu de edição (`open_editor`, em `editor_menu.py`).
- Cancelar o Explorador volta ao menu principal sem mensagem.
- Esc no menu de edição volta ao menu principal. Ao fechar o editor, a saída de áudio do player é fechada.

**Protótipos (histórico):** durante o desenvolvimento, o editor e o player foram testados separadamente por `editor_prototype.py` e `player_prototype.py`, na raiz. Os arquivos do editor já ficavam nas pastas definitivas, então a integração só trocou a ação de Abrir arquivo em `main_menu.py`. Depois da integração, os protótipos foram removidos. O editor é testado pelo programa normal (`python sound_mine.py`) com os arquivos de `tests\audios`.

- Remover, Misturar e Desfazer alteram o áudio na memória (ver **Operações de edição**).

**Arquivos:**

| Arquivo | Responsabilidade |
|---|---|
| `src/controllers/editor_menu.py` | Menu de edição e submenus |
| `src/models/audio_edit.py` | Operações de edição sobre as amostras (sem interface, testadas em `tests/test_audio_edit.py`) |
| `src/models/audio_player.py` | Player real (DT08) |
| `src/view/editor_screen.py` | Tela do menu de edição |
| `src/view/player_screen.py` | Tela do player |

**Menus:** todos os menus do editor usam `LetterMode.ACTIVATE` e `has_help=True`, e exibem a opção com a letra (DT04).

| Menu | Opções |
|---|---|
| Menu de edição | T - Tocar arquivo, R - Remover, M - Misturar, D - Desfazer, S - Salvar |
| Remover | A - Antes do cursor, D - Depois do cursor, E - Entre o cursor e o ponto memorizado |
| Misturar | A - Adição de áudio, F - Fundo sonoro |
| Adição de áudio e Fundo sonoro | I - No início, C - No cursor, F - No final |
| Desfazer alterações | N - Não, S - Sim |

**Navegação no estilo DOSVOX:**

- Ao abrir, o menu de edição fala apenas "Qual sua opção?". Os submenus falam o título seguido de "Qual sua opção?" (por exemplo, "Remover. Qual sua opção?"), e a confirmação do Desfazer fala a própria pergunta.
- A lista de opções começa fechada: nenhuma opção é exibida nem falada, e Enter não faz nada.
- As letras executam a opção diretamente, com a lista aberta ou fechada, sem falar o nome da opção.
- A lista só é aberta pelas setas: seta para baixo mostra a primeira opção, seta para cima mostra a última. Com a lista aberta, as setas e o Enter funcionam como nos outros menus (DT03).
- Depois de executar uma opção, ou ao voltar de um submenu ou do player, a lista é fechada de novo e a pergunta é falada outra vez.
- A pergunta é falada 150 ms depois (`ANNOUNCE_DELAY_MS`) e sem interromper. Assim, ela não é cortada pelo anúncio do NVDA quando a janela ganha o foco ou uma caixa de diálogo fecha, e vem depois da resposta da opção. Qualquer tecla cancela a pergunta pendente.
- A opção **Desativar dicas do programa** não altera as falas do editor, porque elas não contêm dicas de navegação. As explicações das teclas ficam no F1.
- A janela mostra o arquivo e a posição do cursor (por exemplo, "musica.mp3 - cursor em 0:42 de 3:00"), atualizados depois de cada operação.

- Na confirmação do Desfazer, **Não** é a primeira opção, para que um Enter acidental não recupere a versão salva.
- Sim exibe a caixa de diálogo de conclusão e volta ao menu de edição. Não volta ao menu de edição e fala "Operação cancelada.".
- Esc volta ao menu anterior. No menu de edição, volta ao menu principal.
- **Confirmação de saída:** se houver alterações não salvas, o Esc no menu de edição abre a confirmação **Sair do editor**: "Há alterações não salvas. Deseja sair sem salvar? N para não, S para sim.". **Não** é a primeira opção e volta ao editor; **Sim** sai sem salvar. Esc na confirmação também volta ao editor. Sem alterações (ou logo depois de salvar), o Esc sai direto.
- A confirmação vale só para o Esc. Fechar a janela (Alt+F4) ainda sai sem perguntar.

**Player:** a opção T - Tocar arquivo abre a tela do player e começa a tocar. Enquanto o player está aberto, o menu de edição fica bloqueado: as letras, o Enter e as setas para cima e para baixo não fazem nada.

| Tecla | Comportamento |
|---|---|
| Espaço | Toca ou pausa. Ao pausar, fala "Pausado". No fim do som, recomeça do início. |
| Seta para a esquerda | Volta 5 segundos (`SEEK_SECONDS`). Ao chegar ao começo, fala "Início do som". |
| Seta para a direita | Avança 5 segundos. Ao chegar ao fim, pausa e fala "Fim do som". |
| Home | Vai para o começo e fala "Início do som". |
| End | Vai para o fim, pausa e fala "Fim do som". |
| F1 | Ajuda com as teclas do player. |
| F2 | Fala o tempo percorrido e a duração total (por exemplo, "42 segundos de 3 minutos"). |
| F3 e F4 | Diminuem e aumentam o volume de 10 em 10, entre 0% e 100%, e falam o valor. O volume inicial é 100%. |
| M | Memoriza a posição atual e fala "Ponto memorizado em ...". Usado em Remover entre o cursor e o ponto memorizado. |
| Esc | Pausa e volta ao menu de edição. A posição em que o som parou é o cursor usado pelas operações de edição. |

- Quando o som termina sozinho, o programa fala "Fim do som" e o player continua aberto.
- Ao começar a tocar, o programa não fala nada, porque o próprio som é o retorno.
- A janela mostra o estado do player (arquivo, tocando ou pausado, tempo, volume) e a lista das teclas. O estado é verificado a cada 100 ms (`REFRESH_MS`), e o texto só muda quando o valor muda.

**Decisões provisórias:** os pontos abaixo não estão definidos nas regras de negócio e devem ser revistos antes da integração.

- As letras das opções, exceto o T de Tocar arquivo.
- Qual tecla, F3 ou F4, diminui o volume, o passo e os limites.
- Fundo sonoro: o volume do áudio original vale só no trecho em que o fundo toca, os volumes padrão são 100% e 30%, e "No final" faz o fundo terminar junto com o áudio.

**Operações de edição:**

- A edição acontece nas amostras que o player guarda na memória. O arquivo original nunca é alterado.
- Remover antes do cursor apaga do início até o cursor, e o cursor vai para o início. Remover depois do cursor apaga do cursor até o fim. Remover entre o cursor e o ponto memorizado apaga o trecho entre os dois pontos, em qualquer ordem, e o cursor fica no começo do trecho apagado.
- Toda operação apaga o ponto memorizado, porque a posição dele deixa de corresponder ao mesmo trecho do som.
- Uma operação que deixaria o áudio vazio é recusada.
- Desfazer volta à última versão salva. Enquanto não existe a opção Salvar, essa versão é o áudio como foi aberto. Sem alterações, o programa informa "não há alterações para desfazer" e não abre a confirmação.
- A versão salva é guardada como referência às amostras originais. As remoções não ocupam memória extra.
- Ao concluir, o programa exibe a caixa de diálogo de conclusão (DT05), por exemplo "Trecho antes do cursor removido.".

**Misturar (etapa 2):**

- As duas opções abrem o Explorador de Arquivos (`choose_audio_file`). O arquivo escolhido passa pelas mesmas validações da abertura (DT08) e é convertido para a mesma taxa de amostragem do áudio editado. Cancelar o Explorador não faz nada.
- **Adição de áudio:** insere o arquivo no início, no cursor ou no final. O cursor fica no começo do trecho inserido.
- **Fundo sonoro:** depois de escolher o arquivo, abre o formulário **Fundo sonoro no início/no cursor/no final** (`background_form.py`), com Tab e Shift+Tab, sem navegação circular:
  1. Volume do áudio original: controle deslizante, 0 a 100%, padrão 100%.
  2. Volume da música de fundo: controle deslizante, 0 a 100%, padrão 30%.
  3. Adicionar fundo sonoro: aplica a mistura, mostra a caixa de conclusão e volta ao submenu.
  4. Cancelar (ou Esc): volta ao submenu sem alterar o áudio.
- Os controles deslizantes funcionam como nas configurações: setas de 5 em 5, Page Up e Page Down de 10 em 10, Home e End nos limites.
- Posição do fundo: No início começa em 0, No cursor começa no cursor, e No final termina junto com o fim do áudio (ou começa em 0, se o fundo for mais longo).
- O fundo nunca aumenta a duração: o que passa do fim do áudio é cortado. O volume do áudio original vale só no trecho em que o fundo toca.
- A soma dos dois sons é limitada à faixa válida (-1 a 1), para não estourar.
- O resultado precisa caber no limite de memória (DT08), contando também a versão salva usada pelo Desfazer.

**Salvar (etapa 3):**

- A opção S - Salvar abre a janela "Salvar arquivo de áudio" do Windows, na pasta do arquivo aberto, propondo o nome `<nome>_editado.<formato>`. Se o nome já termina em `_editado`, propõe o mesmo nome.
- O formato, o tipo de canal e a taxa de amostragem vêm das **Configurações** (guia Geral). A janela só mostra arquivos do formato configurado. Uma extensão diferente é recusada, com a explicação de qual extensão usar.
- Gravar por cima de um arquivo que já existe, inclusive o original, exige a confirmação do próprio Windows (`FD_OVERWRITE_PROMPT`).
- A gravação é feita em um arquivo temporário na mesma pasta e só depois substitui o destino (`os.replace`). Se algo falhar, o temporário é apagado e o arquivo de destino fica como estava.
- Antes de gravar, o programa fala "Salvando o arquivo.". Ao terminar, mostra a caixa de conclusão "Arquivo salvo: nome." (DT05).
- Depois de salvar, o editor passa a mostrar o nome do arquivo salvo, e o Desfazer volta a essa versão (RN02.4).
- Cancelar a janela não faz nada.

| Formato | Gravação | Taxas |
|---|---|---|
| MP3 | PyAV (`libmp3lame`), 192 kbps | 44100 e 48000. Com 96000 configurado, grava em 48000 e avisa na mensagem de conclusão. |
| M4A | PyAV (`aac`, contêiner `ipod`), 192 kbps | 44100, 48000 e 96000 |
| WAV | soundfile, PCM 16 bits | 44100, 48000 e 96000 |
| OGG | soundfile, Vorbis, gravado em blocos de 1 segundo | 44100, 48000 e 96000 |

- O OGG usa a soundfile porque o FFmpeg do pacote só tem o codificador Vorbis experimental. A gravação em blocos evita o estouro de pilha da libsndfile ao gravar Vorbis longo de uma vez (DT08).
- A conversão de taxa e de canais é feita pelo PyAV (`AudioResampler`). Mono é a mistura dos dois canais.

**Erros de operação:** quando uma operação não pode ser realizada (cursor no início ou no final, falta de ponto memorizado), o programa exibe uma caixa de diálogo de erro iniciada por "A operação não pode ser realizada:" (DT05).

**Alteração em `keys.py`:** foram acrescentados os comandos `TIME` (F2), `VOLUME_DOWN` (F3) e `VOLUME_UP` (F4). Nas telas que não os utilizam, a tecla segue sem efeito.

## DT08 — Player de áudio

O player usa o **PyAV** (FFmpeg) para ler o arquivo e a **sounddevice** para tocar.

**Histórico:** a primeira versão lia com a soundfile, que não lê M4A. A soundfile foi trocada pelo PyAV para atender todos os formatos previstos. Os sons da interface continuam com a soundfile, para não alterar uma funcionalidade já validada.

**Motivo da escolha:**

- O FFmpeg lê todos os formatos previstos e é instalado pelo pip, sem programas externos.
- O arquivo inteiro é decodificado para a memória como amostras (`numpy`, float32, estéreo, na taxa da placa de som). Ir para o começo, para o fim ou avançar 5 segundos é só mudar a posição, com precisão, em qualquer formato.
- As mesmas amostras servirão às operações de edição (remover e misturar).
- O FFmpeg do pacote também grava AAC (M4A) e MP3, usados pelo Salvar (DT07).
- A saída de áudio é aberta como nos sons da interface: WASAPI na taxa da própria placa de som, com a saída padrão do Windows como alternativa. O PyAV converte o arquivo para essa taxa ao carregar. A primeira versão deixava a conversão para o WASAPI (`auto_convert`), e o som não saía no headset de teste (48000 Hz) com arquivos de 44100 Hz.

**Alternativas avaliadas e descartadas:** soundfile (não lê M4A e trava ao gravar OGG Vorbis longo de uma vez, com estouro de pilha), python-vlc e python-mpv (exigem programas ou DLLs externos e não entregam as amostras para a edição), FFmpeg executável (exige distribuir o `ffmpeg.exe` e controlar um processo externo), Media Foundation do Windows (não lê OGG sem extensões da loja), pygame, pyminiaudio, pydub, simpleaudio e playsound.

**Formatos aceitos:** `.mp3`, `.m4a` (AAC), `.wav` e `.ogg` (Vorbis e Opus). Outros formatos que o FFmpeg lê, como FLAC, continuam recusados até serem incluídos nas regras de negócio.

**Segurança e validação (`load_audio`):**

- O arquivo é tratado como não confiável.
- Só são aceitas as quatro extensões previstas. Arquivos inexistentes ou vazios são recusados antes de chegar ao FFmpeg.
- O formato real, identificado pelo FFmpeg, precisa corresponder à extensão. Um WAV renomeado para `.ogg` ou um M4A renomeado para `.mp3`, por exemplo, são recusados.
- Só a primeira faixa de áudio é decodificada. Capas e vídeo são ignorados, e um arquivo sem áudio é recusado.
- Limite de memória: a duração declarada é conferida antes de decodificar, e o tamanho real é conferido durante a decodificação, caso a duração declarada seja falsa. O limite é o campo **Memória em megabytes** das configurações. Em Automático (0), é 1024 MB (`DEFAULT_MEMORY_MB`).
- Limite de tempo: a decodificação é cancelada depois de 60 segundos (`DECODE_TIME_LIMIT_SECONDS`), para que um arquivo malformado não trave o programa.
- Qualquer erro do FFmpeg vira a mensagem "O arquivo está corrompido ou não é um áudio válido.", sem fechar o programa.
- A reprodução roda em uma thread de áudio que só copia amostras já carregadas, protegida por trava. Ela não lê arquivos nem chama a interface.

**Riscos:**

- O FFmpeg lê muitos formatos e tem falhas de segurança publicadas com frequência. O PyAV deve ser mantido atualizado, porque cada versão traz um FFmpeg recente. A versão fica fixada no `requirements.txt`.
- Licença: o PyAV é BSD-3. O FFmpeg do pacote se declara "LGPL version 3 or later" e foi compilado com `--enable-version3`, sem `--enable-gpl`. Mesmo assim, ele foi compilado com `--enable-libx264` e `--enable-libx265` e o pacote traz essas DLLs, que são GPL e servem só para vídeo. Essa combinação é contraditória e precisa de revisão antes de distribuir o Sound Mine. Caminhos possíveis: adotar para o Sound Mine uma licença compatível com a GPL, ou distribuir um FFmpeg compilado só com áudio, sem bibliotecas GPL.
- O pacote ocupa dezenas de MB, por causa do FFmpeg.

**Player simulado:** o `PlayerState`, usado no início do desenvolvimento do editor, foi retirado. Hoje só existe o `AudioPlayer`.

**Arquivos de teste:** `python tests\gerar_audios.py` cria em `tests\audios` um arquivo de 30 segundos para cada formato aceito e arquivos inválidos para testar as recusas. O tom fica mais agudo do começo para o fim, e há um bipe a cada 5 segundos.
