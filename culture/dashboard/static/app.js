"use strict";

// Mission Control SPA — vanilla JS, no build step.
const state = { selected: null, kind: "audit", es: null, chatTimer: null };

const $ = (sel) => document.querySelector(sel);
const el = (tag, cls, text) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
};

function toast(msg, isErr) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden", "err");
  if (isErr) t.classList.add("err");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 3000);
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  let data = {};
  try { data = await res.json(); } catch (_) {}
  if (!res.ok || data.error) {
    throw new Error(data.error || `HTTP ${res.status}`);
  }
  return data;
}

async function post(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

// ---- Agents grid -----------------------------------------------------------

// Group agents into teams: a boss heads its own team; an agent's `boss` field
// places it under that boss (even if the boss is offline); the rest are
// "unassigned". This mirrors the spawn hierarchy so teams read as units.
function groupTeams(agents) {
  const teams = new Map(); // bossNick -> { boss, workers: [] }
  const unassigned = [];
  const team = (k) => {
    if (!teams.has(k)) teams.set(k, { boss: null, workers: [] });
    return teams.get(k);
  };
  for (const a of agents) {
    if (a.is_boss) team(a.nick).boss = a;
    else if (a.boss) team(a.boss).workers.push(a);
    else unassigned.push(a);
  }
  return { teams, unassigned };
}

function teamHeader(text, count, noun) {
  const li = el("li", "team-header");
  li.appendChild(el("span", "team-name", text));
  li.appendChild(el("span", "team-count", `${count} ${noun}${count === 1 ? "" : "s"}`));
  return li;
}

function renderAgentItem(a, isWorker) {
  const item = el("li", "agent-item" + (isWorker ? " team-worker" : ""));
  if (a.nick === state.selected) item.classList.add("selected");
  item.onclick = () => selectAgent(a.nick);

  const row = el("div", "agent-row");
  const nick = el("span", "agent-nick");
  nick.appendChild(el("span", "dot " + a.state));
  nick.appendChild(document.createTextNode(a.nick));
  if (a.is_boss) nick.appendChild(el("span", "boss-tag", "BOSS"));
  row.appendChild(nick);
  if (a.pending > 0) row.appendChild(el("span", "agent-pending", a.pending + " ⏳"));
  item.appendChild(row);

  const meta = el("div", "agent-meta");
  meta.appendChild(el("span", null, a.state));
  meta.appendChild(el("span", null, a.last_action || ""));
  item.appendChild(meta);

  const actions = el("div", "agent-actions");
  actions.appendChild(ctlBtn("pause", "Pause", a.nick));
  actions.appendChild(ctlBtn("resume", "Resume", a.nick));
  const close = el("button", "btn btn-sm btn-danger", "Close");
  close.onclick = (e) => { e.stopPropagation(); confirmClose(a.nick); };
  actions.appendChild(close);
  item.appendChild(actions);
  return item;
}

async function refreshAgents() {
  let data;
  try { data = await api("/api/agents"); } catch (e) { return; }
  const list = $("#agent-list");
  list.replaceChildren();
  if (!data.agents.length) {
    list.appendChild(el("div", "empty", "No agents registered."));
    return;
  }
  const { teams, unassigned } = groupTeams(data.agents);
  for (const [bossNick, t] of teams) {
    const label = t.boss ? `${bossNick} · team` : `${bossNick} · team (boss offline)`;
    list.appendChild(teamHeader(label, t.workers.length, "worker"));
    if (t.boss) list.appendChild(renderAgentItem(t.boss, false));
    for (const w of t.workers) list.appendChild(renderAgentItem(w, true));
  }
  if (unassigned.length) {
    list.appendChild(teamHeader("unassigned", unassigned.length, "agent"));
    for (const a of unassigned) list.appendChild(renderAgentItem(a, false));
  }
}

function ctlBtn(action, label, nick) {
  const b = el("button", "btn btn-sm", label);
  b.onclick = async (e) => {
    e.stopPropagation();
    try {
      const r = await post("/api/" + action, { nick });
      toast(r.ok ? `${label} ${nick}` : `${label} ${nick} failed`, !r.ok);
      refreshAgents();
    } catch (err) { toast(err.message, true); }
  };
  return b;
}

function confirmClose(nick) {
  if (!confirm(`Close agent ${nick}? Its daemon will be stopped.`)) return;
  post("/api/close", { nick })
    .then((r) => { toast(r.ok ? `Closed ${nick}` : `Close failed`, !r.ok); refreshAgents(); })
    .catch((e) => toast(e.message, true));
}

// ---- Stream (per-agent session / daemon-log) -------------------------------

function selectAgent(nick) {
  state.selected = nick;
  $("#stream-title").textContent = nick;
  refreshAgents();
  openStream();
}

function openStream() {
  if (state.es) { state.es.close(); state.es = null; }
  if (state.chatTimer) { clearInterval(state.chatTimer); state.chatTimer = null; }
  const box = $("#stream");
  box.replaceChildren();
  const chatInput = $("#chat-input");
  if (state.kind === "chat") {
    chatInput.classList.remove("hidden");
    if (!state.selected) return;
    refreshChat();
    state.chatTimer = setInterval(refreshChat, 2500);
    return;
  }
  chatInput.classList.add("hidden");
  if (!state.selected) return;
  const url = `/api/stream/${state.kind}/${encodeURIComponent(state.selected)}`;
  const es = new EventSource(url);
  state.es = es;
  es.onmessage = (ev) => {
    if (!ev.data) return;
    appendStreamLine(box, ev.data);
  };
  es.onerror = () => { /* EventSource auto-reconnects */ };
}

// ---- Chat (talk to an agent in its channel) --------------------------------

async function refreshChat() {
  if (!state.selected || state.kind !== "chat") return;
  let data;
  try { data = await api(`/api/channel/${encodeURIComponent(state.selected)}`); }
  catch (_) { return; }
  const box = $("#stream");
  box.replaceChildren();
  if (!data.messages || !data.messages.length) {
    box.appendChild(el("div", "empty", `No messages in ${data.channel} yet.`));
  } else {
    for (const m of data.messages) box.appendChild(el("div", "stream-line", m));
  }
  box.scrollTop = box.scrollHeight;
}

function sendChat() {
  const input = $("#chat-text");
  const text = input.value.trim();
  if (!text || !state.selected) return;
  post("/api/message", { nick: state.selected, text })
    .then((r) => { input.value = ""; toast(`Sent to ${r.channel}`); refreshChat(); })
    .catch((e) => toast(e.message, true));
}

function appendStreamLine(box, raw) {
  let rec;
  try { rec = JSON.parse(raw); } catch (_) { rec = null; }
  const line = el("div", "stream-line");
  if (rec && state.kind === "audit") {
    line.appendChild(el("span", "ts", (rec.ts || "") + "  "));
    if (rec.text) line.appendChild(document.createTextNode(rec.text));
    if (rec.tool_uses && rec.tool_uses.length) {
      const tools = rec.tool_uses.map((t) => t.name).join(", ");
      line.appendChild(el("div", "tools", "→ " + tools));
    }
  } else if (rec && state.kind === "daemon-log") {
    line.appendChild(el("span", "ts", (rec.ts || "") + "  "));
    line.appendChild(el("span", "action", rec.action || "?"));
    const detail = rec.detail ? " " + Object.entries(rec.detail).map(([k, v]) => `${k}=${v}`).join(" ") : "";
    if (detail) line.appendChild(document.createTextNode(detail));
  } else {
    line.textContent = raw;
  }
  box.appendChild(line);
  box.scrollTop = box.scrollHeight;
}

// ---- Pending approvals -----------------------------------------------------

async function refreshPending() {
  let data;
  try { data = await api("/api/pending"); } catch (_) { return; }
  const list = $("#pending-list");
  list.replaceChildren();
  const badge = $("#pending-badge");
  if (!data.pending.length) {
    list.appendChild(el("div", "empty", "Nothing waiting."));
    badge.classList.add("hidden");
    return;
  }
  badge.textContent = data.pending.length + " pending";
  badge.classList.remove("hidden");
  for (const p of data.pending) {
    const item = el("li", "pending-item");
    item.appendChild(el("div", "ptool", p.tool_name || "?"));
    item.appendChild(el("div", "pworker", p.helper_nick || ""));
    item.appendChild(el("div", "pinput", inputPreview(p)));
    const actions = el("div", "pending-actions");
    const ok = el("button", "btn btn-sm btn-ok", "Approve");
    ok.onclick = () => decide("approve", p.id, { id: p.id });
    const okAlways = el("button", "btn btn-sm btn-ok", "Always");
    okAlways.onclick = () => decide("approve", p.id, { id: p.id, always: true });
    const no = el("button", "btn btn-sm btn-danger", "Deny");
    no.onclick = () => {
      const reason = prompt("Deny reason (optional):") || "";
      decide("deny", p.id, { id: p.id, reason });
    };
    actions.appendChild(ok);
    actions.appendChild(okAlways);
    actions.appendChild(no);
    item.appendChild(actions);
    list.appendChild(item);
  }
}

function inputPreview(p) {
  const inp = p.input || {};
  if (p.tool_name === "Bash") return inp.command || "";
  if (p.tool_name === "Edit" || p.tool_name === "Write") return inp.file_path || "";
  try { return JSON.stringify(inp); } catch (_) { return ""; }
}

async function decide(kind, id, body) {
  try {
    await post("/api/" + kind, body);
    toast(`${kind} ${id}`);
    refreshPending();
    refreshAgents();
  } catch (e) { toast(e.message, true); }
}

// ---- Emergency controls ----------------------------------------------------

$("#btn-stop-pause").onclick = async () => {
  if (!confirm("Pause EVERY running agent?")) return;
  try { const r = await post("/api/stop-all", { mode: "pause" }); toast(`Paused ${(r.paused||[]).length} agent(s)`); refreshAgents(); }
  catch (e) { toast(e.message, true); }
};

$("#btn-stop-kill").onclick = async () => {
  if (!confirm("EMERGENCY STOP — kill every agent (including the boss)?")) return;
  try { await post("/api/stop-all", { mode: "kill" }); toast("Stopped all agents"); refreshAgents(); }
  catch (e) { toast(e.message, true); }
};

// ---- Stream tabs -----------------------------------------------------------

document.querySelectorAll(".tab").forEach((tab) => {
  tab.onclick = () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    state.kind = tab.dataset.kind;
    openStream();
  };
});

// ---- Chat input ------------------------------------------------------------

$("#chat-send").onclick = sendChat;
$("#chat-text").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });

// ---- Boot ------------------------------------------------------------------

refreshAgents();
refreshPending();
setInterval(refreshAgents, 2500);
setInterval(refreshPending, 2000);
