# CT03 — Acessar configurações

## Título:
Acessar configurações.

## Descrição:
Verificar se o programa permite acessar a tela de configurações e disponibiliza corretamente as opções de personalização do Sound Mine.

## Pré-requisitos:
- Ter o Sound Mine aberto;
- Ter o NVDA disponível para validação da acessibilidade.

## Passos para a reprodução:
1. Acessar o menu principal;
2. Navegar até a opção Configurações;
3. Ativar a opção utilizando a tecla Enter;
4. Verificar se a tela de configurações foi carregada;
5. Navegar pelas opções utilizando as teclas Tab, Shift + Tab e as setas, conforme o comportamento de cada controle;
6. Verificar se as opções e seus respectivos valores são anunciados corretamente pelo NVDA;
7. Acessar a seção de efeitos;
8. Navegar utilizando a tecla Tab até a opção Salvar.

## Comportamento esperado — caminho feliz:
- A tela de configurações deve ser carregada com sucesso;
- Todas as opções de configuração previstas devem ser apresentadas;
- Os controles devem permitir navegação e interação;
- O NVDA deve anunciar corretamente os nomes dos controles e seus respectivos valores;
- A navegação deve respeitar a ordem dos controles;
- As configurações devem permitir a alteração dos valores disponíveis.

## Comportamento esperado — caminho não feliz:
- Caso a tela de configurações não seja carregada, o programa deve apresentar uma mensagem de erro correspondente;
- O programa não deve encerrar inesperadamente durante o acesso às configurações;
- Os controles não devem apresentar falhas que impeçam a navegação ou interação;
- Informações importantes não devem deixar de ser anunciadas pelo NVDA;
- A navegação não deve apresentar atrasos que prejudiquem a utilização dos controles.

## Resultado da execução:
Pendente de conclusão.

## Observações:
Durante a navegação pela seção de efeitos, utilizando a tecla Tab até a opção Salvar, foi identificado um atraso na leitura das informações pelo NVDA.

A ocorrência foi registrada no arquivo bugs_sound_mine.txt para investigação.

É necessário verificar se o atraso está relacionado à atualização dos controles, ao processamento da interface ou à comunicação com o leitor de telas.