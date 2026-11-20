# Sistema de efeitos — 01. Análise arquitetural

Análise da arquitetura atual do Sound Mine para planejar a integração do sistema de efeitos descrito em `docs/regras_negocio_efeitos.md` (RN01 a RN12).

Este documento **não** propõe a implementação final. Ele levanta o que existe, onde os efeitos podem se encaixar e o que precisa ser decidido antes.

**Convenção usada:**

- **[Fato]** — observado no código, nos documentos ou no ambiente, com a referência.
- **[Hipótese]** — conclusão provável, ainda não verificada por teste ou medição.
- **[Recomendação]** — sugestão técnica, sujeita à aprovação do responsável pelo projeto.

Base analisada: branch `develop`, commit `82f7a96`.

---

## 1. Estrutura atual dos componentes envolvidos

**[Fato]** O projeto segue a divisão da DT01: `sound_mine.py` (entrada), `src/controllers`, `src/models`, `src/view` e `tests/` (`unittest`).

Componentes que participam de carregamento, edição e reprodução:

| Camada | Arquivo | Papel no fluxo de áudio |
|---|---|---|
| Model | `src/models/audio_player.py` | Carrega o arquivo (`load_audio`), guarda as amostras, o cursor, o ponto memorizado e a versão salva; aplica edições (`edit`), desfaz (`undo`), salva (`save`) e fornece as amostras à saída de som (`audio_callback`). |
| Model | `src/models/audio_edit.py` | Operações de edição como funções puras sobre `numpy` (remover, inserir, misturar). Sem interface. |
| Model | `src/models/audio_save.py` | Conversão de taxa e canais (PyAV) e gravação nos quatro formatos. |
| Model | `src/models/audio_output.py` | `OutputCoordinator`: único dono das saídas de som; abre um stream por cliente registrado. |
| Model | `src/models/settings.py` | Valores das configurações, incluindo eco e reverbe, com faixas em `RANGES`. |
| Model | `src/models/settings_store.py` | Persistência das configurações (`settings.dat`). |
| Model | `src/models/errors.py` | `SoundMineError`, nomes das operações para o log e para o título dos erros. |
| Controller | `src/controllers/editor_menu.py` | Menus do editor e as ações (`apply`, `add_background`, `open_undo`, `save_audio_file`). Já contém um esboço do menu de efeitos. |
| Controller | `src/controllers/background_form.py` | Formulário de volumes do Fundo sonoro, montado sobre `SettingsForm`. |
| Controller | `src/controllers/settings.py` | Formulário de configurações, incluindo a guia **Efeitos de áudio**. |
| Controller | `src/controllers/confirmation.py` | Modelo das confirmações (DT09). |
| View | `src/view/editor_screen.py` | Tela do menu de edição (estilo DOSVOX, letras ativam). |
| View | `src/view/player_screen.py` | Tela do player (Espaço, setas, Home/End, M, F2, F3/F4, Esc). |
| View | `src/view/confirm_screen.py` | Tela de confirmação (DT09). |
| View | `src/view/settings_screen.py` | Tela de formulário com controles nativos (DT02). |

### 1.1. Comunicação entre os módulos

**[Fato]**

- **View → Controller:** as telas recebem as teclas pelo `EVT_CHAR_HOOK` da janela, traduzidas em `Command` por `src/view/keys.py`, e executam as ações (`Callable`) dos `MenuItem`, dos botões dos formulários ou das confirmações.
- **Controller → Model:** as ações chamam o model diretamente (`player.edit`, `player.save`, `player.undo`, `load_compatible`). As operações de edição são passadas como funções (`lambda data, cursor, marked: ...`).
- **Controller → View:** os controllers empilham telas no `ScreenManager` (`push`, `pop`, `replace`, `pop_through`) e informam o usuário por `manager.announcer` (caixas de erro e conclusão) e `manager.speaker` (falas diretas).
- **Model → View:** o model não conhece a interface. Ele informa erros por exceções (`SoundMineError` e derivadas); o estado é lido pelas telas por consulta periódica (timer de 100 ms no player, 500 ms nas saídas de som). A única notificação ativa é o `set_listener` do `OutputCoordinator`, que avisa o `ScreenManager` da troca de saída.
- **Thread de áudio:** comunica-se com o resto apenas pelo estado do `AudioPlayer`, protegido por `_lock`. Os avisos do PortAudio só marcam um `threading.Event`; a reação acontece na thread do wx (DT10).
- **Dependências compartilhadas:** `ScreenManager` concentra `settings`, `announcer`, `speaker`, `sounds` e `outputs`, e é passado aos controllers e às telas.

