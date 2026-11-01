#!/usr/bin/env python3
"""
jwt_analyzer.py — JWT Token Decoder, Analyzer & Security Auditor
Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)

Decodes JWT tokens without external dependencies, checks for common
security misconfigurations, and highlights potential attack vectors.

Usage:
    python3 jwt_analyzer.py <token>
    echo "eyJ..." | python3 jwt_analyzer.py -

No external dependencies required — stdlib only.
"""

import base64
import json
import sys
import time
from datetime import datetime, timezone


def b64_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)


def decode_jwt(token: str) -> tuple[dict, dict, str]:
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWT: expected 3 parts, got {len(parts)}")
    header = json.loads(b64_decode(parts[0]))
    payload = json.loads(b64_decode(parts[1]))
    signature = parts[2]
    return header, payload, signature


def check_time_claims(payload: dict) -> list[str]:
    findings = []
    now = time.time()

    if "exp" in payload:
        exp = payload["exp"]
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        if exp < now:
            findings.append(f"  [!] EXPIRED at {exp_dt.isoformat()} ({int(now - exp)}s ago)")
        else:
            findings.append(f"  [*] Expires: {exp_dt.isoformat()} (in {int(exp - now)}s)")

        if "iat" in payload:
            lifetime = exp - payload["iat"]
            if lifetime > 86400 * 30:
                findings.append(f"  [!] LONG LIFETIME: {lifetime / 86400:.1f} days")
    else:
        findings.append("  [!] NO EXPIRATION CLAIM (exp) — token never expires")

    if "nbf" in payload:
        nbf = payload["nbf"]
        if nbf > now:
            findings.append(f"  [!] NOT YET VALID (nbf is in the future)")

    if "iat" in payload:
        iat_dt = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        findings.append(f"  [*] Issued: {iat_dt.isoformat()}")

    return findings


def security_audit(header: dict, payload: dict, signature: str) -> list[str]:
    findings = []

    alg = header.get("alg", "").upper()
    if alg == "NONE":
        findings.append("  [!!] CRITICAL: Algorithm is 'none' — signature not verified!")
    elif alg in ("HS256", "HS384", "HS512"):
        findings.append(f"  [!] Symmetric algorithm ({alg}) — shared secret; brute-forceable")
    elif alg.startswith("RS") or alg.startswith("ES") or alg.startswith("PS"):
        findings.append(f"  [+] Asymmetric algorithm ({alg})")
    else:
        findings.append(f"  [?] Unknown algorithm: {alg}")

    if "jku" in header:
        findings.append(f"  [!] JKU header present: {header['jku']} — SSRF / key injection risk")
    if "x5u" in header:
        findings.append(f"  [!] X5U header present: {header['x5u']} — certificate injection risk")
    if "kid" in header:
        findings.append(f"  [*] KID: {header['kid']} — check for SQL injection in kid lookup")

    if signature == "" or all(c == "A" for c in signature):
        findings.append("  [!!] CRITICAL: Empty or null signature detected!")

    sensitive_keys = {"password", "passwd", "secret", "credit_card", "ssn", "api_key", "token"}
    found = sensitive_keys & set(k.lower() for k in payload.keys())
    if found:
        findings.append(f"  [!] Sensitive data in payload: {', '.join(found)}")

    role_fields = {k: v for k, v in payload.items() if k.lower() in ("role", "roles", "is_admin", "admin", "group", "groups", "scope", "permissions")}
    if role_fields:
        findings.append(f"  [*] Authorization claims: {json.dumps(role_fields)}")

    return findings


def pretty_json(obj: dict) -> str:
    return json.dumps(obj, indent=2, default=str)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 jwt_analyzer.py <token>")
        print("       echo 'eyJ...' | python3 jwt_analyzer.py -")
        sys.exit(1)

    token = sys.stdin.read().strip() if sys.argv[1] == "-" else sys.argv[1]

    try:
        header, payload, signature = decode_jwt(token)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[!] Failed to decode JWT: {e}")
        sys.exit(1)

    print(f"\n{'=' * 58}")
    print("  JWT TOKEN ANALYSIS")
    print(f"{'=' * 58}")

    print(f"\n  HEADER:")
    for line in pretty_json(header).split("\n"):
        print(f"    {line}")

    print(f"\n  PAYLOAD:")
    for line in pretty_json(payload).split("\n"):
        print(f"    {line}")

    print(f"\n  SIGNATURE:")
    print(f"    {signature[:60]}{'...' if len(signature) > 60 else ''}")

    print(f"\n{'─' * 58}")
    print("  TIME ANALYSIS")
    print(f"{'─' * 58}")
    for finding in check_time_claims(payload):
        print(finding)

    print(f"\n{'─' * 58}")
    print("  SECURITY AUDIT")
    print(f"{'─' * 58}")
    for finding in security_audit(header, payload, signature):
        print(finding)

    print(f"\n{'=' * 58}\n")


if __name__ == "__main__":
    main()
