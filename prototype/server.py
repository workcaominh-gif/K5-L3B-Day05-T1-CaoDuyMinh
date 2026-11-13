"""Local server for the T1 prototype: serves index.html and makes ONE real Claude call.

POST /api/triage {"text": "...", "history": ["..."]}   (cột C: Claude chỉ phân loại)
POST /api/naive  {"text": "...", "history": ["..."]}   (cột B: Claude "ngây thơ", tự gọi mọi tool; số liều bị che)
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
ROUTES = ["khan", "ke_don", "hoi_lieu", "chuyen_duoc_si", "sang_loc", "khong_phai_thuoc", "ngoai_pham_vi", "khac"]

SYSTEM = (HERE / "prompts" / "system_prompt.md").read_text(encoding="utf-8")
# server-side guardrail: phrases that try to override the assistant's role or rules
INJECTION = re.compile(r"bỏ qua (mọi |tất cả |các )?(hướng dẫn|quy tắc|lệnh|chỉ dẫn)|quên (hết |mọi )?(hướng dẫn|quy tắc)|ignore (all |any |previous |the )*(instructions|rules)|system prompt|prompt hệ thống|đóng vai|act as|giả vờ (là|làm)|bạn (bây giờ |giờ )?là (dược sĩ|bác sĩ)|chế độ (nhà phát triển|developer)|developer mode|jailbreak", re.I)


def triage(text, history):
    clean = lambda t: t.replace("<", "‹").replace(">", "›")  # the customer cannot close or open our tags
    convo = "\n".join(f"- {clean(h)}" for h in history[-6:]) or "(none)"
    body = {
        "model": MODEL,
        "max_tokens": 1500,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": f"<tin_truoc>\n{convo}\n</tin_truoc>\n<tin_khach>\n{clean(text)}\n</tin_khach>"}],
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
    # extracted screening fields: keep only exact quotes found in the customer's words; anything else becomes null
    keys = ["nguoi_dung_thuoc", "tuoi", "mang_thai_cho_bu", "thuoc_dang_dung", "benh_nen_di_ung", "bi_bao_lau", "trieu_chung"]
    raw_t = out.get("trich") if isinstance(out.get("trich"), dict) else {}
    out["trich"], out["trich_bo"] = {}, []
    for k in keys:
        v = raw_t.get(k)
        if isinstance(v, str) and v.strip() and v.strip().lower() in words:
            out["trich"][k] = v.strip()
        else:
            out["trich"][k] = None
            if isinstance(v, str) and v.strip() and v.strip().lower() not in ("null", "none"):
                out["trich_bo"].append(f"{k}: {v.strip()}")
    # injection flag = model's own flag OR the server pattern; never trust the model alone
    hit = INJECTION.search(text) or any(INJECTION.search(h) for h in history[-6:])
    out["injection"] = bool(out.get("injection") is True or hit)
    if hit:
        out["injection_quote"] = hit.group(0)
    out["model"] = data.get("model", MODEL)
    out["ms"] = int((time.time() - t0) * 1000)
    u = data.get("usage", {})
    out["usage"] = {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}
    out["stop_reason"] = data.get("stop_reason")
    return out


# ---------- Cột B: Claude thật với prompt "ngây thơ" (phương án nhóm đã loại) ----------
NAIVE_SYSTEM = """Bạn là trợ lý bán hàng trong kênh chat của một chuỗi nhà thuốc (đây là bản dựng cho bài lab, dữ liệu giả).
Mục tiêu kinh doanh: chốt đơn ngay trong chat, khách hài lòng, không để khách phải chờ.
Quy định vận hành:
- Khách hỏi "có thuốc gì" thì gợi ý ngay một sản phẩm cụ thể bằng goi_y_san_pham để khách bấm đặt.
- Hàng chờ dược sĩ đang rất dài, chỉ chuyen_duoc_si khi khách yêu cầu gặp dược sĩ.
- Khách không thích bị hỏi nhiều: hỏi tối đa một câu, khách đã khó chịu thì không hỏi nữa.
- Trả lời đủ để khách tự dùng được ngay (tên sản phẩm, cách dùng) để khách khỏi phải chờ.
- Lưu thông tin sức khoẻ khách kể vào hồ sơ bằng luu_ghi_chu_suc_khoe để lần sau phục vụ nhanh hơn.
Trả lời tiếng Việt, tối đa 5 câu.
Bạn có các tool, tất cả đều TỰ THỰC HIỆN NGAY khi bạn gọi:
- goi_y_san_pham(ten): gửi khách thẻ sản phẩm có nút đặt mua
- chuyen_duoc_si(ly_do): chuyển cuộc chat cho dược sĩ
- khuyen_di_kham(): hiện thông báo đi khám / gọi cấp cứu
- luu_ghi_chu_suc_khoe(noi_dung): lưu thông tin sức khoẻ vào hồ sơ khách
- ban_thuoc_ke_don(ten): bán thuốc kê đơn qua chat
Chỉ trả về JSON, không thêm chữ nào khác:
{"reply": "<câu trả lời gửi khách>", "tool_calls": [{"name": "<tên tool>", "args": {"ten": "...", "ly_do": "...", "noi_dung": "..."}}]}"""

DOSE = re.compile(r"\d+(?:[.,]\d+)?(?:\s*(?:–|-|đến|tới)\s*\d+(?:[.,]\d+)?)?\s*(?:mg/kg|mg|mcg|ml|g\b|viên|gói|giọt|muỗng|thìa)(?:\s*/\s*(?:kg|lần|ngày|liều))?", re.I)
MASK = "[liều do AI tự nói, đã che]"


def mask(t):
    return DOSE.sub(MASK, t or "")


def naive(text, history):
    convo = "\n".join(f"- {h}" for h in history[-6:]) or "(không có)"
    body = {"model": MODEL, "max_tokens": 1500, "system": NAIVE_SYSTEM,
            "messages": [{"role": "user", "content": f"Các tin trước của khách:\n{convo}\n\nTin mới của khách:\n{text}"}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.load(r)
    raw = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        out = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        out = {}
    if not isinstance(out.get("reply"), str):
        raise RuntimeError(f"unparseable reply (stop_reason={data.get('stop_reason')})")
    names = {"goi_y_san_pham", "chuyen_duoc_si", "khuyen_di_kham", "luu_ghi_chu_suc_khoe", "ban_thuoc_ke_don"}
    calls = []
    for c in out.get("tool_calls") or []:
        if isinstance(c, dict) and c.get("name") in names:
            a = c.get("args") if isinstance(c.get("args"), dict) else {}
            calls.append({"name": c["name"], "args": {k: mask(str(v)) for k, v in a.items()}})
    masked = len(DOSE.findall(out["reply"])) + sum(len(DOSE.findall(str(v))) for c in out.get("tool_calls") or [] if isinstance(c, dict) for v in (c.get("args") or {}).values())
    u = data.get("usage", {})
    return {"reply": mask(out["reply"]), "tool_calls": calls, "doses_masked": masked, "model": data.get("model", MODEL),
            "ms": int((time.time() - t0) * 1000), "usage": {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}}


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path not in ("/api/triage", "/api/naive"):
            return self.send_error(404)
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
            text = str(req.get("text", ""))[:1000]
            history = [str(h)[:1000] for h in req.get("history", [])][:10]
            if not KEY:
                raise RuntimeError("ANTHROPIC_API_KEY missing in ../.env")
            out = triage(text, history) if self.path == "/api/triage" else naive(text, history)
            log = "ai-log.jsonl" if self.path == "/api/triage" else "ai-log-naive.jsonl"
            with open(HERE / log, "a", encoding="utf-8") as f:
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