### 1.2. Padrões arquiteturais adotados

**[Fato]**

| Padrão | Onde aparece |
|---|---|
| Separação model / controller / view por pastas | DT01. Os models não importam `wx`. |
| Funções puras para operações sobre áudio | `audio_edit.py`: entrada não alterada, resultado novo, erros por exceção. |
| Comando como função (*callable*) | `MenuItem.action`, `ButtonField`, `AudioPlayer.edit(operation)`. |
| Menus declarativos | Uma lista de `MenuItem` dentro de um `Menu`; acrescentar uma opção não muda a navegação (DT02, "Expansão"). |
| Pilha de telas | `ScreenManager` com `push`/`pop`; cada tela implementa `on_activate`, `handle_command`, `help_lines`. |
| Formulário genérico reaproveitado | `SettingsForm` usado nas configurações e no Fundo sonoro (`background_form.py`). |
| Coordenador único de recurso | `OutputCoordinator` é o único dono das saídas de som; clientes só fornecem `prepare_output` e `audio_callback`. |
| Validação centralizada no model | `OPTIONS`, `RANGES` e `is_valid` em `src/models/settings.py`. |
| Erros padronizados | `SoundMineError(reason, hint)`, `user_message`, `error_title`, contexto `operation` do log (DT05, DT11). |
| Substitutos nos testes | `PortAudioBackend` isolado para testes; operações testadas com arrays sintéticos. |

**[Fato]** Não há injeção de dependências por framework, nem eventos/observadores além do `set_listener`, nem registro (*registry*) de plugins.

---

## 2. Responsabilidades dos módulos

### 2.1. `AudioPlayer` (`src/models/audio_player.py`)

**[Fato]** Concentra todo o estado do áudio em edição:

| Atributo | Conteúdo |
|---|---|
| `_data` | Amostras atuais: `numpy.ndarray`, `float32`, formato `(quadros, 2)`, estéreo. |
| `_rate` | Taxa de amostragem (a da placa de som no momento da abertura). Não há propriedade pública para ler a taxa. |
| `_saved` | Referência à versão salva (ou à versão aberta, antes do primeiro Salvar). |
| `_frame` | Cursor, em quadros. |
| `_marked` | Ponto memorizado, em quadros, ou `None`. |
| `_playing` | Intenção de tocar. |
| `volume` | Volume de **reprodução** (0 a 100, passo 10, F3/F4). Não altera as amostras. |
| `_lock` | `threading.Lock` que protege o estado entre a thread do wx e a thread de áudio. |

Métodos relevantes para efeitos:

- `edit(operation)` (linha 170): recebe uma função `(data, cursor, marked) -> (novo_data, novo_cursor)`, executa-a **dentro da trava**, confere o limite de memória e substitui `_data`. Sempre pausa a reprodução e apaga o ponto memorizado.
- `undo()` (linha 198): volta `_data` para `_saved`.
- `has_changes` (linha 156): compara por identidade (`_data is not _saved`).
- `audio_callback` (linha 262): copia `_data[_frame:...]` multiplicado por `volume / 100` para a saída.

### 2.2. `audio_edit` (`src/models/audio_edit.py`)

**[Fato]** Funções puras, testadas em `tests/test_audio_edit.py`. Recebem as amostras e devolvem um novo array e o novo cursor. Erros previstos usam `EditError` com motivo e orientação (DT05). Esse é o padrão de código mais próximo do que os efeitos precisarão.

### 2.3. `editor_menu` (`src/controllers/editor_menu.py`)

**[Fato]** Monta os menus com `MenuItem` e `Menu` (`LetterMode.ACTIVATE`, `has_help=True`). A função interna `apply(edit, message, operation)` (linha 56) é o caminho comum das edições: abre o contexto do log, chama `player.edit`, mostra o erro ou a caixa de conclusão.

