# Regras de negócio — Sistema de efeitos de áudio do Sound Mine

## 1. Objetivo

Definir as regras de negócio e os critérios de funcionamento do sistema de efeitos de áudio do Sound Mine.

Inicialmente, o sistema será composto pelos seguintes efeitos:

1. Aumento de volume;
2. Diminuição de volume;
3. Fade in;
4. Fade out;
5. Eco;
6. Super eco;
7. Reverberação;
8. Super reverberação.

Ao longo das atualizações do Sound Mine, novos efeitos poderão ser implementados, ampliando as possibilidades de edição de áudio.

## 2. Funcionamento geral

O menu de efeitos será acionado por meio da tecla de atalho `E`, permitindo que o usuário navegue pelas opções utilizando as setas do teclado.

Os efeitos também poderão ser acionados diretamente por teclas de atalho, seguindo o padrão de interação já utilizado nos menus do editor.

Após selecionar um efeito, o sistema deverá disponibilizar uma prévia do áudio processado, permitindo que o usuário escute o resultado antes de confirmar a alteração. O funcionamento da prévia está definido na RN09.

A interface de prévia deverá disponibilizar as seguintes opções, apresentadas quando o usuário interrompe a reprodução da prévia com a tecla `Esc` (RN09):

- **Aplicar efeito:** confirma a operação e incorpora o efeito ao áudio em edição.
- **Não aplicar:** descarta a alteração proposta, preservando o estado anterior do áudio.
- **Ouvir novamente:** volta à reprodução da prévia.

Após selecionar Aplicar efeito ou Não aplicar, o sistema deverá retornar ao menu de efeitos.

A prévia deverá ser temporária e não poderá modificar permanentemente o áudio em edição antes da confirmação do usuário.

---

## 3. Regras de negócio

### RN01 — Aumento de volume

Permite aumentar a intensidade do volume do áudio em incrementos fixos de 25 pontos percentuais, calculados em relação ao volume original do áudio, conforme a escala definida na RN13. O limite máximo inicial é de 200%.

O aumento é aplicado somente ao trecho selecionado, quando houver seleção (RN19), ou ao áudio inteiro, quando não houver.

**Critérios de aceitabilidade:**

- Permitir o aumento progressivo do volume, passando a cada aplicação para o nível seguinte da escala (RN13), até 200%.
- Utilizar como referência o volume original do áudio, e não o resultado matemático da operação imediatamente anterior.
- Estabelecer 200% como limite máximo inicial de amplificação.
- Informar ao usuário quando o limite máximo for atingido, com a mensagem "O volume máximo permitido foi atingido.", anunciada corretamente pelo NVDA.
- Fazer prevalecer a segurança do áudio sobre o limite percentual, impedindo que o aumento provoque clipping ou distorção.
- Recusar o passo de aumento que provocaria clipping, mesmo que o limite de 200% ainda não tenha sido atingido, informando ao usuário a mensagem "O volume não pode ser aumentado sem causar distorção.", anunciada corretamente pelo NVDA.
- Utilizar a mensagem "O volume máximo permitido foi atingido." somente quando o limite de 200% da escala for atingido.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir que a amplificação provoque clipping ou distorção digital decorrente da ultrapassagem dos limites de amplitude.
- Não permitir novos aumentos quando o limite máximo estabelecido for atingido.
- Não utilizar a normalização (RN17) para compensar um passo de aumento que provocaria clipping.
- Não calcular o novo nível a partir do resultado da operação anterior.

### RN02 — Diminuição de volume

Permite reduzir a intensidade do volume do áudio em incrementos fixos de 25 pontos percentuais, calculados em relação ao volume original do áudio, conforme a escala definida na RN13. O limite mínimo inicial é de 25%.

A diminuição é aplicada somente ao trecho selecionado, quando houver seleção (RN19), ou ao áudio inteiro, quando não houver.

**Critérios de aceitabilidade:**

- Permitir a redução progressiva do volume, passando a cada aplicação para o nível anterior da escala (RN13), até 25%.
- Utilizar como referência o volume original do áudio, e não o resultado matemático da operação imediatamente anterior.
- Estabelecer 25% como limite mínimo inicial de redução.
- Informar ao usuário quando o limite mínimo for atingido, com a mensagem "O volume mínimo permitido foi atingido.", anunciada corretamente pelo NVDA.

**Critérios de não aceitabilidade:**

- Não permitir que a redução de volume resulte em silêncio absoluto.
- Não permitir novas reduções quando o limite mínimo estabelecido for atingido.
- Não calcular o novo nível a partir do resultado da operação anterior.

### RN03 — Fade in

Permite aumentar gradativamente o volume do áudio a partir do silêncio até atingir o volume que o áudio possuía antes da aplicação do efeito.

Quando não houver seleção, o Fade in é aplicado desde o início do áudio. Quando houver seleção, ele é aplicado somente a partir do início do trecho selecionado.

A duração do Fade in é configurável pelo usuário e não pode ultrapassar o tamanho do trecho disponível. A forma de informar a duração e os seus limites estão definidos na RN18.

**Critérios de aceitabilidade:**

