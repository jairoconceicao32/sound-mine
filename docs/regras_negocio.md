# Sound Mine

# Regras de Negócio — Primeira Versão do Protótipo

Este documento apresenta as regras de negócio e os critérios de aceitabilidade e não aceitabilidade definidos para a primeira versão do protótipo do Sound Mine.

---

## RN01 — Menu principal

O menu principal do Sound Mine terá as seguintes opções:

### 1. Abrir arquivo

Permite abrir um arquivo de áudio para edição.

**Formatos suportados:**

- MP3
- M4A
- WAV
- OGG

Ao selecionar a opção **Abrir arquivo**, o programa utilizará o próprio Explorador de Arquivos do Windows para que o usuário localize e selecione o arquivo desejado.

Após a abertura de um arquivo válido, o programa apresentará as opções de edição disponíveis.

A navegação seguirá o estilo do DOSVOX, permitindo acessar as opções por letras.

Ao utilizar as setas do teclado, será possível visualizar e navegar pelas opções disponíveis no menu de edição.

**Atalhos:**

- `F1`: Exibe uma ajuda com as opções disponíveis no programa.
- `Espaço`: Reproduz ou pausa o arquivo de áudio.

#### Critérios de aceitabilidade

- O programa deverá permitir a abertura de arquivos nos formatos suportados.
- O usuário deverá conseguir localizar e selecionar arquivos utilizando o Explorador de Arquivos do Windows.
- O arquivo selecionado deverá ser válido e estar em um formato compatível com o Sound Mine.
- Após a abertura de um arquivo válido, o programa deverá disponibilizar o menu de edição.
- O atalho `F1` deverá apresentar uma ajuda com as opções disponíveis.
- O atalho `Espaço` deverá reproduzir ou pausar o arquivo de áudio.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a abertura de arquivos corrompidos.
- Caso seja detectado um arquivo corrompido, o programa deverá apresentar uma mensagem informando o erro.
- Caso o arquivo esteja em um formato não suportado, o programa deverá informar que o formato é inválido ou não suportado.
- O programa não deverá disponibilizar as funcionalidades de edição caso não exista um arquivo de áudio válido aberto.

---

### RN01.1 — Configurações do programa

Nesta opção, o usuário poderá definir as configurações gerais do Sound Mine.

As configurações são organizadas em guias, no mesmo estilo do Over Drive. Ao final de todas as guias ficam as opções **Salvar configurações** e **Cancelar**.

Nesta versão do protótipo, as configurações ficam guardadas apenas enquanto o programa está aberto. Ainda não existe arquivo de configurações: ao abrir o programa, todos os valores voltam ao padrão.

#### Navegação

- `Tab` e `Shift+Tab`: passam pelos campos da guia atual e pelas opções Salvar configurações e Cancelar. Não há navegação circular.
- O primeiro campo é o seletor de guias. Nele, as setas para cima e para baixo trocam de guia.
- `Ctrl+Tab` e `Ctrl+Shift+Tab`: trocam de guia a partir de qualquer campo.
- Nos campos de lista, as setas para cima e para baixo trocam o valor.
- `Enter`: ativa Salvar configurações ou Cancelar.
- `Esc`: cancela as configurações e volta ao menu principal.

#### Guia Geral

| Campo | Tipo | Opções | Padrão |
|---|---|---|---|
| Idioma | Lista | Português, inglês, espanhol | Português |
| Formato de áudio que o arquivo será salvo | Lista | mp3, m4a, wav, ogg | mp3 |
| Tipo de canal que o arquivo será salvo | Lista | Estéreo, Mono | Estéreo |
| Taxa de amostragem que o áudio será salvo | Lista | 44100, 48000, 96000 | 44100 |
| Desativar sons da interface | Caixa de seleção | Marcada ou não marcada | Não marcada |
| Desativar dicas do programa | Caixa de seleção | Marcada ou não marcada | Não marcada |

