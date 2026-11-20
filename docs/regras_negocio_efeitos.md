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

Após selecionar um efeito, o sistema deverá disponibilizar uma prévia do áudio processado, permitindo que o usuário escute o resultado antes de confirmar a alteração.

A interface de prévia deverá disponibilizar as seguintes opções:

- **Aplicar efeito:** confirma a operação e incorpora o efeito ao áudio em edição.
- **Não aplicar:** descarta a alteração proposta, preservando o estado anterior do áudio.

Após selecionar uma das opções, o sistema deverá retornar ao menu de efeitos.

A prévia deverá ser temporária e não poderá modificar permanentemente o áudio em edição antes da confirmação do usuário.

---

## 3. Regras de negócio

### RN01 — Aumento de volume

Permite aumentar a intensidade do volume do áudio em incrementos de 25%.

**Critérios de aceitabilidade:**

- Permitir o aumento progressivo do volume em incrementos de 25%.
- Estabelecer um limite máximo de amplificação.
- Informar ao usuário quando o limite máximo de amplificação for atingido.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir que a amplificação provoque clipping ou distorção digital decorrente da ultrapassagem dos limites de amplitude.
- Não permitir novos aumentos quando o limite máximo estabelecido for atingido.

### RN02 — Diminuição de volume

Permite reduzir a intensidade do volume do áudio em incrementos de 25%.

**Critérios de aceitabilidade:**

- Permitir a redução progressiva do volume em incrementos de 25%.
- Estabelecer um limite mínimo de redução.
- Informar ao usuário quando o limite mínimo de redução for atingido.

**Critérios de não aceitabilidade:**

- Não permitir que a redução de volume resulte em silêncio absoluto.
- Não permitir novas reduções quando o limite mínimo estabelecido for atingido.

### RN03 — Fade in

Permite aumentar gradativamente o volume do áudio a partir do silêncio até atingir o nível de volume original.

**Critérios de aceitabilidade:**

- Iniciar o áudio com volume reduzido, partindo do silêncio.
- Aumentar gradativamente o volume até atingir o nível original do áudio.
- Permitir a definição de um intervalo de duração para a aplicação do efeito.
- Respeitar o nível de volume original como limite máximo durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir que o volume ultrapasse o nível original do áudio.
- Não permitir aumentos abruptos de volume durante a aplicação do efeito.
- Não alterar indevidamente a duração original do áudio.

### RN04 — Fade out

Permite reduzir gradativamente o volume do áudio até atingir o silêncio, proporcionando um encerramento suave.

**Critérios de aceitabilidade:**

- Reduzir progressivamente o volume do áudio até atingir o silêncio.
- Permitir a definição de um intervalo de duração para a aplicação do efeito.
- Aplicar a redução gradativa a partir do trecho final do áudio.
- Garantir uma transição suave entre o volume original e o silêncio.

**Critérios de não aceitabilidade:**

- Não permitir interrupções abruptas do áudio antes da conclusão do efeito.
- Não permitir aumentos de volume durante a aplicação do efeito.
- Não alterar indevidamente a duração original do áudio.

### RN05 — Eco

Permite adicionar repetições atrasadas do áudio original, criando a percepção de eco durante a reprodução.

**Critérios de aceitabilidade:**

- Respeitar os parâmetros de intensidade e duração do eco.
- Respeitar os valores previamente definidos pelo usuário nas configurações do Sound Mine.
- Permitir a aplicação do efeito ao áudio em edição.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir a utilização de valores inválidos nos parâmetros do efeito.
- Não permitir que parâmetros obrigatórios recebam valores iguais a zero quando as configurações determinarem um valor mínimo superior a zero.

### RN06 — Super eco

Permite adicionar um efeito de eco mais intenso, proporcionando maior percepção das repetições sonoras.

**Critérios de aceitabilidade:**

- Produzir um efeito de eco mais intenso que o efeito tradicional.
- Respeitar os parâmetros definidos para a modalidade Super eco.
- Garantir que o processamento mantenha a estabilidade do áudio.

