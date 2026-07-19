# Stadium Copilot 🏟️
### A GenAI operations layer for fans, staff, and organizers — FIFA World Cup 2026

---

## The Idea

**Stadium Copilot** is a single web app with six GenAI-powered tools that a fan or a
staff member opens on match day:

| Tool | What it does | Categories it hits |
|---|---|---|
| **Ask Copilot** | Multilingual chat assistant grounded in real stadium context (gates, transit, accessibility, sustainability, food, emergency info). Answers in 12 languages. | Navigation, multilingual assistance |
| **Crowd Intelligence** | Reads live (simulated) gate-occupancy data and has GenAI write a plain-English *operations advisory* — which gate is congested, what to do about it — instead of a raw dashboard. Includes summary statistics and animated visualizations. | Crowd management, operational intelligence, real-time decision support |
| **Accessibility** | Rewrites dense stadium announcements into plain, 6th-grade-level language in any of 6 languages, with one-tap read-aloud (browser TTS). Includes sample text presets. | Accessibility, multilingual assistance |
| **Getting There** | Given a fan's starting point, GenAI recommends the lowest-carbon *practical* route using only the transit options this stadium actually offers, with quick-info transit cards. | Transportation, sustainability |
| **Stadium Map** | Interactive SVG map of MetLife Stadium with clickable gate markers. Shows live occupancy status, services, and capacity per gate. | Navigation, real-time decision support |
| **Volunteer & Staff Assistant** | Role-aware AI assistant for volunteers, security, medical, concessions, and guest services staff. Provides duty briefings, emergency protocols, and situational awareness based on assigned zone. | Operational intelligence, real-time decision support |

One codebase, one running server, six demoable stories — GenAI actually reasoning
over structured data (not just a wrapped chatbot) in every tab.

---

## Architecture

```
                    ┌─────────────────────────────┐
   Browser  ──────► │   frontend/  (static HTML/   │
   (fan/staff)       │   CSS/JS, no build step)     │
                    └──────────────┬────────────────┘
                                   │ fetch() JSON
                                   ▼
                    ┌─────────────────────────────┐
                    │   backend/main.py (FastAPI)   │
                    │   /api/chat                   │
                    │   /api/volunteer-chat          │
                    │   /api/crowd-insight           │
                    │   /api/accessibility-simplify  │
                    │   /api/sustainability-tip      │
                    │   /api/health                  │
                    └──────────────┬────────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                                    ▼
      backend/mock_data.py                  backend/llm.py
      (gates, live occupancy,                (provider-agnostic
       transit, accessibility,                GenAI wrapper —
       food, emergencies,                     OpenAI or Anthropic)
       sustainability context)                         │
                                                       ▼
                                          Google Gemini API
```

---

## Where GenAI is actually used

Every endpoint makes exactly one LLM call, with a purpose-built system prompt:

1. **Fan Chat** — grounded in the full stadium context (gates, transit, accessibility, food, emergencies, sustainability) so it can't hallucinate. Replies in the fan's chosen language (12 supported).
2. **Crowd Advisory** — turns raw occupancy numbers into a directive control-room briefing. The AI is reasoning over live data, not just chatting.
3. **Accessibility Rewrite** — plain-language rewrite task with explicit reading-level target, in the fan's chosen language.
4. **Sustainability Route** — constrained recommendation from the stadium's real transit options, with emissions comparison.
5. **Volunteer/Staff Chat** — role-aware (volunteer/security/medical/concessions/guest services) and zone-aware prompts give context-specific duty briefings and emergency protocols.

---

## Setup

```bash
git clone <your-repo-url>
cd stadium-copilot

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Open .env and paste your API key:
# GEMINI_API_KEY=your-gemini-key-here
# (Default LLM_PROVIDER is "gemini")

cd backend
uvicorn main:app --reload --port 8000
```

Open **http://127.0.0.1:8000** — that's the whole app, frontend included.

No API key yet? The app still runs — every endpoint returns a clear, non-crashing
error so you can demo the UI while you wire up a key.

---

## Demo Script (~90 seconds)

1. **Ask Copilot** — click the "Food options" chip, then switch language to Spanish and ask a follow-up. Shows multilingual + navigation in one breath.
2. **Crowd Intelligence** — hit "Refresh live data" twice so judges see the bars animate and the advisory text change. Point out the summary stats update too.
3. **Accessibility** — click the "Re-entry policy" sample, hit Simplify, then "Read aloud". Concrete, visible accessibility win.
4. **Getting There** — type "Midtown Manhattan", submit, read the recommendation out loud.
5. **Stadium Map** — click different gates, show live status colors changing with crowd data.
6. **Volunteers** — select "Security Staff" + "Gate A", ask "What's my emergency protocol?". Shows operational intelligence for staff.

Close with: *"Six tools, one GenAI call each, one server — covering all eight categories in the brief."*

---

## Categories Covered

| Category | Where |
|---|---|
| ✅ Navigation | Ask Copilot, Stadium Map |
| ✅ Crowd management | Crowd Intelligence |
| ✅ Accessibility | Accessibility tab, sensory room info |
| ✅ Transportation | Getting There |
| ✅ Sustainability | Getting There (lowest-carbon route) |
| ✅ Multilingual assistance | Ask Copilot (12 languages), Accessibility (6 languages) |
| ✅ Operational intelligence | Crowd Intelligence, Volunteer Assistant |
| ✅ Real-time decision support | Crowd advisory, live gate occupancy, map status |

---

*Demo data only. Not affiliated with or endorsed by FIFA.*
