#!/usr/bin/env python3
"""Validate BREERO deployment configuration without contacting a live host."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DIGEST_IMAGE = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")
PINNED_ACTION = re.compile(r"^[0-9a-f]{40}$")
PERMISSION_SCOPES = {
    "actions",
    "attestations",
    "checks",
    "contents",
    "deployments",
    "discussions",
    "id-token",
    "issues",
    "models",
    "packages",
    "pages",
    "pull-requests",
    "security-events",
    "statuses",
}
APP_SECRET_BINDINGS = {
    "DATABASE_URL_FILE": "/run/secrets/breero_database_url",
    "REDIS_URL_FILE": "/run/secrets/breero_redis_url",
    "JWT_SECRET_FILE": "/run/secrets/breero_jwt_access_secret",
    "JWT_REFRESH_SECRET_FILE": "/run/secrets/breero_jwt_refresh_secret",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Unable to read Compose JSON {path}: {exc}") from exc
    require(isinstance(document, dict), f"Compose JSON must be an object: {path}")
    return document


def names(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value)
    if isinstance(value, list):
        return {str(item) for item in value if isinstance(item, str)}
    return set()


def secret_sources(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value)
    sources: set[str] = set()
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                sources.add(item)
            elif isinstance(item, dict) and isinstance(item.get("source"), str):
                sources.add(item["source"])
    return sources


def environment_map(value: Any) -> dict[str, str | None]:
    if isinstance(value, dict):
        return {str(key): None if item is None else str(item) for key, item in value.items()}
    environment: dict[str, str | None] = {}
    if isinstance(value, list):
        for item in value:
            if not isinstance(item, str):
                continue
            key, separator, configured = item.partition("=")
            environment[key] = configured if separator else None
    return environment


def assert_digest(image: Any, service: str) -> None:
    require(
        isinstance(image, str) and DIGEST_IMAGE.fullmatch(image) is not None,
        f"{service} must use an immutable image digest",
    )


def assert_no_dangerous_runtime(service_name: str, service: dict[str, Any]) -> None:
    require(not service.get("ports"), f"{service_name} must not publish host ports")
    require(service.get("privileged") is not True, f"{service_name} must not be privileged")
    require(service.get("network_mode") != "host", f"{service_name} must not use host networking")
    require(service.get("pid") != "host", f"{service_name} must not use host PID namespace")
    require(service.get("ipc") != "host", f"{service_name} must not use host IPC namespace")
    require(not service.get("devices"), f"{service_name} must not map host devices")
    for mount in service.get("volumes", []) or []:
        text = json.dumps(mount, sort_keys=True)
        require("/var/run/docker.sock" not in text, f"{service_name} must not mount Docker socket")


def assert_hardened_application(service_name: str, service: dict[str, Any]) -> None:
    require(service.get("read_only") is True, f"{service_name} must have a read-only root filesystem")
    require(service.get("init") is True, f"{service_name} must enable init")
    require("ALL" in set(service.get("cap_drop", []) or []), f"{service_name} must drop all capabilities")
    require(
        "no-new-privileges:true" in set(service.get("security_opt", []) or []),
        f"{service_name} must set no-new-privileges",
    )
    require(int(service.get("pids_limit", 0)) > 0, f"{service_name} must define a PID limit")
    require(service.get("mem_limit") is not None, f"{service_name} must define a memory limit")
    assert_digest(service.get("image"), service_name)


def validate_backend(document: dict[str, Any]) -> list[str]:
    services = document.get("services") or {}
    require(isinstance(services, dict), "Backend Compose must define services")
    required = {"migrate", "api", "worker", "scheduler", "postgres", "redis"}
    missing = sorted(required - set(services))
    require(not missing, f"Backend Compose is missing services: {', '.join(missing)}")

    for name, raw in services.items():
        require(isinstance(raw, dict), f"Backend service {name} must be an object")
        assert_no_dangerous_runtime(name, raw)

    required_app_secrets = {
        "breero_database_url",
        "breero_redis_url",
        "breero_jwt_access_secret",
        "breero_jwt_refresh_secret",
    }
    for name in ("migrate", "api", "worker", "scheduler"):
        assert_hardened_application(name, services[name])
        missing_secrets = sorted(required_app_secrets - secret_sources(services[name].get("secrets")))
        require(not missing_secrets, f"{name} is missing file-backed application secrets: {', '.join(missing_secrets)}")
        environment = environment_map(services[name].get("environment"))
        for variable, expected_path in APP_SECRET_BINDINGS.items():
            require(
                environment.get(variable) == expected_path,
                f"{name} must bind {variable} to {expected_path}",
            )

    require(bool(services["api"].get("healthcheck")), "api must define a healthcheck")
    require(
        {"breero_private", "caddy_shared"} <= names(services["api"].get("networks")),
        "api must join the private application plane and approved Caddy edge",
    )
    for name in ("worker", "scheduler", "migrate", "postgres", "redis"):
        require(
            "breero_private" in names(services[name].get("networks")),
            f"{name} must join the private network",
        )

    for name in ("postgres", "redis"):
        assert_digest(services[name].get("image"), name)
        require(services[name].get("read_only") is True, f"{name} must be read-only outside declared data paths")
        require("ALL" in set(services[name].get("cap_drop", []) or []), f"{name} must drop all capabilities")
        require(
            "no-new-privileges:true" in set(services[name].get("security_opt", []) or []),
            f"{name} must set no-new-privileges",
        )
        require(bool(services[name].get("healthcheck")), f"{name} must define a healthcheck")

    postgres_environment = environment_map(services["postgres"].get("environment"))
    require(
        postgres_environment.get("POSTGRES_PASSWORD_FILE") == "/run/secrets/breero_postgres_password",
        "postgres must consume its file-backed password through POSTGRES_PASSWORD_FILE",
    )
    require(
        "breero_postgres_password" in secret_sources(services["postgres"].get("secrets")),
        "postgres must mount breero_postgres_password",
    )

    redis_command = json.dumps(services["redis"].get("command", []), sort_keys=True)
    require(
        "/run/secrets/breero_redis_acl" in redis_command,
        "redis must consume the mounted ACL file",
    )
    require(
        "breero_redis_acl" in secret_sources(services["redis"].get("secrets")),
        "redis must mount breero_redis_acl",
    )

    networks = document.get("networks") or {}
    require(
        networks.get("breero_private", {}).get("internal") is True,
        "breero_private must be internal",
    )
    require(
        networks.get("caddy_shared", {}).get("external") is True,
        "caddy_shared must be externally provisioned",
    )

    secrets = document.get("secrets") or {}
    require(bool(secrets), "Backend Compose must use file-backed secrets")
    for name, definition in secrets.items():
        require(
            isinstance(definition, dict) and bool(definition.get("file")),
            f"Secret {name} must be file-backed",
        )

    warnings: list[str] = []
    if not services["worker"].get("healthcheck"):
        warnings.append("WORKER_HEALTHCHECK=UNVERIFIED")
    if not services["scheduler"].get("healthcheck"):
        warnings.append("SCHEDULER_HEALTHCHECK=UNVERIFIED")
    return warnings


def validate_frontend(document: dict[str, Any]) -> None:
    services = document.get("services") or {}
    require(set(services) == {"web"}, "Frontend Compose must contain only the web service")
    web = services["web"]
    assert_no_dangerous_runtime("web", web)
    assert_hardened_application("web", web)
    require(
        str(web.get("user", "")).split(":", 1)[0] not in {"", "0", "root"},
        "web must declare a non-root runtime user",
    )
    require(bool(web.get("healthcheck")), "web must define a healthcheck")
    require("frontend" in names(web.get("networks")), "web must join the frontend edge network")
    networks = document.get("networks") or {}
    require(
        networks.get("frontend", {}).get("external") is True,
        "frontend network must be externally provisioned",
    )


def leading_spaces(line: str) -> int:
    prefix = line[: len(line) - len(line.lstrip(" \t"))]
    require("\t" not in prefix, "Workflow indentation must not contain tabs")
    return len(prefix)


def validate_permissions(text: str) -> None:
    lines = text.splitlines()
    blocks: list[tuple[int, dict[str, str]]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.lstrip(" \t")
        if not re.match(r"^permissions\s*:", stripped):
            index += 1
            continue

        indent = leading_spaces(line)
        require(
            re.fullmatch(r"permissions\s*:\s*(?:#.*)?", stripped) is not None,
            "Workflow permissions must use an explicit block mapping",
        )
        entries: dict[str, str] = {}
        child_indent: int | None = None
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            candidate_stripped = candidate.lstrip(" \t")
            if not candidate_stripped or candidate_stripped.startswith("#"):
                cursor += 1
                continue
            candidate_indent = leading_spaces(candidate)
            if candidate_indent <= indent:
                break
            if child_indent is None:
                child_indent = candidate_indent
                require(child_indent == indent + 2, "Workflow permissions must use one explicit mapping level")
            require(candidate_indent == child_indent, "Nested or ambiguous workflow permissions are forbidden")
            match = re.fullmatch(
                r"([a-z][a-z-]*):\s*(read|none)\s*(?:#.*)?",
                candidate_stripped,
            )
            require(match is not None, "Every workflow permission must be explicitly read or none")
            scope, access = match.groups()
            require(scope in PERMISSION_SCOPES, f"Unknown workflow permission scope: {scope}")
            require(scope not in entries, f"Duplicate workflow permission scope: {scope}")
            require(not (scope == "id-token" and access != "none"), "id-token must remain none")
            entries[scope] = access
            cursor += 1

        require(bool(entries), "Workflow permissions block must not be empty")
        blocks.append((indent, entries))
        index = cursor

    top_level = [entries for indent, entries in blocks if indent == 0]
    require(len(top_level) == 1, "Workflow must contain exactly one top-level permissions block")
    require(top_level[0].get("contents") == "read", "Top-level contents permission must be read")
    for _, entries in blocks:
        require(all(access in {"read", "none"} for access in entries.values()), "Workflow permissions must be read-only")


def validate_workflow(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require("pull_request_target:" not in text, "Deployment preflight must not use pull_request_target")
    require("persist-credentials: false" in text, "Checkout credentials must not persist")
    validate_permissions(text)

    forbidden = (
        "secrets.",
        "environment: production",
        "docker " + "login",
        "docker " + "push",
        "docker compose " + "up",
        "docker compose " + "down",
        "caddy " + "reload",
        "systemctl " + "restart",
        "systemctl " + "reload",
        "appleboy/" + "ssh-action",
    )
    for token in forbidden:
        require(token not in text, f"Deployment preflight contains forbidden live-action token: {token}")

    references = re.findall(r"^\s*(?:-\s+)?uses:\s+([^\s#]+)", text, flags=re.MULTILINE)
    require(bool(references), "Deployment preflight must declare reviewed actions explicitly")
    for reference in references:
        if reference.startswith("./"):
            continue
        action, separator, revision = reference.rpartition("@")
        require(bool(action) and separator == "@", f"Action reference is invalid: {reference}")
        require(PINNED_ACTION.fullmatch(revision) is not None, f"Action must be pinned to a 40-character commit: {reference}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-json", type=Path, required=True)
    parser.add_argument("--frontend-json", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warnings = validate_backend(load_json(args.backend_json))
    validate_frontend(load_json(args.frontend_json))
    validate_workflow(args.workflow)
    print("DEPLOYMENT_COMPOSE_SECURITY=PASS")
    print("DEPLOYMENT_WORKFLOW_MUTATION_AUTHORITY=NONE")
    print("LIVE_SERVER_CHANGED=NO")
    for warning in warnings:
        print(warning)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"DEPLOYMENT_PREFLIGHT_ERROR={exc}")
        raise SystemExit(2) from exc
