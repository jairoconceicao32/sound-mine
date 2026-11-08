# CT02 — Abrir arquivo

## Título:
Abrir arquivo.

## Descrição:
Verificar se o programa permite selecionar, abrir e carregar arquivos de áudio nos formatos suportados pelo Sound Mine.

## Pré-requisitos:
- Ter o Sound Mine aberto;
- Ter arquivos de áudio disponíveis para teste nos formatos MP3, M4A, WAV e OGG.

## Passos para a reprodução:
1. Acessar o menu principal;
2. Navegar até a opção Abrir arquivo;
3. Ativar a opção utilizando a tecla Enter;
4. Navegar pelo seletor de arquivos até localizar o arquivo desejado;
5. Selecionar o arquivo e confirmar a abertura;
6. Aguardar o processamento e o carregamento do arquivo.

## Comportamento esperado — caminho feliz:
- O seletor de arquivos deve ser aberto corretamente;
- O seletor deve apresentar os formatos de áudio suportados pelo programa;
- O arquivo selecionado deve ser carregado com sucesso;
- O programa deve disponibilizar o arquivo para edição.

## Comportamento esperado — caminho não feliz:
- Arquivos corrompidos ou inválidos devem ser recusados;
- Arquivos vazios devem ser recusados;
- O programa deve apresentar uma mensagem de erro correspondente quando não conseguir carregar o arquivo;
- Arquivos que não sejam de áudio não devem ser apresentados como formatos disponíveis no filtro do seletor;
- O programa não deve apresentar falhas ou encerrar inesperadamente durante uma tentativa de abertura inválida.

## Resultado da execução:
Aprovado.

## Observações:
A funcionalidade de abertura de arquivos foi validada com sucesso.

Durante a utilização do editor após o carregamento do arquivo, foi identificada uma ocorrência relacionada ao player, registrada separadamente no arquivo bugs_sound_mine.txt.