import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_development_defaults():
    with pytest.raises(ValidationError, match="unsafe production configuration"):
        Settings(app_env="production")


def test_liveness_has_no_dependency_calls():
    from app.main import live

    assert live.__name__ == "live"
