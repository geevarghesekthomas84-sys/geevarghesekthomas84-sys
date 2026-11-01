#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  RECON BLADE — Offensive Recon Multi-Tool                       ║
║  Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)       ║
║  Zero dependencies. Pure Python 3.10+ stdlib.                   ║
║  For authorized penetration testing and bug bounty only.        ║
╚══════════════════════════════════════════════════════════════════╝

A single-file reconnaissance Swiss army knife that runs:

  [1] TCP Port Scan        — async, 1000 concurrent, banner grab
  [2] HTTP Header Audit    — 12 security headers, A+ → F grading
  [3] Subdomain Enumeration — async DNS brute-force, 150+ built-in wordlist
  [4] DNS Records          — A, AAAA, MX, NS, TXT, SOA, CNAME
  [5] WHOIS Lookup         — registrar, dates, nameservers
  [6] Tech Fingerprint     — server, framework, CDN detection from headers
  [7] Full Recon           — all modules, exported to JSON + HTML report

Usage:
    python3 recon_blade.py example.com                   # full recon
    python3 recon_blade.py example.com --mode scan       # port scan only
    python3 recon_blade.py example.com --mode headers    # header audit only
    python3 recon_blade.py example.com --mode subdomains # subdomain enum
    python3 recon_blade.py example.com --mode dns        # DNS records
    python3 recon_blade.py example.com --mode whois      # WHOIS lookup
    python3 recon_blade.py example.com --mode tech       # tech fingerprint
    python3 recon_blade.py example.com -o report.json    # save JSON report
    python3 recon_blade.py example.com --html report.html # save HTML report
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import html
import json
import re
import socket
import ssl
import struct
import sys
import time
import urllib.request
from datetime import datetime, timezone
from urllib.error import URLError

# ═══════════════════════════════════════════════════════════════
#  COLORS & UI
# ═══════════════════════════════════════════════════════════════

class C:
    R  = "\033[0;31m"   # red
    G  = "\033[0;32m"   # green
    Y  = "\033[1;33m"   # yellow
    B  = "\033[0;34m"   # blue
    M  = "\033[0;35m"   # magenta
    CN = "\033[0;36m"   # cyan
    W  = "\033[1;37m"   # white bold
    D  = "\033[0;90m"   # dim
    BD = "\033[1m"      # bold
    X  = "\033[0m"      # reset

    @staticmethod
    def strip(text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)


def banner():
    print(f"""
{C.CN}╔══════════════════════════════════════════════════════════════╗
║{C.X}  {C.W}██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗{C.X}                ║
║{C.X}  {C.W}██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║{C.X}                ║
║{C.X}  {C.R}██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║{C.X}                ║
║{C.X}  {C.R}██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║{C.X}                ║
║{C.X}  {C.Y}██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║{C.X}                ║
║{C.X}  {C.Y}╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝{C.X}               ║
║{C.X}  {C.CN}████████████████████████{C.R}  BLADE{C.X}  {C.D}v1.0{C.X}                  ║
{C.CN}╠══════════════════════════════════════════════════════════════╣
║{C.X}  {C.D}Offensive Recon Multi-Tool — Zero Dependencies{C.X}              ║
║{C.X}  {C.D}Author: @geevarghesekthomas84-sys{C.X}                          ║
║{C.X}  {C.D}For authorized testing only.{C.X}                                ║
{C.CN}╚══════════════════════════════════════════════════════════════╝{C.X}
""")


def section(title: str):
    line = "─" * (56 - len(title))
    print(f"\n{C.CN}┌─[ {C.W}{title} {C.CN}]{line}┐{C.X}")


def section_end():
    print(f"{C.CN}└{'─' * 60}┘{C.X}")