- **Formato de áudio que o arquivo será salvo:** define o formato de áudio utilizado para salvar o arquivo após a edição.
- **Tipo de canal que o arquivo será salvo:** define se o arquivo será salvo em Estéreo ou Mono.
- **Taxa de amostragem que o áudio será salvo:** define a taxa de amostragem, em hertz, do arquivo salvo. Substitui a opção **Qualidade do áudio** (DVD, Rádio, CD) prevista inicialmente.
- **Desativar sons da interface:** quando marcada, os sons de navegação, confirmação e fechamento deixam de tocar. O som de abertura sempre toca, porque acontece antes de as configurações poderem ser alteradas.
- **Desativar dicas do programa:** quando marcada, os menus falam apenas o título ao abrir (por exemplo, "Menu principal"), sem a explicação de navegação.
- **Idioma:** inglês e espanhol ainda não têm tradução; a escolha é guardada, mas a interface continua em português.

#### Guia Efeitos de áudio

| Campo | Tipo | Faixa | Padrão |
|---|---|---|---|
| Milissegundos para o eco | Caixa de edição | 10 a 2000 | 300 |
| Percentual do eco | Controle deslizante | 0 a 100% | 75% |
| Milissegundos para o reverbe | Caixa de edição | 10 a 2000 | 200 |
| Percentual do reverbe | Controle deslizante | 0 a 100% | 80% |

Os efeitos serão aplicados ao áudio quando as operações de edição forem implementadas.

#### Guia Desempenho

| Campo | Tipo | Faixa | Padrão |
|---|---|---|---|
| Memória em megabytes | Caixa de edição | 0 a 4096 (0 = Automático) | 0 (Automático) |
| Buffers para tocar | Caixa de edição | 1 a 32 | 4 |
| Buffers para gravar | Caixa de edição | 1 a 32 | 4 |

#### Tipos de campo

- **Lista:** as setas para cima e para baixo trocam o valor.
- **Caixa de edição:** o valor é digitado. Aceita apenas números. `Backspace` e `Delete` apagam, e o leitor de tela informa "em branco" quando o campo fica vazio. `Tab`, `Shift+Tab`, `Ctrl+Tab` ou `Enter` confirmam o valor. `Esc` desfaz a edição; um segundo `Esc` cancela as configurações.
- **Controle deslizante:** as setas mudam o valor de 5 em 5, `Page Up` e `Page Down` de 10 em 10, e `Home` e `End` levam ao mínimo e ao máximo.
- **Caixa de seleção:** `Espaço` marca e desmarca.

#### Opções

**Salvar configurações:** aplica e guarda as configurações, volta ao menu principal e informa "Configurações salvas.".

**Cancelar:** descarta as alterações e volta ao menu principal.

#### Critérios de aceitabilidade

- O programa deverá permitir a seleção do idioma disponível.
- O programa deverá permitir a seleção de um formato de áudio suportado para salvar o arquivo.
- O programa deverá permitir a seleção da taxa de amostragem.
- O programa deverá permitir a seleção entre Mono e Estéreo.
- O programa deverá permitir digitar os valores das caixas de edição e ajustar os controles deslizantes dentro das faixas definidas.
- O programa deverá permitir desativar os sons da interface e as dicas do programa.
- O usuário deverá conseguir navegar entre as guias e os campos usando apenas o teclado.
- O leitor de tela deverá anunciar o nome, o tipo e o valor de cada campo.
- A opção **Salvar configurações** deverá aplicar e guardar as alterações realizadas.
- A opção **Cancelar** e a tecla `Esc` deverão descartar as alterações realizadas durante a configuração.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a seleção de formatos não suportados.
- O programa não deverá aplicar configurações inválidas.
- O programa não deverá aceitar valores fora da faixa ou que não sejam números. Nesse caso, deverá informar "Valor inválido", manter o valor anterior e permanecer no campo.
- A opção **Cancelar** não deverá aplicar as alterações realizadas durante a configuração.
- O programa não deverá apresentar as configurações como salvas caso a operação de salvamento não tenha sido concluída.
- O título do programa não deverá ser falado ao navegar entre os campos.

---

## RN02 — Menu de edição

O menu de edição será apresentado após a abertura de um arquivo de áudio válido.

Nesse menu, o usuário terá acesso às funcionalidades de edição disponíveis no Sound Mine.

As opções disponíveis deverão permitir a navegação por letras, seguindo o estilo do DOSVOX.

Ao utilizar as setas do teclado, será possível visualizar e navegar pelas opções disponíveis no menu.

**Funcionalidades previstas:**

