# Production security review

Status: **FAIL** due to P1 exposure issue #19.

Verified positives: target Compose uses read-only non-root containers, dropped capabilities,
no-new-privileges, private DB/Redis network and digest-pinned infrastructure images; Caddy syntax
validates; CI security tests and dependency scans are green.

P1 findings: public PostgreSQL 5432, Redis 6379 and API 8000; running database behind the release
head; independent firewall/Hetzner review absent. Unverified items include TLS/header/CORS/cookie
review on final DNS, object-storage privacy and signed uploads, production secret scan, and live
two-customer/two-vendor RBAC UAT. No P0 was observed. No P1 may remain open for GO.
