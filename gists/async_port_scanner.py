#!/usr/bin/env python3
"""
async_port_scanner.py — Fast Async Port Scanner with Banner Grabbing
Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)

Usage:
    python3 async_port_scanner.py <target> [--ports 1-1024] [--timeout 2] [--workers 500]

For authorized penetration testing and security assessments only.
"""

import asyncio
import argparse
import socket
import sys
from datetime import datetime

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 111: "RPCbind", 135: "MSRPC", 139: "NetBIOS",
    143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
    1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 6379: "Redis", 8080: "HTTP-Proxy",
    8443: "HTTPS-Alt", 9200: "Elasticsearch", 27017: "MongoDB",
}


async def grab_banner(reader, writer, timeout):
    try:
        writer.write(b"\r\n")
        await writer.drain()
        banner = await asyncio.wait_for(reader.read(1024), timeout=timeout)
        return banner.decode(errors="replace").strip()[:120]
    except (asyncio.TimeoutError, ConnectionError, OSError):
        return ""


async def scan_port(sem, target, port, timeout, results):
    async with sem:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target, port), timeout=timeout
            )
            banner = await grab_banner(reader, writer, timeout)
            writer.close()
            await writer.wait_closed()

            service = COMMON_PORTS.get(port, "unknown")
            results.append((port, service, banner))
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            pass


def parse_ports(port_str):
    ports = set()
    for part in port_str.split(","):
        if "-" in part:
            start, end = map(int, part.split("-", 1))
            ports.update(range(start, end + 1))
        else:
            ports.add(int(part))
    return sorted(p for p in ports if 1 <= p <= 65535)


async def main():
    parser = argparse.ArgumentParser(description="Async Port Scanner with Banner Grabbing")
    parser.add_argument("target", help="Target IP or hostname")
    parser.add_argument("--ports", "-p", default="1-1024", help="Port range (default: 1-1024)")
    parser.add_argument("--timeout", "-t", type=float, default=2.0, help="Timeout per port (s)")
    parser.add_argument("--workers", "-w", type=int, default=500, help="Max concurrent connections")
    args = parser.parse_args()

    try:
        target_ip = socket.gethostbyname(args.target)
    except socket.gaierror:
        print(f"[!] Cannot resolve: {args.target}")
        sys.exit(1)

    ports = parse_ports(args.ports)
    sem = asyncio.Semaphore(args.workers)
    results = []

    print(f"\n{'=' * 62}")
    print(f"  Target   : {args.target} ({target_ip})")
    print(f"  Ports    : {len(ports)} ports")
    print(f"  Workers  : {args.workers}")
    print(f"  Started  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 62}\n")

    tasks = [scan_port(sem, target_ip, p, args.timeout, results) for p in ports]
    await asyncio.gather(*tasks)

    results.sort(key=lambda r: r[0])

    if results:
        print(f"  {'PORT':<10} {'SERVICE':<18} {'BANNER'}")
        print(f"  {'─' * 10} {'─' * 18} {'─' * 30}")
        for port, service, banner in results:
            banner_display = banner if banner else "—"
            print(f"  {port:<10} {service:<18} {banner_display}")
        print(f"\n  [+] {len(results)} open ports found.\n")
    else:
        print("  [-] No open ports found.\n")


if __name__ == "__main__":
    asyncio.run(main())
