from django.core.management.base import BaseCommand

from apps.contas.perfis import PERFIS, criar_perfis_padrao


class Command(BaseCommand):
    help = "Cria os perfis de acesso (grupos) Administrador e Atendente."

    def handle(self, *args, **opcoes):
        criar_perfis_padrao()
        self.stdout.write(self.style.SUCCESS(f"Perfis prontos: {', '.join(PERFIS)}"))
