"""HookBus Dashboard - Embedded HTML/CSS/JS template."""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HookBus Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #0a0a0a;
  --card: #1a1a1a;
  --card-border: #2a2a2a;
  --green: #00ff88;
  --green-dim: #00cc6a;
  --red: #ff4444;
  --blue: #4488ff;
  --amber: #ffc800;
  --text: #e0e0e0;
  --text-dim: #888;
  --text-bright: #fff;
  --mono: 'JetBrains Mono', 'SF Mono', monospace;
  --sans: 'Inter', -apple-system, sans-serif;
}
html, body { height: 100%; overflow: hidden; }
body { font-family: var(--sans); background: var(--bg); color: var(--text); }

/* HEADER */
.header {
  height: 52px;
  border-bottom: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(10,10,10,0.95);
  backdrop-filter: blur(12px);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-logo {
  font-family: var(--mono);
  font-size: 1rem;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 1.5px;
}
.header-logo span { color: var(--text-dim); font-weight: 400; font-size: 0.75rem; }
.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-dim);
}
.header-status .dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--green);
  animation: pulse-dot 2s ease-in-out infinite;
}
.header-stats {
  display: flex;
  gap: 20px;
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-dim);
}
.header-stats .stat-val { color: var(--text-bright); font-weight: 600; }
.header-stats .stat-label { margin-left: 4px; }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* MAIN LAYOUT */
.main {
  display: grid;
  grid-template-columns: 200px 1fr 240px 320px;
  height: calc(100vh - 52px);
}

/* PUBLISHERS COLUMN */
.col-publishers {
  border-right: 1px solid var(--card-border);
  padding: 16px;
  overflow-y: auto;
}
.col-label {
  font-family: var(--mono);
  font-size: 0.65rem;
  color: var(--text-dim);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.pub-node {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  transition: all 0.3s;
  opacity: 0;
  transform: translateX(-10px);
}
.pub-node.visible {
  opacity: 1;
  transform: translateX(0);
}
.pub-node.dimmed {
  opacity: 0.3;
}
.pub-node.flash-allow { border-color: var(--green); box-shadow: 0 0 12px rgba(0,255,136,0.2); }
.pub-node.flash-deny { border-color: var(--red); box-shadow: 0 0 12px rgba(255,68,68,0.2); }
.pub-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-bright);
}
.pub-meta {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  margin-top: 2px;
}
.pub-empty {
  font-size: 0.75rem;
  color: var(--text-dim);
  font-style: italic;
  padding: 20px 0;
  text-align: center;
}

/* BUS CENTRE */
.col-bus {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.bus-node {
  border: 2px solid var(--green);
  border-radius: 16px;
  padding: 32px 48px;
  text-align: center;
  background: linear-gradient(135deg, rgba(0,255,136,0.12), rgba(0,255,136,0.03));
  box-shadow: 0 0 40px rgba(0,255,136,0.15), 0 0 80px rgba(0,255,136,0.05);
  animation: pulse-glow 3s ease-in-out infinite;
  position: relative;
  z-index: 2;
}
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 40px rgba(0,255,136,0.15), 0 0 80px rgba(0,255,136,0.05); }
  50% { box-shadow: 0 0 60px rgba(0,255,136,0.25), 0 0 120px rgba(0,255,136,0.1); }
}
.bus-title {
  font-family: var(--mono);
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 3px;
}
.bus-subtitle {
  font-size: 0.7rem;
  color: var(--text-dim);
  margin-top: 4px;
  margin-bottom: 12px;
}
.bus-features {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--green-dim);
}

/* Flow lines */
.flow-line-left, .flow-line-right {
  position: absolute;
  top: 50%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--green), transparent);
  z-index: 1;
  opacity: 0.3;
}
.flow-line-left { left: 0; right: 50%; margin-right: 80px; }
.flow-line-right { left: 50%; margin-left: 80px; right: 0; }

.flow-line-left.flash, .flow-line-right.flash {
  opacity: 1;
  height: 3px;
  transition: opacity 0.1s;
}
.flow-line-left.flash-deny, .flow-line-right.flash-deny {
  background: linear-gradient(90deg, transparent, var(--red), transparent);
  opacity: 1;
}