- Iniciar o efeito em silêncio, no início do áudio ou no início do trecho selecionado.
- Aumentar gradativamente o volume, ao longo da duração configurada, até atingir o volume que o áudio possuía antes do efeito.
- Manter, após o término da transição, o volume que o áudio possuía antes do efeito.
- Permitir que o usuário configure a duração do efeito.
- Respeitar o volume anterior ao efeito como limite máximo durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir que o volume ultrapasse o volume que o áudio possuía antes do efeito.
- Não permitir aumentos abruptos de volume durante a aplicação do efeito.
- Não permitir que a duração do efeito ultrapasse o tamanho do trecho disponível.
- Não alterar indevidamente a duração original do áudio.

### RN04 — Fade out

Permite reduzir gradativamente o volume do áudio até atingir o silêncio, proporcionando um encerramento suave.

Quando não houver seleção, o Fade out é aplicado ao final do áudio. Quando houver seleção, ele é aplicado somente na parte final do trecho selecionado, chegando ao silêncio no final desse trecho.

A duração do Fade out é configurável pelo usuário e não pode ultrapassar o tamanho do trecho disponível. A forma de informar a duração e os seus limites estão definidos na RN18.

**Critérios de aceitabilidade:**

- Reduzir progressivamente o volume, ao longo da duração configurada, até atingir o silêncio no final do áudio ou no final do trecho selecionado.
- Permitir que o usuário configure a duração do efeito.
- Garantir uma transição suave entre o volume original e o silêncio.
- Manter inalterado o áudio anterior ao início do Fade out.

**Critérios de não aceitabilidade:**

- Não permitir interrupções abruptas do áudio antes da conclusão do efeito.
- Não permitir aumentos de volume durante a aplicação do efeito.
- Não permitir que a duração do efeito ultrapasse o tamanho do trecho disponível.
- Não alterar indevidamente a duração original do áudio.

### RN05 — Eco

Permite adicionar repetições atrasadas do áudio original, criando a percepção de eco durante a reprodução.

O Eco pertence à família Eco, junto com o Super eco (RN14).

Os parâmetros do Eco vêm das configurações, guia **Efeitos de áudio**:

- **Milissegundos para o eco** é o intervalo entre as repetições.
- **Percentual do eco** é a mistura entre o som original e o eco. O som original continua em 100%, e o percentual é o volume das repetições somadas a ele. Com 75%, a primeira repetição tem 75% do volume original.

Cada repetição tem metade do volume da anterior, até ficar inaudível.

O eco continua soando depois do fim do som que o originou (cauda). Sem seleção, o áudio fica mais longo para a cauda terminar. Com seleção, a cauda continua sobre o áudio que vem depois do trecho, misturada a ele; se ela passar do fim do áudio, o áudio fica mais longo.

**Critérios de aceitabilidade:**

- Respeitar os parâmetros de intensidade e duração do eco.
- Usar o intervalo e o percentual definidos nas configurações, com cada repetição na metade do volume da anterior.
- Manter o som original em 100% do seu volume, somando a ele as repetições.
- Permitir que a cauda do eco termine, estendendo o áudio quando necessário.
- Respeitar os valores previamente definidos pelo usuário nas configurações do Sound Mine.
- Permitir a aplicação do efeito ao áudio em edição, somente no trecho selecionado, quando houver seleção (RN19), ou no áudio inteiro, quando não houver.
- Oferecer a substituição, conforme a RN15, quando o áudio já possuir um efeito da família Eco, inclusive o próprio Eco.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir a utilização de valores inválidos nos parâmetros do efeito.
- Não permitir que parâmetros obrigatórios recebam valores iguais a zero quando as configurações determinarem um valor mínimo superior a zero.
- Não acumular o Eco sobre outro efeito da família Eco.

### RN06 — Super eco

Permite adicionar um efeito de eco mais intenso, proporcionando maior percepção das repetições sonoras.

O Super eco pertence à família Eco, junto com o Eco (RN14).

O Super eco usa os mesmos valores das configurações do Eco, com a mesma equivalência, porém mais intenso: o percentual do eco é multiplicado por 1,5, até o limite de 100%, e cada repetição tem 70% do volume da anterior, em vez de metade, o que faz o eco durar mais. A cauda segue a mesma regra do Eco (RN05).

**Critérios de aceitabilidade:**

- Produzir um efeito de eco mais intenso que o efeito tradicional.
- Usar os valores das configurações do Eco, com o percentual multiplicado por 1,5, limitado a 100%, e cada repetição com 70% do volume da anterior.
- Respeitar os parâmetros definidos para a modalidade Super eco.
- Permitir a aplicação do efeito somente no trecho selecionado, quando houver seleção (RN19), ou no áudio inteiro, quando não houver.
- Oferecer a substituição, conforme a RN15, quando o áudio já possuir um efeito da família Eco, inclusive o próprio Super eco.
- Garantir que o processamento mantenha a estabilidade do áudio.

**Critérios de não aceitabilidade:**

- Não permitir a aplicação do Super eco sobre um áudio que já possua o efeito Eco ou Super eco aplicado, sem que o efeito anterior seja previamente removido ou substituído, conforme a RN15.
- Não permitir parâmetros inválidos durante o processamento.

### RN07 — Reverberação

