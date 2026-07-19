/* ============================================================
   STADIUM COPILOT — app.js
   Frontend logic for all 6 feature tabs.
   ============================================================ */

const API = ""; // same-origin

// ============================================================
// TAB SWITCHING
// ============================================================

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => {
      t.classList.remove("is-active");
      t.setAttribute("aria-selected", "false");
    });
    panels.forEach((p) => p.classList.remove("is-active"));

    tab.classList.add("is-active");
    tab.setAttribute("aria-selected", "true");
    document.getElementById(`panel-${tab.dataset.tab}`).classList.add("is-active");

    // Auto-load crowd data when switching to that tab
    if (tab.dataset.tab === "crowd" && !crowdLoaded) loadCrowdInsight();
    // Auto-load map data
    if (tab.dataset.tab === "map" && !mapLoaded) loadMapData();
  });
});

// ============================================================
// MATCH TICKER (simulated live)
// ============================================================

const matchTicker = document.getElementById("match-time");
const MATCHES = [
  { teams: "🇧🇷 Brazil vs Argentina 🇦🇷", minute: 34 },
  { teams: "🇩🇪 Germany vs Japan 🇯🇵", minute: 67 },
  { teams: "🇫🇷 France vs Spain 🇪🇸", minute: 12 },
  { teams: "🇲🇽 Mexico vs USA 🇺🇸", minute: 88 },
];

let currentMatch = MATCHES[0];
let matchMinute = currentMatch.minute;

function updateMatchTicker() {
  matchMinute++;
  if (matchMinute > 90) matchMinute = 45; // wrap around for demo
  const extraTime = matchMinute > 45 && matchMinute <= 48 ? "45+" + (matchMinute - 45) : matchMinute;
  matchTicker.textContent = `Live — ${extraTime}'`;
}

setInterval(updateMatchTicker, 15000); // advance every 15s for demo feel

// ============================================================
// ASSISTANT (Ask Copilot)
// ============================================================

const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-text");
const chatLang = document.getElementById("chat-lang");

function addMessage(chatEl, role, text, isTyping = false) {
  const wrap = document.createElement("div");
  wrap.className = `msg msg--${role}`;
  const bubble = document.createElement("div");
  bubble.className = "msg__bubble";
  if (role === "bot") {
    const label = document.createElement("span");
    label.className = "msg__label";
    label.textContent = "Stadium Copilot";
    bubble.appendChild(label);
  }
  const textNode = document.createElement("span");
  if (isTyping) {
    textNode.className = "typing-dots";
    textNode.textContent = "Thinking";
  } else {
    textNode.textContent = text;
  }
  bubble.appendChild(textNode);
  wrap.appendChild(bubble);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
  return wrap;
}

async function askCopilot(message) {
  addMessage(chatLog, "user", message);
  const placeholder = addMessage(chatLog, "bot", "", true);

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, language: chatLang.value }),
    });
    const data = await res.json();
    placeholder.remove();
    if (!res.ok) {
      addMessage(chatLog, "bot", `Sorry — ${data.detail || "something went wrong."}`);
      return;
    }
    addMessage(chatLog, "bot", data.reply);
  } catch (err) {
    placeholder.remove();
    addMessage(chatLog, "bot", "Couldn't reach the server. Is the backend running?");
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  askCopilot(text);
});

document.querySelectorAll(".chip:not(.vol-chip):not([data-sample])").forEach((chip) => {
  chip.addEventListener("click", () => askCopilot(chip.dataset.q));
});

// ============================================================
// CROWD INTELLIGENCE
// ============================================================

const pulseBars = document.getElementById("pulse-bars");
const advisoryText = document.getElementById("advisory-text");
const crowdRefresh = document.getElementById("crowd-refresh");
const crowdUpdated = document.getElementById("crowd-updated");
const statTotal = document.getElementById("stat-total");
const statBusiest = document.getElementById("stat-busiest");
const statQuietest = document.getElementById("stat-quietest");
let crowdLoaded = false;
let lastCrowdData = null;