/* SUBSCRIBERS COLUMN */
.col-subscribers {
  border-left: 1px solid var(--card-border);
  border-right: 1px solid var(--card-border);
  padding: 16px;
  overflow-y: auto;
}
.sub-card {
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s;
}
.sub-card.sync { border-left: 3px solid var(--green); }
.sub-card.async { border-left: 3px solid var(--blue); }
.sub-card.flash-allow { box-shadow: 0 0 12px rgba(0,255,136,0.15); }
.sub-card.flash-deny { box-shadow: 0 0 12px rgba(255,68,68,0.15); }

.sub-info { flex: 1; }
.sub-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-bright);
  display: flex;
  align-items: center;
  gap: 6px;
}
.sub-status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block;
}
.sub-status-dot.online { background: var(--green); }
.sub-status-dot.offline { background: var(--red); }
.sub-status-dot.unknown { background: var(--text-dim); }
.sub-type {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  margin-top: 2px;
}

/* Toggle switch */
.toggle {
  position: relative;
  width: 36px;
  height: 20px;
  flex-shrink: 0;
  cursor: pointer;
}
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute;
  inset: 0;
  background: #333;
  border-radius: 10px;
  transition: background 0.2s;
}
.toggle-slider::before {
  content: '';
  position: absolute;
  width: 16px; height: 16px;
  left: 2px; top: 2px;
  background: var(--text-dim);
  border-radius: 50%;
  transition: all 0.2s;
}
.toggle input:checked + .toggle-slider {
  background: rgba(0,255,136,0.3);
}
.toggle input:disabled + .toggle-slider {
  opacity: 0.35;
  cursor: not-allowed;
}
.toggle input:checked + .toggle-slider::before {
  transform: translateX(16px);
  background: var(--green);
}

/* EVENT LOG */
.col-events {
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.events-header {
  padding: 16px 16px 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--card-border);
}
.events-header .col-label { margin-bottom: 0; }
.events-count {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-dim);
}
.events-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.event-row {
  padding: 6px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.02);
  font-size: 0.7rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  animation: slide-in 0.2s ease-out;
}
@keyframes slide-in {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.event-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.event-tool {
  font-family: var(--mono);
  font-weight: 600;
  color: var(--text-bright);
  font-size: 0.7rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.event-cmd {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.event-meta {
  font-family: var(--mono);
  font-size: 0.55rem;
  color: var(--text-dim);
}
.event-badge {
  font-family: var(--mono);
  font-size: 0.6rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  white-space: nowrap;
  align-self: center;
}
.event-badge.allow { background: rgba(0,255,136,0.1); color: var(--green); }
.event-badge.deny { background: rgba(255,68,68,0.1); color: var(--red); }
.event-badge.ask { background: rgba(255,200,0,0.1); color: var(--amber); }
.event-badge.review { background: rgba(68,136,255,0.1); color: var(--blue); }
.event-row { cursor: pointer; transition: background 0.15s; }
.event-row:hover { background: rgba(255,255,255,0.04); }
.event-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 100; align-items: center; justify-content: center; }
.event-modal.show { display: flex; }
.event-modal-box { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; width: 90%; max-width: 600px; max-height: 80vh; overflow: auto; padding: 24px; }
.event-modal-close { float: right; font-size: 1.2rem; color: var(--text-dim); cursor: pointer; background: none; border: none; }
.event-modal-close:hover { color: var(--text-bright); }
.event-modal-title { font-family: var(--mono); font-size: 1rem; font-weight: 700; margin-bottom: 16px; color: var(--text-bright); }
.event-modal-pre { font-family: var(--mono); font-size: 0.75rem; color: var(--text); white-space: pre-wrap; word-break: break-word; }

/* Legend */
.legend {
  padding: 12px 16px;
  border-top: 1px solid var(--card-border);
  display: flex;
  gap: 16px;
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-dim);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.legend-bar {
  width: 12px;
  height: 3px;
  border-radius: 1px;
}
.legend-bar.sync { background: var(--green); }
.legend-bar.async { background: var(--blue); }

/* SSE disconnected banner */
.sse-banner {
  display: none;
  position: fixed;
  top: 52px;
  left: 0;
  right: 0;
  background: rgba(255,68,68,0.15);
  border-bottom: 1px solid var(--red);
  padding: 6px 24px;
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--red);
  text-align: center;
  z-index: 50;
}
.sse-banner.show { display: block; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--card-border); border-radius: 2px; }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="header-logo">HOOKBUS <span>Dashboard</span></div>
    <div class="header-status"><div class="dot" id="sseDot"></div><span id="sseStatus">Connecting...</span></div>
  </div>
  <div class="header-stats">
    <div><span class="stat-val" id="statRate">0</span><span class="stat-label">events/min</span></div>
    <div><span class="stat-val" id="statTotal">0</span><span class="stat-label">total</span></div>
    <div><span class="stat-val" style="color:var(--green)" id="statAllow">0</span><span class="stat-label">allow</span></div>
    <div><span class="stat-val" style="color:var(--red)" id="statDeny">0</span><span class="stat-label">deny</span></div>
    <div><span class="stat-val" id="statUptime">0s</span><span class="stat-label">uptime</span></div>
  </div>