Permite adicionar ao áudio a ambientação de um salão ou de uma igreja, com o som se propagando em todas as direções e uma cauda longa e envolvente.

A Reverberação pertence à família Reverberação, junto com a Super reverberação (RN14).

Os parâmetros vêm das configurações, guia **Efeitos de áudio**, e são os mesmos da Super reverberação (RN08):

- **Milissegundos para o reverbe** é a duração de referência: o tempo que a reverberação do ambiente menor (Super reverberação) leva para sumir. O padrão é de 1200 ms.
- **Percentual do reverbe** segue a mesma regra do Eco: o som original continua em 100%, e o percentual é o volume da reverberação somada a ele.

A Reverberação usa esses valores mais intensos: a duração é multiplicada por 3, e o percentual é multiplicado por 1,2, até o limite de 100%. Com o padrão de 1200 ms, a Reverberação dura 3,6 segundos. O reforço do percentual é menor que o do Super eco, porque uma cauda tão forte quanto o som original faz a reverberação soar como eco.

Como num ambiente real, o som demora alguns milésimos para voltar das paredes: há um atraso inicial proporcional ao tamanho do ambiente, de cerca de 1,5% da duração, entre 5 e 60 ms.

A cauda segue a mesma regra do Eco (RN05): sem seleção, o áudio fica mais longo para a reverberação terminar; com seleção, a cauda continua sobre o áudio seguinte e, se passar do fim, estende o áudio.

**Critérios de aceitabilidade:**

- Produzir a ambientação de um salão ou de uma igreja, mais ampla e mais intensa que a da Super reverberação.
- Usar os valores das configurações com a duração multiplicada por 3 e o percentual multiplicado por 1,2, limitado a 100%.
- Respeitar os valores previamente definidos pelo usuário nas configurações do Sound Mine.
- Permitir a aplicação do efeito ao áudio em edição, somente no trecho selecionado, quando houver seleção (RN19), ou no áudio inteiro, quando não houver.
- Oferecer a substituição, conforme a RN15, quando o áudio já possuir um efeito da família Reverberação, inclusive a própria Reverberação.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir a utilização de valores inválidos nos parâmetros do efeito.
- Não permitir que parâmetros obrigatórios recebam valores iguais a zero quando as configurações determinarem um valor mínimo superior a zero.
- Não acumular a Reverberação sobre outro efeito da família Reverberação.

### RN08 — Super reverberação

Permite adicionar uma reverberação mais simples, de um ambiente menor, como uma sala, com o mesmo caráter da Reverberação.

A Super reverberação pertence à família Reverberação, junto com a Reverberação (RN14).

A Super reverberação usa diretamente os valores das configurações, sem reforço: a duração é a de **Milissegundos para o reverbe**, e o volume é o de **Percentual do reverbe** (RN07). Com o padrão de 1200 ms, a Super reverberação dura 1,2 segundo. O atraso inicial e a cauda seguem as mesmas regras da Reverberação (RN07).

**Critérios de aceitabilidade:**

- Produzir uma reverberação de ambiente menor, mais curta que a Reverberação.
- Usar a duração e o percentual definidos nas configurações, sem reforço.
- Permitir a aplicação do efeito somente no trecho selecionado, quando houver seleção (RN19), ou no áudio inteiro, quando não houver.
- Oferecer a substituição, conforme a RN15, quando o áudio já possuir um efeito da família Reverberação, inclusive a própria Super reverberação.
- Garantir a estabilidade do processamento do áudio.

**Critérios de não aceitabilidade:**

- Não permitir a aplicação da Super reverberação sobre um áudio que já possua o efeito Reverberação ou Super reverberação aplicado, sem que o efeito anterior seja previamente removido ou substituído, conforme a RN15.
- Não permitir parâmetros inválidos durante o processamento.

---

## 4. Regras gerais do sistema de efeitos

### RN09 — Prévia dos efeitos

O sistema deverá permitir que o usuário escute o resultado de um efeito antes de confirmar sua aplicação.

A prévia respeita o estado atual do áudio no editor. Quando não houver seleção, ela reproduz o áudio inteiro com o efeito aplicado temporariamente. Quando houver seleção, ela reproduz exclusivamente o trecho selecionado, considerando o efeito aplicado sobre esse trecho. Nos efeitos com cauda, como o Eco e o Super eco, a prévia continua depois do trecho até o fim da cauda, já misturada ao áudio seguinte. O áudio original permanece preservado até que o usuário confirme explicitamente a aplicação definitiva do efeito.

Durante a prévia, são reutilizados os comandos de reprodução do player existente. A tecla `Espaço` reproduz ou pausa. A seta para a esquerda retrocede cinco segundos, e a seta para a direita avança cinco segundos. A tecla `Home` retorna ao início da prévia, e a tecla `End` avança até o final da prévia.

Quando a reprodução chegar ao final, ela para e o usuário permanece na tela de prévia, podendo reproduzi-la novamente sem precisar selecionar o efeito outra vez.

A tecla `Enter` não tem efeito durante a reprodução da prévia.

A prévia tem dois momentos: a reprodução e as opções do efeito. A tecla `Esc` é a passagem entre eles: durante a reprodução, ela interrompe a reprodução e apresenta as opções do efeito. A tecla `Esc` nunca aplica nem descarta o efeito. Essa decisão é tomada somente nas opções do efeito, pela tecla `Enter`.

