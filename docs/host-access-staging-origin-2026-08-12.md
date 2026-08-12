# Host access and staging-origin activation evidence

Recorded 2026-08-12T14:16:36Z. Target: `49.12.145.207`.

## SSH hard gate

| Field | Result |
|---|---|
| Source public IP | `49.12.145.107` |
| Network path | direct IPv4 TCP from `.107` to `.207:22` |
| TCP/22 | timeout / closed-or-filtered |
| SSH mode | batch authentication, 10-second connection timeout |
| SSH result | `connect to host 49.12.145.207 port 22: Connection timed out` |
| Key exchange/authentication | not reached |
| Hetzner firewall/security group | inaccessible with available credentials/tooling |
| Target host firewall | uninspectable without SSH |

The timeout occurs before SSH authentication, so no conclusion can be drawn about authorized keys.
The network path must first allow the approved administration source or provide an approved bastion,
VPN, console, or alternate SSH endpoint.

## Activation decision

**BLOCKED — HOST ACCESS.** Per the activation runbook, no capacity inventory, Docker/network/volume
inspection, secret creation, image pull/build, network creation, data-service start, migration,
backend/web deployment, Caddy change, or UAT was attempted.

## Conditions to resume

1. Confirm `.207` ownership and intended SSH endpoint from the Hetzner console.
2. Confirm the Hetzner firewall permits TCP/22 from the approved administrative path (`.107` if
   intentionally approved), or provide the authorized bastion/VPN/console procedure.
3. Confirm host firewall and `sshd` are listening through provider console access.
4. Supply the correct non-root administrative principal/key policy if root SSH is intentionally
   disabled.
5. Re-run authenticated SSH. Only after success perform the required read-only inventory.

No production or staging infrastructure was mutated.

## Reverification

At 2026-08-12T14:22:00Z, source public IP `49.12.145.107` again received a TCP/22 timeout and
OpenSSH again timed out before key exchange. No new Hetzner firewall/console access was available.
The hard gate remains unchanged.