</div>

<div class="sse-banner" id="sseBanner">SSE disconnected. Reconnecting...</div>

<div class="main">
  <!-- PUBLISHERS -->
  <div class="col-publishers">
    <div class="col-label">Publishers</div>
    <div id="publisherList">
      <div class="pub-empty">Waiting for events...</div>
    </div>
  </div>

  <!-- BUS -->
  <div class="col-bus">
    <div class="flow-line-left" id="flowLeft"></div>
    <div class="bus-node">
      <div class="bus-title">HOOKBUS</div>
      <div class="bus-subtitle">Lifecycle Event Bus</div>
      <div class="bus-features">
        <span>Event Routing</span>
        <span>Fan-out</span>
        <span>Deny-wins</span>
        <span>Hot Reload</span>
        <span>Health Checks</span>
      </div>
    </div>
    <div class="flow-line-right" id="flowRight"></div>
  </div>

  <!-- SUBSCRIBERS -->
  <div class="col-subscribers">
    <div class="col-label">Subscribers</div>
    <div id="subscriberList"></div>
    <div class="legend">
      <div class="legend-item"><div class="legend-bar sync"></div> Sync (blocks)</div>
      <div class="legend-item"><div class="legend-bar async"></div> Async (observe)</div>
    </div>
  </div>

  <!-- EVENT LOG -->
  <div class="col-events">
    <div class="events-header">
      <div class="col-label">Event Log</div>
      <div class="events-count" id="eventsCount">0 events</div>
    </div>
    <div class="events-scroll" id="eventsScroll"></div>
  </div>
</div>

