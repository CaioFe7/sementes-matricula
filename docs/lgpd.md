# LGPD e segurança

O sistema guarda dados pessoais de crianças e adolescentes. A Lei Geral de Proteção de Dados (Lei nº 13.709/2018) trata esses dados com cuidado especial no art. 14: o tratamento deve ser feito no melhor interesse da criança e com o consentimento de pelo menos um dos pais ou do responsável legal.

Este documento é um ponto de partida técnico. O texto do termo e da política de privacidade deve ser revisado com a ONG.

## Quais dados são coletados e por quê

| Dado | De quem | Por que é coletado |
| --- | --- | --- |
| Nome completo | Responsável e criança | Identificar a família e o atendido |
| CPF | Responsável | Evitar cadastro duplicado e identificar quem consentiu |
| Data de nascimento | Responsável e criança | Diferenciar pessoas com o mesmo nome (responsável); calcular idade e faixa etária (criança) |
| Parentesco | Responsável | Saber a relação com a criança |
| Telefones e e-mail | Responsável | Confirmar a matrícula e avisar sobre as atividades |
| Endereço e bairro | Responsável e criança | Relatório de bairros atendidos e contato |
| Sexo | Criança | Relatório de meninas e meninos atendidos (há a opção "Prefiro não informar") |
| Escola e série | Criança | Acompanhamento escolar (opcional) |
| Observações de saúde | Criança | Cuidado durante as atividades: alergias, medicação (opcional) |
| Atividade, datas e situação | Matrícula | Organizar turmas e vagas |
| Consentimento, data e versão do termo | Matrícula | Comprovar que o responsável autorizou |

Regra geral: coletar só o que a ONG realmente usa. Se um campo não for usado, remova.

As observações de saúde são dado pessoal sensível. São opcionais e aparecem apenas na ficha da criança e na ficha da matrícula; não entram nos relatórios exportados.

## Quem acessa

| Quem | O que vê |
| --- | --- |
| Público (sem login) | Apenas o formulário de matrícula e os próprios dados digitados durante o preenchimento |
| Atendente | Cadastros e matrículas. Não exclui e não exporta |
| Administrador | Tudo, incluindo exclusão, exportação e gestão de usuários |

Os relatórios do painel e o PDF mostram apenas totais, sem nomes. A planilha Excel traz a lista nominal e por isso só o Administrador pode gerá-la.

## Consentimento

- No formulário público, a matrícula só é enviada com a caixa de consentimento marcada.
- Ficam gravados: que houve consentimento, a data e a hora, e a versão do termo aceito.
- Quando o texto do termo mudar, aumente `VERSAO_TERMO` em `config/settings/base.py`.
- Na matrícula feita pela equipe, o atendente confirma que o responsável assinou o termo em papel.
- Enquanto o responsável preenche as etapas, os dados ficam guardados na sessão do navegador (tabela de sessões do Django) e só vão para os cadastros depois do consentimento. Formulários abandonados expiram sozinhos; para apagar as sessões vencidas, agende `python manage.py clearsessions` (por exemplo, uma vez por semana).

## Direitos do titular

O responsável pode pedir para ver, corrigir ou apagar os dados. Como atender:

- **Ver ou corrigir:** a equipe abre a ficha do responsável ou da criança e edita.
- **Apagar:** o Administrador exclui a criança (as matrículas vão junto) e depois o responsável.

O contato para esses pedidos aparece na página de privacidade e é definido na variável `CONTATO_PRIVACIDADE`.

## Medidas de segurança no sistema

- HTTPS obrigatório em produção, cookies seguros e HSTS (`config/settings/prod.py`).
- Senhas da equipe com no mínimo 10 caracteres, guardadas com hash pelo Django.
- A área interna inteira exige login; cada tela confere o perfil.
- Endereço do admin do Django configurável (`ADMIN_URL`).
- Proteção contra CSRF em todos os formulários e campo-armadilha contra robôs no formulário público.
- Registro de quem aprovou cada matrícula e quando.
- Nenhuma senha, chave ou credencial no código: tudo em variáveis de ambiente.
- `.env`, banco SQLite, backups e arquivos exportados estão no `.gitignore`.

## Regras para quem desenvolve

- **Nunca** use dados reais no GitHub, em issues, em capturas de tela ou no ambiente de desenvolvimento.
- Para testar, use `python manage.py popular_dados_ficticios`.
- Dados reais só existem no ambiente de produção.
- Não copie o banco de produção para a sua máquina.

## Backup do banco (PostgreSQL)

Faça o backup com `pg_dump`. A conexão vem da variável `DATABASE_URL` do ambiente de produção.

```bash
# Gera um arquivo compactado com a data no nome
pg_dump "$DATABASE_URL" --format=custom --no-owner --file="backup-$(date +%Y-%m-%d).dump"
```

Recomendações:

- Faça backup automático diário (muitos serviços de hospedagem oferecem; se não, agende o comando acima).
- Guarde as cópias fora do servidor do site, em local com acesso restrito à coordenação da ONG.
- O arquivo de backup contém dados pessoais: proteja com senha e não envie por e-mail ou WhatsApp.
- Mantenha as cópias por um período definido (por exemplo, 30 dias) e apague as antigas.

## Restauração

```bash
# Restaura o backup em um banco vazio
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" backup-2026-01-31.dump
```

**Teste a restauração** pelo menos uma vez antes de o sistema entrar no ar, e depois a cada semestre:

1. Crie um banco vazio de teste.
2. Restaure o backup mais recente nele.
3. Aponte uma cópia do sistema para esse banco e confira se os cadastros aparecem.
4. Apague o banco de teste.

Um backup que nunca foi restaurado não é garantia de nada.

## Se houver um incidente

Se houver suspeita de acesso indevido ou vazamento:

1. Troque as senhas da equipe e a `SECRET_KEY`.
2. Avise a coordenação da ONG imediatamente.
3. Registre o que aconteceu, quando e quais dados foram afetados.
4. A ONG avalia a comunicação aos responsáveis e à ANPD, conforme a LGPD.

## Checklist antes de usar com dados reais

- [ ] Texto do termo e da política de privacidade revisado com a ONG
- [ ] `CONTATO_PRIVACIDADE` definido
- [ ] `SECRET_KEY` forte e exclusiva de produção
- [ ] `ADMIN_URL` diferente do padrão
- [ ] HTTPS funcionando
- [ ] Usuários de teste removidos e senhas fortes para a equipe
- [ ] Backup automático configurado e restauração testada
- [ ] Conta de hospedagem em nome da ONG
- [ ] Dados fictícios apagados do banco de produção