def ok(msg: str):    print(f"{C.CN}│{C.X}  {C.G}[+]{C.X} {msg}")
def warn(msg: str):  print(f"{C.CN}│{C.X}  {C.Y}[!]{C.X} {msg}")
def fail(msg: str):  print(f"{C.CN}│{C.X}  {C.R}[✗]{C.X} {msg}")
def info(msg: str):  print(f"{C.CN}│{C.X}  {C.CN}[*]{C.X} {msg}")
def dim(msg: str):   print(f"{C.CN}│{C.X}  {C.D}    {msg}{C.X}")


# ═══════════════════════════════════════════════════════════════
#  MODULE 1: TCP PORT SCAN
# ═══════════════════════════════════════════════════════════════

SERVICES = {
    21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",
    110:"POP3",111:"RPCbind",135:"MSRPC",139:"NetBIOS",143:"IMAP",
    443:"HTTPS",445:"SMB",993:"IMAPS",995:"POP3S",1433:"MSSQL",
    1521:"Oracle",3306:"MySQL",3389:"RDP",5432:"PostgreSQL",
    5900:"VNC",6379:"Redis",8080:"HTTP-Proxy",8443:"HTTPS-Alt",
    9200:"Elasticsearch",27017:"MongoDB",
}

async def _grab_banner(reader, writer, timeout=2.0):
    try:
        writer.write(b"\r\n")
        await writer.drain()
        data = await asyncio.wait_for(reader.read(1024), timeout=timeout)
        return data.decode(errors="replace").strip()[:100]
    except Exception:
        return ""

async def _scan_one(sem, ip, port, timeout, hits):
    async with sem:
        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            bnr = await _grab_banner(r, w, timeout)
            w.close()
            await w.wait_closed()
            hits.append({"port": port, "service": SERVICES.get(port, "unknown"), "banner": bnr})
        except Exception:
            pass

async def port_scan(target: str, ports: str = "1-1024", workers: int = 1000, timeout: float = 1.5) -> list[dict]:
    section("TCP PORT SCAN")
    ip = socket.gethostbyname(target)
    info(f"Target: {target} ({ip})")
    info(f"Ports: {ports}  Workers: {workers}")

    port_list = []
    for part in ports.split(","):
        if "-" in part:
            a, b = map(int, part.split("-", 1))
            port_list.extend(range(a, b + 1))
        else:
            port_list.append(int(part))
    port_list = sorted(set(p for p in port_list if 1 <= p <= 65535))

    sem = asyncio.Semaphore(workers)
    hits: list[dict] = []
    t0 = time.time()
    await asyncio.gather(*[_scan_one(sem, ip, p, timeout, hits) for p in port_list])
    elapsed = time.time() - t0
    hits.sort(key=lambda h: h["port"])

    if hits:
        print(f"{C.CN}│{C.X}")
        print(f"{C.CN}│{C.X}  {C.W}{'PORT':<8} {'SERVICE':<16} {'BANNER'}{C.X}")
        print(f"{C.CN}│{C.X}  {'─'*8} {'─'*16} {'─'*32}")
        for h in hits:
            bnr = h["banner"] or "—"
            print(f"{C.CN}│{C.X}  {C.G}{h['port']:<8}{C.X} {C.Y}{h['service']:<16}{C.X} {C.D}{bnr}{C.X}")
        print(f"{C.CN}│{C.X}")
        ok(f"{C.W}{len(hits)}{C.X} open ports found in {elapsed:.1f}s")
    else:
        warn("No open ports found")

    section_end()
    return hits


# ═══════════════════════════════════════════════════════════════
#  MODULE 2: HTTP SECURITY HEADERS
# ═══════════════════════════════════════════════════════════════