**Critérios de não aceitabilidade:**

- Não permitir a aplicação do Super eco sobre um áudio que já possua o efeito Eco ou Super eco aplicado, sem que o efeito anterior seja previamente removido ou substituído.
- Não permitir parâmetros inválidos durante o processamento.

### RN07 — Reverberação

Permite adicionar ao áudio uma ambientação sonora, simulando a percepção acústica de um ambiente fechado, como uma sala.

**Critérios de aceitabilidade:**

- Respeitar os parâmetros de intensidade e duração da reverberação.
- Respeitar os valores previamente definidos pelo usuário nas configurações do Sound Mine.
- Permitir a aplicação do efeito ao áudio em edição.
- Preservar a qualidade do áudio durante o processamento.

**Critérios de não aceitabilidade:**

- Não permitir a utilização de valores inválidos nos parâmetros do efeito.
- Não permitir que parâmetros obrigatórios recebam valores iguais a zero quando as configurações determinarem um valor mínimo superior a zero.

### RN08 — Super reverberação

Permite adicionar uma camada de reverberação mais intensa e ampla, proporcionando a percepção de um ambiente sonoro de maiores dimensões.

**Critérios de aceitabilidade:**

- Produzir uma reverberação mais intensa que a modalidade tradicional.
- Proporcionar uma percepção de ambiência mais ampla.
- Respeitar os parâmetros definidos para a modalidade Super reverberação.
- Garantir a estabilidade do processamento do áudio.

**Critérios de não aceitabilidade:**

- Não permitir a aplicação da Super reverberação sobre um áudio que já possua o efeito Reverberação ou Super reverberação aplicado, sem que o efeito anterior seja previamente removido ou substituído.
- Não permitir parâmetros inválidos durante o processamento.

---

## 4. Regras gerais do sistema de efeitos

### RN09 — Prévia dos efeitos

O sistema deverá permitir que o usuário escute o resultado de um efeito antes de confirmar sua aplicação.

**Critérios de aceitabilidade:**

- Disponibilizar uma prévia do áudio processado.
- Permitir que o usuário escute a prévia quantas vezes forem necessárias.
- Disponibilizar as opções de aplicar ou não aplicar o efeito.

**Critérios de não aceitabilidade:**

- Não modificar permanentemente o áudio antes da confirmação do usuário.
- Não permitir que a reprodução da prévia altere o estado original do áudio em edição.

### RN10 — Descarte de efeitos

Quando o usuário selecionar a opção de não aplicar, o sistema deverá descartar o processamento temporário.

**Critérios de aceitabilidade:**

- Preservar integralmente o estado do áudio anterior à tentativa de aplicação.
- Retornar ao menu de efeitos após o descarte.

### RN11 — Preservação de alterações anteriores

A aplicação de um novo efeito deverá preservar os efeitos anteriormente confirmados, respeitando as regras de compatibilidade entre as funcionalidades.

**Critérios de aceitabilidade:**

- Permitir a combinação de efeitos compatíveis.
- Preservar as alterações previamente confirmadas.
- Garantir que a prévia de um novo efeito considere o estado atual do áudio em edição.

**Critérios de não aceitabilidade:**

- Não permitir que a aplicação de um novo efeito descarte indevidamente alterações anteriormente confirmadas.
- Não permitir a combinação de efeitos declarados incompatíveis.

### RN12 — Integridade do áudio

O processamento dos efeitos deverá preservar a integridade do áudio em edição.

**Critérios de aceitabilidade:**

- Evitar clipping e distorções digitais decorrentes do processamento.
- Preservar a taxa de amostragem e a quantidade de canais, salvo quando uma operação específica justificar sua alteração.
- Garantir que o processamento não provoque corrupção do arquivo ou perda indevida de dados.

**Critérios de não aceitabilidade:**

- Não permitir que falhas durante o processamento comprometam o áudio original.
- Não permitir que operações incompletas sejam confirmadas como alterações concluídas.