**[Fato]** Já existe um esboço do menu de efeitos (linhas 139 a 146), ligado ao menu de edição pela letra `E` (linha 155):

| Letra | Rótulo atual | Ação |
|---|---|---|
| A | almenta o volume | `lambda: None` |
| D | Diminui o volume | `lambda: None` |
| E | Eco | `lambda: None` |
| S | super eco | `lambda: None` |
| R | Reverberação | `lambda: None` |
| X | Super reverberação | `lambda: None` |

Observações sobre o esboço (fatos, sem correção nesta etapa):

- Faltam **Fade in** e **Fade out** (RN03 e RN04).
- O título é "Qual efeito"; o rótulo do menu de edição é "efeitos", em minúscula, diferente das demais opções.
- "almenta" está grafado com L.
- As letras minúsculas funcionam, porque `MenuItem` as converte para maiúsculas (`menu_model.py`).
- A DT07 (tabela **Menus**) ainda não lista a opção de efeitos.

### 2.4. Configurações (`src/models/settings.py` e `src/controllers/settings.py`)

**[Fato]** A guia **Efeitos de áudio** já existe e é persistida:

| Campo | Chave | Faixa (`RANGES`) | Padrão |
|---|---|---|---|
| Milissegundos para o eco | `echo_delay` | 10 a 2000 | 300 |
| Percentual do eco | `echo_percent` | 0 a 100 | 75 |
| Milissegundos para o reverbe | `reverb_delay` | 10 a 2000 | 200 |
| Percentual do reverbe | `reverb_percent` | 0 a 100 | 80 |

- Nenhum código lê esses valores além do formulário e da persistência.
- Não há campos para Super eco, Super reverberação, duração do fade in ou do fade out, nem limites de volume.
- `settings_from` completa chaves ausentes com o padrão e as marca como corrigidas (`CORRECTED`, só registrado no log). **[Hipótese]** Acrescentar novos campos não invalida um `settings.dat` existente, mas gera um registro de "corrigido" na primeira abertura.
- `docs/regras_negocio.md`, logo abaixo da tabela da guia, diz: "Os efeitos serão aplicados ao áudio quando as operações de edição forem implementadas."

---

## 3. Fluxo atual

### 3.1. Carregamento

**[Fato]** `main_menu.py` → Explorador → `AudioPlayer(path, memory_mb, outputs)` → `load_audio`:

1. Valida extensão, existência e tamanho zero.
2. Abre com PyAV e confere se o formato real corresponde à extensão.
3. Estima o tamanho pela duração declarada e recusa se passar do limite de memória.
4. Decodifica a primeira faixa de áudio, convertendo para `float32` estéreo na taxa da placa (`AudioResampler`).
5. Confere memória e tempo (60 s) durante a decodificação.
6. O player se registra no `OutputCoordinator`.

### 3.2. Edição

**[Fato]** Menu de edição → opção → `apply` → `player.edit(função)`:

1. A trava é adquirida e a reprodução é pausada.
2. A função recebe `_data`, `_frame` e `_marked` e devolve um array novo.
3. O uso de memória é `_saved.nbytes` mais o novo array, quando ele não compartilha memória com `_saved`.
4. Acima do limite, `EditError`; senão `_data` e o cursor são substituídos e `_marked` vira `None`.
5. O controller mostra a caixa de conclusão (`announcer.done`) ou o erro.

Tudo acontece **de forma síncrona na thread do wx**.

### 3.3. Reprodução

**[Fato]** `PlayerScreen` chama `play()`, que pede uma saída ao `OutputCoordinator` (`ensure`). A thread de áudio chama `audio_callback`, que lê `_data` a partir de `_frame`. Ao sair do player (Esc), a posição em que parou é o cursor das edições.

### 3.4. Gravação

**[Fato]** `save_audio_file` → `player.save` → `save_audio`: converte taxa e canais, aplica `np.clip(-1, 1)` (`audio_save.py:50`), grava em arquivo temporário e troca com `os.replace`. Depois, `_saved` passa a ser o array salvo.

---

## 4. Armazenamento dos dados de áudio

