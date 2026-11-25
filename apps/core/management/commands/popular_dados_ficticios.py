"""Preenche o banco com dados FICTÍCIOS para desenvolvimento e demonstração."""
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.cadastros.models import Bairro, Crianca, Responsavel
from apps.core.utils import gerar_cpf, subtrair_anos
from apps.matriculas.models import Atividade, Matricula

# Bairros de exemplo de Taboão da Serra. Trocar pela lista real da ONG.
BAIRROS = [
    "Jardim Mirna",
    "Centro",
    "Parque Pinheiros",
    "Jardim Record",
    "Jardim Salete",
    "Jardim Maria Rosa",
    "Jardim Trianon",
    "Jardim Saint Moritz",
    "Parque Santos Dumont",
    "Vila Iasi",
    "Jardim Helena",
    "Jardim São Judas Tadeu",
]

# (nome, idade mínima, idade máxima, dias e horários, vagas)
ATIVIDADES = [
    ("Artes e brincadeiras", 4, 8, "Segundas e quartas, das 9h às 11h", 20),
    ("Reforço escolar", 6, 14, "Terças e quintas, das 14h às 16h", 25),
    ("Futebol", 7, 17, "Sábados, das 9h às 11h", 30),
    ("Capoeira", 6, 17, "Quartas e sextas, das 15h às 16h30", 25),
    ("Informática", 10, 17, "Terças e quintas, das 16h às 17h30", 15),
    ("Violão", 9, 17, "Sextas, das 14h às 16h", 12),
]

SITUACOES = [
    (Matricula.Status.ATIVA, 70),
    (Matricula.Status.PENDENTE, 15),
    (Matricula.Status.ENCERRADA, 10),
    (Matricula.Status.RECUSADA, 5),
]

ESCOLAS = [
    "E.M. Jardim das Flores",
    "E.E. Professora Maria Exemplo",
    "E.M. Parque do Saber",
    "E.E. Vila Esperança",
]