HEADERS_SPEC = {
    "Strict-Transport-Security":    (10, lambda v: "max-age" in v.lower()),
    "Content-Security-Policy":      (10, lambda v: "default-src" in v.lower() or "script-src" in v.lower()),
    "X-Content-Type-Options":       (5,  lambda v: v.strip().lower() == "nosniff"),
    "X-Frame-Options":              (5,  lambda v: v.strip().upper() in ("DENY","SAMEORIGIN")),
    "Referrer-Policy":              (5,  lambda v: bool(v.strip())),
    "Permissions-Policy":           (5,  lambda v: bool(v.strip())),
    "X-XSS-Protection":            (3,  lambda v: "1" in v),
    "Cross-Origin-Opener-Policy":   (4,  lambda v: bool(v.strip())),
    "Cross-Origin-Resource-Policy": (4,  lambda v: bool(v.strip())),
    "Cross-Origin-Embedder-Policy": (3,  lambda v: bool(v.strip())),
    "X-Permitted-Cross-Domain":     (2,  lambda v: bool(v.strip())),
    "Cache-Control":                (3,  lambda v: "no-store" in v.lower() or "private" in v.lower()),
}

LEAK_HEADERS = ["Server", "X-Powered-By", "X-AspNet-Version", "X-AspNetMvc-Version", "X-Generator"]

def header_audit(target: str) -> dict:
    section("HTTP SECURITY HEADERS")
    url = target if target.startswith("http") else f"https://{target}"
    info(f"URL: {url}")

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ReconBlade/1.0")

    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            headers = dict(resp.headers)
            status = resp.status
    except URLError as e:
        fail(f"Connection failed: {e}")
        section_end()
        return {"error": str(e)}

    info(f"Status: {status}")
    print(f"{C.CN}│{C.X}")

    max_score = sum(w for w, _ in HEADERS_SPEC.values())
    earned = 0
    present, missing, leaks = [], [], []

    for name, (weight, check) in HEADERS_SPEC.items():
        val = headers.get(name)
        if val and check(val):
            earned += weight
            ok(f"{name}: {C.D}{val.strip()[:60]}{C.X}")
            present.append({"header": name, "value": val.strip(), "status": "good"})
        elif val:
            earned += weight // 2
            warn(f"{name}: {C.D}{val.strip()[:60]}{C.X} {C.Y}(weak){C.X}")
            present.append({"header": name, "value": val.strip(), "status": "weak"})
        else:
            fail(f"{name} {C.R}— MISSING{C.X}")
            missing.append(name)

    print(f"{C.CN}│{C.X}")
    for name in LEAK_HEADERS:
        val = headers.get(name)
        if val:
            warn(f"Info leak: {C.R}{name}: {val.strip()}{C.X}")
            leaks.append({"header": name, "value": val.strip()})

    score = round((earned / max_score) * 100) if max_score else 0
    grades = [(90,"A+",C.G),(80,"A",C.G),(70,"B",C.Y),(50,"C",C.Y),(30,"D",C.R),(0,"F",C.R)]
    grade, color = next((g, c) for threshold, g, c in grades if score >= threshold)

    print(f"{C.CN}│{C.X}")
    info(f"Score: {color}{C.BD}{score}%{C.X}  Grade: {color}{C.BD}{grade}{C.X}")
    section_end()

    return {"score": score, "grade": grade, "present": present, "missing": missing, "leaks": leaks}


# ═══════════════════════════════════════════════════════════════
#  MODULE 3: SUBDOMAIN ENUMERATION
# ═══════════════════════════════════════════════════════════════

WORDLIST = [
    "www","mail","ftp","cpanel","webmail","smtp","pop","imap","blog",
    "forum","shop","store","api","dev","staging","test","admin","portal",
    "vpn","remote","gateway","proxy","cdn","ns1","ns2","ns3","dns",
    "dns1","dns2","mx","mx1","mx2","app","apps","mobile","m","beta",
    "alpha","demo","sandbox","git","gitlab","github","ci","cd","jenkins",
    "build","docs","doc","wiki","help","support","status","monitor",
    "grafana","prometheus","kibana","elastic","logs","sentry","db",
    "database","mysql","postgres","redis","mongo","sql","auth","login",
    "sso","oauth","id","identity","accounts","static","assets","media",
    "images","img","files","upload","s3","storage","backup","archive",
    "old","legacy","v1","v2","internal","intranet","extranet","private",
    "corp","office","crm","erp","hr","jira","confluence","slack","teams",
    "staging2","uat","qa","preprod","prod","production","web","web1",
    "web2","server","srv","node","cluster","k8s","kubernetes","docker",
    "container","registry","analytics","tracking","metrics","telemetry",
    "events","payment","pay","billing","invoice","checkout","cart",
    "email","newsletter","calendar","meet","video","chat","ws","wss",
    "graphql","rest","rpc","grpc","webhook","callback","notify","push",
]