<script>
(function() {
  // State
  const publishers = {};
  let eventCount = 0;
  let evtSource = null;

  // --- SSE ---
  function connectSSE() {
    if (evtSource) { try { evtSource.close(); } catch(e) {} }
    evtSource = new EventSource('/api/events/stream');

    evtSource.onopen = function() {
      document.getElementById('sseStatus').textContent = 'Connected';
      document.getElementById('sseDot').style.background = 'var(--green)';
      document.getElementById('sseBanner').classList.remove('show');
    };

    evtSource.onmessage = function(e) {
      try {
        const event = JSON.parse(e.data);
        handleEvent(event);
      } catch(err) {}
    };

    evtSource.onerror = function() {
      document.getElementById('sseStatus').textContent = 'Reconnecting...';
      document.getElementById('sseDot').style.background = 'var(--red)';
      document.getElementById('sseBanner').classList.add('show');
    };
  }

  // --- Handle incoming event ---
  function handleEvent(event) {
    addEventRow(event);
    updatePublisher(event.source || 'Agent', event.decision);
    flashFlow(event.decision);
    flashSubscriber(event.decision);
    eventCount++;
    document.getElementById('eventsCount').textContent = eventCount + ' events';
  }

  // --- Event log ---
  function addEventRow(event) {
    const scroll = document.getElementById('eventsScroll');
    const row = document.createElement('div');
    row.className = 'event-row';

    const decision = (event.decision || '').toLowerCase();
    const badgeClass = decision === 'allow' ? 'allow' :
                       decision === 'deny' ? 'deny' :
                       decision === 'ask' ? 'ask' : 'review';

    const time = event.timestamp ? event.timestamp.split(' ')[1] || event.timestamp.split('T')[1] || '' : '';
    const shortTime = time ? time.substring(0, 8) : '';

    row.innerHTML = `
      <div class="event-main">
        <div class="event-tool">${esc((event.tool_name && event.tool_name !== 'unknown') ? event.tool_name : (event.hook || 'unknown'))}</div>
        <div class="event-cmd">${esc(event.command || '')}</div>
        <div class="event-meta">${esc(event.source || '')} &middot; ${esc(shortTime)} &middot; #${event.id || '?'}</div>
      </div>
      <div class="event-badge ${badgeClass}">${esc(decision || '?')}</div>
    `;
    row.addEventListener('click', function() { showEventDetail(event); });

    scroll.insertBefore(row, scroll.firstChild);

    // Cap at 200 rows
    while (scroll.children.length > 200) {
      scroll.removeChild(scroll.lastChild);
    }
  }

  // --- Publishers ---
  function updatePublisher(name, decision) {
    if (!name) return;
    publishers[name] = { lastSeen: Date.now(), decision: decision };
    renderPublishers();
  }

  function renderPublishers() {
    const container = document.getElementById('publisherList');
    const names = Object.keys(publishers).sort((a, b) => publishers[b].lastSeen - publishers[a].lastSeen);

    if (names.length === 0) {
      container.innerHTML = '<div class="pub-empty">Waiting for events...</div>';
      return;
    }

    const now = Date.now();
    container.innerHTML = names.map(name => {
      const p = publishers[name];
      const age = (now - p.lastSeen) / 1000;
      const dimmed = age > 60 ? ' dimmed' : '';
      const flash = age < 2 ? (p.decision === 'deny' ? ' flash-deny' : ' flash-allow') : '';
      const ago = age < 60 ? Math.round(age) + 's ago' : Math.round(age / 60) + 'm ago';
      return `<div class="pub-node visible${dimmed}${flash}">
        <div class="pub-name">${esc(name)}</div>
        <div class="pub-meta">${ago}</div>
      </div>`;
    }).join('');
  }

  // --- Flash effects ---
  function flashFlow(decision) {
    const left = document.getElementById('flowLeft');
    const right = document.getElementById('flowRight');
    const cls = decision === 'deny' ? 'flash-deny' : 'flash';

    left.classList.add(cls);
    right.classList.add(cls);
    setTimeout(() => {
      left.classList.remove('flash', 'flash-deny');
      right.classList.remove('flash', 'flash-deny');
    }, 400);
  }

  function flashSubscriber(decision) {
    const cards = document.querySelectorAll('.sub-card');
    const cls = decision === 'deny' ? 'flash-deny' : 'flash-allow';
    cards.forEach(card => {
      if (card.querySelector('.sub-status-dot.online')) {
        card.classList.add(cls);
        setTimeout(() => card.classList.remove('flash-allow', 'flash-deny'), 400);
      }
    });
  }

  // --- Subscribers ---
  function loadSubscribers() {
    fetch('/api/subscribers')
      .then(r => r.json())
      .then(data => renderSubscribers(data.subscribers || []))
      .catch(() => {});
  }

  function renderSubscribers(subs) {
    const container = document.getElementById('subscriberList');
    container.innerHTML = subs.map(s => {
      const typeClass = s.type === 'sync' ? 'sync' : 'async';
      const isEnabled = s.enabled !== false;
      const title = 'Enable or disable subscriber routing state';
      const uiLink = s.has_ui && s.ui_port ? `<a href="http://${location.hostname}:${s.ui_port}/" target="_blank" style="font-family:var(--mono);font-size:0.55rem;color:var(--green);margin-top:2px;display:inline-block;">Open UI :${s.ui_port} &#8599;</a>` : '';
      return `<div class="sub-card ${typeClass}" data-name="${esc(s.name)}">
        <div class="sub-info">
          <div class="sub-name">
            <span class="sub-status-dot ${s.status}"></span>
            ${esc(s.label)}
          </div>
          <div class="sub-type">${s.type} &middot; ${s.status} ${uiLink}</div>
        </div>
        <label class="toggle" title="${esc(title)}">
          <input type="checkbox" ${isEnabled ? 'checked' : ''}
                 onchange="window._toggleSub('${esc(s.name)}', this.checked)">
          <span class="toggle-slider"></span>
        </label>
      </div>`;
    }).join('');
  }

  window._toggleSub = function(name, checked) {
    const action = checked ? 'start' : 'stop';
    const input = document.querySelector(`.sub-card[data-name="${CSS.escape(name)}"] input[type="checkbox"]`);
    if (input) input.disabled = true;
    fetch('/api/subscribers/toggle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, action: action})
    })
    .then(r => r.json())
    .then(data => {
      if (!data.ok) {
        alert('Toggle failed: ' + (data.error || 'unknown'));
      }
      // Refresh after a moment
      setTimeout(loadSubscribers, 1000);
    })
    .catch(err => alert('Error: ' + err))
    .finally(() => {
      setTimeout(() => {
        if (input) input.disabled = false;
      }, 1000);
    });
  };

  // --- Stats ---
  function loadStats() {
    fetch('/api/stats')
      .then(r => r.json())
      .then(data => {
        document.getElementById('statRate').textContent = data.events_per_min || 0;
        document.getElementById('statTotal').textContent = data.total || 0;
        document.getElementById('statAllow').textContent = data.allow || 0;
        document.getElementById('statDeny').textContent = data.deny || 0;
        const uptime = data.uptime_seconds || 0;
        if (uptime < 60) document.getElementById('statUptime').textContent = uptime + 's';
        else if (uptime < 3600) document.getElementById('statUptime').textContent = Math.round(uptime / 60) + 'm';
        else document.getElementById('statUptime').textContent = Math.round(uptime / 3600) + 'h';
      })
      .catch(() => {});
  }

  // --- Load initial events ---
  function loadInitialEvents() {
    fetch('/api/events')
      .then(r => r.json())
      .then(data => {
        const events = (data.events || []).reverse();
        events.forEach(e => {
          addEventRow(e);
          if (e.source) {
            publishers[e.source] = { lastSeen: Date.now() - 30000, decision: e.decision };
          }
        });
        eventCount = events.length;
        document.getElementById('eventsCount').textContent = eventCount + ' events';
        renderPublishers();
      })
      .catch(() => {});
  }

  // --- Utility ---
  function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // --- Event detail modal ---
  function showEventDetail(event) {
    document.getElementById('eventModalTitle').textContent = (event.tool_name || event.hook || 'unknown') + ' - ' + (event.decision || '?');
    document.getElementById('eventModalBody').textContent = JSON.stringify(event, null, 2);
    document.getElementById('eventModal').classList.add('show');
  }
  function closeEventDetail() {
    document.getElementById('eventModal').classList.remove('show');
  }
  // Inline `onclick` attributes on the modal HTML run in global scope and
  // can't see IIFE-scoped functions. Expose to window so the X button and
  // backdrop click handlers can reach it.
  window.closeEventDetail = closeEventDetail;

  // --- Init ---
  loadSubscribers();
  loadInitialEvents();
  loadStats();
  connectSSE();

  // Refresh subscribers and stats periodically
  setInterval(loadSubscribers, 5000);
  setInterval(loadStats, 3000);
  // Dim old publishers
  setInterval(renderPublishers, 10000);

})();
</script>

<div class="event-modal" id="eventModal" onclick="if(event.target===this)closeEventDetail()">
  <div class="event-modal-box">
    <button class="event-modal-close" onclick="closeEventDetail()">&times;</button>
    <div class="event-modal-title" id="eventModalTitle">Event Detail</div>
    <pre class="event-modal-pre" id="eventModalBody"></pre>
  </div>
</div>

</body>
</html>"""