1. Tocar arquivo.
2. Remover partes do áudio.
3. Misturar arquivos de áudio.
4. Desfazer alterações.
5. Salvar arquivo.

Cada funcionalidade deverá apresentar suas respectivas opções de edição.

Ao fechar o editor com a tecla `Esc` ou com `Alt+F4`, caso existam alterações não salvas, o programa deverá apresentar a confirmação **Sair do editor**, com as opções:

- **Salvar e sair:** salva as alterações e fecha o editor somente depois que o salvamento for concluído com sucesso. Se o salvamento for cancelado ou falhar, o editor continua aberto, com as alterações preservadas, e o usuário é informado.
- **Sair sem salvar:** descarta as alterações e fecha o editor.
- **Cancelar:** cancela o fechamento e volta ao editor, preservando as alterações.

Pelo `Esc`, fechar o editor volta ao menu principal. Pelo `Alt+F4`, fecha o programa. Sem alterações não salvas, o editor fecha diretamente, sem confirmação.

Todas as confirmações do programa apresentam as opções por extenso. As letras apenas selecionam a opção correspondente, sem executá-la; a resposta é dada com `Enter`. Os atalhos por letras do editor continuam executando as funcionalidades normalmente.

#### Critérios de aceitabilidade

- O programa deverá apresentar o menu de edição após a abertura de um arquivo válido.
- O menu deverá disponibilizar as funcionalidades previstas nesta regra.
- O usuário deverá conseguir acessar as opções utilizando letras.
- O usuário deverá conseguir navegar pelas opções utilizando as setas do teclado.
- As funcionalidades deverão executar as ações correspondentes às opções selecionadas.

#### Critérios de não aceitabilidade

- O programa não deverá disponibilizar o menu de edição caso não exista um arquivo de áudio válido aberto.
- O programa não deverá executar funcionalidades de edição sobre arquivos inválidos.
- O programa não deverá executar uma operação diferente daquela selecionada pelo usuário.

---

### RN02.1 — Tocar arquivo

Permite reproduzir o arquivo de áudio aberto no programa.

**Atalho:**

- `T`: Executa a mesma ação disponível na opção Tocar arquivo do menu de edição.

O Sound Mine contará com um mini player para reprodução do arquivo de áudio.

Durante a reprodução, o usuário poderá acessar os controles disponíveis no mini player.

Ao selecionar **Tocar arquivo**, o programa abre o mini player e inicia a reprodução.

Enquanto o mini player estiver aberto, o menu de edição fica bloqueado, seguindo o estilo do DOSVOX. A tecla `Esc` pausa a reprodução e volta ao menu de edição, que pergunta novamente "Qual sua opção?".

#### Critérios de aceitabilidade

- O programa deverá reproduzir arquivos de áudio válidos.
- O arquivo deverá estar em um formato suportado pelo Sound Mine.
- A reprodução deverá funcionar utilizando a opção Tocar arquivo do menu.
- O atalho `T` deverá executar a mesma ação disponível no menu.
- O mini player deverá permitir a reprodução do arquivo aberto.
- O usuário deverá conseguir acessar os controles disponíveis no mini player.
- O menu de edição deverá ficar bloqueado enquanto o mini player estiver aberto.

#### Critérios de não aceitabilidade

- O programa não deverá reproduzir arquivos corrompidos.
- Caso o arquivo não seja válido, o programa deverá informar o erro ao usuário.
- O programa não deverá iniciar a reprodução caso não exista um arquivo de áudio válido aberto.
- O atalho `T` não deverá iniciar a reprodução de um arquivo inválido.

---

### RN02.2 — Remover partes do áudio

A opção **Remover** permitirá excluir partes específicas do arquivo de áudio aberto.

O usuário poderá selecionar uma das seguintes opções:

- **Antes do cursor:** Remove o trecho do áudio que está antes da posição atual do cursor.
- **Depois do cursor:** Remove o trecho do áudio que está depois da posição atual do cursor.
- **Entre o cursor e o ponto memorizado:** Remove o trecho compreendido entre a posição atual do cursor e o ponto previamente memorizado.

A operação deverá respeitar a posição atual do cursor e, quando necessário, o ponto memorizado.

#### Critérios de aceitabilidade