**[Fato]**

- O áudio inteiro fica em memória, como um único `ndarray` `float32` estéreo (8 bytes por quadro).
- Não existe representação por trechos, lista de operações nem metadados associados ao áudio (por exemplo, quais edições ou efeitos foram aplicados).
- O array é tratado como imutável na prática: as operações devolvem um array novo (`overlay` usa `data.copy()`), e as remoções podem devolver uma *view* que compartilha memória com a versão salva.
- O limite de memória (`memory_limit_bytes`) considera duas cópias: a versão salva e a atual.
- A taxa é fixada na abertura e não muda durante a edição (DT10).

**[Hipótese]** Um efeito que mantém a duração (volume, fades) cria um array do mesmo tamanho; com a versão salva, isso dobra o uso. Com uma prévia guardada ao mesmo tempo, seriam **três** arrays do mesmo tamanho (salva, atual e prévia), o que o limite atual não contabiliza.

---

## 5. Histórico e desfazer

**[Fato]**

- Não existe histórico de várias etapas. Há apenas um nível: a **última versão salva** (`_saved`).
- `undo()` descarta **todas** as alterações desde o último Salvar (ou desde a abertura), mediante confirmação Sim/Não (DT07, DT09).
- `has_changes` é verdadeiro sempre que `_data` não é o mesmo objeto de `_saved`.
- A RN02.4 prevê que o Desfazer "poderá ser ampliado" no futuro; `proximos-passos.md` lista "Desfazer de múltiplos níveis" como funcionalidade que exige regra de negócio.

**Consequências para os efeitos:**

- **[Fato]** "Não aplicar" (RN10) não pode usar o Desfazer: ele também descartaria edições confirmadas antes, o que a RN11 proíbe. A prévia precisa existir fora de `_data`.
- **[Fato]** Não há como remover um efeito específico depois de confirmado. A única forma de "remover" um eco hoje seria desfazer tudo até a versão salva.
- **[Hipótese]** As regras de incompatibilidade (RN06, RN08) exigem saber quais efeitos estão aplicados. Esse estado não existe e precisaria ser criado e mantido junto com `_data` e `_saved` (zerado no Desfazer; tratamento a definir no Salvar e ao reabrir).

---

## 6. Bibliotecas e dependências relevantes

**[Fato]** `requirements.txt`: wxPython 4.3.2, accessible_output2 0.17, soundfile 0.13.1, sounddevice 0.5.2, av 19.0.2, numpy 2.5.4.

**[Fato]** Verificado no `venv` do projeto: o FFmpeg empacotado no PyAV 19.0.2 tem os filtros `volume`, `afade`, `aecho`, `afir`, `alimiter`, `dynaudnorm` e `loudnorm`. **Não** tem filtro de reverberação pronto (`freeverb`, `areverb`). A `scipy` não está instalada.

Opções para o processamento (avaliação inicial, sem decisão):

| Opção | Nova dependência? | Cobertura | Observações |
|---|---|---|---|
| **numpy** (já usado) | Não | Volume e fades: triviais. Eco: atraso com realimentação, processado em blocos do tamanho do atraso. Reverberação: convolução por FFT (`numpy.fft`) com resposta ao impulso gerada pelo programa, ou filtros em pente processados em blocos. | Mesmo padrão de `audio_edit.py` (funções puras e testáveis). Controle total dos parâmetros e dos limites. Exige implementar e testar os algoritmos. |
| **Filtros do FFmpeg via PyAV** (`av.filter.Graph`) | Não | `volume`, `afade`, `aecho`, `alimiter`. Reverberação só com `afir` e uma resposta ao impulso fornecida. | Algoritmos prontos e mantidos. Parâmetros do `aecho` não correspondem diretamente a "milissegundos/percentual" das configurações. Exige converter o array em frames e de volta. Aumenta a superfície do FFmpeg usada pelo programa (DT08 já registra o FFmpeg como componente de risco). |
| **scipy** (`signal.lfilter`, `fftconvolve`) | **Sim** | Filtros recursivos e convolução eficientes. | Dependência grande (dezenas de MB). Pela regra do CLAUDE.md, só com justificativa técnica e aprovação. **[Hipótese]** Desnecessária para os oito efeitos iniciais. |

