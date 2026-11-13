# CT05 — Fechar o editor com alterações não salvas

## Título:
Fechar o editor com alterações não salvas (BUG05).

## Descrição:
Verificar se o programa apresenta a confirmação **Sair do editor** ao fechar o editor com alterações não salvas, tanto pela tecla Esc quanto por Alt + F4, e se as três opções funcionam corretamente.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o NVDA em execução;
- Ter um arquivo de áudio válido para abrir.

## Passos para a reprodução:

**Sem alterações:**

1. Abrir um arquivo de áudio;
2. Pressionar Esc e verificar se o programa volta direto ao menu principal;
3. Abrir o arquivo novamente e pressionar Alt + F4;
4. Verificar se o programa fecha sem confirmação.

**Confirmação pelo Esc:**

1. Abrir um arquivo de áudio e remover um trecho;
2. Pressionar Esc;
3. Verificar se o NVDA fala a pergunta "Sair do editor. Há alterações não salvas. O que deseja fazer?" e depois "Salvar e sair";
4. Navegar com as setas e verificar se são faladas as opções "Salvar e sair", "Sair sem salvar" e "Cancelar", com o som de borda nas pontas;
5. Pressionar S várias vezes e verificar se a seleção alterna entre "Salvar e sair" e "Sair sem salvar", sem executar a opção;
6. Pressionar N e verificar se nada acontece;
7. Pressionar C e verificar se "Cancelar" é selecionado, sem executar a opção;
8. Pressionar F1 e verificar se a ajuda mostra a pergunta, as opções e as teclas;
9. Repetir os passos 1 e 2 para cada opção abaixo, confirmando com Enter:
   - **Cancelar:** deve falar "Operação cancelada." e voltar ao editor, com as alterações preservadas;
   - **Esc na confirmação:** deve ter o mesmo resultado de Cancelar;
   - **Sair sem salvar:** deve voltar ao menu principal; ao reabrir o arquivo, as alterações não devem existir;
   - **Salvar e sair:** deve abrir a janela de salvar; ao salvar, deve mostrar "Arquivo salvo" e voltar ao menu principal;
   - **Salvar e sair, cancelando a janela de salvar:** deve falar "O arquivo não foi salvo. O editor continua aberto." e voltar ao editor, com as alterações preservadas.

**Confirmação pelo Alt + F4:**

1. Abrir um arquivo de áudio e remover um trecho;
2. Pressionar Alt + F4;
3. Verificar se a mesma confirmação é apresentada e o programa não fecha;
4. Repetir as opções do passo 9 anterior. Em **Salvar e sair** e **Sair sem salvar**, o programa deve fechar, em vez de voltar ao menu principal;
5. Repetir com o player aberto (T) e com um submenu aberto (R), verificando se a confirmação aparece e se Cancelar volta à tela em que o usuário estava;
6. Pressionar Esc no editor com alterações e, com a confirmação aberta, pressionar Alt + F4. Verificar se a pergunta é repetida, sem abrir outra confirmação.

**Atalhos e outras confirmações:**

1. No menu de edição, verificar se T, R, M, D e S continuam executando as funcionalidades;
2. Na confirmação do Desfazer (D, com alterações), verificar se as opções são "Sim" e "Não", se abre em "Não", e se S e N apenas selecionam, sem executar.

## Comportamento esperado — caminho feliz:
- A confirmação deve ser apresentada pelo Esc e pelo Alt + F4 sempre que houver alterações não salvas;
- As opções devem ser faladas por extenso, sem letras;
- As letras devem apenas selecionar as opções;
- O Enter deve executar a opção selecionada;
- O foco deve continuar no programa ao abrir e fechar a confirmação, sem anúncios de "desconhecido" ou do título da janela.

## Comportamento esperado — caminho não feliz:
- Uma falha ou o cancelamento do salvamento não deve fechar o editor nem descartar as alterações;
- O programa não deve fechar como se o salvamento tivesse sido concluído;
- O programa não deve apresentar travamentos nem mensagens de erro inesperadas.

## Resultado da execução:
Aprovado.

## Observações:
A confirmação de saída foi validada com o NVDA pela tecla Esc e por Alt + F4, com as três opções.

Quando o Windows está sendo desligado, o fechamento pode não ser vetável, e o programa fecha sem perguntar (DT07).
