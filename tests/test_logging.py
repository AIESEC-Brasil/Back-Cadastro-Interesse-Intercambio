import logging

from app.core.logger import log_resposta_externa


def test_log_resposta_externa_redacts_sensitive_values(caplog) -> None:
    logger = logging.getLogger("test.integration")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        log_resposta_externa(
            logger,
            "B2C",
            502,
            {
                "message": (
                    "Falha para pessoa@example.org, telefone "
                    "+55 11 99999-1234, Bearer segredo"
                ),
                "data": {"nome": "Pessoa", "access_token": "segredo"},
                "raw": '{"password": "segredo-json"}',
            },
        )

    mensagem = caplog.text
    assert "Falha para" in mensagem
    assert "502" in mensagem
    assert "Pessoa" not in mensagem
    assert "pessoa@example.org" not in mensagem
    assert "99999-1234" not in mensagem
    assert "segredo" not in mensagem
    assert "segredo-json" not in mensagem
