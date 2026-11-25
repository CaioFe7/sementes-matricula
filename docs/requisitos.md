# Requisitos

Levantados a partir do pedido da ONG Sementes do Amanhã. Os itens marcados com "a confirmar" dependem da reunião inicial e da ficha de matrícula atual da ONG.

## O que a ONG pediu

1. Matrícula e cadastro on-line das crianças e adolescentes
2. Quantidade de meninas e meninos atendidos
3. Organização por faixa etária e idade
4. Bairros onde os atendidos residem
5. Cadastro de pais e responsáveis
6. Relatórios quantitativos e estatísticos
7. Consulta dos dados de forma simples e acessível

## Perfis de usuário

| Perfil | Quem é | O que faz |
| --- | --- | --- |
| Responsável | Pai, mãe ou responsável legal | Faz a matrícula on-line, sem login |
| Atendente | Equipe da ONG | Cadastra, consulta, edita e aprova matrículas |
| Administrador | Coordenação da ONG | Tudo o que o atendente faz, mais excluir, exportar e gerenciar usuários, bairros e atividades |

## Requisitos funcionais

| Código | Requisito | Onde está |
| --- | --- | --- |
| RF01 | Matrícula on-line pública em etapas (responsável, criança, atividade, termo), com mais de uma criança por responsável, protocolo ao final, situação inicial Pendente, consentimento obrigatório com data e versão, proteção contra spam e validação de CPF, CEP e telefone | `apps/matriculas/views_publico.py` |
| RF02 | Fila de matrículas pendentes para aprovar ou recusar, com motivo | `apps/matriculas/views.py` |
| RF03 | Cadastro, edição e consulta de responsáveis, crianças e matrículas pela equipe, sem o admin do Django | `apps/cadastros`, `apps/matriculas` |
| RF04 | Listagem com busca por nome ou CPF, filtros por bairro, sexo, faixa etária, atividade e situação, paginação e tela de detalhe com responsáveis e histórico de matrículas | `apps/cadastros/views.py` |
| RF05 | Painel com cartões (atendidos ativos, pendentes, meninas, meninos), gráficos por sexo, faixa etária, bairro e atividade, e filtros por período e situação | `apps/relatorios` |
| RF06 | Exportação dos relatórios em Excel e PDF com os mesmos filtros do painel | `apps/relatorios/exportacao.py` |
| RF07 | Cadastro de bairros e atividades pelo Administrador | `apps/cadastros`, `apps/matriculas` |
| RF08 | Login obrigatório na área interna, com os perfis Administrador e Atendente criados automaticamente | `apps/contas` |
| RF09 | Comandos para criar dados fictícios, os perfis e um usuário admin de teste | `apps/core/management`, `apps/contas/management` |

## Requisitos não funcionais

| Código | Requisito |
| --- | --- |
| RNF01 | Interface simples e em português, pensada para quem tem pouca familiaridade com tecnologia |
| RNF02 | Layout responsivo (mobile first): a matrícula precisa funcionar bem no celular |
| RNF03 | Acessibilidade: rótulos em todos os campos, bom contraste, botões grandes, navegação por teclado |
| RNF04 | Mensagens de erro claras, em português |
| RNF05 | Máscaras de CPF, telefone e CEP; datas no formato dd/mm/aaaa |
| RNF06 | Segurança: HTTPS, cookies seguros, senhas fortes, segredos em variáveis de ambiente |
| RNF07 | LGPD: consentimento, coleta mínima, controle de acesso e backup (ver `lgpd.md`) |
| RNF08 | Custo zero ou muito baixo de hospedagem para a ONG |
| RNF09 | Código organizado, com testes automatizados e CI |

## Histórias de usuário

**Responsável**

- Como mãe, quero matricular meu filho pelo celular, para não precisar ir até a ONG só para preencher uma ficha.
- Como responsável por mais de uma criança, quero matricular todas de uma vez, para não repetir meus dados.
- Como responsável, quero receber um número de protocolo, para acompanhar a matrícula com a equipe.
- Como responsável, quero saber para que meus dados serão usados antes de enviar, para decidir com tranquilidade.

**Atendente**

- Como atendente, quero ver a lista de matrículas pendentes, para aprovar ou recusar cada uma.
- Como atendente, quero buscar uma criança pelo nome ou pelo CPF do responsável, para encontrar o cadastro rápido.
- Como atendente, quero cadastrar uma matrícula feita presencialmente, para que ela também entre nos números.
- Como atendente, quero ver o telefone do responsável na ficha da criança, para entrar em contato.

**Administrador**

- Como coordenadora, quero ver quantas meninas e meninos são atendidos, para prestar contas a parceiros e editais.
- Como coordenadora, quero ver os atendidos por faixa etária e por bairro, para planejar as atividades.
- Como coordenadora, quero exportar o relatório em Excel e PDF, para anexar a prestações de contas.
- Como coordenadora, quero controlar quem tem acesso ao sistema, para proteger os dados das famílias.

## A confirmar com a ONG

- [ ] Campos da ficha de matrícula atual (ajustar os models)
- [ ] Faixas etárias usadas pela ONG (`FAIXAS_ETARIAS` em `config/settings/base.py`)
- [ ] Lista real de bairros e de atividades
- [ ] Quem usa o sistema e por qual aparelho
- [ ] Quais relatórios a ONG entrega e para quem
- [ ] Texto do termo de consentimento e contato para pedidos sobre dados
- [ ] Quem cuida do sistema depois do semestre
