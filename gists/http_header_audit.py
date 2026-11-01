#!/usr/bin/env python3
"""
http_header_audit.py — HTTP Security Header Analyzer
Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)

Checks a target URL for missing or misconfigured HTTP security headers,
grades the overall posture, and suggests fixes.

Usage:
    python3 http_header_audit.py https://example.com
    python3 http_header_audit.py https://example.com --json

No external dependencies — stdlib only.
"""

import argparse
import json
import ssl
import sys
import urllib.request
from urllib.error import URLError

SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "weight": 10,
        "description": "Enforces HTTPS connections",
        "fix": 'Strict-Transport-Security: max-age=63072000; includeSubDomains; preload',
        "check": lambda v: "max-age" in v.lower(),
    },
    "Content-Security-Policy": {
        "weight": 10,
        "description": "Mitigates XSS and injection attacks",
        "fix": "Content-Security-Policy: default-src 'self'; script-src 'self'",
        "check": lambda v: "default-src" in v.lower() or "script-src" in v.lower(),
    },
    "X-Content-Type-Options": {
        "weight": 5,
        "description": "Prevents MIME-type sniffing",
        "fix": "X-Content-Type-Options: nosniff",
        "check": lambda v: v.lower().strip() == "nosniff",
    },
    "X-Frame-Options": {
        "weight": 5,
        "description": "Prevents clickjacking",
        "fix": "X-Frame-Options: DENY",
        "check": lambda v: v.upper().strip() in ("DENY", "SAMEORIGIN"),
    },
    "Referrer-Policy": {
        "weight": 5,
        "description": "Controls referrer information leakage",
        "fix": "Referrer-Policy: strict-origin-when-cross-origin",
        "check": lambda v: v.strip() != "",
    },
    "Permissions-Policy": {
        "weight": 5,
        "description": "Restricts browser feature access",
        "fix": "Permissions-Policy: camera=(), microphone=(), geolocation=()",
        "check": lambda v: v.strip() != "",
    },
    "X-XSS-Protection": {
        "weight": 3,
        "description": "Legacy XSS filter (still useful for older browsers)",
        "fix": "X-XSS-Protection: 1; mode=block",
        "check": lambda v: "1" in v,
    },
    "Cross-Origin-Opener-Policy": {
        "weight": 4,
        "description": "Isolates browsing context from cross-origin documents",
        "fix": "Cross-Origin-Opener-Policy: same-origin",
        "check": lambda v: v.strip() != "",
    },
    "Cross-Origin-Resource-Policy": {
        "weight": 4,
        "description": "Prevents cross-origin reads of resources",
        "fix": "Cross-Origin-Resource-Policy: same-origin",
        "check": lambda v: v.strip() != "",
    },
    "Cross-Origin-Embedder-Policy": {
        "weight": 3,
        "description": "Prevents loading cross-origin resources without explicit opt-in",
        "fix": "Cross-Origin-Embedder-Policy: require-corp",
        "check": lambda v: v.strip() != "",
    },
}

DANGEROUS_HEADERS = [
    "Server",
    "X-Powered-By",
    "X-AspNet-Version",
    "X-AspNetMvc-Version",
]

GRN = "\033[0;32m"
YEL = "\033[1;33m"
RED = "\033[0;31m"
CYN = "\033[0;36m"
BLD = "\033[1m"
RST = "\033[0m"


def fetch_headers(url: str) -> dict:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "SecurityHeaderAudit/1.0")
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        return dict(resp.headers)


def audit(headers: dict) -> dict:
    results = {"present": [], "missing": [], "info_leak": [], "score": 0}
    max_score = sum(h["weight"] for h in SECURITY_HEADERS.values())
    earned = 0

    for name, spec in SECURITY_HEADERS.items():
        value = headers.get(name)
        if value and spec["check"](value):
            earned += spec["weight"]
            results["present"].append({"header": name, "value": value.strip(), "status": "good"})
        elif value:
            earned += spec["weight"] // 2
            results["present"].append({"header": name, "value": value.strip(), "status": "weak", "fix": spec["fix"]})
        else:
            results["missing"].append({"header": name, "description": spec["description"], "fix": spec["fix"]})

    for name in DANGEROUS_HEADERS:
        value = headers.get(name)
        if value:
            results["info_leak"].append({"header": name, "value": value.strip()})

    results["score"] = round((earned / max_score) * 100)
    return results


def grade(score: int) -> tuple[str, str]:
    if score >= 90: return "A+", GRN
    if score >= 80: return "A", GRN
    if score >= 70: return "B", YEL
    if score >= 50: return "C", YEL
    if score >= 30: return "D", RED
    return "F", RED


def print_report(url: str, results: dict):
    g, color = grade(results["score"])

    print(f"\n{CYN}{'=' * 60}{RST}")
    print(f"  {BLD}HTTP Security Header Audit{RST}")
    print(f"  Target: {url}")
    print(f"  Grade:  {color}{BLD}{g}{RST} ({results['score']}%)")
    print(f"{CYN}{'=' * 60}{RST}")

    if results["present"]:
        print(f"\n  {BLD}Present Headers:{RST}")
        for h in results["present"]:
            icon = f"{GRN}[+]{RST}" if h["status"] == "good" else f"{YEL}[~]{RST}"
            print(f"  {icon} {h['header']}: {h['value']}")
            if h["status"] == "weak":
                print(f"      {YEL}Recommended: {h['fix']}{RST}")

    if results["missing"]:
        print(f"\n  {BLD}Missing Headers:{RST}")
        for h in results["missing"]:
            print(f"  {RED}[-]{RST} {h['header']} — {h['description']}")
            print(f"      {GRN}Add: {h['fix']}{RST}")

    if results["info_leak"]:
        print(f"\n  {BLD}Information Leakage:{RST}")
        for h in results["info_leak"]:
            print(f"  {RED}[!]{RST} {h['header']}: {h['value']} — remove this header")

    print(f"\n{CYN}{'=' * 60}{RST}\n")


def main():
    parser = argparse.ArgumentParser(description="HTTP Security Header Analyzer")
    parser.add_argument("url", help="Target URL (e.g. https://example.com)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else f"https://{args.url}"

    try:
        headers = fetch_headers(url)
    except URLError as e:
        print(f"[!] Failed to connect: {e}")
        sys.exit(1)

    results = audit(headers)

    if args.json:
        print(json.dumps({"url": url, **results}, indent=2))
    else:
        print_report(url, results)


if __name__ == "__main__":
    main()
