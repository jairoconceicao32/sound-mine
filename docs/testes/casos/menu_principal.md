# CT01 — Menu principal

## Título:
Menu principal.

## Descrição:
Verificar se o menu principal do Sound Mine é apresentado corretamente e permite acessar as funcionalidades disponíveis no programa.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o NVDA disponível para validação da acessibilidade.

## Passos para a reprodução:
1. Abrir o programa;
2. Aguardar a inicialização;
3. Verificar se as opções do menu principal são apresentadas;
4. Navegar pelas opções utilizando as teclas de seta para cima e seta para baixo;
5. Selecionar uma opção desejada;
6. Ativar a opção utilizando a tecla Enter.

## Comportamento esperado — caminho feliz:
- O programa deve iniciar corretamente;
- O menu principal deve ser apresentado com as opções disponíveis;
- A navegação entre as opções deve funcionar corretamente utilizando as setas;
- A opção selecionada deve ser anunciada corretamente pelo NVDA;
- A tecla Enter deve ativar a opção selecionada;
- As funcionalidades correspondentes às opções selecionadas devem ser acessadas corretamente.

## Comportamento esperado — caminho não feliz:
- Caso o menu principal não seja carregado, o programa deve apresentar uma mensagem de erro correspondente;
- O programa não deve encerrar inesperadamente durante a navegação;
- As opções não devem apresentar falhas de identificação ou seleção;
- O NVDA não deve deixar de anunciar as opções disponíveis e a opção selecionada;
- A ativação de uma opção não deve executar uma ação diferente daquela correspondente à seleção.

## Resultado da execução:
Aguardando conclusão da validação de todos os comportamentos previstos.

## Observações:
Durante a investigação, foi identificado que o NVDA repete o anúncio da opção selecionada ao pressionar repetidamente determinadas letras, mesmo sem alteração na seleção.

O mesmo comportamento foi observado em outros programas. Portanto, a ocorrência permanece em investigação e ainda não foi confirmada como uma falha específica do Sound Mine.