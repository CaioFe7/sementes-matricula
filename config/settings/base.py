"""Configurações comuns a todos os ambientes.

Nenhuma senha ou chave fica neste arquivo: tudo o que é sensível vem de
variáveis de ambiente (veja o arquivo .env.example).
"""
from pathlib import Path

import environ
from django.contrib.messages import constants as niveis_mensagem

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Endereço do admin do Django, configurável para não ficar no caminho padrão.
ADMIN_URL = env("ADMIN_URL", default="admin/").strip("/") + "/"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.contas",
    "apps.cadastros",
    "apps.matriculas",
    "apps.relatorios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.area_interna",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Banco de dados: PostgreSQL quando DATABASE_URL está definida;
# SQLite apenas como apoio no desenvolvimento local.
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "contas:login"
LOGIN_REDIRECT_URL = "relatorios:painel"
LOGOUT_REDIRECT_URL = "core:inicio"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MESSAGE_TAGS = {niveis_mensagem.ERROR: "danger", niveis_mensagem.DEBUG: "secondary"}

# ---------------------------------------------------------------------------
# Configurações do projeto
# ---------------------------------------------------------------------------

NOME_ONG = "ONG Sementes do Amanhã"

# Faixas etárias usadas nos filtros e relatórios (idade mínima, idade máxima).
# Este é o único lugar a alterar quando a ONG confirmar as faixas.
FAIXAS_ETARIAS = [(0, 5), (6, 8), (9, 11), (12, 14), (15, 17)]

# Idade máxima aceita no formulário público de matrícula.
IDADE_MAXIMA_ATENDIMENTO = 17

# Versão do termo de consentimento. Mude o número sempre que o texto mudar,
# para ficar registrado qual versão cada responsável aceitou.
VERSAO_TERMO = "1.0"

PREFIXO_PROTOCOLO = "SEM"

# Contato exibido na página de privacidade (e-mail ou telefone da ONG).
CONTATO_PRIVACIDADE = env("CONTATO_PRIVACIDADE", default="")
