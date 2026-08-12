# Disk capacity report

## Observed state

On 2026-08-12 `/dev/md2` was 436 GiB total, 412 GiB used, 1.5 GiB available and reported 100%.
Inodes were healthy at 48%. Journald used 696 MiB. Docker reported 343.7 GB of images, 23.35 GB
of container writable layers, 14.36 GB of volumes and 58.14 GB of build cache.

The largest stopped writable layers were anonymous containers of 5.4 GB, 4.76 GB, and two at
3.85 GB. Their names do not establish ownership. The host also runs many non-BREERO production
and staging stacks. They are unsafe to remove without service-owner confirmation.

## Remediation classification

| Candidate | Estimate | Decision |
|---|---:|---|
| Unowned stopped container layers | ~22 GB | BLOCKED: identify repository, owner and recovery need first |
| Docker images reported reclaimable | 73.32 GB | BLOCKED: image reference/rollback inventory required |
| Build cache reported reclaimable | 4.36 GB | Candidate after active build audit; no global prune |
| Journald | 696 MB | Retain until incident owner approves time/size cap |
| Known BREERO audit containers/images | <2 GB | Candidate only after evidence export and owner approval |
| Database volumes, backups, uploads, Caddy data | unknown | DO NOT DELETE |

No cleanup was performed. With only 1.5 GiB free, building a new frontend image or staging stack
on this host is unsafe. Target reserve is below 80% used after owner-approved remediation, with
alerts at warning 80%, critical 90%, emergency 95%. Issue #17 remains open.