- O programa deverá permitir a remoção de trechos de arquivos de áudio válidos.
- O arquivo deverá estar em um formato suportado pelo Sound Mine.
- O usuário deverá conseguir posicionar o cursor para definir o trecho que deseja remover.
- A opção **Antes do cursor** deverá remover o trecho anterior à posição atual do cursor.
- A opção **Depois do cursor** deverá remover o trecho posterior à posição atual do cursor.
- A opção **Entre o cursor e o ponto memorizado** deverá remover o trecho compreendido entre as duas posições.
- A operação deverá respeitar a posição do cursor e o ponto memorizado, conforme a opção selecionada.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a remoção de trechos de arquivos em formatos inválidos ou não suportados.
- O programa não deverá permitir a remoção caso não exista um arquivo de áudio válido aberto.
- Caso o cursor não esteja em uma posição válida para a operação selecionada, o programa deverá informar que a operação não pode ser realizada.
- Caso não exista um ponto memorizado para a operação **Entre o cursor e o ponto memorizado**, o programa deverá informar que a operação não pode ser realizada.
- O programa não deverá executar a remoção caso não seja possível identificar corretamente o trecho selecionado.

---

### RN02.3 — Misturar arquivos de áudio

A opção **Misturar** permitirá adicionar outro arquivo de áudio ao arquivo que está sendo editado.

O usuário poderá escolher entre as seguintes funcionalidades:

#### 3.1. Adição de áudio

Permite adicionar outro arquivo de áudio ao arquivo atual.

**Opções disponíveis:**

- **No início:** Adiciona o arquivo selecionado ao início do áudio que está sendo editado.
- **No cursor:** Adiciona o arquivo selecionado na posição atual do cursor.
- **No final:** Adiciona o arquivo selecionado ao final do áudio que está sendo editado.

A operação deverá respeitar a posição selecionada pelo usuário.

#### 3.2. Fundo sonoro

Permite adicionar outro arquivo de áudio como música de fundo ao arquivo que está sendo editado.

O usuário poderá definir a porcentagem de volume de cada arquivo:

- Volume do áudio que está sendo editado.
- Volume do arquivo que será adicionado como fundo sonoro.

A funcionalidade deverá permitir ajustar o volume dos dois arquivos para definir o resultado da mistura.

Os volumes são definidos em um formulário com dois controles deslizantes, navegados por `Tab` e `Shift+Tab`: **Volume do áudio original** (padrão 100%) e **Volume da música de fundo** (padrão 30%), seguidos das opções **Adicionar fundo sonoro** e **Cancelar**.

O fundo sonoro poderá ser adicionado nas seguintes posições:

- No início.
- No cursor.
- No final.

A operação deverá respeitar a posição selecionada pelo usuário.

#### Critérios de aceitabilidade

- O programa deverá permitir a adição de arquivos de áudio válidos.
- Os arquivos utilizados deverão estar em formatos suportados pelo Sound Mine.
- O usuário deverá conseguir selecionar o arquivo que deseja adicionar.
- A opção **No início** deverá adicionar o arquivo selecionado ao início do áudio que está sendo editado.
- A opção **No cursor** deverá adicionar o arquivo selecionado na posição atual do cursor.
- A opção **No final** deverá adicionar o arquivo selecionado ao final do áudio que está sendo editado.
- A funcionalidade **Fundo sonoro** deverá permitir a seleção de um arquivo de áudio para ser utilizado como música de fundo.
- O usuário deverá conseguir definir o volume do áudio que está sendo editado.
- O usuário deverá conseguir definir o volume do arquivo que será adicionado como fundo sonoro.
- A mistura deverá respeitar os volumes definidos pelo usuário.
- A adição de áudio e o fundo sonoro deverão respeitar a posição selecionada.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a adição de arquivos em formatos inválidos ou não suportados.
- O programa não deverá permitir a mistura caso não exista um arquivo de áudio válido aberto.
- Caso o arquivo selecionado para adição esteja corrompido, o programa deverá informar o erro.
- Caso não seja possível identificar uma posição válida para a adição, o programa deverá informar que a operação não pode ser realizada.
- O programa não deverá executar a mistura caso os arquivos selecionados não sejam válidos.
- O programa não deverá aplicar a mistura caso os volumes definidos sejam inválidos.

---

### RN02.4 — Desfazer alterações