async function loadCrowdInsight() {
  advisoryText.textContent = "Analyzing gate data with AI…";
  advisoryText.style.color = "var(--ink-dim)";
  crowdRefresh.disabled = true;

  try {
    const res = await fetch(`${API}/api/crowd-insight`);
    const data = await res.json();
    if (!res.ok) {
      advisoryText.textContent = `Sorry — ${data.detail || "couldn't load the advisory."}`;
      return;
    }
    renderPulse(data.gates);
    renderCrowdStats(data.gates);
    advisoryText.textContent = data.advisory;
    advisoryText.style.color = "var(--ink)";
    lastCrowdData = data.gates;
    crowdLoaded = true;

    const now = new Date();
    crowdUpdated.textContent = `Updated ${now.toLocaleTimeString()}`;

    // Update map gate statuses if map is loaded
    updateMapGateStatuses(data.gates);
  } catch (err) {
    advisoryText.textContent = "Couldn't reach the server. Is the backend running?";
  } finally {
    crowdRefresh.disabled = false;
  }
}

function renderPulse(gates) {
  pulseBars.innerHTML = "";
  gates.forEach((g) => {
    const row = document.createElement("div");
    row.className = "pulse__row";

    const statusEmoji = g.status === "critical" ? "🔴" : g.status === "busy" ? "🟡" : "🟢";

    row.innerHTML = `
      <div class="pulse__gate">
        <strong>Gate ${g.id}</strong>
        ${statusEmoji} ${g.status}
      </div>
      <div class="pulse__track">
        <div class="pulse__fill ${g.status}" style="width:0%"></div>
      </div>
      <div class="pulse__pct">${g.occupancy_pct}%</div>
    `;
    pulseBars.appendChild(row);

    // Animate the bar fill
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        row.querySelector(".pulse__fill").style.width = `${g.occupancy_pct}%`;
      });
    });
  });
}

function renderCrowdStats(gates) {
  const avgOccupancy = Math.round(gates.reduce((sum, g) => sum + g.occupancy_pct, 0) / gates.length);
  const busiest = gates.reduce((a, b) => a.occupancy_pct > b.occupancy_pct ? a : b);
  const quietest = gates.reduce((a, b) => a.occupancy_pct < b.occupancy_pct ? a : b);

  statTotal.textContent = `${avgOccupancy}%`;
  statTotal.style.color = avgOccupancy >= 85 ? "var(--red)" : avgOccupancy >= 60 ? "var(--amber)" : "var(--turf-bright)";
  statBusiest.textContent = `Gate ${busiest.id}`;
  statBusiest.style.color = busiest.status === "critical" ? "var(--red)" : "var(--amber)";
  statQuietest.textContent = `Gate ${quietest.id}`;
  statQuietest.style.color = "var(--turf-bright)";
}

crowdRefresh.addEventListener("click", loadCrowdInsight);

// ============================================================
// ACCESSIBILITY
// ============================================================

const accessInput = document.getElementById("access-input");
const accessLang = document.getElementById("access-lang");
const accessSubmit = document.getElementById("access-submit");
const accessResult = document.getElementById("access-result");
const accessOutput = document.getElementById("access-output");
const accessSpeak = document.getElementById("access-speak");

// Sample text chips
document.querySelectorAll("[data-sample]").forEach((chip) => {
  chip.addEventListener("click", () => {
    accessInput.value = chip.dataset.sample;
    accessInput.focus();
  });
});

