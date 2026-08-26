#!/usr/bin/env python3
"""Validate BREERO deployment configuration without contacting a live host."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

DIGEST_IMAGE = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")


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
        return {str(item) for item in value}
    return set()


def assert_digest(image: Any, service: str) -> None:
    require(isinstance(image, str) and DIGEST_IMAGE.fullmatch(image) is not None,
            f"{service} must use an immutable image digest")


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

    for name in ("migrate", "api", "worker", "scheduler"):
        assert_hardened_application(name, services[name])

    require(bool(services["api"].get("healthcheck")), "api must define a healthcheck")
    require(
        {"breero_private", "caddy_shared"} <= names(services["api"].get("networks")),
        "api must join only the private application plane and approved Caddy edge",
    )
    for name in ("worker", "scheduler", "migrate", "postgres", "redis"):
        require("breero_private" in names(services[name].get("networks")),
                f"{name} must join the private network")

    for name in ("postgres", "redis"):
        assert_digest(services[name].get("image"), name)
        require(services[name].get("read_only") is True, f"{name} must be read-only outside declared data paths")
        require("ALL" in set(services[name].get("cap_drop", []) or []), f"{name} must drop all capabilities")
        require(
            "no-new-privileges:true" in set(services[name].get("security_opt", []) or []),
            f"{name} must set no-new-privileges",
        )
        require(bool(services[name].get("healthcheck")), f"{name} must define a healthcheck")

    networks = document.get("networks") or {}
    require(networks.get("breero_private", {}).get("internal") is True,
            "breero_private must be internal")
    require(networks.get("caddy_shared", {}).get("external") is True,
            "caddy_shared must be externally provisioned")

    secrets = document.get("secrets") or {}
    require(bool(secrets), "Backend Compose must use file-backed secrets")
    for name, definition in secrets.items():
        require(isinstance(definition, dict) and bool(definition.get("file")),
                f"Secret {name} must be file-backed")

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
    require(str(web.get("user", "")).split(":", 1)[0] not in {"", "0", "root"},
            "web must declare a non-root runtime user")
    require(bool(web.get("healthcheck")), "web must define a healthcheck")
    require("frontend" in names(web.get("networks")), "web must join the frontend edge network")
    networks = document.get("networks") or {}
    require(networks.get("frontend", {}).get("external") is True,
            "frontend network must be externally provisioned")


def validate_workflow(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require("pull_request_target:" not in text, "Deployment preflight must not use pull_request_target")
    require("contents: read" in text, "Deployment preflight must use read-only repository permissions")
    forbidden = (
        "secrets.",
        "id-token: write",
        "contents: write",
        "packages: write",
        "deployments: write",
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
