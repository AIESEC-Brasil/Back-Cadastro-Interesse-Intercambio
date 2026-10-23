import os
import unittest
from datetime import datetime
from unittest.mock import patch

for key, value in {
    "AMBIENTE": "TEST",
    "CACHE_TTL": "3600",
    "APPSCRIPT_B2C": "https://example.test/b2c",
    "APPSCRIPT_DIVISAO_MERCADO": "https://example.test/market",
    "APPSCRIPT_EXPA": "https://example.test/expa",
    "TOKEN_EXPA": "test-token",
    "DOMINIOS_PERMITIDOS": "example.test",
}.items():
    os.environ.setdefault(key, value)

from app.cache import cache
from app.dto import CriarPreCadastroLead, LeadPreCadastroOutput, QualificacaoLead
from app.dto.persistence import LeadPersistencia
from app.controller import NewLeadOgxController as cadastro_controller
from app.utils.payload import montar_dto_persistencia


class LeadPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        cache.store.clear()
        options = {
            "produto": [{"id": 1, "text": "Voluntário Global"}],
            "aiesec_proxima": [{"id": 23, "text": "AIESEC em São Paulo"}],
            "origem": [{"id": 4, "text": "Instagram"}],
            "termo_privacidade": [{"id": 1, "text": "sim"}],
            "categoriaContato": [
                {"id": 8, "text": "home", "status": "active"},
                {"id": 9, "text": "work", "status": "active"},
            ],
        }
        cache.store["metadados_b2c"] = {
            "data": {
                "fields": [
                    {
                        "external_id": external_id,
                        "config": {"settings": {"options": field_options}},
                    }
                    for external_id, field_options in options.items()
                ]
            }
        }
        cache.store["metadados_escritorios"] = {
            "data": {
                "dados": [
                    {
                        "nome": "São Paulo",
                        "oGV": "AIESEC em São Paulo",
                        "oGT": "AIESEC em São Paulo",
                    }
                ]
            }
        }

    def test_contact_types_are_replaced_with_persistence_ids(self) -> None:
        lead = CriarPreCadastroLead(
            nome="Ana Maria",
            sobrenome="Silva Santos",
            dataNascimento=datetime(2000, 1, 2),
            telefone=[
                {"tipo": "home", "numero": "11912345678"},
                {"tipo": "work", "numero": "21912345678"},
            ],
            email=[
                {"tipo": "home", "email": "ana@example.com"},
                {"tipo": "work", "email": "ana.work@example.com"},
            ],
            produto={
                "id": 1,
                "id_expa": 7,
                "titulo": "Voluntário Global",
            },
            autorizacao=1,
            origem={"id": 4, "nome": "Instagram"},
            senha="StrongPass@123",
            comite={"id": 23, "nome": "AIESEC em São Paulo"},
        )
        lead_output = LeadPreCadastroOutput.model_validate(
            {
                **lead.model_dump(mode="json", exclude={"senha"}),
                "id": 98765,
            }
        )

        persisted = montar_dto_persistencia(lead, lead_output)
        payload = persisted.model_dump(mode="json")

        self.assertEqual(
            [contact["tipo"] for contact in payload["telefone"]],
            [8, 9],
        )
        self.assertEqual(
            [contact["tipo"] for contact in payload["email"]],
            [8, 9],
        )
        self.assertEqual(payload["telefone"][0]["numero"], "11912345678")
        self.assertEqual(payload["email"][0]["email"], "ana@example.com")

    def test_post_sends_fixed_pre_registration_status_to_b2c(self) -> None:
        lead = CriarPreCadastroLead(
            nome="Ana Maria",
            sobrenome="Silva Santos",
            dataNascimento=datetime(2000, 1, 2),
            telefone=[{"tipo": "home", "numero": "11912345678"}],
            email=[{"tipo": "home", "email": "ana@example.com"}],
            produto={"id": 1, "id_expa": 7, "titulo": "Voluntário Global"},
            autorizacao=1,
            origem={"id": 4, "nome": "Instagram"},
            senha="StrongPass@123",
            comite={"id": 23, "nome": "AIESEC em São Paulo"},
        )
        payload_b2c: dict[str, object] = {}

        def adapt_async(func):
            if func is cadastro_controller.enviar_payload_expa:
                return lambda payload: (
                    200,
                    {"sucesso": True, "person_id": 98765},
                )

            def send_to_b2c(payload):
                payload_b2c.update(payload)
                return 201, {"sucesso": True}

            return send_to_b2c

        with patch.object(
            cadastro_controller, "async_to_sync", side_effect=adapt_async
        ):
            resposta, status = cadastro_controller.CadastroLeadView().post(lead)

        self.assertEqual(status, 201)
        self.assertIsInstance(resposta, LeadPersistencia)
        self.assertEqual(payload_b2c["status"], "pré-cadastro")
        self.assertNotIn("senha", payload_b2c)

    def test_put_sends_fixed_qualification_status_to_b2c(self) -> None:
        payload_b2c: dict[str, object] = {}

        def adapt_async(_func):
            def send_to_b2c(payload):
                payload_b2c.update(payload)
                return 200, {"sucesso": True}

            return send_to_b2c

        with patch.object(
            cadastro_controller, "async_to_sync", side_effect=adapt_async
        ):
            resposta, status = cadastro_controller.CadastroLeadView().put(
                QualificacaoLead(id=98765, status="pré-cadastro")
            )

        self.assertEqual(status, 200)
        self.assertEqual(resposta, {"sucesso": True})
        self.assertEqual(payload_b2c, {"id": 98765, "status": "qualificação"})


if __name__ == "__main__":
    unittest.main()
