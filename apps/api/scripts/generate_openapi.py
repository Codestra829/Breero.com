"""Generate a deterministic OpenAPI artifact for contract review and CI."""

import json
import os
from pathlib import Path

from app.main import app

target = Path(os.getenv("OPENAPI_PATH", "openapi.json"))
target.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
print(target)
