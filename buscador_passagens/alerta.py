"""Envio de alertas por e-mail.

Duas formas (configuradas por variáveis de ambiente / segredos do GitHub):

1) Brevo (recomendado — não precisa de senha de e-mail):
    ALERTA_EMAIL      destinatário(s), separados por vírgula
    BREVO_API_KEY     chave da API da Brevo (brevo.com > SMTP & API > API Keys)
    REMETENTE_EMAIL   e-mail confirmado como remetente na Brevo

2) SMTP (ex.: Gmail com senha de app):
    ALERTA_EMAIL, SMTP_USUARIO, SMTP_SENHA
    SMTP_SERVIDOR (padrão smtp.gmail.com), SMTP_PORTA (padrão 465)
"""
import os
import smtplib
from email.message import EmailMessage

import requests

from .modelos import Oferta

URL_BREVO = "https://api.brevo.com/v3/smtp/email"


class ConfigEmailFaltando(Exception):
    pass


class ErroEnvioEmail(Exception):
    pass


def montar_email(ofertas: list[Oferta], titulo_busca: str, top: int = 5) -> tuple[str, str]:
    """Devolve (assunto, corpo) do e-mail."""
    melhor = ofertas[0]
    assunto = f"✈️ {titulo_busca}: {melhor.preco} {melhor.moeda} ({melhor.companhia})"
    linhas = [f"Melhores preços encontrados para {titulo_busca}:", ""]
    for i, o in enumerate(ofertas[:top], 1):
        linhas.append(f"{i}. {o.resumo()}")
    linhas += ["", "Preço total para todos os passageiros. Confira bagagem e regras "
                   "de tarifa no site da companhia antes de comprar."]
    return assunto, "\n".join(linhas)


def _destinatarios() -> list[str]:
    return [e.strip() for e in os.environ.get("ALERTA_EMAIL", "").split(",") if e.strip()]


def _enviar_brevo(assunto: str, corpo: str, destinatarios: list[str]) -> None:
    remetente = os.environ.get("REMETENTE_EMAIL")
    if not remetente:
        raise ConfigEmailFaltando("Defina REMETENTE_EMAIL (o e-mail confirmado na Brevo).")
    resposta = requests.post(
        URL_BREVO,
        headers={"api-key": os.environ["BREVO_API_KEY"], "accept": "application/json"},
        json={
            "sender": {"name": "Alerta de Passagens", "email": remetente},
            "to": [{"email": e} for e in destinatarios],
            "subject": assunto,
            "textContent": corpo,
        },
        timeout=30,
    )
    if resposta.status_code >= 400:
        raise ErroEnvioEmail(f"Brevo respondeu {resposta.status_code}: {resposta.text[:300]}")


def _enviar_smtp(assunto: str, corpo: str, destinatarios: list[str]) -> None:
    usuario, senha = os.environ.get("SMTP_USUARIO"), os.environ.get("SMTP_SENHA")
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = usuario
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(corpo)
    servidor = os.environ.get("SMTP_SERVIDOR", "smtp.gmail.com")
    porta = int(os.environ.get("SMTP_PORTA", "465"))
    with smtplib.SMTP_SSL(servidor, porta, timeout=30) as smtp:
        smtp.login(usuario, senha)
        smtp.send_message(msg)


def enviar_email(assunto: str, corpo: str) -> list[str]:
    destinatarios = _destinatarios()
    if not destinatarios:
        raise ConfigEmailFaltando("Defina ALERTA_EMAIL (quem recebe o alerta).")
    if os.environ.get("BREVO_API_KEY"):
        _enviar_brevo(assunto, corpo, destinatarios)
    elif os.environ.get("SMTP_USUARIO") and os.environ.get("SMTP_SENHA"):
        _enviar_smtp(assunto, corpo, destinatarios)
    else:
        raise ConfigEmailFaltando(
            "Defina BREVO_API_KEY + REMETENTE_EMAIL (Brevo) ou SMTP_USUARIO + SMTP_SENHA.")
    return destinatarios
