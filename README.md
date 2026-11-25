# Plataforma de Matrícula - ONG Sementes do Amanhã

Sistema web para matrícula on-line e cadastro das crianças e adolescentes atendidos pela ONG Sementes do Amanhã, com painel de indicadores e relatórios.

## Sobre o projeto de extensão

| Item | Descrição |
| --- | --- |
| Instituição de ensino | UniFECAF (Taboão da Serra/SP) |
| Curso | Análise e Desenvolvimento de Sistemas |
| Instituição parceira | ONG Sementes do Amanhã, Jardim Mirna, Taboão da Serra/SP |
| Temática | Temática 1 - Digitalização e Automação de Processos Sociais (com parte da Temática 2 nos relatórios) |
| ODS | ODS 4 (Educação de qualidade) e ODS 10 (Redução das desigualdades) |

## Problema e solução

**Problema.** A ONG precisa organizar a matrícula e o cadastro dos atendidos e responder perguntas simples com rapidez: quantas meninas e meninos são atendidos, de quais idades, de quais bairros. Sem um sistema, esses números dependem de contagem manual.

**Solução.** Uma plataforma em que os pais fazem a matrícula pelo celular, a equipe confere e aprova, e os números aparecem prontos em um painel, com exportação para Excel e PDF.

## Funcionalidades

- **Matrícula on-line pública** em quatro etapas (responsável, criança, atividade, termo), com mais de uma criança por responsável, número de protocolo e consentimento obrigatório.
- **Fila de aprovação**: as matrículas entram como pendentes e a equipe aprova ou recusa (com motivo). Fica registrado quem aprovou e quando.
- **Cadastro interno** de responsáveis, crianças e matrículas, sem precisar do admin do Django.
- **Consulta** com busca por nome ou CPF e filtros por bairro, sexo, faixa etária, atividade e situação.
- **Painel de indicadores** com totais e gráficos por sexo, faixa etária, bairro e atividade.
- **Exportação** dos relatórios em Excel e PDF.
- **Perfis de acesso**: Administrador (acesso total) e Atendente (não exclui nem exporta).
- **Dados fictícios** para desenvolvimento e demonstração.

## Tecnologias utilizadas

| Camada | Tecnologia |
| --- | --- |
| Back-end | Python 3.12 e Django 5.2 (LTS) |
| Banco de dados | PostgreSQL (produção) e SQLite (somente desenvolvimento local) |
| Front-end | Templates do Django e Bootstrap 5 (mobile first) |
| Gráficos | Chart.js |
| Exportação | openpyxl (Excel) e ReportLab (PDF) |
| Configuração | django-environ (variáveis de ambiente) |
| Testes | pytest e pytest-django |
| Dados fictícios | Faker (pt_BR) |
| Produção | gunicorn e WhiteNoise |

O Bootstrap e o Chart.js são carregados por CDN (jsDelivr).

## Estrutura de pastas

```
sementes-matricula/
├── manage.py
├── conftest.py              fixtures dos testes
├── config/                  configuração do projeto
│   ├── settings/            base.py (comum), dev.py (local), prod.py (produção)
│   └── urls.py              rotas principais
├── apps/
│   ├── core/                funções de CPF/idade, validadores, página inicial, privacidade,
│   │                        comando de dados fictícios
│   ├── contas/              login, perfis de acesso, usuários da equipe
│   ├── cadastros/           Bairro, Responsável, Criança/Adolescente
│   ├── matriculas/          Atividade, Matrícula, formulário público, fila de aprovação
│   └── relatorios/          painel de indicadores e exportações
├── templates/               base.html e as telas de cada app
├── static/                  css e js
├── docs/                    requisitos, modelagem, LGPD e manual do usuário
└── .github/                 CI, modelos de issue e de pull request
```

Cada app tem `models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py` (quando tem models) e uma pasta `tests/`.

## Como rodar localmente

Você precisa do Python 3.12 instalado.

### Opção 1: sem Docker (SQLite)

```bash
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate

# 2. Instalar as dependências
pip install -r requirements-dev.txt

# 3. Criar o arquivo de configuração
cp .env.example .env             # no Windows: copy .env.example .env

# 4. Aplicar as migrations (cria as tabelas)
python manage.py migrate

# 5. Criar os usuários de teste e os dados fictícios
python manage.py criar_admin_teste
python manage.py popular_dados_ficticios

# 6. Subir o servidor
python manage.py runserver
```

Abra http://127.0.0.1:8000/. A área da equipe fica em http://127.0.0.1:8000/conta/entrar/.

> Sempre que você alterar um model, rode `python manage.py makemigrations` e inclua no Git o arquivo criado na pasta `migrations/` do app. O CI confere se as migrations estão em dia.