Nas opções do efeito, são apresentadas as opções **Aplicar efeito**, **Não aplicar** e **Ouvir novamente**, nessa ordem. Elas seguem o padrão das confirmações do Sound Mine: as setas para cima e para baixo navegam entre as opções, as letras apenas selecionam a opção, sem executá-la, e a tecla `Enter` executa a opção selecionada. A opção **Aplicar efeito** vem selecionada ao abrir.

As opções não são apresentadas em uma caixa de diálogo. Ao abri-las, o programa fala a pergunta "Deseja aplicar o efeito *nome do efeito*?" e, em seguida, a opção selecionada. A pergunta também aparece escrita na janela.

Ao abrir a prévia, o programa fala "Prévia do efeito *nome do efeito*" e começa a reprodução. Quando a reprodução chega ao final, o programa fala "Fim da prévia".

- **Aplicar efeito** confirma a aplicação definitiva do efeito, apresenta a caixa de conclusão "Efeito *nome do efeito* aplicado." e retorna ao menu de efeitos.
- **Não aplicar** descarta o processamento temporário, preserva o áudio anterior, conforme a RN10, fala "Efeito não aplicado." e retorna ao menu de efeitos.
- **Ouvir novamente** volta à reprodução da prévia, desde o início.

Nas opções do efeito, a tecla `Enter` executa a opção selecionada. Depois de **Aplicar efeito** ou **Não aplicar**, o usuário retorna ao menu de efeitos. Nas opções do efeito, a tecla `Esc` não tem efeito.

As teclas `Tab` e `Shift+Tab` não são utilizadas como comandos para escolher entre aplicar ou não aplicar o efeito.

Quando a prévia fizer parte de uma substituição de efeitos, ela segue estas mesmas regras, com as particularidades definidas na RN15.

**Critérios de aceitabilidade:**

- Disponibilizar uma prévia do áudio processado, respeitando o estado atual do áudio em edição.
- Reproduzir o áudio inteiro, quando não houver seleção, ou exclusivamente o trecho selecionado, quando houver.
- Permitir que o usuário escute a prévia quantas vezes forem necessárias.
- Disponibilizar os comandos de reprodução `Espaço`, seta para a esquerda, seta para a direita, `Home` e `End`, reutilizados do player.
- Parar a reprodução ao chegar ao final e permanecer na tela de prévia.
- Interromper a reprodução e apresentar as opções do efeito quando o usuário pressionar `Esc` durante a reprodução.
- Apresentar as opções Aplicar efeito, Não aplicar e Ouvir novamente, no padrão das confirmações do Sound Mine, com Aplicar efeito selecionada ao abrir.
- Executar a opção selecionada pela tecla `Enter`, nas opções do efeito, e retornar ao menu de efeitos depois de Aplicar efeito ou Não aplicar.
- Permitir voltar à reprodução da prévia pela opção Ouvir novamente.
- Garantir que o foco e as mensagens sejam corretamente apresentados pelo leitor de tela NVDA.

**Critérios de não aceitabilidade:**

- Não modificar permanentemente o áudio antes da confirmação do usuário.
- Não permitir que a reprodução da prévia altere o estado original do áudio em edição.
- Não utilizar `Tab` ou `Shift+Tab` para escolher entre aplicar ou não aplicar o efeito.
- Não encerrar a tela de prévia quando a reprodução chegar ao final.
- Não aplicar nem descartar o efeito pela tecla `Esc`, em nenhum momento da prévia.
- Não aplicar o efeito pela tecla `Enter` durante a reprodução da prévia.
- Não executar uma opção apenas porque a sua letra foi pressionada.

### RN10 — Descarte de efeitos

Quando o usuário escolher a opção Não aplicar, nas opções do efeito (RN09), o sistema deverá descartar o processamento temporário.

**Critérios de aceitabilidade:**

- Preservar integralmente o estado do áudio anterior à tentativa de aplicação.
- Retornar ao menu de efeitos após o descarte.

### RN11 — Preservação de alterações anteriores

A aplicação de um novo efeito deverá preservar os efeitos anteriormente confirmados, respeitando as regras de compatibilidade entre as funcionalidades (RN14).

**Critérios de aceitabilidade:**

- Permitir a combinação de efeitos de famílias diferentes, desde que o processamento seja tecnicamente seguro.
- Preservar as alterações previamente confirmadas.
- Garantir que a prévia de um novo efeito considere o estado atual do áudio em edição.

**Critérios de não aceitabilidade:**

- Não permitir que a aplicação de um novo efeito descarte indevidamente alterações anteriormente confirmadas.
- Não permitir a combinação de efeitos declarados incompatíveis, salvo pela substituição definida na RN15.

### RN12 — Integridade do áudio

O processamento dos efeitos deverá preservar a integridade do áudio em edição.

**Critérios de aceitabilidade:**

- Evitar clipping e distorções digitais decorrentes do processamento, conforme a RN17.
- Preservar a taxa de amostragem e a quantidade de canais, salvo quando uma operação específica justificar sua alteração.
- Garantir que o processamento não provoque corrupção do arquivo ou perda indevida de dados.