class Command(BaseCommand):
    help = (
        "Cria bairros, atividades, responsáveis, crianças e matrículas fictícias "
        "(nomes e CPFs inventados). Nunca use dados reais no desenvolvimento."
    )

    def add_arguments(self, parser):
        parser.add_argument("--quantidade", type=int, default=80, help="Número de crianças.")
        parser.add_argument("--semente", type=int, default=None, help="Semente do sorteio.")
        parser.add_argument(
            "--forcar",
            action="store_true",
            help="Permite rodar com DEBUG=False (não use no banco com dados reais).",
        )

    def handle(self, *args, **opcoes):
        if not settings.DEBUG and not opcoes["forcar"]:
            raise CommandError(
                "Este comando só roda em desenvolvimento (DEBUG=True). "
                "Ele não deve ser usado no banco de produção."
            )
        try:
            from faker import Faker
        except ImportError as erro:
            raise CommandError(
                "O pacote Faker não está instalado. Rode: pip install -r requirements-dev.txt"
            ) from erro

        self.sorteio = random.Random(opcoes["semente"])
        self.fake = Faker("pt_BR")
        if opcoes["semente"] is not None:
            self.fake.seed_instance(opcoes["semente"])

        with transaction.atomic():
            bairros = [Bairro.objects.get_or_create(nome=nome)[0] for nome in BAIRROS]
            atividades = self._criar_atividades()
            total = self._criar_familias(opcoes["quantidade"], bairros, atividades)

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados fictícios criados: {total} crianças, {len(bairros)} bairros "
                f"e {len(atividades)} atividades."
            )
        )

    def _criar_atividades(self):
        atividades = []
        for nome, minima, maxima, horarios, vagas in ATIVIDADES:
            atividade, _ = Atividade.objects.get_or_create(
                nome=nome,
                defaults={
                    "idade_minima": minima,
                    "idade_maxima": maxima,
                    "dias_horarios": horarios,
                    "vagas": vagas,
                },
            )
            atividades.append(atividade)
        return atividades

    def _criar_familias(self, quantidade, bairros, atividades):
        """Cria famílias com 1 a 3 crianças até atingir a quantidade pedida."""
        criadas = 0
        while criadas < quantidade:
            sobrenome = self.fake.last_name()
            # O Jardim Mirna (bairro da ONG) aparece mais vezes no sorteio.
            bairro = self.sorteio.choice(bairros + [bairros[0]] * 4)
            responsavel = self._criar_responsavel(sobrenome, bairro)
            for _ in range(self.sorteio.choice([1, 1, 2, 2, 3])):
                if criadas >= quantidade:
                    break
                crianca = self._criar_crianca(sobrenome, bairro, responsavel)
                self._criar_matricula(crianca, atividades)
                criadas += 1
        return criadas

    def _cpf_inedito(self):
        while True:
            cpf = gerar_cpf(self.sorteio)
            if not Responsavel.objects.filter(cpf=cpf).exists():
                return cpf

    def _telefone(self):
        return "119" + "".join(str(self.sorteio.randint(0, 9)) for _ in range(8))

    def _criar_responsavel(self, sobrenome, bairro):
        feminino = self.sorteio.random() < 0.7
        primeiro_nome = self.fake.first_name_female() if feminino else self.fake.first_name_male()
        tipos = Responsavel.Parentesco
        if feminino:
            parentesco = self.sorteio.choice([tipos.MAE, tipos.MAE, tipos.AVO])
        else:
            parentesco = self.sorteio.choice([tipos.PAI, tipos.PAI, tipos.TIO])
        hoje = timezone.localdate()
        nascimento = subtrair_anos(hoje, self.sorteio.randint(24, 65)) - timedelta(
            days=self.sorteio.randint(0, 364)
        )
        return Responsavel.objects.create(
            nome=f"{primeiro_nome} {sobrenome}",
            cpf=self._cpf_inedito(),
            data_nascimento=nascimento,
            parentesco=parentesco,
            telefone=self._telefone(),
            email=f"familia{self.sorteio.randint(1000, 999999)}@example.com",
            cep=f"067{self.sorteio.randint(50, 99)}{self.sorteio.randint(0, 999):03d}",
            logradouro=f"Rua {self.fake.last_name()} {self.fake.last_name()}",
            numero=str(self.sorteio.randint(1, 999)),
            bairro=bairro,
        )

    def _criar_crianca(self, sobrenome, bairro, responsavel):
        sexo = self.sorteio.choice([Crianca.Sexo.FEMININO, Crianca.Sexo.MASCULINO])
        primeiro_nome = (
            self.fake.first_name_female()
            if sexo == Crianca.Sexo.FEMININO
            else self.fake.first_name_male()
        )
        idade = self.sorteio.randint(4, 17)
        nascimento = subtrair_anos(timezone.localdate(), idade) - timedelta(
            days=self.sorteio.randint(0, 364)
        )
        return Crianca.objects.create(
            nome=f"{primeiro_nome} {sobrenome}",
            data_nascimento=nascimento,
            sexo=sexo,
            bairro=bairro,
            escola=self.sorteio.choice(ESCOLAS),
            serie=f"{max(1, min(idade - 5, 9))}º ano" if idade >= 6 else "Educação infantil",
            responsavel=responsavel,
        )

    def _criar_matricula(self, crianca, atividades):
        possiveis = [a for a in atividades if a.aceita_idade(crianca.idade)]
        if not possiveis:
            return None
        status = self.sorteio.choices(
            [situacao for situacao, _ in SITUACOES], weights=[peso for _, peso in SITUACOES]
        )[0]
        agora = timezone.now()
        solicitacao = agora - timedelta(days=self.sorteio.randint(0, 300))
        matricula = Matricula(
            crianca=crianca,
            atividade=self.sorteio.choice(possiveis),
            status=status,
            origem=self.sorteio.choice(list(Matricula.Origem)),
            data_solicitacao=solicitacao,
            consentimento_lgpd=True,
            data_consentimento=solicitacao,
            versao_termo=settings.VERSAO_TERMO,
        )
        if status in (Matricula.Status.ATIVA, Matricula.Status.ENCERRADA):
            matricula.data_aprovacao = solicitacao + timedelta(days=1)
        if status == Matricula.Status.ENCERRADA:
            matricula.motivo = "Mudança de endereço (dado fictício)."
        if status == Matricula.Status.RECUSADA:
            matricula.motivo = "Turma sem vagas (dado fictício)."
        matricula.save()
        return matricula