**[Recomendação]** Avaliar primeiro a implementação só com `numpy`, sem dependência nova, e medir o tempo de processamento com os arquivos de `tests/audios` e com um arquivo longo (por exemplo, 30 minutos). Os filtros do PyAV ficam como alternativa caso o desempenho ou a qualidade não sejam aceitáveis. A escolha final será apresentada em documento próprio, com os critérios do CLAUDE.md (seção 3.3).

---

## 7. Pontos de integração possíveis

### 7.1. Processamento — novo módulo de model

**[Recomendação]** `src/models/audio_effects.py`, com funções puras no mesmo estilo de `audio_edit.py`: recebem as amostras, a taxa e os parâmetros já validados, e devolvem um array novo, sem alterar a entrada. Testes em `tests/test_audio_effects.py`.

**[Fato]** A assinatura atual de `AudioPlayer.edit` entrega `(data, cursor, marked)`, mas não a taxa. Eco, reverberação e fades precisam da taxa para converter milissegundos ou segundos em quadros. Será preciso expor a taxa (por exemplo, uma propriedade pública) ou passá-la por fechamento (*closure*) no controller.

### 7.2. Prévia — ponto central da integração

A prévia (RN09) exige tocar um áudio que **não** é `_data`, sem alterar `_data`, o cursor nem o ponto memorizado.

**[Fato]** O `OutputCoordinator` aceita vários clientes (`_clients` é uma lista, e cada um recebe a sua saída), como já acontece com o player e os sons da interface.

Duas abordagens possíveis:

| Abordagem | Como funciona | Vantagens | Riscos |
|---|---|---|---|
| **A. Prévia dentro do `AudioPlayer`** | O player guarda um array pendente e um cursor próprio da prévia. O `audio_callback` lê do pendente enquanto a prévia está ativa. "Aplicar" promove o pendente a `_data`; "Não aplicar" o descarta. | Reaproveita a saída já aberta e a troca de dispositivo (DT10). Um único dono do estado. | Aumenta as responsabilidades do `AudioPlayer`. Exige cuidado para que o cursor e o ponto memorizado do editor não sejam alterados pela prévia. |
| **B. Cliente de prévia separado** | Um objeto próprio, registrado no `OutputCoordinator`, com seu array e seu cursor. O `AudioPlayer` só é alterado ao aplicar. | Isolamento total: a prévia não toca no estado do editor (RN09, RN10). | Abre uma segunda saída de som; cada troca de dispositivo passa a reabrir três streams. Duplica parte da lógica do player. |

**[Recomendação]** Decidir entre A e B antes do documento de arquitetura proposta. A tendência técnica é a abordagem **A**, por reaproveitar a saída e a troca de dispositivo já validadas, desde que o cursor da prévia seja separado do cursor do editor.

### 7.3. Controller e telas

- **[Fato]** O menu de efeitos já está em `editor_menu.py`; as ações serão ligadas a ele.
- **[Fato]** O retorno ao menu de efeitos depois de aplicar ou descartar (seção 2 das regras) é compatível com o comportamento atual: ao voltar de uma tela (`manager.pop`), o `EditorScreen` fecha a lista e fala de novo a pergunta do menu.
- **[Hipótese]** A tela de prévia não se encaixa em nenhuma tela existente: precisa das teclas de reprodução do `PlayerScreen` e das opções **Aplicar efeito** / **Não aplicar** de uma confirmação. Será uma tela nova, que deve seguir a DT09 (opções por extenso, letras só selecionam, Enter confirma) e a DT02 (foco no `FocusSink`).
- **[Hipótese]** Se algum efeito pedir parâmetros na hora (por exemplo, a duração do fade), o formulário pode reaproveitar `SettingsForm` com `show_tab_selector=False`, como o Fundo sonoro (`background_form.py`).

### 7.4. Configurações

- **[Fato]** Eco e reverbe já têm campos persistidos. Novos parâmetros entram em `Settings`, `RANGES`, no formulário da guia **Efeitos de áudio** e na persistência, sem mudança de formato (ver 2.4).

### 7.5. Erros, mensagens e log

