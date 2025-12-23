#!/usr/bin/env python3
"""
Tsukuyomi v2 - Telemetry-first honey endpoint (bounded + safe)

Purpose:
- Detect and profile automated scanners/crawlers that ignore robots/noindex and follow hidden/internal links.
- Provide actionable telemetry (not infinite traps).

Notes:
- Keep this on a separate vhost/path (e.g., /_honey/) away from real app routes.
- Respect privacy and local laws: log minimization, retention policy, and notice if required.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

from flask import Flask, request, make_response, g

# ----------------------------
# Configuration
# ----------------------------

APP_NAME = "Tsukuyomi v2"
DB_PATH = os.environ.get("TSUKUYOMI_DB", "tsukuyomi_telemetry.sqlite3")
SECRET_KEY = os.environ.get("TSUKUYOMI_SECRET", None)

# Hard limits (bounded behavior)
MAX_DEPTH = int(os.environ.get("TSUKUYOMI_MAX_DEPTH", "12"))
LINKS_PER_PAGE = int(os.environ.get("TSUKUYOMI_LINKS_PER_PAGE", "6"))
MAX_PAGES_PER_CLIENT_PER_HOUR = int(os.environ.get("TSUKUYOMI_MAX_PAGES_PER_HOUR", "120"))

# Rate limiting (token bucket per client)
RATE_LIMIT_RPS = float(os.environ.get("TSUKUYOMI_RL_RPS", "2.0"))        # average
RATE_LIMIT_BURST = int(os.environ.get("TSUKUYOMI_RL_BURST", "10"))       # burst capacity

# Response behavior
ADD_ARTIFICIAL_DELAY_FOR_HIGH_SCORE = True
MAX_DELAY_SECONDS = 1.5

# If not set, generate an ephemeral secret (NOT recommended for production)
if not SECRET_KEY:
    SECRET_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")

SECRET_BYTES = SECRET_KEY.encode("utf-8")

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


# ----------------------------
# Minimal in-memory rate limiting
# (Use Redis for multi-worker deployments)
# ----------------------------

@dataclass
class Bucket:
    tokens: float
    last: float


_buckets: Dict[str, Bucket] = {}


def client_key() -> str:
    """
    Best-effort client key. If you are behind a trusted reverse proxy,
    configure Flask/werkzeug ProxyFix and rely on X-Forwarded-For safely.
    """
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "0.0.0.0")
    # Use first IP in XFF if present
    ip = ip.split(",")[0].strip()
    ua = request.headers.get("User-Agent", "")
    # Hash UA to avoid logging raw UA in rate limiter key
    ua_hash = hashlib.sha256(ua.encode("utf-8", "ignore")).hexdigest()[:12]
    return f"{ip}:{ua_hash}"


def allow_request(key: str) -> bool:
    now = time.time()
    b = _buckets.get(key)
    if b is None:
        _buckets[key] = Bucket(tokens=float(RATE_LIMIT_BURST - 1), last=now)
        return True

    # Refill
    elapsed = now - b.last
    b.last = now
    b.tokens = min(float(RATE_LIMIT_BURST), b.tokens + elapsed * RATE_LIMIT_RPS)

    if b.tokens >= 1.0:
        b.tokens -= 1.0
        return True
    return False


# ----------------------------
# SQLite telemetry store
# ----------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS hits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    client_ip TEXT,
    client_key TEXT,
    method TEXT,
    path TEXT,
    query TEXT,
    referer TEXT,
    user_agent TEXT,
    accept TEXT,
    accept_lang TEXT,
    accept_enc TEXT,
    connection TEXT,
    sec_ch_ua TEXT,
    sec_ch_platform TEXT,
    sec_fetch_site TEXT,
    sec_fetch_mode TEXT,
    sec_fetch_dest TEXT,
    cookies_present INTEGER,
    depth INTEGER,
    score INTEGER,
    chain TEXT,
    latency_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_hits_ts ON hits(ts);
CREATE INDEX IF NOT EXISTS idx_hits_client_key ON hits(client_key);
CREATE INDEX IF NOT EXISTS idx_hits_path ON hits(path);
"""


def db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.executescript(SCHEMA)
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def insert_hit(row: dict) -> None:
    conn = db()
    cols = ", ".join(row.keys())
    qs = ", ".join(["?"] * len(row))
    conn.execute(f"INSERT INTO hits ({cols}) VALUES ({qs})", list(row.values()))
    conn.commit()


