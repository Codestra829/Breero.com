from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.main import EXPECTED_SCHEMA_REVISION


def test_readiness_revision_matches_the_single_alembic_head() -> None:
    api_root = Path(__file__).resolve().parents[1]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "migrations"))
    heads = ScriptDirectory.from_config(config).get_heads()

    assert heads == [EXPECTED_SCHEMA_REVISION]