- **[Fato]** Novas operações precisam de um nome em `src/models/errors.py` (título "Erro ao ..."), do contexto `operation` do log (DT11) e das mensagens nas tabelas da DT05, seguindo as regras de redação (motivo + o que fazer).

### 7.6. Expansão para novos efeitos

As regras preveem novos efeitos no futuro (seção 1 de `regras_negocio_efeitos.md`).

- **[Fato]** Os menus já são declarativos: um efeito novo no menu é só mais um `MenuItem`, com letra única verificada ao montar o menu.
- **[Hipótese]** Sem uma descrição comum dos efeitos, cada efeito novo exigiria mexer em vários pontos: menu, função de processamento, parâmetros, regras de incompatibilidade, mensagens e prévia.
- **[Recomendação]** Avaliar, no documento de arquitetura proposta, uma definição única por efeito (nome, letra, função de processamento, origem dos parâmetros, grupo de incompatibilidade), da qual o menu e a prévia seriam montados. A definição deve continuar simples (uma lista, como os menus), sem mecanismo de plugins, para não acrescentar complexidade desnecessária (CLAUDE.md, seção 8).

### 7.7. Testes

- **[Fato]** `tests/gerar_audios.py` gera arquivos de 30 s em todos os formatos. Os testes atuais de edição usam arrays sintéticos (`frames`, `quiet`), o que serve também aos efeitos (pico, duração, ausência de NaN, entrada não alterada).

---

## 8. Limitações e riscos técnicos

### 8.1. Processamento na thread da interface e dentro da trava

- **[Fato]** `apply` roda na thread do wx, e `player.edit` executa a operação **segurando a trava** que o `audio_callback` também usa.
- **[Hipótese]** Para remover ou misturar, o custo é pequeno. Reverberação e eco em arquivos longos podem levar segundos. Durante esse tempo, a interface e as falas do programa ficam paradas, e a thread de áudio fica bloqueada na trava (o que pode afetar inclusive os sons da interface, se compartilharem o mesmo ciclo do PortAudio).
- **[Recomendação]** Calcular o efeito **fora** da trava (a entrada não é alterada), e só substituir o array dentro dela. Medir o tempo antes de decidir se é preciso uma thread de trabalho com aviso falado ("Processando...") e limite de tempo, como pede a seção 6 do CLAUDE.md.

### 8.2. Memória

- **[Fato]** O limite considera só a versão salva e a atual.
- **[Hipótese]** Prévia + atual + salva pode chegar a três vezes o tamanho do áudio. A convolução por FFT de um arquivo inteiro usa arrays complexos de 64 bits e pode, sozinha, ocupar várias vezes o tamanho do áudio; processar em blocos (*overlap-add*) evita isso.
- **[Recomendação]** Incluir a prévia e a memória de trabalho do efeito na verificação do limite, com a mesma mensagem já usada (DT05).

### 8.3. Clipping

- **[Fato]** O Fundo sonoro limita a soma com `np.clip` (`audio_edit.py:79`), e o Salvar também (`audio_save.py:50`). Esse corte é, por definição, clipping.
- **[Fato]** RN01 e RN12 proíbem clipping e distorção digital. Aumento de volume, eco e reverberação somam energia e podem ultrapassar 1,0.
- **[Hipótese]** `np.clip` não atende às regras para os efeitos. Será preciso limitar o ganho pelo pico do áudio (aumento de volume), reduzir a mistura do efeito ou normalizar o resultado. Cada opção altera o som de forma diferente e é uma decisão do responsável (seção 9).

### 8.4. Estabilidade numérica

- **[Hipótese]** Eco com realimentação e reverberação recursiva podem divergir se o ganho de realimentação chegar a 1 (100%). Os parâmetros precisam ser limitados abaixo disso e o resultado conferido (sem NaN nem infinito) antes de ser aceito, atendendo à RN12 ("operações incompletas não podem ser confirmadas").

### 8.5. Estado dos efeitos aplicados

- **[Fato]** O áudio não carrega metadados. Ao salvar e reabrir, o programa não tem como saber que o arquivo já tem eco ou reverberação.
- **[Hipótese]** As regras de incompatibilidade (RN06, RN08) só podem ser aplicadas dentro da sessão de edição, a partir de um registro mantido pelo programa. Um arquivo que já chegou com eco não será detectado.

