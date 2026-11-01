#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# linux_recon.sh — Automated Linux Enumeration & Recon Script
# Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)
#
# Gathers system info, network config, users, SUID binaries,
# cron jobs, writable dirs, and potential privilege escalation
# vectors. For authorized security assessments only.
#
# Usage: chmod +x linux_recon.sh && ./linux_recon.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

RED='\033[0;31m'
GRN='\033[0;32m'
YEL='\033[1;33m'
CYN='\033[0;36m'
RST='\033[0m'

banner() {
    echo -e "\n${CYN}╔══════════════════════════════════════════════════╗${RST}"
    echo -e "${CYN}║${RST}  ${YEL}$1${RST}"
    echo -e "${CYN}╚══════════════════════════════════════════════════╝${RST}"
}

info()  { echo -e "  ${GRN}[+]${RST} $1"; }
warn()  { echo -e "  ${YEL}[!]${RST} $1"; }
alert() { echo -e "  ${RED}[!!]${RST} $1"; }

OUTFILE="/tmp/recon_$(hostname)_$(date +%Y%m%d_%H%M%S).txt"

{
echo -e "\n${CYN}════════════════════════════════════════════════════════${RST}"
echo -e "${CYN}  Linux Recon — $(date)${RST}"
echo -e "${CYN}════════════════════════════════════════════════════════${RST}"

# ── System Info ──
banner "SYSTEM INFORMATION"
info "Hostname   : $(hostname)"
info "Kernel     : $(uname -r)"
info "OS         : $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '"' || echo 'Unknown')"
info "Arch       : $(uname -m)"
info "Uptime     : $(uptime -p 2>/dev/null || uptime)"

# ── Current User ──
banner "CURRENT USER & PRIVILEGES"
info "User       : $(whoami) (UID=$(id -u))"
info "Groups     : $(id -Gn 2>/dev/null | tr ' ' ', ')"
if sudo -n true 2>/dev/null; then
    alert "PASSWORDLESS SUDO AVAILABLE"
fi
sudo -l 2>/dev/null | head -20 && true

# ── Network ──
banner "NETWORK CONFIGURATION"
info "Interfaces:"
ip -br addr 2>/dev/null || ifconfig 2>/dev/null | grep -E 'inet |flags'
echo ""
info "Routing table:"
ip route 2>/dev/null || route -n 2>/dev/null
echo ""
info "Listening ports:"
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null
echo ""
info "ARP cache:"
ip neigh 2>/dev/null || arp -a 2>/dev/null

# ── Users ──
banner "USERS & AUTHENTICATION"
info "Users with shell access:"
grep -vE '(nologin|false|sync|halt|shutdown)$' /etc/passwd 2>/dev/null | \
    awk -F: '{printf "  %-20s UID=%-6s HOME=%s\n", $1, $3, $6}'
echo ""
info "Currently logged in:"
w 2>/dev/null || who 2>/dev/null
echo ""
info "Last logins:"
last -n 10 2>/dev/null

# ── SUID/SGID Binaries ──
banner "SUID / SGID BINARIES (Priv-Esc Candidates)"
warn "Searching for SUID binaries..."
find / -perm -4000 -type f 2>/dev/null | while read -r bin; do
    echo -e "  ${RED}SUID${RST}  $bin"
done
echo ""
warn "Searching for SGID binaries..."
find / -perm -2000 -type f 2>/dev/null | head -20 | while read -r bin; do
    echo -e "  ${YEL}SGID${RST}  $bin"
done

# ── Capabilities ──
banner "FILE CAPABILITIES"
getcap -r / 2>/dev/null | head -30 && true

# ── Cron Jobs ──
banner "SCHEDULED TASKS & CRON"
info "System crontabs:"
ls -la /etc/cron* 2>/dev/null
echo ""
cat /etc/crontab 2>/dev/null
echo ""
info "User crontab:"
crontab -l 2>/dev/null || echo "  (none)"
echo ""
info "Systemd timers:"
systemctl list-timers --no-pager 2>/dev/null | head -15

# ── Writable Directories ──
banner "WORLD-WRITABLE DIRECTORIES"
find / -writable -type d 2>/dev/null | grep -v proc | head -25 | while read -r d; do
    echo "  $d"
done

# ── Interesting Files ──
banner "INTERESTING FILES"
for f in /etc/shadow /etc/sudoers /root/.ssh/id_rsa /root/.bash_history \
         /home/*/.ssh/id_rsa /home/*/.bash_history /var/log/auth.log; do
    if [ -r "$f" ] 2>/dev/null; then
        alert "READABLE: $f"
    fi
done
echo ""
info "Config files with passwords:"
grep -rl 'password\|passwd\|credential' /etc/ 2>/dev/null | head -10 && true

# ── Docker / Containers ──
banner "CONTAINER & VIRTUALIZATION"
if [ -f /.dockerenv ]; then alert "Running inside Docker"; fi
if grep -q 'docker\|lxc\|kubepods' /proc/1/cgroup 2>/dev/null; then
    alert "Container environment detected"
fi
if command -v docker &>/dev/null; then
    info "Docker available — checking socket..."
    if [ -w /var/run/docker.sock ]; then
        alert "Docker socket writable — container escape possible"
    fi
fi

echo -e "\n${CYN}════════════════════════════════════════════════════════${RST}"
echo -e "${GRN}  Recon complete.${RST}"
echo -e "${CYN}════════════════════════════════════════════════════════${RST}\n"

} 2>&1 | tee "$OUTFILE"

echo -e "  ${GRN}[+]${RST} Output saved to: ${YEL}$OUTFILE${RST}\n"