accessSubmit.addEventListener("click", async () => {
  const text = accessInput.value.trim();
  if (!text) return;
  accessSubmit.disabled = true;
  accessSubmit.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg> Simplifying…`;

  try {
    const res = await fetch(`${API}/api/accessibility-simplify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language: accessLang.value }),
    });
    const data = await res.json();
    if (!res.ok) {
      accessOutput.textContent = `Sorry — ${data.detail || "couldn't simplify that."}`;
    } else {
      accessOutput.textContent = data.simplified;
    }
    accessResult.hidden = false;
  } catch (err) {
    accessOutput.textContent = "Couldn't reach the server. Is the backend running?";
    accessResult.hidden = false;
  } finally {
    accessSubmit.disabled = false;
    accessSubmit.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg> Simplify`;
  }
});

accessSpeak.addEventListener("click", () => {
  if (!("speechSynthesis" in window)) {
    alert("Read-aloud isn't supported in this browser.");
    return;
  }
  const utter = new SpeechSynthesisUtterance(accessOutput.textContent);

  // Try to match the selected language
  const langMap = {
    "English": "en-US", "Spanish": "es-ES", "French": "fr-FR",
    "Portuguese": "pt-BR", "Hindi": "hi-IN", "Arabic": "ar-SA",
  };
  utter.lang = langMap[accessLang.value] || "en-US";

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
});

// ============================================================
// SUSTAINABILITY
// ============================================================

const sustainForm = document.getElementById("sustain-form");
const sustainOrigin = document.getElementById("sustain-origin");
const sustainMode = document.getElementById("sustain-mode");
const sustainResult = document.getElementById("sustain-result");
const sustainOutput = document.getElementById("sustain-output");

sustainForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const origin = sustainOrigin.value.trim();
  if (!origin) return;

  const btn = sustainForm.querySelector(".btn-action--primary");
  btn.disabled = true;
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/></svg> Finding route…`;

  try {
    const res = await fetch(`${API}/api/sustainability-tip`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        origin,
        destination: "MetLife Stadium",
        mode_preference: sustainMode.value,
      }),
    });
    const data = await res.json();
    sustainOutput.textContent = res.ok
      ? data.tip
      : `Sorry — ${data.detail || "couldn't get a route."}`;
    sustainResult.hidden = false;
  } catch (err) {
    sustainOutput.textContent = "Couldn't reach the server. Is the backend running?";
    sustainResult.hidden = false;
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Get sustainable route`;
  }
});

// ============================================================
// INTERACTIVE STADIUM MAP
// ============================================================

let mapLoaded = false;

const gateDetails = {
  A: {
    name: "Gate A — North Plaza",
    capacity: 9000,
    notes: "Nearest to NJ Transit rail platform",
    services: ["🚆 NJ Transit Rail access", "🎫 Ticket scanning", "🚻 Restrooms nearby", "🍔 Food court — Section 101"],
  },
  B: {
    name: "Gate B — East Concourse",
    capacity: 7500,
    notes: "Accessible entrance, ramp + lift access",
    services: ["♿ Wheelchair ramp & lift", "👁️ Guest Services desk", "🏥 First Aid station", "🐕 Service animal relief area"],
  },
  C: {
    name: "Gate C — South Plaza",
    capacity: 9000,
    notes: "Nearest to main parking lots",
    services: ["🅿️ Parking Lots A-D access", "🚗 Rideshare pickup (Lot F)", "🚻 Restrooms", "🛍️ Merchandise store"],
  },
  D: {
    name: "Gate D — West Concourse",
    capacity: 6000,
    notes: "Nearest to shuttle bus drop-off",
    services: ["🚌 Shuttle bus drop-off", "🚲 Bike valet (free)", "🐕 Service animal relief area", "🧘 Sensory room — Section 105"],
  },
  E: {
    name: "Gate E — Media/VIP",
    capacity: 3000,
    notes: "Lower footfall, general fans may use as overflow",
    services: ["📹 Media credentials", "🎩 VIP lounge access", "🍷 Premium dining", "📡 Press room"],
  },
};

const mapInfo = document.getElementById("map-info");
const gateMarkers = document.querySelectorAll(".gate-marker");

function showGateInfo(gateId) {
  const gate = gateDetails[gateId];
  if (!gate) return;

  // Find live data if available
  let liveStatus = null;
  if (lastCrowdData) {
    liveStatus = lastCrowdData.find((g) => g.id === gateId);
  }

  const statusClass = liveStatus ? liveStatus.status : "clear";
  const statusText = liveStatus ? `${liveStatus.occupancy_pct}% — ${liveStatus.status}` : "No live data";

  mapInfo.innerHTML = `
    <div class="map-info__detail">
      <h4>${gate.name}</h4>
      <span class="gate-status-badge ${statusClass}">${statusText}</span>
      <p style="font-size:12px; color:var(--ink-dim); margin-bottom:12px;">
        Capacity: ${gate.capacity.toLocaleString()} · ${gate.notes}
      </p>
      <ul>
        ${gate.services.map((s) => `<li>${s}</li>`).join("")}
      </ul>
    </div>
  `;

  // Highlight active gate
  gateMarkers.forEach((m) => m.classList.remove("active"));
  document.querySelector(`[data-gate="${gateId}"]`).classList.add("active");
}

gateMarkers.forEach((marker) => {
  marker.addEventListener("click", () => showGateInfo(marker.dataset.gate));
  marker.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      showGateInfo(marker.dataset.gate);
    }
  });
});

function updateMapGateStatuses(gates) {
  gates.forEach((g) => {
    const marker = document.querySelector(`[data-gate="${g.id}"]`);
    if (!marker) return;
    marker.classList.remove("status-busy", "status-critical");
    if (g.status === "busy") marker.classList.add("status-busy");
    if (g.status === "critical") marker.classList.add("status-critical");
  });
}

async function loadMapData() {
  mapLoaded = true;
  if (!lastCrowdData) {
    await loadCrowdInsight();
  } else {
    updateMapGateStatuses(lastCrowdData);
  }
}

// ============================================================
// VOLUNTEER / STAFF ASSISTANT
// ============================================================

const volChatLog = document.getElementById("vol-chat-log");
const volChatForm = document.getElementById("vol-chat-form");
const volChatInput = document.getElementById("vol-chat-text");
const volRole = document.getElementById("vol-role");
const volZone = document.getElementById("vol-zone");

async function askVolunteerCopilot(message) {
  addMessage(volChatLog, "user", message);
  const placeholder = addMessage(volChatLog, "bot", "", true);

  // Augment the message with the selected role and zone context
  const augmentedMessage = `[Context: I am a ${volRole.value} assigned to ${volZone.value}]\n\n${message}`;

  try {
    const res = await fetch(`${API}/api/volunteer-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: augmentedMessage, role: volRole.value, zone: volZone.value }),
    });
    const data = await res.json();
    placeholder.remove();
    if (!res.ok) {
      addMessage(volChatLog, "bot", `Sorry — ${data.detail || "something went wrong."}`);
      return;
    }
    addMessage(volChatLog, "bot", data.reply);
  } catch (err) {
    placeholder.remove();
    addMessage(volChatLog, "bot", "Couldn't reach the server. Is the backend running?");
  }
}

volChatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = volChatInput.value.trim();
  if (!text) return;
  volChatInput.value = "";
  askVolunteerCopilot(text);
});

document.querySelectorAll(".vol-chip").forEach((chip) => {
  chip.addEventListener("click", () => askVolunteerCopilot(chip.dataset.q));
});

// ============================================================
// INIT
// ============================================================

addMessage(chatLog, "bot", "Hi! 👋 I'm Stadium Copilot — your AI assistant for today's match at MetLife Stadium. Ask me about gates, transit, accessibility, food, or anything else!");
addMessage(volChatLog, "bot", "Welcome, team! 💪 I'm your Staff Assistant. Select your role and zone above, then ask me anything about your duties, protocols, or stadium operations.");
