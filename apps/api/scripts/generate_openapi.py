"""Generate deterministic OpenAPI and endpoint-policy artifacts for CI review."""

import json
import os
from pathlib import Path

from app.api.policy_registry import get_endpoint_registry
from app.main import app

openapi_target = Path(os.getenv("OPENAPI_PATH", "openapi.json"))
registry_target = Path(os.getenv("ENDPOINT_REGISTRY_PATH", "endpoint-registry.json"))

registry = get_endpoint_registry(app)
schema = app.openapi()
schema["x-breero-endpoint-registry-digest"] = registry["digest"]

operation_ids: dict[str, str] = {}
for path, operations in schema.get("paths", {}).items():
    for method, operation in operations.items():
        if method not in {"get", "put", "post", "delete", "options", "head", "patch", "trace"}:
            continue
        operation_id = operation.get("operationId")
        if not operation_id:
            raise SystemExit(f"Missing operationId for {method.upper()} {path}")
        if operation_id in operation_ids:
            raise SystemExit(
                f"Duplicate operationId {operation_id}: {operation_ids[operation_id]} and "
                f"{method.upper()} {path}"
            )
        policy = operation.get("x-breero-policy")
        if not isinstance(policy, dict) or method.upper() not in policy:
            raise SystemExit(f"Missing endpoint policy for {method.upper()} {path}")
        operation_ids[operation_id] = f"{method.upper()} {path}"

openapi_target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
registry_target.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
print(
    f"validated {len(schema.get('paths', {}))} paths / {len(operation_ids)} operations / "
    f"{len(registry['endpoints'])} endpoint policies"
)
print(f"endpoint registry digest: {registry['digest']}")
print(openapi_target)
print(registry_target)
