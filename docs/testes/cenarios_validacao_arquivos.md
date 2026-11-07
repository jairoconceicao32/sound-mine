# Validação de formatos de arquivos

## 1. Objetivo

Testar se os formatos de arquivos de áudio são válidos, inválidos ou estão corrompidos, verificando se o Sound Mine consegue identificar e carregar corretamente os arquivos suportados.

## 2. Pré-condições

* Possuir arquivos de áudio válidos, inválidos, corrompidos e vazios para a execução dos testes.

## 3. Dados para validação

* Arquivos de áudio;
* Formatos de arquivos suportados: MP3, M4A, OGG e WAV;
* Arquivos com extensões não suportadas;
* Arquivos de áudio com diferentes durações.

## 4. Cenários para validação

### CT01 - Formato de arquivo válido

Dado um arquivo de áudio válido nos formatos MP3, M4A, OGG ou WAV,

Quando a função de abrir arquivos for acionada,

Então o arquivo deve ser carregado corretamente,

E deve ser exibida uma mensagem curta de confirmação de carregamento,

E as opções do editor devem ser apresentadas.

### CT02 - Formato de arquivo inválido

Dado um arquivo com formato não suportado pelo Sound Mine,

Quando a função de abrir arquivos for acionada,

Então os arquivos com extensões não suportadas não devem ser apresentados como opções de abertura,

E o sistema não deve permitir o carregamento de formatos não suportados.

### CT03 - Arquivos grandes

Dado um arquivo de áudio válido com duração superior a 30 minutos,

Quando a função de abrir arquivos for acionada,

Então o arquivo deve ser carregado corretamente,

E deve ser exibida uma mensagem curta de confirmação de carregamento,

E o sistema deve respeitar os limites de memória e as configurações estabelecidas.

### CT04 - Validar a integridade do arquivo

Dado um arquivo de áudio corrompido,

Quando a função de abrir arquivos for acionada,

Então o arquivo não deve ser carregado,

E deve ser exibida uma mensagem de erro,

E o Sound Mine deve permanecer funcional após a tentativa de abertura.

### CT05 - Arquivo de outro formato renomeado para uma extensão de áudio suportada

Dado um arquivo de formato não suportado, como TXT, renomeado com uma extensão de áudio suportada, como MP3,

Quando a função de abrir arquivos for acionada,

Então o arquivo deve ser identificado como inválido,

E não deve ser carregado pelo Sound Mine.

### CT06 - Arquivo de áudio vazio

Dado um arquivo de áudio sem conteúdo,

Quando a função de abrir arquivos for acionada,

Então o arquivo não deve ser carregado,

E deve ser exibida uma mensagem informando que o arquivo está vazio ou é inválido.