async def _resolve(sem, domain, hits):
    async with sem:
        try:
            loop = asyncio.get_event_loop()
            addrs = await asyncio.wait_for(
                loop.getaddrinfo(domain, None, family=socket.AF_UNSPEC), timeout=3.0
            )
            ips = sorted({a[4][0] for a in addrs})
            hits.append({"subdomain": domain, "ips": ips})
            ok(f"{C.W}{domain:<40}{C.X} {C.D}{', '.join(ips)}{C.X}")
        except Exception:
            pass

async def subdomain_enum(target: str, wordlist_path: str | None = None, workers: int = 150) -> list[dict]:
    section("SUBDOMAIN ENUMERATION")

    if wordlist_path:
        with open(wordlist_path) as f:
            words = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        info(f"Wordlist: {wordlist_path} ({len(words)} entries)")
    else:
        words = WORDLIST
        info(f"Built-in wordlist: {len(words)} entries")

    info(f"Workers: {workers}")
    print(f"{C.CN}│{C.X}")

    subs = [f"{w}.{target}" for w in words]
    sem = asyncio.Semaphore(workers)
    hits: list[dict] = []
    t0 = time.time()
    await asyncio.gather(*[_resolve(sem, s, hits) for s in subs])
    elapsed = time.time() - t0
    hits.sort(key=lambda h: h["subdomain"])

    print(f"{C.CN}│{C.X}")
    info(f"{C.W}{len(hits)}{C.X} live subdomains found in {elapsed:.1f}s")
    section_end()
    return hits


# ═══════════════════════════════════════════════════════════════
#  MODULE 4: DNS RECORDS
# ═══════════════════════════════════════════════════════════════

def _dns_query(domain: str, qtype: int) -> list[str]:
    TYPE_NAMES = {1:"A", 28:"AAAA", 15:"MX", 2:"NS", 16:"TXT", 6:"SOA", 5:"CNAME"}
    tid = struct.pack("!H", int(time.time()) % 65536)
    flags = b"\x01\x00"
    counts = struct.pack("!4H", 1, 0, 0, 0)
    qname = b""
    for part in domain.split("."):
        qname += bytes([len(part)]) + part.encode()
    qname += b"\x00"
    question = qname + struct.pack("!2H", qtype, 1)
    packet = tid + flags + counts + question

    results = []
    for server in ["8.8.8.8", "1.1.1.1"]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            sock.sendto(packet, (server, 53))
            data, _ = sock.recvfrom(4096)
            sock.close()

            _, flags_r = struct.unpack("!HH", data[:4])
            qd, an = struct.unpack("!HH", data[4:8])

            offset = 12
            for _ in range(qd):
                while data[offset] != 0:
                    if data[offset] & 0xC0 == 0xC0:
                        offset += 2; break
                    else:
                        offset += data[offset] + 1
                else:
                    offset += 1
                offset += 4

            for _ in range(an):
                if data[offset] & 0xC0 == 0xC0:
                    offset += 2
                else:
                    while data[offset] != 0:
                        offset += data[offset] + 1
                    offset += 1

                rtype, rclass, rttl, rdlen = struct.unpack("!HHIH", data[offset:offset+10])
                offset += 10
                rdata = data[offset:offset+rdlen]
                offset += rdlen

                if rtype == 1 and len(rdata) == 4:
                    results.append(socket.inet_ntoa(rdata))
                elif rtype == 28 and len(rdata) == 16:
                    results.append(socket.inet_ntop(socket.AF_INET6, rdata))
                elif rtype == 15 and len(rdata) >= 4:
                    prio = struct.unpack("!H", rdata[:2])[0]
                    mx_name = _decode_dns_name(data, offset - rdlen + 2)
                    results.append(f"{prio} {mx_name}")
                elif rtype in (2, 5):
                    results.append(_decode_dns_name(data, offset - rdlen))
                elif rtype == 16:
                    txt = ""
                    i = 0
                    while i < rdlen:
                        slen = rdata[i]; i += 1
                        txt += rdata[i:i+slen].decode(errors="replace"); i += slen
                    results.append(txt)
                elif rtype == 6:
                    mname = _decode_dns_name(data, offset - rdlen)
                    results.append(f"SOA {mname}")

            if results:
                break
        except Exception:
            continue
    return results

