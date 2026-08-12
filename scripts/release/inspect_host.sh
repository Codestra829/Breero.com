#!/usr/bin/env sh
set -eu

# Read-only inventory. Run on the target host and redirect output to a controlled evidence file.
date -u
hostname
df -h
docker system df
docker ps --format '{{.Names}}|{{.Image}}|{{.Ports}}|{{.Status}}'
docker volume ls
docker network ls
journalctl --disk-usage
du -sh /root/backups /root/.cache 2>/dev/null || true
ss -lnt

if [ -d /root/breero/.git ]; then
  git -C /root/breero rev-parse HEAD
fi

getent ahostsv4 api.breero.com || true
getent ahostsv4 breero.com || true
getent ahostsv4 www.breero.com || true
