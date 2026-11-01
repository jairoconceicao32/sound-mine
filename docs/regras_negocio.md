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

**Opções disponíveis:**

**Idioma:** Define o idioma utilizado na interface do programa.

**Formato do arquivo:** Define o formato de áudio utilizado para salvar o arquivo após a edição.

Formatos previstos:

- MP3
- M4A
- WAV
- OGG

**Qualidade do áudio:** Permite definir a qualidade do áudio que será salvo.

Opções previstas:

- DVD
- Rádio
- CD

**Canais de áudio:** Permite definir a configuração dos canais de áudio.

Opções disponíveis:

- Estéreo
- Mono

**Salvar configurações:** Aplica e salva as configurações selecionadas pelo usuário.

**Cancelar:** Cancela as alterações realizadas nas configurações.

**Fechar:** Fecha o programa.

#### Critérios de aceitabilidade

- O programa deverá permitir a seleção do idioma disponível.
- O programa deverá permitir a seleção de um formato de áudio suportado para salvar o arquivo.
- O programa deverá permitir a seleção da qualidade do áudio.
- O programa deverá permitir a seleção entre Mono e Estéreo.
- A opção **Salvar configurações** deverá aplicar e salvar as alterações realizadas.
- A opção **Cancelar** deverá descartar as alterações realizadas durante a configuração.
- A opção **Fechar** deverá encerrar o programa.

#### Critérios de não aceitabilidade

- O programa não deverá permitir a seleção de formatos não suportados.
- O programa não deverá aplicar configurações inválidas.
- A opção **Cancelar** não deverá aplicar as alterações realizadas durante a configuração.
- O programa não deverá apresentar as configurações como salvas caso a operação de salvamento não tenha sido concluída.

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

Cada funcionalidade deverá apresentar suas respectivas opções de edição.

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

As funcionalidades de edição também deverão permanecer acessíveis durante a utilização do mini player, respeitando o comportamento definido para cada operação.

#### Critérios de aceitabilidade

- O programa deverá reproduzir arquivos de áudio válidos.
- O arquivo deverá estar em um formato suportado pelo Sound Mine.
- A reprodução deverá funcionar utilizando a opção Tocar arquivo do menu.
- O atalho `T` deverá executar a mesma ação disponível no menu.
- O mini player deverá permitir a reprodução do arquivo aberto.
- O usuário deverá conseguir acessar os controles disponíveis no mini player.

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

A confirmação deverá ser navegável por letras, seguindo o estilo de navegação do DOSVOX.

O programa deverá apresentar uma caixa de diálogo sinalizando a confirmação da operação.

A funcionalidade poderá ser ampliada para permitir desfazer outras modificações em futuras versões do Sound Mine.

#### Critérios de aceitabilidade

- O programa deverá permitir desfazer alterações realizadas durante a edição de arquivos de áudio válidos.
- O arquivo deverá estar em um formato suportado pelo Sound Mine.
- A opção **Desfazer** deverá apresentar um menu de confirmação.
- O menu de confirmação deverá permitir selecionar Sim ou Não por letras.
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

### Letras dos menus

As letras utilizadas nos menus deverão permitir acessar e executar as funcionalidades de edição disponíveis no Sound Mine.

### Setas do teclado

As setas do teclado também poderão ser utilizadas para acessar e navegar pelas opções disponíveis.

Durante a utilização das setas para acessar as opções de edição, a reprodução do áudio será interrompida automaticamente.

A possibilidade de interromper automaticamente a reprodução durante a navegação poderá ser revisada posteriormente, caso seja identificada uma dificuldade de utilização por parte dos usuários.

#### Critérios de aceitabilidade

- O mini player deverá disponibilizar os controles de reprodução previstos.
- O atalho `F1` deverá apresentar a ajuda com as opções disponíveis no programa.
- O atalho `F2` deverá apresentar informações sobre o tempo de reprodução.
- Os atalhos `F3` e `F4` deverão permitir controlar o volume do áudio.
- As letras dos menus deverão permitir acessar as funcionalidades de edição.
- As setas do teclado deverão permitir navegar pelas opções disponíveis.
- A utilização das setas para acessar as opções de edição deverá interromper automaticamente a reprodução do áudio.
- O usuário deverá conseguir acessar os controles previstos durante a utilização do mini player.

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