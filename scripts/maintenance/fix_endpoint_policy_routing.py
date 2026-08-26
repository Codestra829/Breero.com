from pathlib import Path

REGISTRY_PATH = Path("apps/api/app/api/policy_registry.py")
TEST_PATH = Path("apps/api/tests/test_endpoint_policy_registry.py")


def replace_once(source: str, old: str, new: str, *, label: str) -> str:
    if source.count(old) != 1:
        raise SystemExit(f"Expected exactly one {label}; found {source.count(old)}")
    return source.replace(old, new, 1)


def patch_registry() -> None:
    registry = REGISTRY_PATH.read_text()
    registry = replace_once(
        registry,
        "from dataclasses import asdict, dataclass\nfrom typing import Any, Final, cast\n\nfrom fastapi import FastAPI\n",
        "from collections.abc import Iterator\nfrom dataclasses import asdict, dataclass\nfrom typing import Any, Final, cast\n\nfrom fastapi import FastAPI, routing as fastapi_routing\n",
        label="registry import block",
    )

    helper_marker = "\ndef build_endpoint_policies(app: FastAPI) -> tuple[EndpointPolicy, ...]:\n"
    helper = '''
def iter_api_route_contexts(app: FastAPI) -> Iterator[Any]:
    """Yield FastAPI's effective APIRoute contexts, including nested routers."""

    for route_context in fastapi_routing.iter_route_contexts(app.routes):
        if isinstance(route_context.original_route, APIRoute):
            yield route_context


'''
    registry = replace_once(
        registry,
        helper_marker,
        "\n" + helper + helper_marker.lstrip("\n"),
        label="build_endpoint_policies marker",
    )

    registry = replace_once(
        registry,
        '''    for route in app.routes:
        if not isinstance(route, APIRoute) or route.path in DOCUMENTATION_PATHS:
            continue
''',
        '''    for route in iter_api_route_contexts(app):
        if route.path in DOCUMENTATION_PATHS:
            continue
''',
        label="legacy top-level APIRoute loop",
    )

    install_start = registry.index(
        "def install_endpoint_registry(app: FastAPI) -> dict[str, Any]:"
    )
    get_start = registry.index(
        "\ndef get_endpoint_registry(app: FastAPI) -> dict[str, Any]:", install_start
    )
    install = '''def install_endpoint_registry(app: FastAPI) -> dict[str, Any]:
    """Install a version-resilient OpenAPI policy overlay and store the registry."""

    existing = getattr(app.state, "endpoint_registry", None)
    if existing is not None:
        return cast(dict[str, Any], existing)

    document = endpoint_registry_document(app)
    policies_by_path: dict[str, dict[str, dict[str, object]]] = {}
    for policy in document["endpoints"]:
        assert isinstance(policy, dict)
        path = str(policy["path"])
        method = str(policy["method"])
        policies_by_path.setdefault(path, {})[method] = {
            key: value
            for key, value in policy.items()
            if key not in {"path", "method", "operation_id"}
        }

    original_openapi = app.openapi

    def openapi_with_policy() -> dict[str, Any]:
        schema = original_openapi()
        paths = schema.get("paths")
        if not isinstance(paths, dict):
            raise RuntimeError("OpenAPI schema is missing its paths object")

        for path, method_policies in policies_by_path.items():
            path_item = paths.get(path)
            if not isinstance(path_item, dict):
                raise RuntimeError(f"OpenAPI is missing registered path {path}")
            for method in method_policies:
                operation = path_item.get(method.lower())
                if not isinstance(operation, dict):
                    raise RuntimeError(
                        f"OpenAPI is missing registered operation {method} {path}"
                    )
                operation["x-breero-policy"] = method_policies

        schema["x-breero-endpoint-registry-digest"] = document["digest"]
        app.openapi_schema = schema
        return schema

    app.openapi = openapi_with_policy  # type: ignore[method-assign]
    app.openapi_schema = None
    app.state.endpoint_registry = document
    return document

'''
    registry = registry[:install_start] + install + registry[get_start + 1 :]
    REGISTRY_PATH.write_text(registry)


def replace_tests() -> None:
    TEST_PATH.write_text('''from app.api.policy_registry import (
    DOCUMENTATION_PATHS,
    OPENAPI_METHODS,
    POLICY_RULES,
    get_endpoint_registry,
    iter_api_route_contexts,
)
from app.main import app

REQUIRED_POLICY_FIELDS = {
    "method",
    "path",
    "operation_id",
    "policy_rule",
    "resource_owner",
    "audience",
    "authentication",
    "permission",
    "tenant_scope",
    "record_policy",
    "capability_gate",
    "idempotency_key_policy",
    "request_hash_policy",
    "if_match_version_policy",
    "request_schema",
    "response_schema",
    "emitted_effect",
    "deprecation_status",
    "rate_limit_class",
    "pii_classification",
}


def _runtime_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for route in iter_api_route_contexts(app):
        if route.path in DOCUMENTATION_PATHS:
            continue
        for method in (route.methods or set()) & OPENAPI_METHODS:
            operations.add((method, route.path))
    return operations


def test_every_runtime_operation_has_one_complete_policy() -> None:
    document = get_endpoint_registry(app)
    endpoints = document["endpoints"]
    assert isinstance(endpoints, list)
    registered = {(entry["method"], entry["path"]) for entry in endpoints}

    assert registered == _runtime_operations()
    assert len(registered) == len(endpoints)
    assert len(registered) >= 60
    assert str(document["digest"]).startswith("sha256:")
    assert ("GET", "/api/v1/public/capabilities") in registered
    assert ("POST", "/api/v1/service-requests") in registered
    assert ("GET", "/api/v2/capabilities") in registered
    assert ("GET", "/health/ready") in registered

    for entry in endpoints:
        assert REQUIRED_POLICY_FIELDS == set(entry)
        for field in REQUIRED_POLICY_FIELDS - {"request_schema", "response_schema"}:
            assert str(entry[field]).strip(), (
                f"{entry['method']} {entry['path']} has empty {field}"
            )


def test_policy_rule_names_are_unique_and_explicit() -> None:
    names = [rule.name for rule in POLICY_RULES]
    assert len(names) == len(set(names))
    for rule in POLICY_RULES:
        assert rule.path_pattern.startswith("/")
        assert rule.resource_owner
        assert rule.permission
        assert rule.capability_gate
        assert rule.record_policy


def test_openapi_operations_embed_the_registry_policy() -> None:
    document = get_endpoint_registry(app)
    schema = app.openapi()
    assert schema["x-breero-endpoint-registry-digest"] == document["digest"]

    for entry in document["endpoints"]:
        operation = schema["paths"][entry["path"]][entry["method"].lower()]
        method_policies = operation["x-breero-policy"]
        embedded = method_policies[entry["method"]]
        assert embedded["policy_rule"] == entry["policy_rule"]
        assert embedded["resource_owner"] == entry["resource_owner"]
        assert embedded["permission"] == entry["permission"]
        assert embedded["capability_gate"] == entry["capability_gate"]


def test_high_risk_route_families_are_never_registered_as_always_enabled() -> None:
    endpoints = get_endpoint_registry(app)["endpoints"]
    high_risk_prefixes = (
        "/api/v1/payments",
        "/api/v1/finance",
        "/api/v1/provider/leads",
    )
    for entry in endpoints:
        if entry["path"].startswith(high_risk_prefixes):
            assert entry["capability_gate"] != "always"
''')


if __name__ == "__main__":
    patch_registry()
    replace_tests()
