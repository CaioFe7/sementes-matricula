from django.apps import AppConfig


class ContasConfig(AppConfig):
    name = "apps.contas"
    verbose_name = "Contas e perfis de acesso"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .perfis import criar_perfis_apos_migrate

        # Os perfis Administrador e Atendente são criados sozinhos depois de
        # cada "python manage.py migrate".
        post_migrate.connect(criar_perfis_apos_migrate, dispatch_uid="contas.criar_perfis")
