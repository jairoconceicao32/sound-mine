# CT04 — Sair do programa

## Título:
Sair do programa.

## Descrição:
Verificar se o programa permite encerrar sua execução corretamente por meio da opção Sair, disponível no menu principal, e pela tecla Esc.

## Pré-requisitos:
- Ter o Sound Mine instalado;
- Ter o programa aberto no menu principal.

## Passos para a reprodução:

**Validação pela opção Sair:**

1. Abrir o programa;
2. Acessar o menu principal;
3. Navegar até a opção Sair utilizando as teclas de seta;
4. Ativar a opção utilizando a tecla Enter;
5. Verificar se o programa foi encerrado.

**Validação pela tecla Esc:**

1. Abrir o programa;
2. Permanecer no menu principal;
3. Pressionar a tecla Esc;
4. Verificar se o programa foi encerrado.

## Comportamento esperado — caminho feliz:
- A opção Sair deve estar disponível no menu principal;
- A opção deve ser identificada corretamente pelo NVDA;
- Ao pressionar Enter, o programa deve encerrar sua execução normalmente;
- Ao pressionar Esc, o programa também deve encerrar sua execução, conforme o comportamento implementado;
- O encerramento não deve apresentar erros.

## Comportamento esperado — caminho não feliz:
- O programa não deve apresentar travamentos durante o encerramento;
- O programa não deve apresentar mensagens de erro inesperadas;
- O encerramento não deve deixar processos desnecessários em execução.

## Resultado da execução:
Aprovado.

## Observações:
A funcionalidade de encerramento foi validada com sucesso utilizando tanto a opção Sair, por meio da tecla Enter, quanto a tecla Esc.