### Opção 2: com Docker (PostgreSQL)

```bash
# 1. No arquivo .env, defina POSTGRES_PASSWORD e a DATABASE_URL:
#    DATABASE_URL=postgres://sementes:SUA_SENHA@localhost:5432/sementes

# 2. Subir o banco
docker compose up -d

# 3. Seguir os passos 1, 2, 4, 5 e 6 da opção 1
```

## Variáveis de ambiente

Todas ficam no arquivo `.env` (que não vai para o GitHub). Veja o modelo em `.env.example`.

| Variável | Para que serve | Obrigatória em produção |
| --- | --- | --- |
| `SECRET_KEY` | Chave secreta do Django | Sim |
| `DEBUG` | `True` só no desenvolvimento | Não (em produção é sempre `False`) |
| `ALLOWED_HOSTS` | Endereços do site, separados por vírgula | Sim |
| `CSRF_TRUSTED_ORIGINS` | Endereço com `https://`, se usar domínio próprio | Depende |
| `DATABASE_URL` | Conexão com o PostgreSQL | Sim |
| `ADMIN_URL` | Caminho do admin do Django (troque o padrão) | Recomendado |
| `CONTATO_PRIVACIDADE` | Contato exibido na página de privacidade | Recomendado |
| `DJANGO_SETTINGS_MODULE` | Em produção: `config.settings.prod` | Sim |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Usadas só pelo docker-compose | Não |

## Dados fictícios e usuário admin

```bash
python manage.py criar_admin_teste          # cria "admin" e "atendente" e mostra as senhas sorteadas
python manage.py popular_dados_ficticios    # cerca de 80 crianças, com responsáveis e matrículas
python manage.py popular_dados_ficticios --quantidade 200 --semente 1
python manage.py criar_perfis               # só cria os perfis Administrador e Atendente
```

Os dois primeiros comandos só rodam com `DEBUG=True`. Em produção, crie o primeiro usuário com `python manage.py createsuperuser` e depois cadastre a equipe pela tela **Administração > Usuários**.

Os bairros criados são exemplos de Taboão da Serra e devem ser trocados pela lista real da ONG.

## Como rodar os testes

```bash
pytest               # todos os testes
pytest apps/core     # só um app
ruff check .         # verificação de estilo
```

Os testes cobrem o cálculo de idade e faixa etária, a validação de CPF, o formulário público (consentimento, protocolo e situação pendente), as permissões dos perfis e as contagens do painel.

## LGPD e segurança

O sistema guarda dados de crianças e adolescentes, que a LGPD trata com cuidado especial (art. 14).

- O formulário público exige o consentimento do responsável e registra a data e a versão do termo.
- Só são pedidos os dados que a ONG usa.
- A área interna exige login. Só o Administrador exclui registros e exporta relatórios.
- Fica registrado quem aprovou cada matrícula e quando.
- Senhas e chaves ficam em variáveis de ambiente, nunca no código.
- Em produção: HTTPS obrigatório, cookies seguros e HSTS.
- **É proibido usar dados reais no repositório e no desenvolvimento.** Use apenas os dados fictícios.

Detalhes, backup e restauração em [docs/lgpd.md](docs/lgpd.md).

## Deploy

O projeto está preparado para serviços como Render ou Railway (`render.yaml` e `Procfile`).

1. Crie a conta em nome da ONG, para que ela seja a dona do sistema e dos dados.
2. Crie um banco PostgreSQL e um serviço web apontando para o repositório.
3. Defina as variáveis de ambiente da tabela acima, com `DJANGO_SETTINGS_MODULE=config.settings.prod`.
4. Comando de build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
5. Comando de início: `gunicorn config.wsgi:application`
6. Crie o primeiro usuário com `python manage.py createsuperuser`.
7. Cadastre os bairros e as atividades reais em **Administração**.

Antes de escolher a hospedagem, confira os limites atuais do plano gratuito (alguns serviços apagam o banco gratuito depois de um período ou "adormecem" o site sem uso) e configure o backup descrito em `docs/lgpd.md`.

## Roadmap

Fase 2, depois do MVP entregue:

- Controle de frequência nas atividades
- Lista de espera por turma
- Cadastro de voluntários

## Documentação

- [Requisitos e histórias de usuário](docs/requisitos.md)
- [Modelagem de dados](docs/modelagem.md)
- [LGPD, backup e restauração](docs/lgpd.md)
- [Manual do usuário](docs/manual-usuario.md)

## Autor

Guilherme Cruz - Análise e Desenvolvimento de Sistemas - UniFECAF

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