**Critérios de não aceitabilidade:**

- Não permitir que falhas durante o processamento comprometam o áudio original.
- Não permitir que operações incompletas sejam confirmadas como alterações concluídas.
- Não utilizar o simples corte dos picos do sinal como estratégia de proteção contra clipping.

### RN13 — Escala de volume

Os ajustes de volume (RN01 e RN02) utilizam uma escala de variação em relação ao volume original do áudio, com incrementos fixos de 25 pontos percentuais.

A escala de aumento é composta pelos níveis 100%, que corresponde ao volume original, 125%, 150%, 175% e 200%, que é o limite máximo inicial.

A escala de diminuição é composta pelos níveis 100%, que corresponde ao volume original, 75%, 50% e 25%, que é o limite mínimo inicial.

O aumento e a diminuição percorrem uma única escala, formada pelos níveis 25%, 50%, 75%, 100%, 125%, 150%, 175% e 200%. Cada aumento passa para o nível seguinte, e cada diminuição passa para o nível anterior, inclusive atravessando o nível de 100%. Por exemplo, um trecho em 150% passa para 125% ao diminuir, e um trecho em 75% passa para 100% ao aumentar. Esse funcionamento poderá ser revisto posteriormente, caso os testes indiquem problemas.

O volume original é a referência de 100% e corresponde ao áudio no momento em que ele é aberto no editor. Todos os ajustes de aumento e diminuição utilizam essa referência fixa. O resultado de uma operação anterior nunca se torna uma nova referência.

Cada trecho do áudio possui o próprio nível na escala. Quando o ajuste é aplicado a um trecho selecionado, o novo nível é o próximo nível da escala a partir do nível atual desse trecho, e os limites de 200% e de 25% valem para cada trecho. Por exemplo, se o áudio inteiro estiver em 150% e o usuário selecionar um trecho e aumentar o volume, esse trecho passa para 175%, e o restante do áudio permanece em 150%.

Quando o trecho selecionado possuir partes com níveis diferentes, o trecho inteiro é nivelado. No aumento, o trecho passa para o nível seguinte ao maior nível presente nele. Na diminuição, passa para o nível anterior ao menor nível presente nele. Por exemplo, em um trecho com uma parte em 100% e outra em 150%, o aumento leva o trecho inteiro para 175%, e a diminuição o leva para 75%. Se o maior nível já for 200%, o aumento é recusado com a mensagem de volume máximo. Se o menor nível já for 25%, a diminuição é recusada com a mensagem de volume mínimo.

Nas bordas de um trecho selecionado, a mudança de volume é feita com uma transição curta, dentro do trecho, para evitar estalos audíveis. As bordas que coincidem com o início ou o fim do áudio não precisam de transição.

Os níveis da escala acompanham as demais operações de edição. Ao remover um trecho, o nível da parte removida sai junto com ela, e o restante do áudio mantém o seu nível. O áudio inserido pela Adição de áudio entra em 100%, porque é considerado original. O trecho em que o Fundo sonoro é misturado mantém o nível que já tinha; o volume do fundo é controlado pelos volumes do próprio Fundo sonoro.

Os limites de 200% e de 25% são parâmetros iniciais e poderão ser revisados posteriormente, conforme os resultados dos testes.

O sistema deverá impedir que os ajustes provoquem clipping ou distorção. A segurança do áudio prevalece sobre os limites percentuais definidos.

O limite da escala e a proteção contra clipping são controles diferentes. O limite da escala é fixo: 200% no aumento e 25% na diminuição, e quando é atingido o sistema informa "O volume máximo permitido foi atingido." ou "O volume mínimo permitido foi atingido.". A proteção contra clipping depende do conteúdo do áudio: um passo de aumento pode ser recusado antes de 200%, porque o áudio já está próximo do limite digital, e nesse caso o sistema informa "O volume não pode ser aumentado sem causar distorção." (RN01 e RN17).

**Critérios de aceitabilidade:**

- Utilizar incrementos fixos de 25 pontos percentuais em relação ao volume original.
- Percorrer uma única escala no aumento e na diminuição, atravessando o nível de 100% nas duas direções.
- Considerar como volume original, com referência de 100%, o áudio no momento em que ele é aberto no editor.
- Manter um nível próprio na escala para cada trecho ajustado e aplicar os limites a cada trecho.
- Nivelar o trecho com partes de níveis diferentes pelo maior nível, no aumento, e pelo menor nível, na diminuição.
- Utilizar uma transição curta nas bordas do trecho selecionado, sem estalos audíveis.
- Informar claramente ao usuário quando o limite máximo ou o limite mínimo for atingido.
- Fazer prevalecer a segurança do áudio sobre os limites percentuais.

**Critérios de não aceitabilidade:**

- Não calcular um novo nível a partir do resultado matemático da operação anterior.
- Não ultrapassar os limites da escala.
- Não permitir que os ajustes provoquem clipping ou distorção.

### RN14 — Famílias de efeitos e compatibilidade

Os efeitos são organizados em famílias para controlar a compatibilidade entre eles. O Eco e o Super eco pertencem à família Eco. A Reverberação e a Super reverberação pertencem à família Reverberação.