### 8.6. Ponto memorizado e cursor

- **[Fato]** `edit` sempre apaga o ponto memorizado (DT07: "a posição dele deixa de corresponder ao mesmo trecho do som"). Volume e fades não mudam a duração; eco e reverberação podem mudar, se a cauda for acrescentada.
- **[Fato]** Hoje o cursor e o ponto memorizado são o mesmo estado usado pelo player. Uma prévia que use esse cursor alteraria o ponto de edição (contrário à RN09).

### 8.7. Volume de reprodução × volume do áudio

- **[Fato]** F3/F4 no player alteram só o volume de **reprodução** (`AudioPlayer.volume`), sem mudar as amostras. RN01 e RN02 alteram as **amostras**.
- **[Hipótese]** Os dois conceitos podem ser confundidos pelo usuário, inclusive na prévia (que também toca com o volume de reprodução). Os textos de ajuda e as mensagens precisarão diferenciá-los.

### 8.8. Segurança

- **[Fato]** Os efeitos operam sobre amostras já validadas na abertura (DT08). Não há arquivos novos, nem comandos externos, nem `shell=True`.
- **[Hipótese]** Os riscos são de recursos (memória e tempo em arquivos longos) e de valores inválidos vindos de `settings.dat`. A validação de `settings_from` já recusa valores fora de `RANGES`, mas o model do efeito deve validar de novo, como `overlay` faz com os volumes.
- **[Recomendação]** Se os filtros do PyAV forem usados, registrar o aumento do uso do FFmpeg nos riscos da DT08.

### 8.9. Inconsistências documentais encontradas

- **[Fato]** A DT07 não lista o menu de efeitos.
- **[Fato]** A frase "Os efeitos serão aplicados ao áudio quando as operações de edição forem implementadas" em `docs/regras_negocio.md` ficará desatualizada.
- **[Fato]** As regras de efeitos citam "intensidade e duração" do eco e da reverberação; as configurações têm "milissegundos" e "percentual". A correspondência não está escrita em nenhum documento.
- **[Fato]** `RANGES` permite 0% em `echo_percent` e `reverb_percent`. RN05 e RN07 recusam zero "quando as configurações determinarem um valor mínimo superior a zero" — hoje o mínimo é 0, então um eco de 0% (sem efeito audível) é aceito pelas regras atuais.

---

## 9. Questões para decisão do responsável pelo projeto

### Geral

1. **Prévia:** qual trecho é tocado? O áudio inteiro desde o início, a partir do cursor, ou um trecho de duração fixa? (Para o fade out, o efeito só é ouvido no final.)
2. **Teclas da prévia:** quais controles de reprodução estarão disponíveis (Espaço, setas, Home/End, F2, F3/F4)? Esc equivale a **Não aplicar**? Qual opção vem selecionada ao abrir (pela DT09, a mais segura seria **Não aplicar**)?
3. **Conclusão:** ao aplicar, o programa mostra a caixa de conclusão (como nas demais edições) ou apenas fala a confirmação, antes de voltar ao menu de efeitos?
4. **Abordagem da prévia:** A (dentro do `AudioPlayer`) ou B (cliente separado), conforme a seção 7.2.
5. **Letras do menu de efeitos:** as oito letras, incluindo Fade in e Fade out (hoje: A, D, E, S, R, X), e os rótulos definitivos.
6. **Ponto memorizado:** efeitos que não mudam a duração devem preservar o ponto memorizado, ou seguem a regra atual de apagá-lo?
7. **Duração:** eco e reverberação acrescentam a cauda ao final do áudio (aumentando a duração) ou cortam no tamanho original? As regras só proíbem mudar a duração nos fades.

### Volume (RN01 e RN02)

