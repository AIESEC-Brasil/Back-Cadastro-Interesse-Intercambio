import os
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import inspect

os.environ["AMBIENTE"] = "DEV"
os.environ["API_KEYS_PERMITIDAS"] = "test-key"
os.environ["DOMINIOS_PERMITIDOS"] = "http://localhost"
os.environ["DB_CONNECT"] = "sqlite:///:memory:"
os.environ["ID_APPSCRIPT_EXPA"] = "test"
os.environ["CACHE_TTL"] = "60"
os.environ["CLIENT_ID"] = "test"
os.environ["CLIENT_SECRET"] = "test"
os.environ["APP_ID"] = "test"
os.environ["APP_TOKEN"] = "test"
os.environ["TOKEN_EXPA"] = "test"

from app.main import create_app
from app.core import db
from app.model.divisaoMercadoModel import Universidades, DivisaoCL


class InitialMigrationTest(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.tmpdir = tempfile.TemporaryDirectory(dir=self.repo_root)
        self.db_path = Path(self.tmpdir.name) / "test.sqlite"

        os.environ["DB_CONNECT"] = f"sqlite:///{self.db_path}"

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_initial_migration_creates_tables_and_revision(self):
        app = create_app()

        with app.app_context():
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            self.assertIn("instituicoes_mercado", tables)
            self.assertIn("cl_configuracoes", tables)

            universidades = db.session.query(Universidades).all()
            configuracoes = db.session.query(DivisaoCL).all()

            self.assertTrue(universidades, "Os dados do JSON não foram salvos na tabela de instituições.")
            self.assertTrue(configuracoes, "Os dados do JSON não foram salvos na tabela de configurações.")

        versions_dir = self.repo_root / "migrations" / "versions"
        revision_files = [p for p in versions_dir.glob("*.py") if p.is_file()]
        self.assertTrue(revision_files, "A migração inicial não foi gerada.")

    def test_models_use_utf8mb4_0900_as_ci_collation(self):
        self.assertEqual(Universidades.__table__.kwargs.get("mysql_charset"), "utf8mb4")
        self.assertEqual(Universidades.__table__.kwargs.get("mysql_collate"), "utf8mb4_0900_as_ci")
        self.assertEqual(DivisaoCL.__table__.kwargs.get("mysql_charset"), "utf8mb4")
        self.assertEqual(DivisaoCL.__table__.kwargs.get("mysql_collate"), "utf8mb4_0900_as_ci")