def _decode_dns_name(data: bytes, offset: int) -> str:
    parts = []
    seen = set()
    while offset < len(data) and offset not in seen:
        seen.add(offset)
        length = data[offset]
        if length == 0:
            break
        if length & 0xC0 == 0xC0:
            pointer = struct.unpack("!H", data[offset:offset+2])[0] & 0x3FFF
            parts.append(_decode_dns_name(data, pointer))
            break
        offset += 1
        parts.append(data[offset:offset+length].decode(errors="replace"))
        offset += length
    return ".".join(parts)

def dns_records(target: str) -> dict:
    section("DNS RECORDS")
    info(f"Domain: {target}")
    print(f"{C.CN}│{C.X}")

    record_types = {"A": 1, "AAAA": 28, "MX": 15, "NS": 2, "TXT": 16, "CNAME": 5, "SOA": 6}
    all_records = {}

    for name, qtype in record_types.items():
        try:
            records = _dns_query(target, qtype)
            if records:
                all_records[name] = records
                for r in records:
                    ok(f"{C.W}{name:>5}{C.X}  {r}")
            else:
                dim(f"{name:>5}  (none)")
        except Exception:
            dim(f"{name:>5}  (query failed)")

    section_end()
    return all_records


# ═══════════════════════════════════════════════════════════════
#  MODULE 5: WHOIS LOOKUP
# ═══════════════════════════════════════════════════════════════

