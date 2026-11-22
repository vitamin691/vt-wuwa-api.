"""FastAPI router: POST /abby/chat, POST /bot/heartbeat, GET /bot/status.
Env vars on Render: GROQ_API_KEY, BOT_PUSH_SECRET. Keep knowledge.json next to this file."""
import os, time
import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()
SUPPORT = "https://discord.gg/AEVHRgP5aZ"
FALLBACK = "I don't have verified information about that. You can contact our official support server for assistance: " + SUPPORT
KNOWLEDGE = open(os.path.join(os.path.dirname(__file__), "knowledge.json"), encoding="utf-8").read()
SYSTEM = f"""You are Abby, the assistant of vT Official's WuWa Discord bot website.
Answer ONLY from the VERIFIED KNOWLEDGE below. Rules:
- Never invent commands, features, rewards, prices, mechanics or locations.
- Never present anything listed under not_implemented as available.
- Refuse unrelated general questions and never guess.
- If the knowledge does not answer the question, reply with exactly: {FALLBACK}
- Be brief, friendly, plain text (no markdown tables).
VERIFIED KNOWLEDGE (JSON):
{KNOWLEDGE}"""

_hits: dict = {}
_bot: dict = {}


class Msg(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    messages: list[Msg]


class BeatIn(BaseModel):
    name: str = ""
    status: str | None = None
    guilds: int | None = None
    activity_type: str | None = None
    activity: str | None = None
    url: str | None = None


@router.post("/abby/chat")
async def chat(body: ChatIn, request: Request):
    ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0]
    now = time.time()
    _hits[ip] = [t for t in _hits.get(ip, []) if now - t < 60] + [now]
    if len(_hits[ip]) > 12:
        return {"reply": "You're sending messages too fast. Wait a moment and try again."}
    msgs = [{"role": "assistant" if m.role == "assistant" else "user", "content": m.content[:400]} for m in body.messages[-8:]]
    if not msgs or msgs[-1]["role"] != "user":
        return {"reply": FALLBACK}
    try:
        async with httpx.AsyncClient(timeout=40) as c:
            r = await c.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
                json={"model": "openai/gpt-oss-120b", "temperature": 0.2, "max_completion_tokens": 700,
                      "reasoning_effort": "low", "messages": [{"role": "system", "content": SYSTEM}] + msgs})
            r.raise_for_status()
            reply = (r.json()["choices"][0]["message"].get("content") or "").strip()
    except Exception:
        return {"reply": FALLBACK}
    return {"reply": reply or FALLBACK}


@router.post("/bot/heartbeat")
async def heartbeat(b: BeatIn, x_secret: str = Header(default="")):
    if x_secret != os.environ.get("BOT_PUSH_SECRET", "\0"):
        raise HTTPException(403, "forbidden")
    _bot.update(name=b.name[:40], status=b.status, guilds=b.guilds,
             activity_type=b.activity_type, activity=(b.activity or None) and b.activity[:80],
             url=b.url if (b.url or "").startswith("http") else None, at=time.time())
    return {"ok": True}


@router.get("/bot/status")
async def bot_status():
    if not _bot.get("at") or time.time() - _bot["at"] > 180:
        return {"online": False}
    return {"online": True, "name": _bot["name"], "status": _bot["status"], "guilds": _bot["guilds"],
            "activity_type": _bot.get("activity_type"), "activity": _bot.get("activity"), "url": _bot.get("url")}
