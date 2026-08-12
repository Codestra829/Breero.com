# Monitoring and alert validation

Status: **FAIL/BLOCKED**. Existing dashboards do not prove delivery to an accountable recipient.

Required alerts: host CPU/memory, disk 80/90/95%, inodes, PostgreSQL, Redis, API latency/5xx,
worker queue/failures, Caddy health, provider failures, backup overdue, and business invariants:
captured payment without confirmed booking, confirmed booking without job, assigned job without
assignment, duplicate payout attempt, and integration backlog.

Each rule needs severity, owner, channel and escalation. Acceptance requires controlled synthetic
failures reaching the named Operations/Security/Finance recipients and documented acknowledgement
and recovery. No alert was triggered during this read-only mission.
