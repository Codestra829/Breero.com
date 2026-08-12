# Historical incorrect-target access investigation

Recorded 2026-08-12T14:16:36Z. Investigated target: `49.12.145.207`.

> Correction: `49.12.145.107` is the current BREERO host. `.207` is not an approved/current
> BREERO origin unless separately provisioned and explicitly approved. The evidence below is
> preserved only to document the earlier incorrect-target investigation; DNS resolution did not
> establish ownership.

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

**CLOSED AS INCORRECT TARGET.** No capacity inventory, Docker/network/volume inspection, secret
creation, image pull/build, network creation, data-service start, migration, backend/web deployment,
Caddy change, or UAT was attempted against `.207`.

## Conditions to resume

No `.207` activation work should resume without separate provisioning evidence and explicit
approval. Current-host work must target `.107` and follow the current audit.

No production or staging infrastructure was mutated.

## Reverification

At 2026-08-12T14:22:00Z, source public IP `49.12.145.107` again received a TCP/22 timeout and
OpenSSH again timed out before key exchange. No new Hetzner firewall/console access was available.
This remained a timeout, but it is no longer a current-host gate because `.207` was the wrong target.
