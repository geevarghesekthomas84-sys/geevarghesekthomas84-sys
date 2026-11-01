#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# docker_security_audit.sh — Docker Container Security Audit
# Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)
#
# Scans running containers and images for common security
# misconfigurations, exposed secrets, and hardening gaps.
#
# Usage: chmod +x docker_security_audit.sh && ./docker_security_audit.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[1;33m'
CYN='\033[0;36m'
BLD='\033[1m'
RST='\033[0m'

PASS=0; WARN=0; FAIL=0

pass() { ((PASS++)); echo -e "  ${GRN}[PASS]${RST} $1"; }
warn() { ((WARN++)); echo -e "  ${YEL}[WARN]${RST} $1"; }
fail() { ((FAIL++)); echo -e "  ${RED}[FAIL]${RST} $1"; }

header() {
    echo -e "\n${CYN}┌─────────────────────────────────────────────────┐${RST}"
    echo -e "${CYN}│${RST} ${BLD}$1${RST}"
    echo -e "${CYN}└─────────────────────────────────────────────────┘${RST}"
}

if ! command -v docker &>/dev/null; then
    echo -e "${RED}[!] Docker not found.${RST}"
    exit 1
fi

echo -e "\n${CYN}══════════════════════════════════════════════════════${RST}"
echo -e "${CYN}  Docker Security Audit — $(date +%Y-%m-%d\ %H:%M:%S)${RST}"
echo -e "${CYN}══════════════════════════════════════════════════════${RST}"

# ── Docker Daemon ──
header "DOCKER DAEMON CONFIGURATION"

if docker info 2>/dev/null | grep -q "Live Restore Enabled: true"; then
    pass "Live restore enabled"
else
    warn "Live restore disabled — containers stop on daemon restart"
fi

if docker info 2>/dev/null | grep -q "userns"; then
    pass "User namespace remapping enabled"
else
    warn "User namespace remapping not enabled"
fi

DOCKER_SOCK="/var/run/docker.sock"
if [ -S "$DOCKER_SOCK" ]; then
    SOCK_PERMS=$(stat -c '%a' "$DOCKER_SOCK" 2>/dev/null || stat -f '%Lp' "$DOCKER_SOCK" 2>/dev/null)
    if [ "$SOCK_PERMS" = "660" ] || [ "$SOCK_PERMS" = "600" ]; then
        pass "Docker socket permissions: $SOCK_PERMS"
    else
        fail "Docker socket too permissive: $SOCK_PERMS (should be 660)"
    fi
fi

# ── Running Containers ──
header "RUNNING CONTAINER ANALYSIS"

CONTAINERS=$(docker ps -q 2>/dev/null)
if [ -z "$CONTAINERS" ]; then
    echo -e "  ${YEL}No running containers found.${RST}"
else
    for CID in $CONTAINERS; do
        NAME=$(docker inspect --format '{{.Name}}' "$CID" | sed 's|^/||')
        IMAGE=$(docker inspect --format '{{.Config.Image}}' "$CID")
        echo -e "\n  ${BLD}Container: ${CYN}$NAME${RST} (${IMAGE})"
        echo -e "  $( printf '─%.0s' {1..45} )"

        # Privileged mode
        PRIV=$(docker inspect --format '{{.HostConfig.Privileged}}' "$CID")
        if [ "$PRIV" = "true" ]; then
            fail "$NAME: Running in PRIVILEGED mode"
        else
            pass "$NAME: Not privileged"
        fi

        # Running as root
        USER=$(docker inspect --format '{{.Config.User}}' "$CID")
        if [ -z "$USER" ] || [ "$USER" = "root" ] || [ "$USER" = "0" ]; then
            warn "$NAME: Running as root"
        else
            pass "$NAME: Running as user '$USER'"
        fi

        # Read-only rootfs
        RO=$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$CID")
        if [ "$RO" = "true" ]; then
            pass "$NAME: Read-only root filesystem"
        else
            warn "$NAME: Root filesystem is writable"
        fi

        # No new privileges
        NNP=$(docker inspect --format '{{.HostConfig.SecurityOpt}}' "$CID")
        if echo "$NNP" | grep -q "no-new-privileges"; then
            pass "$NAME: no-new-privileges set"
        else
            warn "$NAME: no-new-privileges not set"
        fi

        # Host network
        NET=$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$CID")
        if [ "$NET" = "host" ]; then
            fail "$NAME: Using host network"
        else
            pass "$NAME: Isolated network ($NET)"
        fi

        # PID namespace
        PID_MODE=$(docker inspect --format '{{.HostConfig.PidMode}}' "$CID")
        if [ "$PID_MODE" = "host" ]; then
            fail "$NAME: Shares host PID namespace"
        else
            pass "$NAME: Isolated PID namespace"
        fi

        # Exposed ports
        PORTS=$(docker inspect --format '{{range $p, $conf := .NetworkSettings.Ports}}{{$p}} {{end}}' "$CID")
        if [ -n "$PORTS" ]; then
            warn "$NAME: Exposed ports: $PORTS"
        fi

        # Environment variable secrets
        docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$CID" | \
            grep -iE 'password|secret|key|token|api_key' | while read -r env_line; do
                KEY=$(echo "$env_line" | cut -d= -f1)
                fail "$NAME: Potential secret in env var: $KEY"
            done

        # Health check
        HC=$(docker inspect --format '{{.State.Health.Status}}' "$CID" 2>/dev/null || echo "none")
        if [ "$HC" = "none" ] || [ -z "$HC" ]; then
            warn "$NAME: No health check configured"
        else
            pass "$NAME: Health check status: $HC"
        fi

        # Resource limits
        MEM=$(docker inspect --format '{{.HostConfig.Memory}}' "$CID")
        CPU=$(docker inspect --format '{{.HostConfig.NanoCpus}}' "$CID")
        if [ "$MEM" = "0" ] && [ "$CPU" = "0" ]; then
            warn "$NAME: No memory or CPU limits set"
        else
            pass "$NAME: Resource limits configured"
        fi
    done
fi

# ── Images ──
header "IMAGE ANALYSIS"

docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null | head -15 | while read -r line; do
    echo -e "  $line"
done

echo ""
DANGLING=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
if [ "$DANGLING" -gt 0 ]; then
    warn "$DANGLING dangling image(s) — run 'docker image prune'"
else
    pass "No dangling images"
fi

# ── Summary ──
echo -e "\n${CYN}══════════════════════════════════════════════════════${RST}"
echo -e "  ${BLD}AUDIT SUMMARY${RST}"
echo -e "  ${GRN}PASS: $PASS${RST}  ${YEL}WARN: $WARN${RST}  ${RED}FAIL: $FAIL${RST}"
TOTAL=$((PASS + WARN + FAIL))
if [ "$TOTAL" -gt 0 ]; then
    SCORE=$(( (PASS * 100) / TOTAL ))
    echo -e "  Score: ${BLD}${SCORE}%${RST}"
fi
echo -e "${CYN}══════════════════════════════════════════════════════${RST}\n"
