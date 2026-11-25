import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.contas.perfis import ADMINISTRADOR, ATENDENTE, criar_perfis_padrao, definir_perfil


class Command(BaseCommand):
    help = (
        "Cria os perfis de acesso e dois usuários de teste (um Administrador e um "
        "Atendente). As senhas são sorteadas e mostradas na tela; nada fica no código."
    )

    def add_arguments(self, parser):
        parser.add_argument("--usuario", default="admin", help="Login do administrador de teste.")
        parser.add_argument("--senha", default=None, help="Senha (se omitida, é sorteada).")
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Permite rodar com DEBUG=False (não use em produção com dados reais).",
        )

    def handle(self, *args, **opcoes):
        if not settings.DEBUG and not opcoes["forcar"]:
            raise CommandError(
                "Este comando é para desenvolvimento. Em produção, crie o primeiro "
                "usuário com 'python manage.py createsuperuser'."
            )
        criar_perfis_padrao()
        senha_admin = opcoes["senha"] or secrets.token_urlsafe(12)
        senha_atendente = secrets.token_urlsafe(12)

        self._criar(opcoes["usuario"], senha_admin, ADMINISTRADOR, superusuario=True)
        self._criar("atendente", senha_atendente, ATENDENTE, superusuario=False)

        self.stdout.write(self.style.SUCCESS("Usuários de teste prontos. Anote as senhas:"))
        self.stdout.write(f"  Administrador -> usuário: {opcoes['usuario']}  senha: {senha_admin}")
        self.stdout.write(f"  Atendente     -> usuário: atendente  senha: {senha_atendente}")

    def _criar(self, login, senha, perfil, superusuario):
        Usuario = get_user_model()
        usuario, _ = Usuario.objects.get_or_create(username=login)
        usuario.is_staff = superusuario
        usuario.is_superuser = superusuario
        usuario.is_active = True
        usuario.set_password(senha)
        usuario.save()
        definir_perfil(usuario, perfil)
        return usuario
