#!/usr/bin/env python3
"""Validate rendered Compose and adapted Caddy evidence without mutating a host."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from collections.abc import Iterable, Mapping
from typing import Any


class EvidenceError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def parse_json_document(raw: bytes, label: str) -> dict[str, Any]:
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    require(isinstance(document, dict), f"{label} must be a JSON object")
    return document


def read_documents() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parts = sys.stdin.buffer.read().split(b"\0")
    require(len(parts) == 3, "expected backend, frontend and Caddy JSON separated by NUL bytes")
    return (
        parse_json_document(parts[0], "backend Compose"),
        parse_json_document(parts[1], "frontend Compose"),
        parse_json_document(parts[2], "adapted Caddy configuration"),
    )


def mapping(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def service_networks(service: Mapping[str, Any]) -> set[str]:
    configured = service.get("networks")
    if isinstance(configured, dict):
        return {str(name) for name in configured}
    if isinstance(configured, list):
        return {str(name) for name in configured if isinstance(name, str)}
    return set()


def actual_network_name(document: Mapping[str, Any], logical_name: str) -> str:
    networks = mapping(document.get("networks") or {}, "Compose networks")
    definition = mapping(networks.get(logical_name), f"network {logical_name}")
    name = definition.get("name")
    require(isinstance(name, str) and bool(name), f"network {logical_name} has no rendered runtime name")
    return name


def validate_compose_bindings(
    backend: Mapping[str, Any],
    frontend: Mapping[str, Any],
    args: argparse.Namespace,
) -> list[str]:
    backend_services = mapping(backend.get("services") or {}, "backend services")
    frontend_services = mapping(frontend.get("services") or {}, "frontend services")

    for name in ("migrate", "api", "worker", "scheduler", "postgres", "redis"):
        require(name in backend_services, f"backend service is missing: {name}")
    require("web" in frontend_services, "frontend web service is missing")

    api = mapping(backend_services["api"], "backend api service")
    web = mapping(frontend_services["web"], "frontend web service")
    require(api.get("image") == args.expected_api_image, "rendered API image does not match the approved digest")
    require(web.get("image") == args.expected_frontend_image, "rendered frontend image does not match the approved digest")

    require(
        actual_network_name(backend, "breero_private") == args.expected_private_network,
        "rendered private network name does not match the approved runtime network",
    )
    require(
        actual_network_name(backend, "caddy_shared") == args.expected_backend_edge_network,
        "rendered backend edge network name does not match the approved runtime network",
    )
    require(
        actual_network_name(frontend, "frontend") == args.expected_frontend_edge_network,
        "rendered frontend edge network name does not match the approved runtime network",
    )

    require(
        {"breero_private", "caddy_shared"} <= service_networks(api),
        "API is not attached to both rendered private and backend edge networks",
    )
    for name in ("migrate", "worker", "scheduler", "postgres", "redis"):
        service = mapping(backend_services[name], f"backend {name} service")
        require(
            "breero_private" in service_networks(service),
            f"{name} is not attached to the rendered private network",
        )
    require("frontend" in service_networks(web), "frontend web is not attached to its rendered edge network")

    secret_definitions = mapping(backend.get("secrets") or {}, "backend secrets")
    require(bool(secret_definitions), "rendered backend Compose contains no file-backed secrets")
    verified_paths: list[str] = []
    for logical_name, raw_definition in secret_definitions.items():
        definition = mapping(raw_definition, f"secret {logical_name}")
        path = definition.get("file")
        require(isinstance(path, str) and path.startswith("/"), f"secret {logical_name} path is not absolute")
        require("\n" not in path and "\r" not in path and "\0" not in path, f"secret {logical_name} path is malformed")
        resolved = os.path.realpath(path)
        require(os.path.isfile(resolved), f"secret {logical_name} is not a regular file")
        require(os.access(resolved, os.R_OK), f"secret {logical_name} is not readable")
        mode = stat.S_IMODE(os.stat(resolved).st_mode)
        require(mode & 0o007 == 0, f"secret {logical_name} is world-accessible")
        verified_paths.append(resolved)

    return sorted(set(verified_paths))


def iter_route_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if isinstance(value.get("match"), list) and isinstance(value.get("handle"), list):
            yield value
        for child in value.values():
            yield from iter_route_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_route_objects(child)


def route_hosts(route: Mapping[str, Any]) -> set[str]:
    hosts: set[str] = set()
    matchers = route.get("match")
    if not isinstance(matchers, list):
        return hosts
    for matcher in matchers:
        if not isinstance(matcher, dict):
            continue
        configured_hosts = matcher.get("host")
        if isinstance(configured_hosts, list):
            hosts.update(str(host) for host in configured_hosts if isinstance(host, str))
    return hosts


def reverse_proxy_upstreams(value: Any) -> set[str]:
    upstreams: set[str] = set()
    if isinstance(value, dict):
        if value.get("handler") == "reverse_proxy":
            configured = value.get("upstreams")
            if isinstance(configured, list):
                for upstream in configured:
                    if isinstance(upstream, dict) and isinstance(upstream.get("dial"), str):
                        upstreams.add(upstream["dial"])
        for child in value.values():
            upstreams.update(reverse_proxy_upstreams(child))
    elif isinstance(value, list):
        for child in value:
            upstreams.update(reverse_proxy_upstreams(child))
    return upstreams


def validate_caddy_routes(caddy: Mapping[str, Any], args: argparse.Namespace) -> None:
    host_upstreams: dict[str, set[str]] = {}
    for route in iter_route_objects(caddy):
        hosts = route_hosts(route)
        if not hosts:
            continue
        upstreams = reverse_proxy_upstreams(route.get("handle"))
        for host in hosts:
            host_upstreams.setdefault(host, set()).update(upstreams)

    web_upstreams = host_upstreams.get(args.expected_web_host, set())
    api_upstreams = host_upstreams.get(args.expected_api_host, set())
    require(
        args.expected_web_upstream in web_upstreams,
        "adapted Caddy routes do not bind the approved web host to the approved web upstream",
    )
    require(
        args.expected_api_upstream in api_upstreams,
        "adapted Caddy routes do not bind the approved API host to the approved API upstream",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-api-image", required=True)
    parser.add_argument("--expected-frontend-image", required=True)
    parser.add_argument("--expected-private-network", required=True)
    parser.add_argument("--expected-backend-edge-network", required=True)
    parser.add_argument("--expected-frontend-edge-network", required=True)
    parser.add_argument("--expected-web-host", required=True)
    parser.add_argument("--expected-api-host", required=True)
    parser.add_argument("--expected-web-upstream", required=True)
    parser.add_argument("--expected-api-upstream", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend, frontend, caddy = read_documents()
    secret_paths = validate_compose_bindings(backend, frontend, args)
    validate_caddy_routes(caddy, args)
    print("COMPOSE_RUNTIME_BINDING=PASS")
    print("CADDY_HOST_UPSTREAM_BINDING=PASS")
    print(f"FILE_BACKED_SECRET_PATHS_VERIFIED={len(secret_paths)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvidenceError as exc:
        print(f"RUNTIME_EVIDENCE_ERROR={exc}", file=sys.stderr)
        raise SystemExit(2) from exc
