import os
import pathlib

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mock_data
import llm

app = FastAPI(title="Stadium Copilot — FIFA World Cup 2026")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CONTEXT = mock_data.stadium_context_block()


# ---------- request models ----------

class ChatRequest(BaseModel):
    message: str
    language: str = "English"


class VolunteerChatRequest(BaseModel):
    message: str
    role: str = "volunteer"
    zone: str = "General Concourse"


class SimplifyRequest(BaseModel):
    text: str
    language: str = "English"


class SustainabilityRequest(BaseModel):
    origin: str
    destination: str
    mode_preference: str = "any"


# ---------- prompts ----------

def chat_system_prompt(language: str) -> str:
    return f"""You are Stadium Copilot, an on-site GenAI assistant for fans at {mock_data.STADIUM_NAME}
during the FIFA World Cup 2026. Answer ONLY using the stadium context below plus
ordinary common sense about stadiums. Be concise (2-4 sentences), friendly, and
concrete — give gate letters, directions, and next steps a fan can act on immediately.
If the context doesn't cover something, say so honestly and suggest asking Guest Services.

Always reply in this language: {language}.

STADIUM CONTEXT:
{CONTEXT}
"""


CROWD_SYSTEM_PROMPT = """You are an operations intelligence assistant for stadium staff.
You receive live gate occupancy data (percent of capacity, status: clear/busy/critical).
Write a short operational advisory (3-5 sentences):
1) Name which gate(s) are critical or busy and by how much.
2) Recommend a concrete rerouting or staffing action (e.g. redirect fans to a clearer gate,
   open an overflow lane, add stewards).
3) Keep the tone calm and directive, like a control-room briefing, not alarmist.
Do not invent gates that aren't in the data."""


ACCESSIBILITY_SYSTEM_PROMPT = """You rewrite stadium information in plain, accessible language
(roughly a 6th-grade reading level), for fans who benefit from simplified text —
including neurodivergent fans, non-native speakers, and fans with cognitive disabilities.
Use short sentences, no jargon, and numbered steps where the instructions involve
more than one action. Preserve every factual detail (gate letters, times, locations).
Reply in this language: {language}."""


SUSTAINABILITY_SYSTEM_PROMPT = """You are a sustainability-minded travel assistant for World Cup fans.
Given a fan's origin, destination, and mode preference, recommend the lowest-carbon
practical way to reach the stadium using ONLY the transport options listed in the
stadium context below. Give one primary recommendation and one backup, plus a rough,
clearly-labeled ESTIMATE (not a precise figure) of the emissions avoided vs. driving alone.
Keep it under 4 sentences.

STADIUM CONTEXT:
""" + CONTEXT


def volunteer_system_prompt(role: str, zone: str) -> str:
    role_name = role.replace("-", " ").title()
    return f"""You are Stadium Copilot Staff Assistant, an AI operations assistant for volunteers
and venue staff at {mock_data.STADIUM_NAME} during the FIFA World Cup 2026.

The person asking is a **{role_name}** assigned to **{zone}**.

Your job is to:
1. Answer questions about their specific duties and responsibilities based on their role.
2. Provide emergency protocols, safety procedures, and escalation contacts.
3. Give directions and info about nearby facilities (restrooms, first aid, water stations).
4. Help them assist fans who speak different languages or have accessibility needs.
5. Provide real-time situational awareness using the stadium context below.

Be concise, directive, and supportive — like a helpful team leader giving a quick briefing.
Use bullet points for multi-step procedures. Always include who to contact or where to go.

ROLE-SPECIFIC GUIDANCE:
- Volunteers: Greet fans, give directions, answer common questions, escalate issues to Guest Services.
- Security Staff: Monitor entry points, handle prohibited items, crowd control, escalate to Security Chief.
- Medical Team: First response protocols, AED locations (Gates A, C, E), first aid kits at every gate.
- Concessions Staff: Menu info, allergen handling, rush-hour prep, cash/card policies.
- Guest Services: Lost & found (Gate B desk), wheelchair loans, ASL interpreter requests, complaints.

STADIUM CONTEXT:
{CONTEXT}
"""


def raise_llm_http_error(e: llm.LLMError):
    status_code = 429 if isinstance(e, llm.LLMRateLimitError) else 500
    raise HTTPException(status_code=status_code, detail=str(e))


# ---------- routes ----------

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        reply = llm.generate(chat_system_prompt(req.language), req.message)
    except llm.LLMError as e:
        raise_llm_http_error(e)
    return {"reply": reply}


@app.post("/api/volunteer-chat")
def volunteer_chat(req: VolunteerChatRequest):
    try:
        reply = llm.generate(
            volunteer_system_prompt(req.role, req.zone), req.message
        )
    except llm.LLMError as e:
        raise_llm_http_error(e)
    return {"reply": reply}


@app.get("/api/crowd-insight")
def crowd_insight():
    snapshot = mock_data.get_live_crowd_snapshot()
    data_summary = "\n".join(
        f"- Gate {g['id']} ({g['name']}): {g['occupancy_pct']}% full, status={g['status']}"
        for g in snapshot
    )
    try:
        advisory = llm.generate(CROWD_SYSTEM_PROMPT, data_summary)
    except llm.LLMError as e:
        raise_llm_http_error(e)
    return {"gates": snapshot, "advisory": advisory}


@app.post("/api/accessibility-simplify")
def simplify(req: SimplifyRequest):
    try:
        reply = llm.generate(
            ACCESSIBILITY_SYSTEM_PROMPT.format(language=req.language), req.text
        )
    except llm.LLMError as e:
        raise_llm_http_error(e)
    return {"simplified": reply}


@app.post("/api/sustainability-tip")
def sustainability_tip(req: SustainabilityRequest):
    prompt = (
        f"Origin: {req.origin}\n"
        f"Destination: {req.destination}\n"
        f"Mode preference: {req.mode_preference}"
    )
    try:
        reply = llm.generate(SUSTAINABILITY_SYSTEM_PROMPT, prompt)
    except llm.LLMError as e:
        raise_llm_http_error(e)
    return {"tip": reply}


# ---------- health check ----------

@app.get("/api/health")
def health():
    return {"status": "ok", "venue": mock_data.STADIUM_NAME, "provider": llm.PROVIDER}


# ---------- serve frontend (static, no build step) ----------

FRONTEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
