"""Envio de alertas por e-mail (SMTP).

Configuração por variáveis de ambiente (arquivo .env ou segredos do GitHub):
    ALERTA_EMAIL     destinatário(s), separados por vírgula
    SMTP_USUARIO     e-mail que envia (ex.: seu Gmail)
    SMTP_SENHA       no Gmail, uma "senha de app" (não a senha normal)
    SMTP_SERVIDOR    padrão: smtp.gmail.com
    SMTP_PORTA       padrão: 465 (SSL)
"""
import os
import smtplib
from email.message import EmailMessage

from .modelos import Oferta


class ConfigEmailFaltando(Exception):
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


def enviar_email(assunto: str, corpo: str) -> list[str]:
    destinatarios = [e.strip() for e in os.environ.get("ALERTA_EMAIL", "").split(",") if e.strip()]
    usuario = os.environ.get("SMTP_USUARIO")
    senha = os.environ.get("SMTP_SENHA")
    if not (destinatarios and usuario and senha):
        raise ConfigEmailFaltando(
            "Defina ALERTA_EMAIL, SMTP_USUARIO e SMTP_SENHA para enviar e-mails.")

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
    return destinatarios