8. **Significado de "incrementos de 25%":** cada aplicação multiplica o áudio atual por 1,25 (e por 0,75 na diminuição), ou o passo é de 25 pontos sobre o volume original (125%, 150%...; 75%, 50%, 25%)?
9. **Passos na prévia ou por aplicação:** cada acionamento do efeito aplica um passo, ou a prévia permite subir e descer o nível antes de aplicar?
10. **Limite máximo:** fixo (por exemplo, 200%) ou o maior ganho que não provoca clipping no pico do áudio? Se o áudio já estiver no pico máximo, o aumento é recusado com mensagem?
11. **Limite mínimo:** qual valor (por exemplo, 25%) evita o "silêncio absoluto"?
12. **Referência do limite:** o limite vale em relação ao arquivo aberto (exige guardar o nível acumulado) ou é calculado a partir do áudio atual (sem estado)?

### Fades (RN03 e RN04)

13. **Onde a duração é definida:** em um formulário ao acionar o efeito, ou em novos campos da guia **Efeitos de áudio**? Qual faixa e qual padrão?
14. **Posição:** fade in sempre no início e fade out sempre no fim, ou a partir do cursor?
15. **Duração maior que o áudio:** recusar, ou ajustar à duração do áudio?
16. **Curva:** linear ou outra (logarítmica soa mais natural)?

### Eco e reverberação (RN05 a RN08)

17. **Correspondência dos parâmetros:** "Milissegundos" é o intervalo entre as repetições (eco) e o pré-atraso ou o tempo de decaimento (reverbe)? "Percentual" é a intensidade das repetições, a realimentação ou a proporção entre som original e efeito?
18. **Parâmetros do Super eco e da Super reverberação:** derivados dos valores das configurações (por exemplo, um multiplicador), valores fixos do programa, ou novos campos nas configurações?
19. **Percentual 0%:** deve ser recusado ao aplicar o efeito (sem efeito audível), ou o mínimo de `RANGES` deve subir?
20. **Incompatibilidades:** Eco sobre Eco e Reverberação sobre Reverberação também são proibidos, ou só o Super sobre um efeito já aplicado (como está escrito em RN06 e RN08)? Eco e reverberação podem ser combinados entre si?
21. **"Removido ou substituído":** como o usuário remove ou substitui um eco já aplicado? Pelo Desfazer atual (que descarta todas as alterações desde o último Salvar), por uma nova opção de substituição, ou por um desfazer de vários níveis (que exigiria nova regra de negócio)?
22. **Depois de salvar:** o registro de efeitos aplicados continua valendo até fechar o editor, ou é zerado ao salvar (a versão salva passa a ser a nova referência do Desfazer)?

### Qualidade e clipping (RN01 e RN12)

23. **Controle de pico:** quando eco ou reverberação ultrapassarem o limite, o programa deve reduzir automaticamente o volume do resultado (normalizar), reduzir só a intensidade do efeito, ou recusar a aplicação?

### Técnicas

24. **Biblioteca:** aprovar a avaliação inicial só com `numpy` (sem dependência nova), com os filtros do PyAV como alternativa (seção 6).
25. **Processamento demorado:** aceitar, como primeira medida, a medição de tempo antes de decidir sobre thread de trabalho e limite de tempo (seção 8.1)?

---

## 10. Resumo

- O áudio em edição é um único array `float32` estéreo no `AudioPlayer`, editado por funções puras de `audio_edit.py` através de `AudioPlayer.edit`. Os efeitos se encaixam naturalmente nesse padrão, num módulo novo de model.
- O Desfazer tem um único nível (a última versão salva). Não serve para "Não aplicar" e não permite remover um efeito específico.
- A prévia é a principal mudança de arquitetura: exige tocar um áudio pendente sem alterar `_data`, o cursor nem o ponto memorizado.
- Não há registro dos efeitos aplicados; as incompatibilidades das RN06 e RN08 exigem criá-lo e valem só dentro da sessão.
- As regras proíbem clipping, mas o projeto hoje limita a soma com `np.clip`; os efeitos precisarão de controle de pico.
- `numpy` e os filtros do FFmpeg já instalados cobrem os oito efeitos sem dependência nova; reverberação não tem filtro pronto no FFmpeg empacotado.
- O processamento atual é síncrono, na thread da interface e dentro da trava do áudio; efeitos longos podem travar a interface e a reprodução.
- Vários parâmetros das regras (passos e limites de volume, duração dos fades, parâmetros dos modos Super, trecho da prévia) precisam de decisão antes do projeto da solução.