Efeitos da mesma família não podem ser acumulados sem a remoção ou a substituição do efeito anterior, conforme a RN15. Essa regra também se aplica quando o usuário tenta aplicar novamente o mesmo efeito.

Efeitos de famílias diferentes podem ser combinados, desde que o processamento seja tecnicamente seguro.

A escala de volume (RN13) resolve os incrementos e os limites de ganho, mas não substitui a regra de compatibilidade entre efeitos da mesma família. São responsabilidades diferentes.

A presença de um efeito da família é controlada no áudio inteiro, mesmo que o efeito tenha sido aplicado somente a um trecho selecionado. Assim, se o áudio possuir um Eco aplicado em um trecho, a aplicação de qualquer efeito da família Eco em outro trecho também depende da substituição definida na RN15. A mesma regra vale para a família Reverberação.

**Critérios de aceitabilidade:**

- Reconhecer, pelo registro dos efeitos (RN16), quando o áudio já possui um efeito da mesma família.
- Permitir a combinação de efeitos de famílias diferentes, desde que o processamento seja tecnicamente seguro.
- Preservar os efeitos anteriormente confirmados quando um novo efeito compatível for aplicado.

**Critérios de não aceitabilidade:**

- Não acumular efeitos da mesma família.
- Não permitir que efeitos da mesma família coexistam em trechos diferentes do áudio sem a substituição definida na RN15.
- Não empilhar um novo processamento sobre o resultado de um efeito da mesma família.

### RN15 — Substituição de efeitos da mesma família

Quando o usuário tentar aplicar um efeito que pertença à mesma família de outro efeito já aplicado, inclusive o mesmo efeito, o sistema deverá informar qual efeito está presente e oferecer a possibilidade de substituí-lo, desde que as condições desta regra sejam atendidas.

A reaplicação permite que o usuário aplique novamente um efeito utilizando parâmetros diferentes, inclusive depois de alterar suas configurações. Ela não empilha o novo processamento sobre o resultado anterior: o efeito da mesma família é substituído, e os demais efeitos e alterações compatíveis são preservados. Essa regra vale para o Eco, o Super eco, a Reverberação e a Super reverberação.

#### Condições para a substituição

A substituição só é possível quando o efeito da mesma família for a última alteração confirmada no áudio. Se houver qualquer alteração posterior a esse efeito, a substituição é recusada, e o sistema informa o motivo ao usuário com a mensagem "O efeito *anterior* não pode ser substituído, porque o áudio foi alterado depois dele. Para aplicar *novo efeito*, desfaça as alterações feitas depois do efeito *anterior*.".

A substituição depende também da disponibilidade do estado anterior do áudio, ou de uma versão recuperável que permita remover o processamento anterior sem comprometer as demais alterações. Quando o usuário aplicar um efeito, salvar o arquivo e depois tentar substituí-lo, o sistema deverá verificar se ainda dispõe dos dados necessários para realizar a operação corretamente.

Se o efeito já estiver incorporado permanentemente ao arquivo salvo e não existir uma versão anterior recuperável, a substituição não deverá ser oferecida como se fosse tecnicamente possível. Nessa situação, o sistema informa claramente que não possui os dados necessários para substituir o efeito, com a mensagem "Não há dados suficientes para substituir o efeito *anterior*. O áudio foi mantido como está.", preserva integralmente o áudio atual, não executa um novo processamento que resulte no acúmulo indesejado do efeito e não compromete as demais alterações já confirmadas.

Uma solução baseada em histórico não destrutivo ou em armazenamento de versões poderá ser avaliada futuramente na documentação técnica. Esta regra não define um mecanismo de persistência.

#### Etapa 1 — Identificação do conflito

Quando as condições forem atendidas, o sistema informa qual efeito está presente e explica que será necessário substituí-lo. Por exemplo: "Este áudio já possui o efeito Eco aplicado. Para utilizar Super eco, será necessário substituir o efeito existente."

São apresentadas as opções **Continuar**, que prossegue para a prévia do novo efeito, e **Cancelar**, que desiste da substituição e preserva o efeito atual. A opção **Cancelar** vem selecionada por padrão, para evitar substituições acidentais. Ao escolher **Cancelar**, ou pressionar `Esc` nessa confirmação, o sistema fala "Operação cancelada." e volta ao menu de efeitos, como nas demais confirmações do Sound Mine.

#### Etapa 2 — Prévia e confirmação

Ao escolher **Continuar**, o usuário acessa a prévia do novo efeito, que respeita todas as regras definidas para a prévia dos efeitos (RN09) e permite ouvir o resultado antes da confirmação definitiva da substituição.

A prévia da substituição segue a RN09: a tecla `Esc` leva da reprodução às opções do efeito, e a tecla `Enter` executa a opção selecionada. A opção Aplicar efeito confirma a substituição. A opção Não aplicar cancela a substituição e preserva o efeito anterior. A substituição ocorre somente depois dessa confirmação explícita do usuário. Quando ela for confirmada, o efeito anterior é removido e o novo efeito é aplicado.

#### Integridade e acessibilidade

A substituição é tratada como uma única operação lógica. Uma falha durante o novo processamento não pode provocar a perda do efeito anterior nem comprometer o áudio, e o estado anterior deve ser preservado.

