#!/usr/bin/env python
"""Utilitário de linha de comando do Django."""
import os
import sys


def main():
    """Executa as tarefas administrativas."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as erro:
        raise ImportError(
            "Não foi possível importar o Django. Ative o ambiente virtual e "
            "instale as dependências com: pip install -r requirements-dev.txt"
        ) from erro
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
