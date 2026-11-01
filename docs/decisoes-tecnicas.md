# Sound Mine — Decisões Técnicas

Este documento registra as decisões técnicas relevantes do Sound Mine e os motivos de cada uma.

---

## DT01 — Estrutura do projeto

- `sound_mine.py` na raiz é o ponto de entrada e apenas chama `src/main.py`.
- Todo o código fica em `src/`:
  - `src/controllers`: modelo e definições dos menus (`menu_model.py`, `menu_navigator.py`, `main_menu.py`).
  - `src/models`: gerenciamento das telas (`screen_manager.py`).
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

- O foco fica na própria janela. Os painéis não aceitam foco (`NoFocusPanel`).
- Todas as teclas chegam pelo `EVT_CHAR_HOOK` da janela e são traduzidas em comandos em um único lugar (`src/view/keys.py`). Isso garante a mesma navegação em todas as telas.
- O foco é devolvido à janela com `wx.CallAfter` sempre que ela é exibida ou reativada.
- Para quem enxerga, o item atual aparece em texto, com a posição (por exemplo, "Abrir arquivo (1 de 3)").

**Expansão:** um menu é uma lista de `MenuItem` dentro de um `Menu`. Para adicionar, remover ou reordenar opções, basta editar essa lista. A lógica de navegação não muda.

## DT03 — Regras de navegação

| Tecla | Comportamento |
|---|---|
| Setas para cima e para baixo | Navegam entre as opções, com o som de navegação. Não há navegação circular: nas pontas, nada acontece (sem fala e sem som). |
| Enter | Executa a opção selecionada. |
| Letra | Nos menus comuns, apenas seleciona a opção (`LetterMode.SELECT`). No editor, executa a opção diretamente (`LetterMode.ACTIVATE`). |
| Esc | Volta à tela anterior. No menu principal, fecha o programa sem confirmação. |
| F1 | Disponível apenas nos menus que declaram `has_help=True` (previsto para o editor). |
| Alt, Aplicativos e Alt+Espaço | Bloqueadas, para não abrir o menu do sistema do Windows. Alt+F4 continua fechando o programa. |

- Letras repetidas em um mesmo menu são recusadas ao montar o menu.
- Opções indisponíveis ficam ocultas (por exemplo, opções de edição sem arquivo aberto). Se a verificação de disponibilidade falhar, a opção também fica oculta.
- A opção Sair existe no menu principal e fecha o programa sem confirmação. Confirmações de saída serão usadas apenas no editor.

## DT04 — Exibição das opções

- Nos menus comuns, a opção é exibida e falada sem o prefixo da letra (por exemplo, "Abrir arquivo").
- No editor, a opção é exibida e falada com o prefixo (por exemplo, "T - Tocar arquivo").

## DT05 — Fala e mensagens

**Fala:** feita pela biblioteca `accessible_output2` (versão 0.17), que fala pelo NVDA, pelo JAWS ou, na falta deles, pela voz do Windows (SAPI).

- Motivo da escolha: suporte a vários leitores de tela, licença MIT e uso já validado no Over Drive.
- Riscos: a biblioteca recebe poucas atualizações e carrega DLLs próprias.
- Proteções: a versão está fixada em `requirements.txt`. Se a fala não iniciar, o programa continua funcionando e avisa o usuário ao abrir.

**Mensagem de abertura:** ao abrir um menu, o programa fala e mostra a mensagem de abertura do menu (`intro`, ou o título quando não houver). Depois de 3 segundos (`MESSAGE_TIME_MS`), o texto sai da janela e o item atual é falado sem interromper a mensagem. Uma seta ou letra interrompe a mensagem imediatamente.

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

Instalação: `python -m pip install -r requirements.txt`