# ----------------------------
# Tokenized link generation (HMAC)
# ----------------------------

def sign(payload: str) -> str:
    mac = hmac.new(SECRET_BYTES, payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode("ascii").rstrip("=")


def make_token(seed: str, depth: int, idx: int, chain: str) -> str:
    """
    Token encodes minimal state to support bounded traversal without server-side sessions.
    """
    payload = json.dumps(
        {"s": seed, "d": depth, "i": idx, "c": chain},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    sig = sign(payload)
    blob = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
    return f"{blob}.{sig}"


def parse_token(token: str) -> Optional[dict]:
    try:
        blob, sig = token.split(".", 1)
        padded = blob + "=" * (-len(blob) % 4)
        payload = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
        if not hmac.compare_digest(sign(payload), sig):
            return None
        obj = json.loads(payload)
        # Minimal validation
        if not isinstance(obj, dict):
            return None
        if not isinstance(obj.get("s"), str):
            return None
        if not isinstance(obj.get("d"), int):
            return None
        if not isinstance(obj.get("i"), int):
            return None
        if not isinstance(obj.get("c"), str):
            return None
        return obj
    except Exception:
        return None


# ----------------------------
# Bot scoring (simple + explainable)
# ----------------------------

def bot_score() -> int:
    score = 0

    ua = request.headers.get("User-Agent", "")
    accept = request.headers.get("Accept", "")
    al = request.headers.get("Accept-Language", "")

    # Very common in scanners / scripts
    scanner_markers = [
        "nikto", "sqlmap", "acunetix", "nessus", "qualys", "openvas", "wpscan",
        "masscan", "nmap", "zaproxy", "burp", "curl", "python-requests", "go-http-client",
        "scrapy", "java/", "apache-httpclient", "libwww", "wget"
    ]
    ua_l = ua.lower()
    if any(m in ua_l for m in scanner_markers):
        score += 4

    # Odd header patterns
    if not ua:
        score += 3
    if not accept:
        score += 2
    if not al:
        score += 1

    # Presence of modern browser client hints may reduce score slightly
    if request.headers.get("Sec-CH-UA"):
        score -= 1
    if request.headers.get("Sec-Fetch-Mode"):
        score -= 1

    # If they send no cookies repeatedly, typical for scanners
    if not request.cookies:
        score += 1

    # Clamp to [0, 10]
    return max(0, min(10, score))


# ----------------------------
# Per-client hourly budget
# ----------------------------

_budget: Dict[Tuple[str, int], int] = {}


def within_hourly_budget(ck: str) -> bool:
    hour = int(time.time() // 3600)
    k = (ck, hour)
    _budget[k] = _budget.get(k, 0) + 1
    return _budget[k] <= MAX_PAGES_PER_CLIENT_PER_HOUR


# ----------------------------
# Responses
# ----------------------------

def common_headers(resp):
    resp.headers["Server"] = APP_NAME
    resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


def render_page(title: str, body_html: str, status: int = 200):
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="robots" content="noindex,nofollow,noarchive">
    <title>{title}</title>
  </head>
  <body style="font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; padding: 1rem;">
    <h1>{title}</h1>
    {body_html}
    <hr>
    <small>ts={time.time():.3f}</small>
  </body>
</html>"""
    resp = make_response(html, status)
    return common_headers(resp)


def render_terminal(depth: int):
    body = f"""
    <p>Traversal ended (depth={depth}).</p>
    <p>If you are a human, there is nothing to do here.</p>
    """
    return render_page("Nothing here", body, 200)


def render_throttled():
    body = """
    <p>Request rate limited.</p>
    """
    return render_page("Slow down", body, 429)


def render_budget_exhausted():
    body = """
    <p>Client hourly budget exhausted.</p>
    """
    return render_page("Budget exhausted", body, 429)


def render_root(seed: str):
    # Root page contains a small number of “normal looking” internal links and one honey path
    # The honey link can be hidden via CSS if desired, but do not rely on that as “security”.
    chain = seed
    token = make_token(seed=seed, depth=0, idx=0, chain=chain)
    honey_url = f"/_honey/{token}"

    body = f"""
    <p>This is a decoy endpoint.</p>
    <ul>
      <li><a href="/status">/status</a></li>
      <li><a href="/docs">/docs</a></li>
      <li><a href="{honey_url}">/internal/metadata</a></li>
    </ul>
    """
    return render_page("Index", body, 200)


def render_honey(seed: str, depth: int, chain: str):
    # Bounded traversal: stop at MAX_DEPTH
    if depth >= MAX_DEPTH:
        return render_terminal(depth)

    # Deterministically derive next “branch seeds”
    links = []
    for i in range(LINKS_PER_PAGE):
        nxt_seed = hashlib.sha256(f"{seed}:{depth}:{i}".encode("utf-8")).hexdigest()[:12]
        nxt_chain = f"{chain}/{nxt_seed}"
        tok = make_token(seed=nxt_seed, depth=depth + 1, idx=i, chain=nxt_chain)
        links.append(f'<li><a href="/_honey/{tok}">node:{nxt_seed}</a></li>')

    # Mildly realistic-looking content (harmless)
    body = f"""
    <p><b>Depth:</b> {depth} / {MAX_DEPTH}</p>
    <p><b>Node:</b> {seed}</p>
    <p><b>Hint:</b> If you are an automated client, this path is intentionally non-actionable.</p>
    <h3>Related</h3>
    <ul>
      {''.join(links)}
    </ul>
    """
    return render_page("Internal metadata", body, 200)


# ----------------------------
# Routes
# ----------------------------

@app.route("/")
def index():
    ck = client_key()
    if not allow_request(ck):
        return render_throttled()
    if not within_hourly_budget(ck):
        return render_budget_exhausted()

    seed = hashlib.sha256(str(time.time()).encode("utf-8")).hexdigest()[:10]
    return render_root(seed)


@app.route("/_honey/<token>")
def honey(token: str):
    t0 = time.time()
    ck = client_key()

    # Rate limit first
    if not allow_request(ck):
        return render_throttled()
    if not within_hourly_budget(ck):
        return render_budget_exhausted()

    # Parse token
    obj = parse_token(token)
    if obj is None:
        # Invalid token: still log it; it is useful signal.
        depth = -1
        seed = "invalid"
        chain = ""
    else:
        seed = obj["s"]
        depth = obj["d"]
        chain = obj["c"]

    score = bot_score()

    # Optional: small delay for high score (do NOT overdo it; keep it bounded)
    if ADD_ARTIFICIAL_DELAY_FOR_HIGH_SCORE and score >= 6:
        delay = min(MAX_DELAY_SECONDS, 0.15 * score)
        time.sleep(delay)

    latency_ms = int((time.time() - t0) * 1000)

    # Log telemetry (minimize what you store if necessary)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ip = ip.split(",")[0].strip()

    row = dict(
        ts=time.time(),
        client_ip=ip,
        client_key=ck,
        method=request.method,
        path=request.path,
        query=request.query_string.decode("utf-8", "ignore"),
        referer=request.headers.get("Referer", ""),
        user_agent=request.headers.get("User-Agent", ""),
        accept=request.headers.get("Accept", ""),
        accept_lang=request.headers.get("Accept-Language", ""),
        accept_enc=request.headers.get("Accept-Encoding", ""),
        connection=request.headers.get("Connection", ""),
        sec_ch_ua=request.headers.get("Sec-CH-UA", ""),
        sec_ch_platform=request.headers.get("Sec-CH-UA-Platform", ""),
        sec_fetch_site=request.headers.get("Sec-Fetch-Site", ""),
        sec_fetch_mode=request.headers.get("Sec-Fetch-Mode", ""),
        sec_fetch_dest=request.headers.get("Sec-Fetch-Dest", ""),
        cookies_present=1 if bool(request.cookies) else 0,
        depth=depth if isinstance(depth, int) else -1,
        score=score,
        chain=chain,
        latency_ms=latency_ms,
    )
    insert_hit(row)

    # Render response
    if obj is None:
        return render_page("Invalid", "<p>Invalid token.</p>", 400)

    return render_honey(seed=seed, depth=depth, chain=chain)


# Simple “normal” decoy endpoints (optional)
@app.route("/status")
def status():
    resp = make_response({"ok": True, "ts": time.time()})
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    return resp


@app.route("/docs")
def docs():
    body = """
    <p>Documentation placeholder.</p>
    <p>If you are seeing this, you are likely not looking for real docs.</p>
    """
    return render_page("Docs", body, 200)


if __name__ == "__main__":
    print(f"{APP_NAME} running on http://0.0.0.0:5000/")
    print(f"DB: {DB_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=False)
