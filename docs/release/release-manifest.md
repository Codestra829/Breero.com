# Frozen release manifest

| Component | Git SHA | Immutable artifact |
|---|---|---|
| Backend | `da57218c73f2050ce1d6ed71f92bbeb737195527` | `breero-api@sha256:b2b1c554cf5e0e1ff835ddbaf639b1f7260a8ca36721f0d6f9ab1204cf726257` |
| Frontend/web | `70b22c9b8d4b978c33fe8190f8b2fff956c56e88` | **BLOCKED: not built/published** |
| Customer/partners/ops | same web workspace; separate artifacts required if deployed separately | **BLOCKED** |
| OpenAPI | backend SHA above | SHA-256 `799c4f399b01d9df99d446c731f2000a9270c240d2c50ac520e63b174e668712` |
| Alembic | backend SHA above | `008_production_readiness` |

Frontend image creation was deliberately not attempted on the 100%-full production host. It must be
built in CI or other isolated capacity with production public configuration, scanned, pushed under
the git SHA, resolved to registry digest, and smoke-tested by digest.
