# CT03 — Acessar configurações

## Título:
Acessar configurações.

## Descrição:
Verificar se o programa permite acessar a tela de configurações e disponibiliza corretamente as opções de personalização do Sound Mine.

## Pré-requisitos:
- Ter o Sound Mine aberto.

## Passos para a reprodução:
1. Acessar o menu principal;
2. Navegar até a opção Configurações;
3. Ativar a opção utilizando a tecla Enter;
4. Verificar se a tela de configurações foi carregada;
5. Navegar pelas opções utilizando as teclas Tab, Shift + Tab e as setas, conforme o comportamento de cada controle;
6. Verificar se as opções e seus respectivos valores são anunciados corretamente pelo NVDA.

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
- Informações importantes não devem deixar de ser anunciadas pelo NVDA.

## Observações:
Validar a navegação e a acessibilidade da tela de configurações utilizando o NVDA, verificando se os controles são identificados corretamente e se permitem interação.