A opção **Desfazer** permitirá recuperar a última versão salva do arquivo de áudio.

A funcionalidade deverá permitir desfazer alterações realizadas durante a edição.

O usuário deverá conseguir acessar a opção Desfazer pelo menu de edição.

Antes de executar a operação, o programa deverá apresentar um menu de confirmação com as opções **Sim** e **Não**.

A confirmação deverá apresentar as opções por extenso. As setas e as letras selecionam a opção, sem executá-la, e o `Enter` confirma a opção selecionada.

O programa deverá apresentar uma caixa de diálogo sinalizando a confirmação da operação.

Enquanto o arquivo não tiver sido salvo, a última versão salva é o arquivo como foi aberto.

A funcionalidade poderá ser ampliada para permitir desfazer outras modificações em futuras versões do Sound Mine.

#### Critérios de aceitabilidade

- O programa deverá permitir desfazer alterações realizadas durante a edição de arquivos de áudio válidos.
- O arquivo deverá estar em um formato suportado pelo Sound Mine.
- A opção **Desfazer** deverá apresentar um menu de confirmação.
- O menu de confirmação deverá permitir selecionar Sim ou Não pelas setas ou por letras, sem que a letra execute a opção.
- O programa deverá apresentar uma caixa de diálogo informando a operação.
- Caso o usuário confirme a operação, o programa deverá recuperar a última versão salva do arquivo.
- Caso o usuário selecione Não, a operação deverá ser cancelada.
- A funcionalidade deverá permitir a recuperação da versão salva do arquivo.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a operação caso o arquivo esteja em um formato inválido ou não suportado.
- O programa não deverá executar a operação caso não exista um arquivo de áudio válido aberto.
- Caso o usuário selecione Não, o programa não deverá recuperar a versão salva.
- O programa não deverá apresentar a operação como concluída caso a recuperação do arquivo não tenha sido realizada.
- O programa deverá informar ao usuário caso não seja possível recuperar a versão salva.

---

### RN02.5 — Salvar arquivo

A opção **Salvar** (letra `S`) grava o áudio editado em um arquivo.

O programa abre a janela de salvar do Windows, na pasta do arquivo aberto, propondo o nome do arquivo seguido de `_editado`.

O arquivo é salvo no formato, no tipo de canal e na taxa de amostragem definidos nas **Configurações**. Se o formato não aceitar a taxa configurada, o programa usa a maior taxa aceita pelo formato e informa o usuário.

Depois de salvar, a versão salva passa a ser a usada pela opção **Desfazer**.

#### Critérios de aceitabilidade

- O programa deverá salvar o áudio editado nos formatos MP3, M4A, WAV e OGG.
- O arquivo salvo deverá respeitar o formato, o tipo de canal e a taxa de amostragem das configurações.
- O programa deverá informar quando o arquivo for salvo.
- A opção **Desfazer** deverá recuperar a última versão salva.

#### Critérios de não aceitabilidade

- O programa não deverá sobrescrever um arquivo existente, inclusive o original, sem confirmação.
- O programa não deverá apresentar o arquivo como salvo caso a gravação não tenha sido concluída.
- Caso a gravação falhe, o programa deverá informar o erro e manter o arquivo de destino como estava.

---

## RN03 — Mini player

O mini player será responsável por disponibilizar os controles de reprodução do arquivo de áudio aberto no Sound Mine.

Esse mini player será composto pelos seguintes controles:

### F1 — Ajuda

Exibe uma caixa de diálogo com as opções disponíveis no programa durante a edição.

A ajuda deverá apresentar as funcionalidades disponíveis no menu de edição.

### F2 — Tempo de reprodução

Exibe informações sobre o tempo de reprodução do arquivo de áudio.

O usuário deverá conseguir consultar o tempo percorrido durante a reprodução.

### F3 e F4 — Controle de volume

Permitem controlar o volume do áudio durante a reprodução.

As opções deverão permitir aumentar e diminuir o volume do arquivo de áudio.

### Espaço — Reproduzir e pausar

Reproduz ou pausa o arquivo de áudio.

### Setas para a esquerda e para a direita — Voltar e avançar

Voltam e avançam a reprodução em 5 segundos.

### Home e End — Início e fim do som

