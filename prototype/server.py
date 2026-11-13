"""Local server for the T1 prototype: serves index.html and makes ONE real Claude call.

POST /api/triage {"text": "...", "history": ["..."]}
  -> {"route": ..., "nguoi_dung_thuoc": ..., "bang_chung": [...], "chua_biet": [...], "model": ...}

The key is read from ../.env (gitignored) or the environment and never sent to the browser.
Claude only CLASSIFIES the message; every sentence the customer reads comes from fixed
templates in index.html, and the rule layer there can only be made stricter by Claude.
Each call is appended to ai-log.jsonl (message + result, no key) as evidence for the bonus.

Run:  python3 server.py   ->  http://localhost:8767
"""
import json, os, re, time, urllib.request, urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "8767"))


def load_env():
    env = HERE.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip().removeprefix("export ").strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("MODEL", "claude-haiku-5-5")
ROUTES = ["khan", "ke_don", "hoi_lieu", "chuyen_duoc_si", "sang_loc", "khong_phai_thuoc", "khac"]

SYSTEM = """You triage messages sent to a Vietnamese pharmacy chain's "Ask a pharmacist" chat.
You do NOT answer the customer and you never name a medicine or a dose. You only classify.

Pick exactly one route, the most cautious one that applies, in this priority order:
- khan: any danger sign for the person who will take the medicine (e.g. drowsy/hard to wake "li bì", "lơ mơ", trouble breathing, chest pain, seizure, fainting, blue lips, vomiting blood, fever >= 40, infant not feeding). They must go to a doctor / call 115 now.
- ke_don: asks to buy or replace a prescription-only medicine (antibiotics, blood-pressure drugs, corticoids...).
- hoi_lieu: asks for a dose or how much/how many to take.
- chuyen_duoc_si: the person who will take the medicine is a child under 12, aged 65+, pregnant or breastfeeding, has a chronic disease or takes other medicines, or has self-medicated 5+ days without improvement, or wants something "stronger".
- sang_loc: asks for a medicine but we do not yet know enough about who will take it (age, pregnancy, other medicines, duration).
- khong_phai_thuoc: only asks about non-medicine products (saline, masks, thermometers), price or stock.
- khac: anything else.

The sender is often NOT the person who will take the medicine; identify that person.
Reply with JSON only, no prose:
{"route": "...", "nguoi_dung_thuoc": "<who will take it, in Vietnamese, or 'chưa rõ'>",
 "bang_chung": ["<exact short quotes copied from the customer's words that justify the route>"],
 "chua_biet": ["<facts still unknown, in Vietnamese>"]}"""


def triage(text, history):
    convo = "\n".join(f"- {h}" for h in history[-6:]) or "(none)"
    body = {
        "model": MODEL,
        "max_tokens": 1500,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": f"Earlier customer messages:\n{convo}\n\nNew customer message:\n{text}"}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    raw = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        out = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        out = {}
    if out.get("route") not in ROUTES:
        raise RuntimeError(f"unparseable reply (stop_reason={data.get('stop_reason')})")
    # keep only quotes that really appear in the customer's words (no invented evidence)
    words = (" ".join(history) + " " + text).lower()
    out["bang_chung"] = [q for q in out.get("bang_chung", []) if isinstance(q, str) and q.lower() in words][:4]
    out["chua_biet"] = [q for q in out.get("chua_biet", []) if isinstance(q, str)][:4]
    out["model"] = data.get("model", MODEL)
    out["ms"] = int((time.time() - t0) * 1000)
    u = data.get("usage", {})
    out["usage"] = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}
    out["stop_reason"] = data.get("stop_reason")
    return out


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def do_POST(self):
        if self.path != "/api/triage":
            return self.send_error(404)
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
            text = str(req.get("text", ""))[:1000]
            history = [str(h)[:1000] for h in req.get("history", [])][:10]
            if not KEY:
                raise RuntimeError("ANTHROPIC_API_KEY missing in ../.env")
            out = triage(text, history)
            with open(HERE / "ai-log.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "text": text, "history": history, "result": out}, ensure_ascii=False) + "\n")
            code, payload = 200, out
        except urllib.error.HTTPError as e:
            code, payload = 502, {"error": f"HTTP {e.code}"}
        except Exception as e:  # network, parse, missing key: the page falls back to its rules
            code, payload = 502, {"error": type(e).__name__ + ": " + str(e)[:120]}
        b = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


if __name__ == "__main__":
    print(f"Prototype on http://localhost:{PORT}  (model {MODEL}, key {'loaded' if KEY else 'MISSING'})")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