def whois_lookup(target: str) -> dict:
    section("WHOIS LOOKUP")
    info(f"Domain: {target}")
    print(f"{C.CN}│{C.X}")

    result = {}
    try:
        tld = target.rsplit(".", 1)[-1]
        whois_servers = {
            "com": "whois.verisign-grs.com", "net": "whois.verisign-grs.com",
            "org": "whois.pir.org", "io": "whois.nic.io", "dev": "whois.nic.google",
            "ai": "whois.nic.ai", "co": "whois.nic.co", "me": "whois.nic.me",
            "info": "whois.afilias.net", "xyz": "whois.nic.xyz",
        }
        server = whois_servers.get(tld, f"whois.nic.{tld}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((server, 43))
        sock.send(f"{target}\r\n".encode())

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        sock.close()
        raw = response.decode(errors="replace")

        fields = {
            "Registrar": r"Registrar:\s*(.+)",
            "Created": r"Creat(?:ion|ed)\s*Date:\s*(.+)",
            "Updated": r"Updated?\s*Date:\s*(.+)",
            "Expires": r"Expir(?:y|ation)\s*Date:\s*(.+)",
            "Status": r"Status:\s*(.+)",
            "Nameservers": r"Name\s*Server:\s*(.+)",
        }

        nameservers = []
        statuses = []
        for line in raw.split("\n"):
            for field, pattern in fields.items():
                m = re.search(pattern, line, re.IGNORECASE)
                if m:
                    val = m.group(1).strip()
                    if field == "Nameservers":
                        nameservers.append(val.lower())
                    elif field == "Status":
                        statuses.append(val.split()[0])
                    else:
                        result[field.lower()] = val
                        ok(f"{C.W}{field:<14}{C.X} {val}")

        if nameservers:
            result["nameservers"] = list(set(nameservers))
            for ns in sorted(set(nameservers)):
                ok(f"{C.W}{'Nameserver':<14}{C.X} {ns}")

        if statuses:
            result["status"] = list(set(statuses))
            info(f"Status codes: {', '.join(set(statuses))}")

        if not result:
            warn("No structured WHOIS data returned")

    except Exception as e:
        fail(f"WHOIS query failed: {e}")
        result["error"] = str(e)

    section_end()
    return result


# ═══════════════════════════════════════════════════════════════
#  MODULE 6: TECH FINGERPRINT
# ═══════════════════════════════════════════════════════════════

def tech_fingerprint(target: str) -> dict:
    section("TECHNOLOGY FINGERPRINT")
    url = target if target.startswith("http") else f"https://{target}"
    info(f"URL: {url}")
    print(f"{C.CN}│{C.X}")

    ctx = ssl.create_default_context()
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    techs = {}
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            headers = dict(resp.headers)
            body = resp.read(50000).decode(errors="replace")

        srv = headers.get("Server", "")
        if srv:
            techs["server"] = srv.strip()
            ok(f"{C.W}Server:{C.X}      {srv.strip()}")

        powered = headers.get("X-Powered-By", "")
        if powered:
            techs["powered_by"] = powered.strip()
            ok(f"{C.W}Powered By:{C.X}  {powered.strip()}")

        cdn_hints = {
            "cloudflare": "Cloudflare", "akamai": "Akamai",
            "fastly": "Fastly", "cloudfront": "CloudFront",
            "varnish": "Varnish", "sucuri": "Sucuri",
        }
        all_headers_str = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
        for hint, cdn_name in cdn_hints.items():
            if hint in all_headers_str:
                techs["cdn"] = cdn_name
                ok(f"{C.W}CDN:{C.X}         {cdn_name}")
                break

        framework_sigs = [
            (r"wp-content|wordpress", "WordPress"),
            (r"drupal", "Drupal"),
            (r"joomla", "Joomla"),
            (r"react", "React"),
            (r"next\.js|__next", "Next.js"),
            (r"vue\.js|__vue", "Vue.js"),
            (r"angular", "Angular"),
            (r"laravel", "Laravel"),
            (r"django", "Django"),
            (r"flask", "Flask"),
            (r"express", "Express.js"),
            (r"rails", "Ruby on Rails"),
            (r"shopify", "Shopify"),
            (r"squarespace", "Squarespace"),
            (r"wix\.com", "Wix"),
        ]

        detected_fw = []
        body_lower = body.lower()
        for pattern, name in framework_sigs:
            if re.search(pattern, body_lower):
                detected_fw.append(name)

        if detected_fw:
            techs["frameworks"] = detected_fw
            for fw in detected_fw:
                ok(f"{C.W}Framework:{C.X}   {fw}")

        cookies = headers.get("Set-Cookie", "")
        cookie_hints = {
            "PHPSESSID": "PHP", "ASP.NET": "ASP.NET", "JSESSIONID": "Java/Tomcat",
            "laravel_session": "Laravel", "rack.session": "Ruby/Rack",
            "connect.sid": "Node.js/Express", "_csrf": "CSRF Protection",
        }
        for cookie_name, tech in cookie_hints.items():
            if cookie_name.lower() in cookies.lower():
                techs.setdefault("cookies", []).append(tech)
                ok(f"{C.W}Cookie:{C.X}      {tech} ({cookie_name})")

        if "text/html" in headers.get("Content-Type", ""):
            title_m = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
            if title_m:
                techs["page_title"] = title_m.group(1).strip()[:80]
                info(f"Title: {techs['page_title']}")

        if not techs:
            warn("No technologies detected")

    except URLError as e:
        fail(f"Connection failed: {e}")
        techs["error"] = str(e)

    section_end()
    return techs


# ═══════════════════════════════════════════════════════════════
#  REPORT GENERATION
# ═══════════════════════════════════════════════════════════════

def save_json(report: dict, path: str):
    with open(path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n{C.G}[+]{C.X} JSON report saved: {C.W}{path}{C.X}")


def save_html(report: dict, path: str):
    target = report.get("target", "unknown")
    timestamp = report.get("timestamp", "")

    def badge(text, color="#E0A82E"):
        return f'<span style="background:{color};color:#0d1117;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{html.escape(str(text))}</span>'

    sections_html = []

    if "port_scan" in report:
        rows = ""
        for p in report["port_scan"]:
            rows += f"<tr><td>{p['port']}</td><td>{html.escape(p['service'])}</td><td>{html.escape(p.get('banner','') or '—')}</td></tr>\n"
        sections_html.append(f"""
        <div class="card">
            <h2>TCP Port Scan</h2>
            <p>{badge(f"{len(report['port_scan'])} open ports", "#ff3b3b" if report['port_scan'] else "#4ade80")}</p>
            <table><tr><th>Port</th><th>Service</th><th>Banner</th></tr>{rows}</table>
        </div>""")

    if "headers" in report and "error" not in report["headers"]:
        h = report["headers"]
        grade_color = {"A+":"#4ade80","A":"#4ade80","B":"#E0A82E","C":"#E0A82E","D":"#ff3b3b","F":"#ff3b3b"}.get(h.get("grade","F"),"#ff3b3b")
        missing_list = "".join(f"<li>{html.escape(m)}</li>" for m in h.get("missing",[]))
        leak_list = "".join(f"<li><b>{html.escape(l['header'])}</b>: {html.escape(l['value'])}</li>" for l in h.get("leaks",[]))
        sections_html.append(f"""
        <div class="card">
            <h2>HTTP Security Headers</h2>
            <p>{badge(f"Grade: {h.get('grade','?')} ({h.get('score',0)}%)", grade_color)}</p>
            {"<h3>Missing Headers</h3><ul>" + missing_list + "</ul>" if missing_list else ""}
            {"<h3>Information Leakage</h3><ul>" + leak_list + "</ul>" if leak_list else ""}
        </div>""")

    if "subdomains" in report:
        sub_rows = "".join(f"<tr><td>{html.escape(s['subdomain'])}</td><td>{html.escape(', '.join(s['ips']))}</td></tr>" for s in report["subdomains"])
        sections_html.append(f"""
        <div class="card">
            <h2>Subdomain Enumeration</h2>
            <p>{badge(f"{len(report['subdomains'])} live subdomains")}</p>
            <table><tr><th>Subdomain</th><th>IPs</th></tr>{sub_rows}</table>
        </div>""")

    if "dns" in report:
        dns_rows = ""
        for rtype, records in report["dns"].items():
            for r in records:
                dns_rows += f"<tr><td><b>{html.escape(rtype)}</b></td><td>{html.escape(r)}</td></tr>"
        sections_html.append(f"""
        <div class="card">
            <h2>DNS Records</h2>
            <table><tr><th>Type</th><th>Value</th></tr>{dns_rows}</table>
        </div>""")

    if "whois" in report and "error" not in report.get("whois", {}):
        whois_rows = ""
        for k, v in report["whois"].items():
            val = ", ".join(v) if isinstance(v, list) else str(v)
            whois_rows += f"<tr><td><b>{html.escape(k.title())}</b></td><td>{html.escape(val)}</td></tr>"
        sections_html.append(f"""
        <div class="card">
            <h2>WHOIS</h2>
            <table>{whois_rows}</table>
        </div>""")

    if "tech" in report and "error" not in report.get("tech", {}):
        tech_rows = ""
        for k, v in report["tech"].items():
            val = ", ".join(v) if isinstance(v, list) else str(v)
            tech_rows += f"<tr><td><b>{html.escape(k.replace('_',' ').title())}</b></td><td>{html.escape(val)}</td></tr>"
        sections_html.append(f"""
        <div class="card">
            <h2>Technology Fingerprint</h2>
            <table>{tech_rows}</table>
        </div>""")

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Recon Blade — {html.escape(target)}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;padding:40px 20px}}
.container{{max-width:900px;margin:0 auto}}
h1{{color:#E0A82E;font-size:28px;margin-bottom:4px}}
.subtitle{{color:#8b949e;margin-bottom:30px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:24px;margin-bottom:20px}}
.card h2{{color:#E0A82E;font-size:18px;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #21262d}}
.card h3{{color:#c9d1d9;font-size:14px;margin:12px 0 6px}}
table{{width:100%;border-collapse:collapse;margin-top:12px;font-size:14px}}
th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #21262d}}
th{{color:#E0A82E;font-weight:600}}
td{{color:#c9d1d9}}
ul{{margin-left:20px;font-size:14px;line-height:1.8}}
.footer{{text-align:center;color:#484f58;font-size:12px;margin-top:30px;padding-top:20px;border-top:1px solid #21262d}}
</style></head><body>
<div class="container">
<h1>RECON BLADE</h1>
<p class="subtitle">Target: <b>{html.escape(target)}</b> &nbsp;|&nbsp; {html.escape(timestamp)}</p>
{"".join(sections_html)}
<div class="footer">Generated by Recon Blade — @geevarghesekthomas84-sys</div>
</div></body></html>"""

    with open(path, "w") as f:
        f.write(page)
    print(f"{C.G}[+]{C.X} HTML report saved: {C.W}{path}{C.X}")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

async def run_full_recon(args) -> dict:
    target = args.target
    report = {"target": target, "timestamp": datetime.now(timezone.utc).isoformat()}

    mode = args.mode or "full"

    if mode in ("full", "scan"):
        report["port_scan"] = await port_scan(target, args.ports)

    if mode in ("full", "headers"):
        report["headers"] = header_audit(target)

    if mode in ("full", "subdomains"):
        report["subdomains"] = await subdomain_enum(target, args.wordlist)

    if mode in ("full", "dns"):
        report["dns"] = dns_records(target)

    if mode in ("full", "whois"):
        report["whois"] = whois_lookup(target)

    if mode in ("full", "tech"):
        report["tech"] = tech_fingerprint(target)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="RECON BLADE — Offensive Recon Multi-Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", help="Target domain or IP")
    parser.add_argument("--mode", "-m", choices=["full","scan","headers","subdomains","dns","whois","tech"],
                        help="Run a specific module (default: full)")
    parser.add_argument("--ports", "-p", default="1-1024", help="Port range for scan (default: 1-1024)")
    parser.add_argument("--wordlist", "-w", help="Custom subdomain wordlist file")
    parser.add_argument("-o", "--output", help="Save JSON report")
    parser.add_argument("--html", help="Save HTML report")

    args = parser.parse_args()
    banner()

    info_line = f"  {C.CN}Target:{C.X} {C.W}{args.target}{C.X}  {C.CN}Mode:{C.X} {C.W}{args.mode or 'full'}{C.X}  {C.CN}Time:{C.X} {C.D}{datetime.now().strftime('%H:%M:%S')}{C.X}"
    print(info_line)

    t0 = time.time()
    report = asyncio.run(run_full_recon(args))
    elapsed = time.time() - t0

    print(f"\n{C.CN}{'═' * 60}{C.X}")
    print(f"  {C.G}Recon complete{C.X} in {C.W}{elapsed:.1f}s{C.X}")
    print(f"{C.CN}{'═' * 60}{C.X}")

    if args.output:
        save_json(report, args.output)
    if args.html:
        save_html(report, args.html)

    if not args.output and not args.html:
        print(f"\n  {C.D}Tip: add -o report.json or --html report.html to save results{C.X}\n")


if __name__ == "__main__":
    main()
