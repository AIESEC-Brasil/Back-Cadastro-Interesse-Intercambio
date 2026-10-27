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
from app.utils.exception import validate_api_response
from app.utils.payload import montar_dto_persistencia


class LeadPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        cache.store.clear()
        options = {
            "produto": [{"id": 1, "text": "Voluntário Global"}],
            "aiesec_proxima": [{"id": 23, "text": "AIESEC em São Paulo"}],
            "origem": [{"id": 4, "text": "Instagram"}],
            "termo_privacidade": [{"id": 1, "text": "sim"}],
            "idiomas": [{"id": 5, "text": "Inglês"}],
            "area_atuacao": [{"id": 6, "text": "Tecnologia"}],
            "nivel_mercado": [{"id": 7, "text": "Estagiário"}],
            "semestre_curso": [{"id": 8, "text": "3º semestre"}],
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
        self.assertEqual(persisted.autorizacao, 1)
        self.assertEqual(payload["autorizacao"], 1)
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
        self.assertEqual(resposta.id, 98765)
        self.assertEqual(resposta.status, "pré-cadastro")
        resposta_validada, status_validado = validate_api_response(
            (resposta, status),
            {201: LeadPersistencia},
        )
        self.assertEqual(status_validado, 201)
        self.assertEqual(resposta_validada["id"], 98765)
        self.assertEqual(payload_b2c["status"], "pré-cadastro")
        self.assertEqual(payload_b2c["autorizacao"], 1)
        self.assertNotIn("senha", payload_b2c)
        self.assertNotIn("id_nivel_mercado", payload_b2c)
        self.assertNotIn("id_semestre_curso", payload_b2c)
        self.assertNotIn("link_drive", payload_b2c)

    def test_post_returns_generic_json_when_expa_rejects_lead(self) -> None:
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
        resposta_expa = {
            "error": (
                'Erro na API EXPA (422): {"message": "requirement not met"}'
            )
        }

        with patch.object(
            cadastro_controller,
            "async_to_sync",
            return_value=lambda _payload: (422, resposta_expa),
        ):
            resposta, status = cadastro_controller.CadastroLeadView().post(lead)

        self.assertEqual(status, 502)
        resposta_validada, status_validado = validate_api_response(
            (resposta, status),
            cadastro_controller.CADASTRO_POST_RESPONSES,
        )
        self.assertEqual(status_validado, 502)
        self.assertEqual(resposta_validada["type"], "ExternalServiceError")
        self.assertEqual(
            resposta_validada["message"],
            "EXPA rejeitou a solicitação (HTTP 422).",
        )
        self.assertIn(
            "requirement not met",
            resposta_validada["error_details"][0]["msg"],
        )

    def test_response_validation_accepts_serialized_creation_datetime(self) -> None:
        lead = LeadPersistencia(
            id=1,
            id_produto=2,
            id_escritorio=26,
            id_origem=1,
            nome="Caio",
            sobrenome="Gabriel",
            telefone=[{"tipo": 1, "numero": "81979056770"}],
            email=[{"tipo": 1, "email": "caio@example.com"}],
            autorizacao=1,
            dataNascimento=datetime(2000, 6, 23),
        )

        resposta_serializada, status_serializado = validate_api_response(
            (lead.model_dump(mode="json"), 201),
            {201: LeadPersistencia},
        )
        self.assertEqual(status_serializado, 201)
        self.assertEqual(
            resposta_serializada["criado_em"],
            lead.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
        )

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
        self.assertEqual(resposta, {"id": 98765, "status": "qualificação"})
        self.assertEqual(payload_b2c, {"id": 98765, "status": "qualificação"})

    def test_put_maps_qualification_references_to_persistence_ids(self) -> None:
        payload_b2c: dict[str, object] = {}

        def adapt_async(_func):
            def send_to_b2c(payload):
                payload_b2c.update(payload)
                return 200, {"sucesso": True}

            return send_to_b2c

        qualificacao = QualificacaoLead(
            id=98765,
            curso="Engenharia",
            idiomas=[{"id": 5, "nome": "Inglês", "nivel": "Avançado"}],
            areaAtuacao={"id": 6, "nome": "Tecnologia"},
            nivelAtuacao={"id": 7, "nome": "Estagiário"},
            semestreCurso={"id": 8, "nome": "3º semestre"},
            curriculo={
                "fileName": "curriculo.pdf",
                "base64": "JVBERi0xLjQK",
            },
        )

        with patch.object(
            cadastro_controller, "async_to_sync", side_effect=adapt_async
        ):
            resposta, status = cadastro_controller.CadastroLeadView().put(
                qualificacao
            )

        self.assertEqual(status, 200)
        self.assertEqual(payload_b2c["id_area_atuacao"], 6)
        self.assertEqual(payload_b2c["id_nivel_mercado"], 7)
        self.assertEqual(payload_b2c["id_semestre_curso"], 8)
        self.assertEqual(payload_b2c["idiomas"], [5])
        self.assertNotIn("areaAtuacao", payload_b2c)
        self.assertNotIn("nivelAtuacao", payload_b2c)
        self.assertNotIn("semestreCurso", payload_b2c)
        self.assertEqual(payload_b2c["curso"], "Engenharia")
        self.assertEqual(
            payload_b2c["curriculo"],
            {"fileName": "curriculo.pdf", "base64": "JVBERi0xLjQK"},
        )
        self.assertEqual(payload_b2c["status"], "qualificação")
        self.assertEqual(resposta, payload_b2c)

    def test_put_preserves_qualification_persistence_ids(self) -> None:
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
                QualificacaoLead(
                    id=98765,
                    id_area_atuacao=11,
                    id_nivel_mercado=12,
                    id_semestre_curso=13,
                )
            )

        self.assertEqual(status, 200)
        self.assertEqual(payload_b2c["id_area_atuacao"], 11)
        self.assertEqual(payload_b2c["id_nivel_mercado"], 12)
        self.assertEqual(payload_b2c["id_semestre_curso"], 13)
        self.assertEqual(resposta, payload_b2c)


if __name__ == "__main__":
    unittest.main()
