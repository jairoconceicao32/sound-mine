# CT06 — Troca automática de dispositivo de som

## Título:
Troca automática de dispositivo de som (BUG04, P3).

## Descrição:
Verificar se o Sound Mine continua funcionando quando o dispositivo de som em uso é desconectado e reconectado, preservando o estado do player e anunciando as trocas pelo NVDA.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o NVDA em execução;
- Ter um headset (ou fone USB) como dispositivo padrão do Windows e outro dispositivo de som disponível, como as caixas da placa-mãe;
- Ter um arquivo de áudio válido com pelo menos um minuto.

## Passos para a reprodução:

**Desconexão durante a reprodução:**

1. Abrir o arquivo e ativar Tocar arquivo (T);
2. Depois de alguns segundos, desconectar o headset;
3. Verificar se o som continua nas caixas, a partir do ponto em que estava;
4. Verificar se o NVDA fala "Saída de som: <nome das caixas>." e se a mesma mensagem aparece na janela.

**Desconexão com o player pausado:**

1. Reconectar o headset e aguardar a volta (ver abaixo);
2. Pausar com Espaço;
3. Desconectar o headset;
4. Verificar se o player continua pausado;
5. Pressionar Espaço e verificar se o som toca nas caixas.

**Volta ao dispositivo preferencial:**

1. Com o som nas caixas, reconectar o headset;
2. Verificar se, depois de alguns segundos, o som volta ao headset sem parar e sem voltar ao início;
3. Verificar se o NVDA fala "Saída de som de volta: <nome do headset>.";
4. Observar em qual dispositivo o NVDA passa a falar.

**Conexão instável:**

1. Conectar e desconectar o headset rapidamente várias vezes;
2. Verificar se o programa não fica alternando nem trava, e se ao final o som fica no dispositivo conectado.

**Troca deliberada no Windows:**

1. Com o headset conectado, mudar o dispositivo padrão para as caixas no Painel de Som do Windows;
2. Verificar se o Sound Mine passa para as caixas e anuncia;
3. Verificar se ele continua nas caixas, mesmo com o headset conectado;
4. Voltar o padrão para o headset no Windows e verificar se o Sound Mine acompanha.

**Sons da interface e edição:**

1. Depois de uma troca, navegar pelos menus e verificar se os sons de navegação saem no novo dispositivo;
2. Remover um trecho, desfazer e salvar, verificando se tudo funciona normalmente.

**Encerramento:**

1. Fechar o programa com o headset desconectado;
2. Abrir de novo, reconectar o headset e fechar logo em seguida;
3. Verificar se o programa fecha sem erros e sem travar.

## Comportamento esperado — caminho feliz:
- O som continua no novo dispositivo, na mesma posição, sem mudar o estado de reprodução ou pausa;
- O programa volta ao dispositivo preferencial quando ele é reconectado;
- Cada troca é anunciada pelo NVDA, com o nome do dispositivo, e escrita na janela;
- Os sons da interface acompanham as trocas.

## Comportamento esperado — caminho não feliz:
- Sem nenhum dispositivo, o player mostra "Aguardando saída de som" e retoma o estado guardado quando um dispositivo aparecer;
- Se o som não puder ser iniciado, aparece a caixa "Erro ao tocar arquivo", e o programa não fala "Reproduzindo";
- O programa não trava, não fecha e não apresenta erros inesperados durante as trocas.

## Resultado da execução:
Pendente.

## Observações:
O cenário "nenhum dispositivo disponível" só pode ser reproduzido em um computador com uma única saída de som. Aparelhos Bluetooth e dispositivos com taxa de amostragem diferente de 48000 Hz não foram testados no diagnóstico (DT10).
