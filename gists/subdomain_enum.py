#!/usr/bin/env python3
"""
subdomain_enum.py — Fast Async Subdomain Enumerator
Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)

Brute-forces subdomains using async DNS resolution.
No external dependencies — stdlib only.

Usage:
    python3 subdomain_enum.py example.com
    python3 subdomain_enum.py example.com --wordlist custom.txt --workers 200
    python3 subdomain_enum.py example.com --output results.json

For authorized security assessments and bug bounty only.
"""

import asyncio
import argparse
import json
import socket
import sys
from datetime import datetime

DEFAULT_WORDLIST = [
    "www", "mail", "ftp", "cpanel", "webmail", "smtp", "pop", "imap",
    "blog", "forum", "shop", "store", "api", "dev", "staging", "test",
    "admin", "portal", "vpn", "remote", "gateway", "proxy", "cdn",
    "ns1", "ns2", "ns3", "dns", "dns1", "dns2", "mx", "mx1", "mx2",
    "app", "apps", "mobile", "m", "beta", "alpha", "demo", "sandbox",
    "git", "gitlab", "github", "ci", "cd", "jenkins", "build",
    "docs", "doc", "wiki", "help", "support", "status", "monitor",
    "grafana", "prometheus", "kibana", "elastic", "logs", "sentry",
    "db", "database", "mysql", "postgres", "redis", "mongo", "sql",
    "auth", "login", "sso", "oauth", "id", "identity", "accounts",
    "static", "assets", "media", "images", "img", "files", "upload",
    "s3", "storage", "backup", "archive", "old", "legacy", "v1", "v2",
    "internal", "intranet", "extranet", "private", "corp", "office",
    "crm", "erp", "hr", "jira", "confluence", "slack", "teams",
    "staging2", "uat", "qa", "preprod", "prod", "production",
    "web", "web1", "web2", "server", "srv", "node", "cluster",
    "k8s", "kubernetes", "docker", "container", "registry",
    "analytics", "tracking", "metrics", "telemetry", "events",
    "payment", "pay", "billing", "invoice", "checkout", "cart",
]


async def resolve(sem: asyncio.Semaphore, domain: str, results: list):
    async with sem:
        try:
            loop = asyncio.get_event_loop()
            addrs = await asyncio.wait_for(
                loop.getaddrinfo(domain, None, family=socket.AF_UNSPEC),
                timeout=3.0,
            )
            ips = sorted({addr[4][0] for addr in addrs})
            results.append({"subdomain": domain, "ips": ips})
            print(f"  \033[0;32m[+]\033[0m {domain:<45} {', '.join(ips)}")
        except (socket.gaierror, asyncio.TimeoutError, OSError):
            pass


async def main():
    parser = argparse.ArgumentParser(description="Async Subdomain Enumerator")
    parser.add_argument("domain", help="Target domain (e.g. example.com)")
    parser.add_argument("--wordlist", "-w", help="Path to wordlist file (one subdomain per line)")
    parser.add_argument("--workers", "-c", type=int, default=100, help="Concurrent resolvers (default: 100)")
    parser.add_argument("--output", "-o", help="Save results as JSON")
    args = parser.parse_args()

    if args.wordlist:
        with open(args.wordlist) as f:
            words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        words = DEFAULT_WORDLIST

    subdomains = [f"{w}.{args.domain}" for w in words]

    print(f"\n{'=' * 58}")
    print(f"  Target    : {args.domain}")
    print(f"  Wordlist  : {len(subdomains)} subdomains")
    print(f"  Workers   : {args.workers}")
    print(f"  Started   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 58}\n")

    sem = asyncio.Semaphore(args.workers)
    results = []
    tasks = [resolve(sem, sub, results) for sub in subdomains]
    await asyncio.gather(*tasks)

    results.sort(key=lambda r: r["subdomain"])

    print(f"\n{'─' * 58}")
    print(f"  Found {len(results)} live subdomains out of {len(subdomains)} tested.")
    print(f"{'─' * 58}\n")

    if args.output and results:
        output = {
            "target": args.domain,
            "scan_time": datetime.now().isoformat(),
            "total_tested": len(subdomains),
            "results": results,
        }
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"  [+] Results saved to: {args.output}\n")


if __name__ == "__main__":
    asyncio.run(main())
