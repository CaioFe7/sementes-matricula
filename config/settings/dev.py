"""Configurações para desenvolvimento local e para os testes."""
from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# Chave apenas para rodar na sua máquina. Em produção a SECRET_KEY é
# obrigatória e vem da variável de ambiente (veja prod.py).
SECRET_KEY = env("SECRET_KEY", default="") or "chave-somente-para-desenvolvimento-local"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
