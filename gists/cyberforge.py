#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  CYBERFORGE — Offensive & Defensive Cybersecurity Multi-Tool    ║
║  Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)       ║
║  Zero dependencies. Pure Python 3.10+ stdlib.                   ║
║  For authorized security operations only.                       ║
╚══════════════════════════════════════════════════════════════════╝

A single-file cybersecurity Swiss army knife with 10 modules:

  cyberforge.py hash     <value>             — Identify hash type & compute hashes
  cyberforge.py crack    <hash> -w wordlist   — Dictionary attack on hash
  cyberforge.py encode   <text> -t base64     — Encode text (base64/hex/url/rot13/binary/morse)
  cyberforge.py decode   <text> -t base64     — Decode text
  cyberforge.py xor      <text> -k KEY        — XOR encrypt/decrypt
  cyberforge.py password <password>           — Audit password strength & entropy
  cyberforge.py forensic <file>               — File forensics (magic bytes, hashes, entropy, strings)
  cyberforge.py logaudit <logfile>            — Analyze auth/syslog for attacks
  cyberforge.py monitor  <dir>               — File integrity monitor (baseline & check)
  cyberforge.py network                      — Local network recon & open connections
"""

from __future__ import annotations

import argparse
import base64
import collections
import hashlib
import math
import os
import re
import socket
import string
import struct
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
#  TERMINAL UI
# ═══════════════════════════════════════════════════════════════

class C:
    R  = "\033[0;31m"
    G  = "\033[0;32m"
    Y  = "\033[1;33m"
    B  = "\033[0;34m"
    M  = "\033[0;35m"
    CN = "\033[0;36m"
    W  = "\033[1;37m"
    D  = "\033[0;90m"
    BD = "\033[1m"
    X  = "\033[0m"


def banner():
    print(f"""
{C.CN}╔══════════════════════════════════════════════════════════════╗
║{C.X}  {C.W} ██████╗██╗   ██╗██████╗ ███████╗██████╗{C.X}                  ║
║{C.X}  {C.W}██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗{C.X}                 ║
║{C.X}  {C.R}██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝{C.X}                 ║
║{C.X}  {C.R}██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗{C.X}                 ║
║{C.X}  {C.Y}╚██████╗   ██║   ██████╔╝███████╗██║  ██║{C.X}                  ║
║{C.X}  {C.Y} ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝{C.X}                 ║
║{C.X}  {C.CN}████████████████████{C.R}  FORGE{C.X}  {C.D}v1.0{C.X}                      ║
{C.CN}╠══════════════════════════════════════════════════════════════╣
║{C.X}  {C.D}Cybersecurity Multi-Tool — Zero Dependencies{C.X}               ║
║{C.X}  {C.D}Author: @geevarghesekthomas84-sys{C.X}                          ║
{C.CN}╚══════════════════════════════════════════════════════════════╝{C.X}
""")


def sec(title: str):
    line = "─" * (56 - len(title))
    print(f"\n{C.CN}┌─[ {C.W}{title} {C.CN}]{line}┐{C.X}")

def sec_end():
    print(f"{C.CN}└{'─' * 60}┘{C.X}")

def ok(msg):    print(f"{C.CN}│{C.X}  {C.G}[+]{C.X} {msg}")
def warn(msg):  print(f"{C.CN}│{C.X}  {C.Y}[!]{C.X} {msg}")
def fail(msg):  print(f"{C.CN}│{C.X}  {C.R}[✗]{C.X} {msg}")
def info(msg):  print(f"{C.CN}│{C.X}  {C.CN}[*]{C.X} {msg}")
def dim(msg):   print(f"{C.CN}│{C.X}      {C.D}{msg}{C.X}")
def row(k, v):  print(f"{C.CN}│{C.X}  {C.W}{k:<16}{C.X} {v}")


# ═══════════════════════════════════════════════════════════════
#  MODULE 1: HASH IDENTIFICATION & COMPUTATION
# ═══════════════════════════════════════════════════════════════

HASH_PATTERNS = [
    (r"^[a-fA-F0-9]{32}$",          ["MD5", "NTLM"]),
    (r"^[a-fA-F0-9]{40}$",          ["SHA-1"]),
    (r"^[a-fA-F0-9]{56}$",          ["SHA-224"]),
    (r"^[a-fA-F0-9]{64}$",          ["SHA-256"]),
    (r"^[a-fA-F0-9]{96}$",          ["SHA-384"]),
    (r"^[a-fA-F0-9]{128}$",         ["SHA-512"]),
    (r"^\$2[aby]?\$\d+\$.{53}$",    ["bcrypt"]),
    (r"^\$6\$",                       ["SHA-512 Crypt (Linux)"]),
    (r"^\$5\$",                       ["SHA-256 Crypt (Linux)"]),
    (r"^\$1\$",                       ["MD5 Crypt"]),
    (r"^\$apr1\$",                    ["Apache MD5"]),
    (r"^\$argon2i",                   ["Argon2i"]),
    (r"^\$argon2id",                  ["Argon2id"]),
    (r"^[a-fA-F0-9]{16}$",          ["MySQL 3.x", "Half MD5"]),
    (r"^\*[A-F0-9]{40}$",           ["MySQL 4.1+"]),
    (r"^[a-f0-9]{32}:[a-f0-9]+$",  ["MD5 Salted"]),
    (r"^sha1\$.+\$.{40}$",          ["Django SHA-1"]),
    (r"^pbkdf2_sha256\$",            ["Django PBKDF2-SHA256"]),
]

def cmd_hash(args):
    value = args.value
    sec("HASH ANALYSIS")

    is_file = os.path.isfile(value)
    if is_file:
        info(f"File: {value}")
        with open(value, "rb") as f:
            data = f.read()
        row("MD5", hashlib.md5(data).hexdigest())
        row("SHA-1", hashlib.sha1(data).hexdigest())
        row("SHA-256", hashlib.sha256(data).hexdigest())
        row("SHA-512", hashlib.sha512(data).hexdigest())
        size = len(data)
        row("Size", f"{size:,} bytes ({size/1024:.1f} KB)")
    else:
        info(f"Input: {C.W}{value}{C.X}")
        print(f"{C.CN}│{C.X}")

        identified = []
        for pattern, names in HASH_PATTERNS:
            if re.match(pattern, value):
                identified.extend(names)

        if identified:
            ok(f"Possible types: {C.Y}{', '.join(identified)}{C.X}")
        else:
            warn("Hash type not recognized")

        print(f"{C.CN}│{C.X}")
        info("Computing hashes of input string:")
        text = value.encode()
        row("MD5", hashlib.md5(text).hexdigest())
        row("SHA-1", hashlib.sha1(text).hexdigest())
        row("SHA-256", hashlib.sha256(text).hexdigest())
        row("SHA-512", hashlib.sha512(text).hexdigest())
        row("NTLM", hashlib.new("md4", value.encode("utf-16-le")).hexdigest())

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 2: HASH CRACKING (Dictionary Attack)
# ═══════════════════════════════════════════════════════════════

def cmd_crack(args):
    target_hash = args.hash.strip().lower()
    wordlist = args.wordlist
    sec("HASH CRACKER")

    hash_len = len(target_hash)
    algos = []
    if hash_len == 32:   algos = ["md5"]
    elif hash_len == 40: algos = ["sha1"]
    elif hash_len == 64: algos = ["sha256"]
    elif hash_len == 128: algos = ["sha512"]
    else:
        fail("Cannot detect hash algorithm from length")
        sec_end()
        return

    info(f"Target: {C.R}{target_hash}{C.X}")
    info(f"Algorithms: {', '.join(algos)}")
    info(f"Wordlist: {wordlist}")

    if not os.path.isfile(wordlist):
        fail(f"Wordlist not found: {wordlist}")
        sec_end()
        return

    print(f"{C.CN}│{C.X}")
    tried = 0
    t0 = time.time()

    with open(wordlist, "r", errors="replace") as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            tried += 1

            for algo in algos:
                h = hashlib.new(algo, word.encode()).hexdigest()
                if h == target_hash:
                    elapsed = time.time() - t0
                    ok(f"{C.G}{C.BD}CRACKED!{C.X}")
                    print(f"{C.CN}│{C.X}")
                    row("Plaintext", f"{C.G}{C.BD}{word}{C.X}")
                    row("Algorithm", algo.upper())
                    row("Attempts", f"{tried:,}")
                    row("Time", f"{elapsed:.2f}s")
                    row("Speed", f"{tried/elapsed:,.0f} H/s" if elapsed > 0 else "instant")
                    sec_end()
                    return

            if tried % 100000 == 0:
                elapsed = time.time() - t0
                speed = tried / elapsed if elapsed > 0 else 0
                print(f"\r{C.CN}│{C.X}  {C.D}[*] Tried {tried:,} words ({speed:,.0f} H/s)...{C.X}", end="", flush=True)

    elapsed = time.time() - t0
    print()
    fail(f"Not cracked. Tried {tried:,} words in {elapsed:.2f}s")
    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 3: ENCODING
# ═══════════════════════════════════════════════════════════════

MORSE = {
    "A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.","H":"....",
    "I":"..","J":".---","K":"-.-","L":".-..","M":"--","N":"-.","O":"---","P":".--.",
    "Q":"--.-","R":".-.","S":"...","T":"-","U":"..-","V":"...-","W":".--","X":"-..-",
    "Y":"-.--","Z":"--..","0":"-----","1":".----","2":"..---","3":"...--","4":"....-",
    "5":".....","6":"-....","7":"--...","8":"---..","9":"----.",".":",","?":"..--..",
    " ":"/",
}
MORSE_REV = {v: k for k, v in MORSE.items()}

def encode_text(text: str, encoding: str) -> str:
    if encoding == "base64":
        return base64.b64encode(text.encode()).decode()
    elif encoding == "base32":
        return base64.b32encode(text.encode()).decode()
    elif encoding == "hex":
        return text.encode().hex()
    elif encoding == "url":
        return urllib.parse.quote(text, safe="")
    elif encoding == "rot13":
        return text.translate(str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"))
    elif encoding == "binary":
        return " ".join(f"{b:08b}" for b in text.encode())
    elif encoding == "morse":
        return " ".join(MORSE.get(c.upper(), c) for c in text)
    elif encoding == "decimal":
        return " ".join(str(b) for b in text.encode())
    elif encoding == "reverse":
        return text[::-1]
    else:
        return f"Unknown encoding: {encoding}"


def decode_text(text: str, encoding: str) -> str:
    try:
        if encoding == "base64":
            return base64.b64decode(text).decode()
        elif encoding == "base32":
            return base64.b32decode(text).decode()
        elif encoding == "hex":
            return bytes.fromhex(text.replace(" ", "")).decode()
        elif encoding == "url":
            return urllib.parse.unquote(text)
        elif encoding == "rot13":
            return encode_text(text, "rot13")
        elif encoding == "binary":
            bits = text.strip().split()
            return "".join(chr(int(b, 2)) for b in bits)
        elif encoding == "morse":
            return "".join(MORSE_REV.get(c, c) for c in text.split(" "))
        elif encoding == "decimal":
            return "".join(chr(int(n)) for n in text.split())
        elif encoding == "reverse":
            return text[::-1]
        else:
            return f"Unknown encoding: {encoding}"
    except Exception as e:
        return f"Decode error: {e}"


ENCODINGS = ["base64", "base32", "hex", "url", "rot13", "binary", "morse", "decimal", "reverse"]

def cmd_encode(args):
    sec("ENCODE")
    info(f"Input: {C.W}{args.text}{C.X}")
    info(f"Type: {C.Y}{args.type}{C.X}")
    print(f"{C.CN}│{C.X}")

    if args.type == "all":
        for enc in ENCODINGS:
            row(enc.upper(), encode_text(args.text, enc))
    else:
        result = encode_text(args.text, args.type)
        ok(f"Result: {C.G}{result}{C.X}")

    sec_end()


def cmd_decode(args):
    sec("DECODE")
    info(f"Input: {C.W}{args.text[:60]}{'...' if len(args.text)>60 else ''}{C.X}")
    info(f"Type: {C.Y}{args.type}{C.X}")
    print(f"{C.CN}│{C.X}")

    if args.type == "auto":
        info("Auto-detecting encoding...")
        print(f"{C.CN}│{C.X}")
        for enc in ENCODINGS:
            try:
                result = decode_text(args.text, enc)
                if result and not result.startswith("Decode error") and result != args.text:
                    if all(c in string.printable for c in result[:50]):
                        row(enc.upper(), result[:80])
            except Exception:
                pass
    else:
        result = decode_text(args.text, args.type)
        ok(f"Result: {C.G}{result}{C.X}")

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 4: XOR CIPHER
# ═══════════════════════════════════════════════════════════════

def cmd_xor(args):
    sec("XOR CIPHER")
    key = args.key
    text = args.text

    info(f"Input: {C.W}{text[:60]}{C.X}")
    info(f"Key: {C.Y}{key}{C.X}")
    print(f"{C.CN}│{C.X}")

    try:
        if all(c in "0123456789abcdefABCDEF " for c in text) and " " not in text and len(text) % 2 == 0:
            data = bytes.fromhex(text)
        else:
            data = text.encode()
    except ValueError:
        data = text.encode()

    result = bytes(b ^ key.encode()[i % len(key)] for i, b in enumerate(data))

    row("Hex", result.hex())
    try:
        ascii_result = result.decode(errors="replace")
        if all(c in string.printable for c in ascii_result[:50]):
            row("ASCII", ascii_result[:80])
    except Exception:
        pass
    row("Base64", base64.b64encode(result).decode())

    if args.brute:
        print(f"{C.CN}│{C.X}")
        info("Single-byte XOR brute-force:")
        for k in range(256):
            decoded = bytes(b ^ k for b in data)
            try:
                txt = decoded.decode("ascii")
                if all(c in string.printable for c in txt) and len(txt) > 3:
                    printable_ratio = sum(1 for c in txt if c in string.ascii_letters + " ") / len(txt)
                    if printable_ratio > 0.8:
                        row(f"Key 0x{k:02x}", txt[:70])
            except (UnicodeDecodeError, ZeroDivisionError):
                pass

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 5: PASSWORD STRENGTH AUDITOR
# ═══════════════════════════════════════════════════════════════

COMMON_PASSWORDS = {
    "password","123456","12345678","qwerty","abc123","monkey","1234567",
    "letmein","trustno1","dragon","baseball","iloveyou","master","sunshine",
    "ashley","michael","shadow","123123","654321","superman","qazwsx",
    "admin","welcome","login","passw0rd","hello","charlie","donald",
    "password1","password123","admin123","root","toor","guest",
}

KEYBOARD_PATTERNS = [
    "qwerty","qwertz","azerty","asdfgh","zxcvbn","1qaz2wsx","qweasd",
    "1234567890","0987654321","abcdef","zyxwvu",
]

LEET_MAP = {"@":"a","4":"a","3":"e","1":"i","!":"i","0":"o","$":"s","5":"s","7":"t","+":"t"}

def password_entropy(pw: str) -> float:
    charset = 0
    if any(c in string.ascii_lowercase for c in pw): charset += 26
    if any(c in string.ascii_uppercase for c in pw): charset += 26
    if any(c in string.digits for c in pw):          charset += 10
    if any(c in string.punctuation for c in pw):     charset += 32
    return len(pw) * math.log2(charset) if charset > 0 else 0

def cmd_password(args):
    pw = args.password
    sec("PASSWORD STRENGTH AUDIT")
    info(f"Password: {C.W}{'*' * len(pw)}{C.X} ({len(pw)} chars)")
    print(f"{C.CN}│{C.X}")

    score = 0
    findings = []

    # Length
    if len(pw) >= 16:
        score += 30; findings.append((C.G, "Excellent length (16+)"))
    elif len(pw) >= 12:
        score += 20; findings.append((C.G, "Good length (12+)"))
    elif len(pw) >= 8:
        score += 10; findings.append((C.Y, "Minimum length (8+)"))
    else:
        findings.append((C.R, f"Too short ({len(pw)} chars, need 8+)"))

    # Character classes
    has_lower = bool(re.search(r"[a-z]", pw))
    has_upper = bool(re.search(r"[A-Z]", pw))
    has_digit = bool(re.search(r"\d", pw))
    has_special = bool(re.search(r"[^a-zA-Z0-9]", pw))
    classes = sum([has_lower, has_upper, has_digit, has_special])

    if classes == 4:
        score += 25; findings.append((C.G, "All 4 character classes used"))
    elif classes == 3:
        score += 15; findings.append((C.Y, f"{classes}/4 character classes"))
    else:
        score += classes * 5; findings.append((C.R, f"Only {classes}/4 character classes"))

    # Entropy
    entropy = password_entropy(pw)
    if entropy >= 80:
        score += 25; findings.append((C.G, f"High entropy: {entropy:.1f} bits"))
    elif entropy >= 50:
        score += 15; findings.append((C.Y, f"Moderate entropy: {entropy:.1f} bits"))
    else:
        findings.append((C.R, f"Low entropy: {entropy:.1f} bits"))

    # Common password check
    pw_lower = pw.lower()
    deleet = pw_lower
    for k, v in LEET_MAP.items():
        deleet = deleet.replace(k, v)

    if pw_lower in COMMON_PASSWORDS or deleet in COMMON_PASSWORDS:
        score -= 30
        findings.append((C.R, "FOUND in common password list!"))
    else:
        score += 10
        findings.append((C.G, "Not in common password list"))

    # Keyboard patterns
    for pattern in KEYBOARD_PATTERNS:
        if pattern in pw_lower or pattern in pw_lower[::-1]:
            score -= 10
            findings.append((C.R, f"Keyboard pattern detected: '{pattern}'"))
            break

    # Repeated characters
    if re.search(r"(.)\1{2,}", pw):
        score -= 5
        findings.append((C.Y, "Repeated characters detected (3+ same char)"))

    # Sequential characters
    sequential = 0
    for i in range(len(pw) - 2):
        if ord(pw[i]) + 1 == ord(pw[i+1]) == ord(pw[i+2]) - 1:
            sequential += 1
    if sequential > 0:
        score -= 5
        findings.append((C.Y, f"Sequential characters detected ({sequential} sequence(s))"))

    # Date patterns
    if re.search(r"(19|20)\d{2}", pw) or re.search(r"\d{2}[/\-]\d{2}[/\-]\d{2,4}", pw):
        score -= 5
        findings.append((C.Y, "Date pattern detected (possible DOB)"))

    # Hash the password
    hashes = {
        "MD5": hashlib.md5(pw.encode()).hexdigest(),
        "SHA-256": hashlib.sha256(pw.encode()).hexdigest(),
        "NTLM": hashlib.new("md4", pw.encode("utf-16-le")).hexdigest(),
    }

    # Print findings
    for color, msg in findings:
        print(f"{C.CN}│{C.X}  {color}{'[+]' if color == C.G else '[!]' if color == C.Y else '[✗]'}{C.X} {msg}")

    # Crack time estimation
    print(f"{C.CN}│{C.X}")
    info("Estimated crack time:")
    speeds = [
        ("Online (10/s)", 10),
        ("Throttled (1K/s)", 1000),
        ("Fast hash (10B/s)", 10_000_000_000),
        ("Slow hash (10K/s)", 10_000),
    ]
    charset_size = sum([26 * has_lower, 26 * has_upper, 10 * has_digit, 32 * has_special]) or 1
    combinations = charset_size ** len(pw)
    for name, speed in speeds:
        seconds = combinations / (2 * speed)
        if seconds < 1:          t = "instant"
        elif seconds < 60:       t = f"{seconds:.0f} seconds"
        elif seconds < 3600:     t = f"{seconds/60:.0f} minutes"
        elif seconds < 86400:    t = f"{seconds/3600:.0f} hours"
        elif seconds < 2592000:  t = f"{seconds/86400:.0f} days"
        elif seconds < 31536000: t = f"{seconds/2592000:.0f} months"
        else:
            years = seconds / 31536000
            if years > 1e15:     t = "heat death of universe"
            elif years > 1e9:    t = f"{years/1e9:.0f} billion years"
            elif years > 1e6:    t = f"{years/1e6:.0f} million years"
            else:                t = f"{years:,.0f} years"
        dim(f"{name:<24} {t}")

    # Overall score
    score = max(0, min(100, score))
    if score >= 80:   grade, color = "STRONG", C.G
    elif score >= 60: grade, color = "MODERATE", C.Y
    elif score >= 40: grade, color = "WEAK", C.Y
    else:             grade, color = "CRITICAL", C.R

    bar_len = 30
    filled = int(bar_len * score / 100)
    bar = f"{color}{'█' * filled}{C.D}{'░' * (bar_len - filled)}{C.X}"

    print(f"{C.CN}│{C.X}")
    print(f"{C.CN}│{C.X}  {bar} {color}{C.BD}{score}% {grade}{C.X}")

    print(f"{C.CN}│{C.X}")
    info("Password hashes:")
    for algo, h in hashes.items():
        row(algo, h)

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 6: FILE FORENSICS
# ═══════════════════════════════════════════════════════════════

MAGIC_BYTES = [
    (b"\x89PNG\r\n\x1a\n",          "PNG Image"),
    (b"\xff\xd8\xff",                "JPEG Image"),
    (b"GIF87a",                      "GIF87a Image"),
    (b"GIF89a",                      "GIF89a Image"),
    (b"%PDF",                        "PDF Document"),
    (b"PK\x03\x04",                  "ZIP Archive (or DOCX/XLSX/APK/JAR)"),
    (b"\x1f\x8b",                    "GZIP Archive"),
    (b"BZ",                          "BZIP2 Archive"),
    (b"\xfd7zXZ\x00",               "XZ Archive"),
    (b"7z\xbc\xaf\x27\x1c",         "7-Zip Archive"),
    (b"Rar!\x1a\x07",               "RAR Archive"),
    (b"\x7fELF",                     "ELF Executable (Linux)"),
    (b"MZ",                          "PE Executable (Windows EXE/DLL)"),
    (b"\xfe\xed\xfa",               "Mach-O Binary (macOS)"),
    (b"\xcf\xfa\xed\xfe",           "Mach-O Binary 64-bit (macOS)"),
    (b"\xca\xfe\xba\xbe",           "Java Class / Mach-O Universal"),
    (b"dex\n",                       "Android DEX (Dalvik)"),
    (b"SQLite format 3",            "SQLite Database"),
    (b"\x00\x00\x01\x00",           "ICO Icon"),
    (b"RIFF",                        "RIFF (AVI/WAV/WebP)"),
    (b"OggS",                        "OGG Audio/Video"),
    (b"fLaC",                        "FLAC Audio"),
    (b"ID3",                         "MP3 Audio (ID3)"),
    (b"\x00\x00\x00\x1cftyp",       "MP4/M4A Video"),
    (b"\x1a\x45\xdf\xa3",           "MKV/WebM Video"),
    (b"<!DOCTYPE",                   "HTML Document"),
    (b"<?xml",                       "XML Document"),
    (b"#!/",                         "Script (shebang)"),
]

def file_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = collections.Counter(data)
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())

def extract_strings(data: bytes, min_len: int = 6) -> list[str]:
    pattern = re.compile(rb"[\x20-\x7e]{%d,}" % min_len)
    return [m.decode() for m in pattern.findall(data)]

def cmd_forensic(args):
    filepath = args.file
    sec("FILE FORENSICS")

    if not os.path.isfile(filepath):
        fail(f"File not found: {filepath}")
        sec_end()
        return

    stat = os.stat(filepath)
    with open(filepath, "rb") as f:
        data = f.read()

    row("File", filepath)
    row("Size", f"{stat.st_size:,} bytes ({stat.st_size/1024:.1f} KB)")
    row("Modified", datetime.fromtimestamp(stat.st_mtime).isoformat())
    row("Permissions", oct(stat.st_mode)[-3:])
    print(f"{C.CN}│{C.X}")

    # Magic bytes
    file_type = "Unknown"
    for magic, name in MAGIC_BYTES:
        if data[:len(magic)] == magic:
            file_type = name
            break
    row("File Type", f"{C.Y}{file_type}{C.X}")
    row("Magic Bytes", " ".join(f"{b:02x}" for b in data[:16]))

    print(f"{C.CN}│{C.X}")

    # Hashes
    info("File hashes:")
    row("MD5", hashlib.md5(data).hexdigest())
    row("SHA-1", hashlib.sha1(data).hexdigest())
    row("SHA-256", hashlib.sha256(data).hexdigest())

    print(f"{C.CN}│{C.X}")

    # Entropy
    ent = file_entropy(data)
    ent_bar_len = 30
    ent_filled = int(ent_bar_len * ent / 8.0)
    if ent > 7.5:
        ent_color, ent_verdict = C.R, "HIGH — likely encrypted/compressed/packed"
    elif ent > 6.0:
        ent_color, ent_verdict = C.Y, "MODERATE — possibly compressed"
    else:
        ent_color, ent_verdict = C.G, "LOW — plaintext/structured data"

    ent_bar = f"{ent_color}{'█' * ent_filled}{C.D}{'░' * (ent_bar_len - ent_filled)}{C.X}"
    info(f"Entropy: {ent_bar} {ent_color}{ent:.4f} / 8.0{C.X}")
    dim(ent_verdict)

    # Strings
    strings = extract_strings(data)
    if strings:
        print(f"{C.CN}│{C.X}")
        info(f"Interesting strings ({len(strings)} total, showing top 20):")

        interesting_patterns = [
            (r"https?://\S+", "URL"),
            (r"[\w.+-]+@[\w-]+\.[\w.-]+", "Email"),
            (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP Address"),
            (r"(?i)(password|passwd|secret|key|token|api.?key|credential)", "Sensitive Keyword"),
            (r"(?i)(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE)\s", "SQL"),
            (r"/etc/(?:passwd|shadow|hosts)", "System Path"),
            (r"(?i)(admin|root|sudo|chmod|chown)", "Admin Keyword"),
        ]

        shown = set()
        for s in strings[:200]:
            for pattern, category in interesting_patterns:
                if re.search(pattern, s) and s not in shown:
                    dim(f"{C.Y}[{category}]{C.X} {s[:80]}")
                    shown.add(s)
                    if len(shown) >= 20:
                        break
            if len(shown) >= 20:
                break

        if not shown:
            for s in strings[:15]:
                dim(s[:80])

    # PE analysis
    if data[:2] == b"MZ" and len(data) > 64:
        print(f"{C.CN}│{C.X}")
        info("PE Analysis:")
        try:
            pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
            if data[pe_offset:pe_offset+4] == b"PE\x00\x00":
                machine = struct.unpack_from("<H", data, pe_offset + 4)[0]
                machines = {0x14c: "x86 (32-bit)", 0x8664: "x64 (64-bit)", 0xAA64: "ARM64"}
                row("Architecture", machines.get(machine, f"Unknown (0x{machine:04x})"))

                num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
                row("Sections", str(num_sections))

                timestamp = struct.unpack_from("<I", data, pe_offset + 8)[0]
                if timestamp > 0:
                    row("Compile Time", datetime.utcfromtimestamp(timestamp).isoformat() + "Z")

                chars = struct.unpack_from("<H", data, pe_offset + 22)[0]
                is_dll = bool(chars & 0x2000)
                row("Type", "DLL" if is_dll else "EXE")
        except Exception:
            dim("PE header parsing failed")

    # ELF analysis
    if data[:4] == b"\x7fELF" and len(data) > 20:
        print(f"{C.CN}│{C.X}")
        info("ELF Analysis:")
        bit_class = {1: "32-bit", 2: "64-bit"}.get(data[4], "Unknown")
        endian = {1: "Little-endian", 2: "Big-endian"}.get(data[5], "Unknown")
        elf_type = {2: "Executable", 3: "Shared Object (.so)", 4: "Core Dump"}.get(
            struct.unpack_from("<H", data, 16)[0], "Unknown")
        row("Class", bit_class)
        row("Endianness", endian)
        row("Type", elf_type)

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 7: LOG AUDIT
# ═══════════════════════════════════════════════════════════════

def cmd_logaudit(args):
    logfile = args.logfile
    sec("LOG SECURITY AUDIT")

    if not os.path.isfile(logfile):
        fail(f"File not found: {logfile}")
        sec_end()
        return

    info(f"Analyzing: {logfile}")

    with open(logfile, errors="replace") as f:
        lines = f.readlines()

    info(f"Total lines: {len(lines):,}")
    print(f"{C.CN}│{C.X}")

    failed_logins: dict[str, int] = collections.defaultdict(int)
    successful_logins: dict[str, int] = collections.defaultdict(int)
    sudo_events: list[str] = []
    ssh_brute: dict[str, int] = collections.defaultdict(int)
    suspicious_cmds: list[str] = []
    root_logins: list[str] = []
    port_changes: list[str] = []

    for line in lines:
        lower = line.lower()

        # SSH failed logins
        m = re.search(r"failed (?:password|publickey) for (?:invalid user )?(\S+) from (\S+)", lower)
        if m:
            user, ip = m.group(1), m.group(2)
            failed_logins[ip] += 1
            ssh_brute[ip] += 1
            continue

        # Successful logins
        m = re.search(r"accepted (?:password|publickey) for (\S+) from (\S+)", lower)
        if m:
            user, ip = m.group(1), m.group(2)
            successful_logins[ip] += 1
            if user == "root":
                root_logins.append(line.strip()[:120])
            continue

        # Sudo events
        if "sudo:" in lower and ("command=" in lower or "authentication failure" in lower):
            sudo_events.append(line.strip()[:120])

        # Suspicious commands
        for pattern in [r"(rm\s+-rf\s+/)", r"(chmod\s+777)", r"(wget|curl).*\|.*sh",
                        r"(nc|ncat|netcat)\s+-[el]", r"(python|perl|ruby|php).*-c.*socket",
                        r"/dev/(tcp|udp)/", r"base64\s+-d", r"(iptables|ufw).*disable"]:
            if re.search(pattern, lower):
                suspicious_cmds.append(line.strip()[:120])
                break

    # Report
    if failed_logins:
        warn(f"{C.R}Failed login attempts:{C.X}")
        for ip, count in sorted(failed_logins.items(), key=lambda x: -x[1])[:15]:
            severity = C.R if count >= 10 else C.Y if count >= 5 else C.D
            brute = f"  {C.R}⚠ BRUTE FORCE{C.X}" if count >= 10 else ""
            dim(f"{severity}{ip:<20} {count:>5} attempts{C.X}{brute}")
        print(f"{C.CN}│{C.X}")

    if successful_logins:
        ok(f"Successful logins:")
        for ip, count in sorted(successful_logins.items(), key=lambda x: -x[1])[:10]:
            dim(f"{ip:<20} {count:>5} sessions")
        print(f"{C.CN}│{C.X}")

    if root_logins:
        fail(f"{C.R}Root logins detected ({len(root_logins)}):{C.X}")
        for entry in root_logins[:5]:
            dim(entry)
        print(f"{C.CN}│{C.X}")

    if sudo_events:
        warn(f"Sudo events ({len(sudo_events)}):")
        for entry in sudo_events[:10]:
            dim(entry)
        print(f"{C.CN}│{C.X}")

    if suspicious_cmds:
        fail(f"{C.R}Suspicious commands ({len(suspicious_cmds)}):{C.X}")
        for entry in suspicious_cmds[:10]:
            dim(f"{C.R}{entry}{C.X}")
        print(f"{C.CN}│{C.X}")

    # Summary
    brute_force_ips = [ip for ip, c in ssh_brute.items() if c >= 10]
    total_failed = sum(failed_logins.values())
    total_success = sum(successful_logins.values())

    print(f"{C.CN}│{C.X}")
    info(f"Summary:")
    row("Failed logins", f"{total_failed:,}")
    row("Successful", f"{total_success:,}")
    row("Brute force IPs", f"{C.R}{len(brute_force_ips)}{C.X}" if brute_force_ips else "0")
    row("Root logins", f"{C.R}{len(root_logins)}{C.X}" if root_logins else "0")
    row("Sudo events", str(len(sudo_events)))
    row("Suspicious cmds", f"{C.R}{len(suspicious_cmds)}{C.X}" if suspicious_cmds else "0")

    threat = "CRITICAL" if brute_force_ips or suspicious_cmds else "ELEVATED" if total_failed > 50 else "LOW"
    threat_color = C.R if threat == "CRITICAL" else C.Y if threat == "ELEVATED" else C.G
    row("Threat Level", f"{threat_color}{C.BD}{threat}{C.X}")

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 8: FILE INTEGRITY MONITOR
# ═══════════════════════════════════════════════════════════════

def cmd_monitor(args):
    target_dir = args.dir
    baseline_file = args.baseline or os.path.join(target_dir, ".integrity_baseline.json")

    sec("FILE INTEGRITY MONITOR")
    info(f"Directory: {target_dir}")
    info(f"Baseline: {baseline_file}")
    print(f"{C.CN}│{C.X}")

    current = {}
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname == ".integrity_baseline.json":
                continue
            fpath = os.path.join(root, fname)
            try:
                stat = os.stat(fpath)
                with open(fpath, "rb") as f:
                    h = hashlib.sha256(f.read()).hexdigest()
                rel = os.path.relpath(fpath, target_dir)
                current[rel] = {
                    "hash": h,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "perms": oct(stat.st_mode)[-3:],
                }
            except (PermissionError, OSError):
                pass

    if not os.path.exists(baseline_file):
        with open(baseline_file, "w") as f:
            json.dump({"created": datetime.now().isoformat(), "files": current}, f, indent=2)
        ok(f"Baseline created with {C.W}{len(current)}{C.X} files")
        info("Run again to check for changes")
    else:
        with open(baseline_file) as f:
            baseline = json.load(f)
        prev = baseline.get("files", {})

        added = set(current) - set(prev)
        removed = set(prev) - set(current)
        modified = []
        perm_changed = []

        for fname in set(current) & set(prev):
            if current[fname]["hash"] != prev[fname]["hash"]:
                modified.append(fname)
            elif current[fname].get("perms") != prev[fname].get("perms"):
                perm_changed.append(fname)

        if added:
            warn(f"{C.Y}New files ({len(added)}):{C.X}")
            for f in sorted(added)[:20]:
                dim(f"{C.Y}+ {f}{C.X}")
            print(f"{C.CN}│{C.X}")

        if removed:
            fail(f"{C.R}Deleted files ({len(removed)}):{C.X}")
            for f in sorted(removed)[:20]:
                dim(f"{C.R}- {f}{C.X}")
            print(f"{C.CN}│{C.X}")

        if modified:
            fail(f"{C.R}Modified files ({len(modified)}):{C.X}")
            for f in sorted(modified)[:20]:
                dim(f"{C.R}~ {f}{C.X}")
                dim(f"  was: {prev[f]['hash'][:16]}...")
                dim(f"  now: {current[f]['hash'][:16]}...")
            print(f"{C.CN}│{C.X}")

        if perm_changed:
            warn(f"Permission changes ({len(perm_changed)}):")
            for f in sorted(perm_changed)[:10]:
                dim(f"  {f}: {prev[f].get('perms','')} → {current[f].get('perms','')}")
            print(f"{C.CN}│{C.X}")

        if not (added or removed or modified or perm_changed):
            ok(f"{C.G}No changes detected. All {len(current)} files intact.{C.X}")
        else:
            total_changes = len(added) + len(removed) + len(modified) + len(perm_changed)
            status = "COMPROMISED" if modified or removed else "CHANGED"
            color = C.R if modified or removed else C.Y
            row("Changes", f"{color}{C.BD}{total_changes} ({status}){C.X}")

        if args.update:
            with open(baseline_file, "w") as f:
                json.dump({"created": datetime.now().isoformat(), "files": current}, f, indent=2)
            ok("Baseline updated")

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MODULE 9: NETWORK RECON
# ═══════════════════════════════════════════════════════════════

def cmd_network(args):
    sec("LOCAL NETWORK RECON")

    info("Hostname & IPs:")
    hostname = socket.gethostname()
    row("Hostname", hostname)
    try:
        local_ip = socket.gethostbyname(hostname)
        row("Local IP", local_ip)
    except socket.gaierror:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        row("Outbound IP", s.getsockname()[0])
        s.close()
    except Exception:
        pass

    print(f"{C.CN}│{C.X}")

    # Network interfaces
    info("Network interfaces:")
    try:
        result = subprocess.run(
            ["ip", "-br", "addr"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                dim(line)
        print(f"{C.CN}│{C.X}")
    except Exception:
        pass

    # Listening ports
    info("Listening ports:")
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[:20]:
                dim(line)
        print(f"{C.CN}│{C.X}")
    except Exception:
        pass

    # Established connections
    info("Established connections:")
    try:
        result = subprocess.run(
            ["ss", "-tnp", "state", "established"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[:15]:
                dim(line)
        print(f"{C.CN}│{C.X}")
    except Exception:
        pass

    # ARP table
    info("ARP neighbors:")
    try:
        result = subprocess.run(
            ["ip", "neigh"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n")[:15]:
                dim(line)
        print(f"{C.CN}│{C.X}")
    except Exception:
        pass

    # DNS resolver
    info("DNS resolvers:")
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.strip().startswith("nameserver"):
                    dim(line.strip())
    except Exception:
        pass

    sec_end()


# ═══════════════════════════════════════════════════════════════
#  MAIN CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="CYBERFORGE — Cybersecurity Multi-Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
modules:
  hash       Identify hash type & compute hashes for a string or file
  crack      Dictionary attack on a hash
  encode     Encode text (base64/hex/url/rot13/binary/morse/all)
  decode     Decode text (auto-detect or specify type)
  xor        XOR encrypt/decrypt with key (--brute for single-byte brute-force)
  password   Audit password strength, entropy & crack time
  forensic   File forensics — magic bytes, hashes, entropy, strings, PE/ELF
  logaudit   Analyze auth/syslog for brute force, root logins, suspicious cmds
  monitor    File integrity monitor — baseline, check for changes
  network    Local network recon — interfaces, ports, connections, ARP
        """,
    )
    sub = parser.add_subparsers(dest="module")

    p = sub.add_parser("hash", help="Hash identification & computation")
    p.add_argument("value", help="Hash string or file path")

    p = sub.add_parser("crack", help="Dictionary hash cracker")
    p.add_argument("hash", help="Target hash")
    p.add_argument("-w", "--wordlist", required=True, help="Wordlist file")

    p = sub.add_parser("encode", help="Encode text")
    p.add_argument("text", help="Text to encode")
    p.add_argument("-t", "--type", default="all", choices=ENCODINGS + ["all"], help="Encoding type")

    p = sub.add_parser("decode", help="Decode text")
    p.add_argument("text", help="Text to decode")
    p.add_argument("-t", "--type", default="auto", choices=ENCODINGS + ["auto"], help="Encoding type")

    p = sub.add_parser("xor", help="XOR cipher")
    p.add_argument("text", help="Text or hex to XOR")
    p.add_argument("-k", "--key", required=True, help="XOR key")
    p.add_argument("--brute", action="store_true", help="Single-byte brute-force")

    p = sub.add_parser("password", help="Password strength auditor")
    p.add_argument("password", help="Password to audit")

    p = sub.add_parser("forensic", help="File forensics analyzer")
    p.add_argument("file", help="File to analyze")

    p = sub.add_parser("logaudit", help="Log file security audit")
    p.add_argument("logfile", help="Log file to analyze")

    p = sub.add_parser("monitor", help="File integrity monitor")
    p.add_argument("dir", help="Directory to monitor")
    p.add_argument("--baseline", "-b", help="Baseline file path")
    p.add_argument("--update", "-u", action="store_true", help="Update baseline after check")

    p = sub.add_parser("network", help="Local network recon")

    args = parser.parse_args()

    if not args.module:
        banner()
        parser.print_help()
        print()
        sys.exit(0)

    banner()

    dispatch = {
        "hash": cmd_hash,
        "crack": cmd_crack,
        "encode": cmd_encode,
        "decode": cmd_decode,
        "xor": cmd_xor,
        "password": cmd_password,
        "forensic": cmd_forensic,
        "logaudit": cmd_logaudit,
        "monitor": cmd_monitor,
        "network": cmd_network,
    }

    dispatch[args.module](args)
    print()


if __name__ == "__main__":
    main()