`Home` leva ao começo do som e `End` leva ao fim do som. O leitor de tela informa "Início do som" e "Fim do som".

### M — Memorizar ponto

Memoriza a posição atual da reprodução. O leitor de tela informa "Ponto memorizado em" seguido do tempo. O ponto memorizado é usado na opção **Entre o cursor e o ponto memorizado** (RN02.2).

### Esc — Voltar ao editor

Pausa a reprodução e volta ao menu de edição. A posição em que o som parou passa a ser a posição do cursor.

### Bloqueio do menu de edição

Enquanto o mini player estiver aberto, as letras e as setas do menu de edição ficam bloqueadas, seguindo o estilo do DOSVOX.

### Troca de dispositivo de som

Quando o dispositivo de som em uso é desconectado, o Sound Mine passa automaticamente para o dispositivo padrão do Windows, tanto no player quanto nos sons da interface.

- A troca não muda o estado do player: se estava reproduzindo, continua reproduzindo a partir da mesma posição; se estava pausado, continua pausado.
- Quando o dispositivo anterior (preferencial) é reconectado, o Sound Mine volta automaticamente a ele depois de alguns segundos de conexão estável, sem alternar repetidamente quando a conexão é instável.
- Uma mudança deliberada do dispositivo padrão no Windows torna o novo dispositivo o preferencial.
- Sem nenhum dispositivo disponível, o player guarda a intenção de reproduzir ou de ficar pausado e volta a esse estado quando um dispositivo for conectado. A tela informa "Aguardando saída de som", e o `Espaço` continua alternando entre reproduzir e pausar.
- O programa anuncia o nome do dispositivo selecionado ("Saída de som: …" e "Saída de som de volta: …") ou a falta de dispositivos ("Nenhuma saída de som disponível."). A mensagem também fica escrita na janela.
- Se houver dispositivos, mas o som não puder ser iniciado, o programa informa o erro e não anuncia "Reproduzindo".

#### Critérios de aceitabilidade

- O mini player deverá disponibilizar os controles de reprodução previstos.
- O atalho `F1` deverá apresentar a ajuda com as opções disponíveis no programa.
- O atalho `F2` deverá apresentar informações sobre o tempo de reprodução.
- Os atalhos `F3` e `F4` deverão permitir controlar o volume do áudio.
- O atalho `Espaço` deverá reproduzir e pausar o áudio.
- As setas para a esquerda e para a direita deverão voltar e avançar 5 segundos.
- Os atalhos `Home` e `End` deverão levar ao início e ao fim do som, com o anúncio "Início do som" e "Fim do som".
- O atalho `Esc` deverá pausar a reprodução e voltar ao menu de edição.
- O menu de edição deverá ficar bloqueado enquanto o mini player estiver aberto.
- O usuário deverá conseguir acessar os controles previstos durante a utilização do mini player.
- A desconexão do dispositivo de som não deverá interromper nem alterar o estado da reprodução, desde que exista outro dispositivo.
- O programa deverá voltar ao dispositivo preferencial quando ele for reconectado.

#### Critérios de não aceitabilidade

- O programa não deverá disponibilizar os controles de reprodução caso não exista um arquivo de áudio válido aberto.
- O programa não deverá apresentar informações incorretas sobre o tempo de reprodução.
- Os atalhos `F3` e `F4` não deverão executar ações diferentes das previstas para o controle de volume.
- O programa não deverá permitir que os controles executem operações sobre arquivos inválidos.
- Caso não seja possível apresentar as informações solicitadas, o programa deverá informar o usuário.

---

## Observações para a primeira versão do protótipo

A primeira versão do Sound Mine deverá ser desenvolvida com foco nas funcionalidades descritas neste documento.

O desenvolvimento deverá priorizar:

- Abertura de arquivos.
- Reprodução de áudio.
- Navegação acessível.
- Remoção de trechos.
- Adição e mistura de arquivos.
- Desfazer alterações.
- Configurações previstas.

Durante o desenvolvimento, poderão ser identificadas necessidades de ajustes ou melhorias.

Essas alterações deverão ser avaliadas antes de serem incorporadas às regras de negócio.

O objetivo é construir um protótipo funcional que permita validar as funcionalidades previstas, mantendo a proposta de um editor de áudio simples, acessível e com navegação inspirada no DOSVOX.