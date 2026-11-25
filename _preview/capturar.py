"""Tira capturas de tela do sistema rodando com dados fictícios (uso temporário)."""
import os
import random
import sys
import traceback
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from apps.core.utils import gerar_cpf, subtrair_anos  # noqa: E402

BASE = "http://127.0.0.1:8000"
SAIDA = Path("_telas")
SAIDA.mkdir(exist_ok=True)
SENHA = os.environ["SENHA_ADMIN"]
erros = []


def foto(pagina, nome):
    pagina.wait_for_timeout(400)
    pagina.screenshot(path=str(SAIDA / f"{nome}.png"), full_page=True)
    print("ok", nome)


def tentar(nome, funcao):
    try:
        funcao()
    except Exception:
        erros.append(f"### {nome}\n{traceback.format_exc()}")
        print("ERRO", nome)


def entrar(pagina):
    pagina.goto(f"{BASE}/conta/entrar/")
    pagina.fill("#id_username", "admin")
    pagina.fill("#id_password", SENHA)
    pagina.click("main button[type=submit]")
    pagina.wait_for_url(f"{BASE}/equipe/")


def fluxo_publico(pagina):
    pagina.goto(f"{BASE}/")
    foto(pagina, "01-celular-inicio")

    pagina.goto(f"{BASE}/matricula/")
    pagina.fill("#id_nome", "Maria Exemplo da Silva")
    pagina.fill("#id_cpf", gerar_cpf(random.Random(7)))
    pagina.fill("#id_data_nascimento", "1990-05-10")
    pagina.select_option("#id_parentesco", "mae")
    pagina.fill("#id_telefone", "11912345678")
    pagina.fill("#id_cep", "06750000")
    pagina.fill("#id_logradouro", "Rua Exemplo")
    pagina.fill("#id_numero", "100")
    pagina.select_option("#id_bairro", label="Jardim Mirna")
    foto(pagina, "02-celular-matricula-responsavel")
    pagina.click("main form button[type=submit]")
    pagina.wait_for_url(f"{BASE}/matricula/crianca/")

    pagina.fill("#id_nome", "Ana Exemplo da Silva")
    pagina.fill("#id_data_nascimento", subtrair_anos(date.today(), 9).isoformat())
    pagina.select_option("#id_sexo", "F")
    foto(pagina, "03-celular-matricula-crianca")
    pagina.click("button[value=continuar]")
    pagina.wait_for_url(f"{BASE}/matricula/atividade/")

    pagina.select_option("#id_atividade_0", index=1)
    foto(pagina, "04-celular-matricula-atividade")
    pagina.click("main form button[type=submit]")
    pagina.wait_for_url(f"{BASE}/matricula/termo/")

    pagina.check("#id_consentimento")
    foto(pagina, "05-celular-matricula-termo")
    pagina.click("main form button[type=submit]")
    pagina.wait_for_url(f"{BASE}/matricula/concluida/")
    foto(pagina, "06-celular-matricula-concluida")


def erro_de_validacao(pagina):
    pagina.goto(f"{BASE}/matricula/")
    pagina.fill("#id_nome", "Teste")
    pagina.fill("#id_cpf", "12345678900")
    pagina.click("main form button[type=submit]")
    foto(pagina, "07-celular-matricula-erros")


def area_interna(pagina, prefixo):
    entrar(pagina)
    pagina.wait_for_timeout(1800)  # tempo para os gráficos desenharem
    foto(pagina, f"{prefixo}-painel")

    pagina.goto(f"{BASE}/equipe/matriculas/pendentes/")
    foto(pagina, f"{prefixo}-pendentes")

    pagina.locator("table tbody a.btn-outline-primary").first.click()
    pagina.wait_for_load_state()
    foto(pagina, f"{prefixo}-matricula-detalhe")

    pagina.goto(f"{BASE}/equipe/criancas/")
    foto(pagina, f"{prefixo}-criancas")

    pagina.locator("table tbody td a").first.click()
    pagina.wait_for_load_state()
    foto(pagina, f"{prefixo}-crianca-detalhe")


def telas_extras(pagina):
    pagina.goto(f"{BASE}/equipe/criancas/nova/")
    foto(pagina, "20-computador-crianca-nova")
    pagina.goto(f"{BASE}/equipe/responsaveis/")
    foto(pagina, "21-computador-responsaveis")
    pagina.goto(f"{BASE}/equipe/atividades/")
    foto(pagina, "22-computador-atividades")
    pagina.goto(f"{BASE}/conta/usuarios/")
    foto(pagina, "23-computador-usuarios")
    pagina.goto(f"{BASE}/privacidade/")
    foto(pagina, "24-computador-privacidade")


with sync_playwright() as p:
    navegador = p.chromium.launch()

    celular = navegador.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="pt-BR"
    )
    pagina = celular.new_page()
    tentar("fluxo público", lambda: fluxo_publico(pagina))
    tentar("erros de validação", lambda: erro_de_validacao(pagina))
    celular.close()

    celular_equipe = navegador.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="pt-BR"
    )
    pagina = celular_equipe.new_page()
    tentar("área interna no celular", lambda: area_interna(pagina, "08-celular"))
    celular_equipe.close()

    computador = navegador.new_context(viewport={"width": 1280, "height": 800}, locale="pt-BR")
    pagina = computador.new_page()
    mensagens = []
    pagina.on("console", lambda m: mensagens.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    pagina.on("pageerror", lambda e: mensagens.append(f"pageerror: {e}"))
    tentar("área interna no computador", lambda: area_interna(pagina, "10-computador"))
    tentar("telas extras", lambda: telas_extras(pagina))
    computador.close()
    navegador.close()

(SAIDA / "erros.txt").write_text("\n\n".join(erros) or "nenhum erro\n")
(SAIDA / "console.txt").write_text("\n".join(mensagens) or "nenhum erro no console\n")