Todas as mensagens, opções, mudanças de foco e confirmações da substituição deverão ser acessíveis pelo NVDA.

**Critérios de aceitabilidade:**

- Informar qual efeito da mesma família está presente no áudio e explicar que será necessário substituí-lo.
- Oferecer a substituição somente quando o efeito da mesma família for a última alteração confirmada e o sistema dispuser dos dados necessários para removê-lo.
- Informar o motivo quando a substituição for recusada por existirem alterações posteriores ao efeito.
- Informar claramente quando o sistema não possuir os dados necessários para substituir o efeito.
- Apresentar as opções Continuar e Cancelar, com Cancelar selecionada por padrão.
- Apresentar a prévia do novo efeito ao escolher Continuar.
- Confirmar a substituição pela opção Aplicar efeito e cancelá-la pela opção Não aplicar, nas opções do efeito da prévia.
- Preservar integralmente o estado anterior do áudio quando o usuário cancelar em qualquer uma das etapas.
- Apresentar as mensagens, as opções, as mudanças de foco e as confirmações de forma acessível pelo NVDA.

**Critérios de não aceitabilidade:**

- Não aplicar o novo efeito sobre o resultado do efeito anterior da mesma família.
- Não oferecer a substituição quando houver alterações posteriores ao efeito da mesma família.
- Não oferecer a substituição como se fosse tecnicamente possível quando o sistema não dispuser dos dados necessários.
- Não realizar a substituição sem a confirmação explícita do usuário na prévia.
- Não permitir que uma falha no novo processamento provoque a perda do efeito anterior ou comprometa o áudio.
- Não descartar outras alterações confirmadas para realizar a substituição.

### RN16 — Registro dos efeitos durante a sessão de edição

O sistema mantém um registro dos efeitos confirmados durante a sessão atual de edição, utilizado no controle de compatibilidade entre efeitos da mesma família (RN14 e RN15).

O registro permanece válido durante toda a sessão de edição, inclusive depois que o usuário salvar o arquivo. Salvar o áudio não zera o registro. Por exemplo, se o usuário aplicar o Eco e salvar o arquivo, o registro do Eco continua ativo, e uma nova tentativa de aplicar o Eco deverá oferecer a substituição. Essa regra evita que o usuário acumule acidentalmente o mesmo efeito apenas porque salvou o arquivo.

O registro dos efeitos não é atualizado isoladamente do estado do áudio. Uma mudança no registro sempre acompanha a alteração correspondente do áudio.

A remoção de trechos não altera o registro. Mesmo que o trecho em que o efeito foi aplicado seja removido, a família continua registrada, e a aplicação de outro efeito da mesma família continua dependendo da substituição (RN15).

Depois de fechar o editor e abrir novamente um arquivo de áudio comum, não se presume que os efeitos existentes possam ser identificados automaticamente. O sistema não identifica efeitos por meio da análise sonora do arquivo. A identificação de efeitos aplicados em sessões anteriores dependerá de um mecanismo confiável de persistência de metadados ou de histórico, cuja solução será avaliada posteriormente na documentação técnica.

**Critérios de aceitabilidade:**

- Registrar os efeitos confirmados durante a sessão atual de edição.
- Manter o registro depois de salvar o arquivo.
- Atualizar o registro quando um efeito for substituído (RN15).

**Critérios de não aceitabilidade:**

- Não zerar o registro ao salvar o arquivo.
- Não atualizar o registro isoladamente do estado do áudio.
- Não considerar, no registro, efeitos que não foram confirmados.
- Não identificar efeitos por meio da análise sonora do arquivo.
- Não presumir a existência ou a ausência de efeitos em um arquivo aberto em outra sessão de edição.

### RN17 — Proteção contra clipping e distorção

Antes de confirmar o processamento definitivo, o sistema deverá analisar o áudio resultante e identificar possíveis riscos de clipping ou distorção.

O sistema não deverá simplesmente cortar os picos do sinal como estratégia de proteção. A estratégia inicial é a normalização automática, utilizada quando necessária, que ajusta o ganho do áudio processado para manter os picos dentro do limite digital.

Quando houver risco de clipping, a normalização é aplicada ao áudio inteiro, mesmo que o efeito tenha sido aplicado somente a um trecho. Essa abordagem pode reduzir também o volume das partes não alteradas pelo efeito e foi adotada inicialmente por ser mais simples e previsível.

A normalização deverá preservar a dinâmica relativa do áudio e não deverá alterar o volume quando não houver risco de clipping.

Considera-se que há risco de clipping quando o efeito eleva o pico do áudio acima de 0,98. Se o arquivo já tiver sido aberto com o pico acima desse valor e o efeito não aumentar o pico, o volume não é alterado.

O aumento de volume não utiliza a normalização. Quando um passo de aumento provocaria clipping, ele é recusado com a mensagem "O volume não pode ser aumentado sem causar distorção.", conforme a RN01. Essa recusa é diferente do limite de 200% da escala de volume (RN13).

Caso não seja possível concluir o processamento com segurança, o sistema deverá informar o usuário e preservar integralmente o estado anterior do áudio.

**Critérios de aceitabilidade:**

