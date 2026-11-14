# CT07 — Registro de erros em arquivo

## Título:
Registro de erros em arquivo (BUG04, etapa 3).

## Descrição:
Verificar se os erros do Sound Mine são gravados no arquivo de log com a operação e os dados técnicos aprovados, sem expor informações pessoais, e se o funcionamento do programa e a experiência com o NVDA continuam iguais.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o NVDA em execução;
- Ter um arquivo de áudio válido com um nome pessoal, por exemplo `C:\testes\Maria voz.mp3`;
- Ter um arquivo corrompido, por exemplo um texto renomeado para `Maria corrompido.wav`;
- Se existirem, apagar a pasta `logs` dentro da pasta do Sound Mine e a pasta `%LOCALAPPDATA%\Sound Mine\logs` antes de começar.

## Passos para a reprodução:

**Arquivo só criado no primeiro erro:**

1. Abrir o Sound Mine, navegar pelos menus e fechar sem provocar erros;
2. Verificar que não foi criada a pasta `logs` dentro da pasta do Sound Mine, nem o arquivo `sound_mine.log` em `%LOCALAPPDATA%\Sound Mine\logs`.

**Erros com operação:**

1. Abrir o arquivo corrompido;
2. Bloquear o arquivo válido pelo PowerShell (ver CT do P1) e tentar abri-lo;
3. Abrir um arquivo válido e, no editor, usar R e depois A com o cursor no início;
4. Pressionar D sem alterações;
5. Usar M, A e I escolhendo o arquivo bloqueado;
6. Tentar salvar em `C:\Program Files` (ver CT do P2);
7. Fechar o programa;
8. Abrir o log em `logs\sound_mine.log`, dentro da pasta do Sound Mine, pelo Bloco de Notas;
9. Verificar que nada foi gravado em `%LOCALAPPDATA%\Sound Mine\logs`, porque a pasta do programa aceita gravação;
10. Conferir com `git status` que a pasta `logs` não aparece como arquivo novo.

**Reserva em `%LOCALAPPDATA%` (opcional):**

1. Com o programa fechado, abrir as propriedades da pasta `logs` do Sound Mine, guia Segurança, e negar a permissão de gravação para o seu usuário;
2. Abrir o programa e provocar um erro;
3. Verificar que o registro foi gravado em `%LOCALAPPDATA%\Sound Mine\logs\sound_mine.log`;
4. Restaurar a permissão da pasta `logs` ao final.

**Conferência do log:**

1. A primeira linha começa com `===` e mostra a versão do Sound Mine, do Windows, do Python, das bibliotecas e se o leitor de tela está disponível;
2. Há **um** registro para cada erro provocado, com `operação=abrir arquivo`, `remover trecho`, `desfazer`, `adicionar áudio` e `salvar`;
3. Os registros de abrir e de adicionar áudio mostram `arquivo=(.wav, … bytes)` ou `arquivo=(.mp3, … bytes)`;
4. O registro de salvar mostra só `arquivo=(.mp3)`, ou a extensão configurada;
5. Pesquisar com Ctrl+F e confirmar que **não** aparecem: "Maria", o nome da pasta dos arquivos, o nome do usuário do Windows nem o nome do dispositivo de som;
6. Os tracebacks mostram caminhos como `src\models\audio_player.py` e `<arquivo>.mp3`.

**Funcionamento preservado:**

1. Em todos os erros acima, o NVDA lê o mesmo título ("Erro ao …") e a mesma mensagem de antes;
2. O foco volta para onde estava depois de fechar cada caixa;
3. Nenhuma mensagem sobre o log é mostrada ou falada.

**Falha do próprio log (opcional):**

1. Com o programa fechado, abrir as propriedades de `sound_mine.log`, marcar "Somente leitura" e aplicar;
2. Abrir o programa e repetir um erro;
3. Verificar que o erro é mostrado normalmente e que o programa não trava;
4. Desmarcar "Somente leitura" ao final.

## Comportamento esperado — caminho feliz:
- Cada erro gera exatamente um registro, com a operação;
- Os dados do arquivo se limitam à extensão e ao tamanho;
- O log não contém dados pessoais;
- O comportamento e as falas do programa não mudam.

## Comportamento esperado — caminho não feliz:
- Se o log não puder ser gravado, o programa continua funcionando sem avisos adicionais;
- O programa não trava nem fecha por causa do log.

## Resultado da execução:
Pendente.

## Observações:
O log fica limitado a 1 MB, com até 3 cópias anteriores (`sound_mine.log.1` a `.3`).
