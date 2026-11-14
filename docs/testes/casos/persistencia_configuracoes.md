# CT08 — Persistência das configurações

## Título:
Persistência das configurações (DT12).

## Descrição:
Verificar se o Sound Mine guarda as configurações no arquivo `settings.dat`, na pasta do programa, carrega os valores ao abrir e informa pelo NVDA quando o arquivo está danificado, foi alterado fora do programa ou não pode ser lido ou gravado.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o NVDA em execução;
- Começar sem o arquivo `settings.dat` na pasta do programa.

## Passos para a reprodução:

**Primeira execução:**

1. Abrir o Sound Mine;
2. Verificar se o som de abertura toca e se nenhum aviso aparece;
3. Verificar que o arquivo `settings.dat` ainda não existe.

**Salvar e abrir de novo:**

1. Em Configurações, mudar o Formato para ogg, marcar "Desativar dicas do programa" e, na guia Desempenho, digitar 2048 em Memória em megabytes;
2. Ativar Salvar configurações e verificar se o NVDA fala "Configurações salvas.";
3. Verificar que o arquivo `settings.dat` foi criado;
4. Fechar e abrir o Sound Mine;
5. Em Configurações, verificar se os três valores foram mantidos.

**Sons da interface desativados:**

1. Em Configurações, marcar "Desativar sons da interface" e salvar;
2. Fechar e abrir o Sound Mine;
3. Verificar se o som de abertura toca;
4. Navegar pelo menu principal e verificar se os sons de navegação e de borda não tocam;
5. Sair do programa e verificar se o som de fechamento toca.

**Cancelar:**

1. Em Configurações, mudar um valor e ativar Cancelar;
2. Fechar e abrir o Sound Mine;
3. Verificar se o valor anterior foi mantido.

**Arquivo alterado fora do programa:**

1. Com o programa fechado, abrir o `settings.dat` no Bloco de Notas, verificar que nenhum valor das configurações aparece de forma legível, trocar uma letra qualquer e salvar;
2. Abrir o Sound Mine;
3. Verificar se aparece a caixa "Erro ao carregar as configurações" com o texto "As configurações estavam danificadas ou foram alteradas fora do Sound Mine. Os valores padrão foram restaurados. Revise as opções em Configurações.";
4. Verificar se as configurações voltaram ao padrão;
5. Verificar que o arquivo foi renomeado para `settings.dat.invalido`.

**Arquivo danificado:**

1. Com o programa fechado, apagar todo o conteúdo do `settings.dat`, ou escrever um texto qualquer, e salvar;
2. Abrir o Sound Mine e verificar o mesmo aviso e o mesmo resultado do cenário anterior.

**Falha ao gravar:**

1. Com o programa fechado, abrir as propriedades do `settings.dat`, marcar "Somente leitura" e confirmar;
2. Abrir o Sound Mine, mudar um valor em Configurações e salvar;
3. Verificar se aparece a caixa "Erro ao salvar as configurações" com o texto "As configurações foram aplicadas, mas não puderam ser guardadas. Elas voltarão ao padrão quando o programa for fechado. Verifique se há espaço livre no disco.";
4. Verificar se o valor novo vale enquanto o programa está aberto;
5. Desmarcar "Somente leitura" ao terminar.

## Comportamento esperado — caminho feliz:
- Na primeira execução, o programa usa os valores padrão, sem aviso;
- Salvar configurações grava o arquivo e fala "Configurações salvas.";
- Ao abrir, o programa usa os valores guardados;
- Com os sons da interface desativados, a opção continua marcada ao abrir de novo, os sons de navegação, confirmação e borda não tocam, e os sons de abertura e de fechamento tocam;
- Cancelar não grava nada.

## Comportamento esperado — caminho não feliz:
- Um arquivo alterado ou danificado é descartado, guardado como `settings.dat.invalido`, e o programa avisa e usa os padrões;
- Se o arquivo não puder ser gravado, as configurações valem até o programa ser fechado, e o programa avisa;
- Os avisos são caixas de erro lidas pelo NVDA, com o título antes do texto;
- O log registra o motivo, sem o caminho do arquivo nem os valores;
- O programa não trava, não fecha e não apresenta erros inesperados.

## Resultado da execução:
Pendente.

## Observações:
O aviso de arquivo sem permissão de leitura ("O arquivo de configurações está em uso por outro programa ou sem permissão de leitura.") é coberto pelos testes automáticos. Reproduzi-lo manualmente exige negar a permissão de leitura do arquivo nas propriedades de segurança do Windows.