- Analisar o áudio resultante antes da confirmação definitiva.
- Aplicar a normalização ao áudio inteiro somente quando houver risco de clipping.
- Preservar a dinâmica relativa do áudio.
- Informar o usuário e preservar o estado anterior quando o processamento não puder ser concluído com segurança.

**Critérios de não aceitabilidade:**

- Não cortar os picos do sinal como estratégia de proteção.
- Não alterar o volume quando não houver risco de clipping.
- Não confirmar um processamento que não pôde ser concluído com segurança.

### RN18 — Duração do Fade in e do Fade out

A duração do Fade in (RN03) e do Fade out (RN04) é solicitada ao usuário no momento em que ele seleciona o efeito, antes da apresentação da prévia.

A duração mínima é de 1 segundo, a duração máxima é de 60 segundos e a duração padrão é de 5 segundos. Esses valores são parâmetros iniciais e poderão ser revisados posteriormente, conforme os resultados dos testes.

A informação da duração deverá ser acessível pelo teclado e corretamente anunciada pelo NVDA.

Se a duração escolhida ultrapassar o tamanho do trecho disponível, o sistema recusa a operação, informa claramente o motivo e permite que o usuário informe outra duração. O sistema não ajusta automaticamente a duração escolhida pelo usuário.

**Critérios de aceitabilidade:**

- Solicitar a duração ao selecionar o Fade in ou o Fade out, antes da prévia.
- Aceitar durações de 1 a 60 segundos, com o valor padrão de 5 segundos.
- Permitir informar a duração pelo teclado, com anúncio correto pelo NVDA.
- Recusar a operação e informar claramente o motivo quando a duração ultrapassar o tamanho do trecho disponível.
- Permitir que o usuário informe outra duração depois da recusa.

**Critérios de não aceitabilidade:**

- Não apresentar a prévia antes de o usuário informar a duração.
- Não aceitar durações fora dos limites definidos.
- Não ajustar automaticamente a duração escolhida pelo usuário.

### RN19 — Seleção de trecho

A seleção é o trecho compreendido entre o cursor e o ponto memorizado no player. O trecho é o mesmo em qualquer ordem, esteja o cursor antes ou depois do ponto memorizado.

Não há seleção quando não existir ponto memorizado ou quando o ponto memorizado estiver na mesma posição do cursor. Nesses casos, o efeito considera o áudio inteiro.

Todos os efeitos consideram a seleção, conforme as regras de cada efeito: o aumento e a diminuição de volume, o Fade in, o Fade out, o Eco, o Super eco, a Reverberação e a Super reverberação. A prévia também considera a seleção (RN09).

Depois que um efeito é aplicado, o ponto memorizado é apagado, seguindo a regra já adotada pelas demais operações de edição. Para aplicar outro efeito ao mesmo trecho, o usuário precisa memorizar o ponto novamente.

**Critérios de aceitabilidade:**

- Considerar como seleção o trecho entre o cursor e o ponto memorizado, em qualquer ordem.
- Considerar o áudio inteiro quando não existir ponto memorizado.
- Considerar o áudio inteiro quando o ponto memorizado estiver na mesma posição do cursor.
- Apagar o ponto memorizado depois que um efeito for aplicado.

**Critérios de não aceitabilidade:**

- Não exigir uma ordem específica entre o cursor e o ponto memorizado.
- Não recusar o efeito apenas porque não existe seleção.

### RN20 — Efeitos incorporados ao aplicativo

Na primeira fase, todos os efeitos são implementados diretamente no código-fonte oficial do Sound Mine e distribuídos junto com o aplicativo.

Os efeitos são organizados em módulos próprios, que seguem um contrato interno padronizado. O núcleo do sistema de efeitos continua responsável pelas regras de negócio, pela validação, pela compatibilidade entre efeitos, pelo processamento, pela segurança do áudio e pelo gerenciamento do estado.

A inclusão de um novo efeito deve seguir um procedimento simples e documentado, sem exigir alterações desnecessárias em várias partes do aplicativo. Novos efeitos, assim como correções e melhorias nos efeitos existentes, são disponibilizados por meio de atualizações do Sound Mine, depois de revisão técnica, testes automatizados e validação de acessibilidade.

Nesta primeira fase, o Sound Mine não carrega, não instala, não executa e não atualiza código de efeitos externo ao aplicativo. A infraestrutura de pacotes externos de efeitos, incluindo assinatura digital, gerenciamento de chaves, instalação e atualização de pacotes, fica adiada e poderá ser reavaliada futuramente. O adiamento não representa o abandono da possibilidade de expansão do projeto.

**Critérios de aceitabilidade:**

- Disponibilizar os efeitos como parte do código-fonte oficial do Sound Mine.
- Organizar cada efeito em um módulo próprio, de acordo com o contrato interno dos efeitos.
- Manter no núcleo as regras de negócio, a validação, a compatibilidade, a segurança do áudio e o gerenciamento do estado.
- Permitir a inclusão de novos efeitos por um procedimento simples e documentado.
- Disponibilizar novos efeitos e correções por meio de atualizações do Sound Mine.

**Critérios de não aceitabilidade:**

- Não carregar, instalar, executar ou atualizar código de efeitos externo ao aplicativo nesta primeira fase.
- Não permitir que um efeito altere as regras de negócio aplicadas pelo núcleo.
