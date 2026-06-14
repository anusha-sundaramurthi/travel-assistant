/**
 * Bot Studio Widget
 * Embed: <script src="https://yourapp.onrender.com/static/widget.js"
 *           data-bot-id="bot_abc123"
 *           data-api-key="ak_xyz789"></script>
 */
(function () {
  // ── Read embed attributes ──────────────────────────────
  const scriptTag = document.currentScript ||
    [...document.querySelectorAll('script[data-bot-id]')].pop();

  const BOT_ID  = scriptTag?.getAttribute('data-bot-id');
  const API_KEY = scriptTag?.getAttribute('data-api-key');
  const BASE    = (() => {
    const src = scriptTag?.src || '';
    return src.replace('/static/widget.js', '');
  })();

  if (!BOT_ID || !API_KEY) {
    console.error('[BotWidget] Missing data-bot-id or data-api-key');
    return;
  }

  // ── State ──────────────────────────────────────────────
  const SESSION_ID     = 'ws_' + Math.random().toString(36).slice(2, 10);
  let   isOpen         = false;
  let   isLoading      = false;
  let   pendingGeneral = null;
  let   botConfig      = null;

  // ── Styles ─────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    #bw-fab {
      position:fixed;bottom:24px;right:24px;width:56px;height:56px;
      border-radius:50%;border:none;cursor:pointer;
      box-shadow:0 4px 20px rgba(0,0,0,.35);
      display:flex;align-items:center;justify-content:center;
      font-size:24px;z-index:9998;transition:transform .2s;
    }
    #bw-fab:hover { transform:scale(1.08); }

    #bw-panel {
      position:fixed;bottom:92px;right:24px;
      width:360px;height:520px;max-height:80vh;
      background:#0d1117;border-radius:16px;
      box-shadow:0 8px 40px rgba(0,0,0,.5);
      display:flex;flex-direction:column;
      z-index:9999;overflow:hidden;
      font-family:'Segoe UI',system-ui,sans-serif;
      transition:opacity .2s, transform .2s;
      opacity:0;transform:translateY(12px) scale(.97);pointer-events:none;
    }
    #bw-panel.open { opacity:1;transform:translateY(0) scale(1);pointer-events:all; }

    #bw-header {
      display:flex;align-items:center;gap:10px;
      padding:14px 16px;flex-shrink:0;
    }
    #bw-avatar {
      width:36px;height:36px;border-radius:50%;
      background:rgba(255,255,255,.15);
      display:flex;align-items:center;justify-content:center;font-size:18px;
    }
    #bw-title { font-weight:700;font-size:15px;color:#e6edf3;flex:1; }
    #bw-close {
      background:transparent;border:none;color:rgba(255,255,255,.6);
      cursor:pointer;font-size:18px;padding:4px;border-radius:6px;
    }
    #bw-close:hover { background:rgba(255,255,255,.1); }

    #bw-messages {
      flex:1;overflow-y:auto;padding:12px 14px;
      display:flex;flex-direction:column;gap:10px;
      scroll-behavior:smooth;
    }
    #bw-messages::-webkit-scrollbar { width:4px; }
    #bw-messages::-webkit-scrollbar-thumb { background:#30363d;border-radius:2px; }

    .bw-msg { display:flex;gap:8px;align-items:flex-start; }
    .bw-msg.user { flex-direction:row-reverse; }

    .bw-av {
      width:28px;height:28px;border-radius:50%;flex-shrink:0;
      display:flex;align-items:center;justify-content:center;font-size:13px;
    }
    .bw-av.bot  { background:rgba(255,255,255,.1); }
    .bw-av.user { background:rgba(255,255,255,.15); }

    .bw-bubble {
      max-width:80%;padding:9px 13px;border-radius:14px;
      font-size:13px;line-height:1.65;white-space:pre-wrap;
    }
    .bw-bubble.bot  { background:#1c2128;color:#e6edf3;border-top-left-radius:4px; }
    .bw-bubble.user { color:#fff;border-top-right-radius:4px; }
    .bw-bubble.error { background:#3a1a1a;color:#ff7b72; }
    .bw-rewrite { font-size:11px;color:#8b949e;margin-top:5px;font-style:italic; }
    .bw-general-note { font-size:11px;margin-top:5px;opacity:.75; }

    .bw-typing { display:flex;align-items:center;gap:4px;padding:10px 13px; }
    .bw-typing span {
      width:6px;height:6px;border-radius:50%;background:#8b949e;
      animation:bwbounce 1s infinite;
    }
    .bw-typing span:nth-child(2){animation-delay:.15s;}
    .bw-typing span:nth-child(3){animation-delay:.3s;}
    @keyframes bwbounce {
      0%,80%,100%{transform:translateY(0);opacity:.5;}
      40%{transform:translateY(-5px);opacity:1;}
    }

    #bw-input-bar {
      padding:10px 12px;border-top:1px solid #21262d;
      display:flex;gap:8px;align-items:flex-end;flex-shrink:0;
    }
    #bw-input {
      flex:1;background:#161b22;border:1px solid #30363d;
      color:#e6edf3;border-radius:10px;padding:8px 12px;
      font-size:13px;font-family:inherit;resize:none;
      outline:none;max-height:100px;line-height:1.5;
    }
    #bw-input:focus { border-color:#1f6feb; }
    #bw-send {
      width:36px;height:36px;border-radius:9px;border:none;
      cursor:pointer;font-size:16px;flex-shrink:0;
      display:flex;align-items:center;justify-content:center;
      transition:opacity .15s;
    }
    #bw-send:disabled { opacity:.4;cursor:default; }

    #bw-powered {
      text-align:center;font-size:10px;color:#484f58;
      padding:6px;flex-shrink:0;
    }

    @media(max-width:420px){
      #bw-panel{width:calc(100vw - 24px);right:12px;bottom:84px;}
      #bw-fab{right:12px;bottom:12px;}
    }
  `;
  document.head.appendChild(style);

  // ── Create elements ────────────────────────────────────
  const fab   = document.createElement('button');
  fab.id      = 'bw-fab';
  fab.title   = 'Chat';
  fab.textContent = '💬';

  const panel = document.createElement('div');
  panel.id    = 'bw-panel';
  panel.innerHTML = `
    <div id="bw-header">
      <div id="bw-avatar">🤖</div>
      <div id="bw-title">AI Assistant</div>
      <button id="bw-close" title="Close">✕</button>
    </div>
    <div id="bw-messages"></div>
    <div id="bw-input-bar">
      <textarea id="bw-input" rows="1" placeholder="Ask me anything…"></textarea>
      <button id="bw-send">➤</button>
    </div>
    <div id="bw-powered">Powered by Bot Studio</div>
  `;

  document.body.appendChild(fab);
  document.body.appendChild(panel);

  // ── Load bot config ────────────────────────────────────
  async function loadConfig() {
    try {
      const res  = await fetch(`${BASE}/widget/config/${BOT_ID}?api_key=${API_KEY}`);
      const data = await res.json();

      if (data.error) {
        showSystemMsg('⚠️ ' + data.error);
        return;
      }

      botConfig = data;
      document.getElementById('bw-title').textContent = data.name;
      fab.style.background    = data.primary_color;
      document.getElementById('bw-send').style.background = data.primary_color;

      // Welcome message
      appendMsg('bot', data.welcome_message);
    } catch (e) {
      showSystemMsg('⚠️ Could not connect to assistant.');
    }
  }

  // ── Toggle panel ───────────────────────────────────────
  fab.addEventListener('click', () => {
    isOpen = !isOpen;
    panel.classList.toggle('open', isOpen);
    fab.textContent = isOpen ? '✕' : '💬';
    if (isOpen) {
      scrollBottom();
      document.getElementById('bw-input').focus();
    }
  });

  document.getElementById('bw-close').addEventListener('click', () => {
    isOpen = false;
    panel.classList.remove('open');
    fab.textContent = '💬';
  });

  // ── Input ──────────────────────────────────────────────
  const inputEl = document.getElementById('bw-input');
  const sendBtn = document.getElementById('bw-send');

  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
  inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 100) + 'px';
  });
  sendBtn.addEventListener('click', send);

  // ── Send ───────────────────────────────────────────────
  async function send() {
    const text = inputEl.value.trim();
    if (!text || isLoading) return;

    inputEl.value = '';
    inputEl.style.height = 'auto';
    appendMsg('user', text);

    // Pending yes/no for general knowledge
    if (pendingGeneral !== null) {
      const orig = pendingGeneral;
      pendingGeneral = null;
      const YES = ['yes','yeah','sure','ok','okay','yep','y','please',
                   'ஆம்','ஆமா','சரி','हाँ','हां','جي','نعم','oui','ja','sí'];
      if (YES.some(w => text.toLowerCase().includes(w))) {
        await askBackend(orig, true);
      } else {
        appendMsg('bot', 'No problem! You can upload a PDF guide for this topic and I\'ll answer from it. 📄');
      }
      return;
    }

    await askBackend(text, false);
  }

  async function askBackend(query, useGeneral) {
    isLoading = true;
    sendBtn.disabled = true;
    showTyping();

    try {
      const res = await fetch(`${BASE}/widget/ask`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          bot_id:      BOT_ID,
          api_key:     API_KEY,
          query:       query,
          session_id:  SESSION_ID,
          use_general: useGeneral,
          language:    'English'
        })
      });

      const data = await res.json();
      hideTyping();

      if (data.error) {
        appendMsg('bot', '⚠️ ' + data.error, true);
        return;
      }

      if (data.response === null) {
        pendingGeneral = query;
        appendMsg('bot',
          "I don't have PDF information for this topic.\n\n" +
          "Would you like me to answer from general knowledge? *(yes / no)*"
        );
      } else {
        appendMsg('bot', data.response, false,
          data.rewritten_query !== query ? data.rewritten_query : null,
          !data.has_pdf_context
        );
      }
    } catch {
      hideTyping();
      appendMsg('bot', '⚠️ Connection error. Please try again.', true);
    } finally {
      isLoading = false;
      sendBtn.disabled = false;
    }
  }

  // ── Render messages ────────────────────────────────────
  function appendMsg(role, text, isError=false, rewritten=null, isGeneral=false) {
    const msgs = document.getElementById('bw-messages');
    const row  = document.createElement('div');
    row.className = 'bw-msg ' + role;

    const av = document.createElement('div');
    av.className = 'bw-av ' + (role==='bot'?'bot':'user');
    av.textContent = role === 'bot' ? '🤖' : '🧑';

    const bubble = document.createElement('div');
    bubble.className = 'bw-bubble ' + (isError ? 'error' : role);
    bubble.style.background = (role==='user' && !isError)
      ? (botConfig?.primary_color || '#1f6feb') : '';
    bubble.innerHTML = renderMarkdown(text);

    if (rewritten) {
      const hint = document.createElement('div');
      hint.className = 'bw-rewrite';
      hint.textContent = '🔍 Searched as: "' + rewritten + '"';
      bubble.appendChild(hint);
    }
    if (isGeneral) {
      const note = document.createElement('div');
      note.className = 'bw-general-note';
      note.textContent = 'ℹ️ From general knowledge';
      bubble.appendChild(note);
    }

    if (role === 'user') { row.appendChild(bubble); row.appendChild(av); }
    else                  { row.appendChild(av); row.appendChild(bubble); }

    msgs.appendChild(row);
    scrollBottom();
  }

  function showSystemMsg(txt) {
    const msgs = document.getElementById('bw-messages');
    const el   = document.createElement('div');
    el.style.cssText = 'text-align:center;font-size:12px;color:#8b949e;padding:8px';
    el.textContent = txt;
    msgs.appendChild(el);
  }

  let typingEl = null;
  function showTyping() {
    const msgs = document.getElementById('bw-messages');
    typingEl   = document.createElement('div');
    typingEl.className = 'bw-msg';
    typingEl.innerHTML = `
      <div class="bw-av bot">🤖</div>
      <div class="bw-bubble bot bw-typing"><span></span><span></span><span></span></div>`;
    msgs.appendChild(typingEl);
    scrollBottom();
  }
  function hideTyping() {
    if (typingEl) { typingEl.remove(); typingEl = null; }
  }

  function scrollBottom() {
    const msgs = document.getElementById('bw-messages');
    msgs.scrollTop = msgs.scrollHeight;
  }

  function renderMarkdown(text) {
    return text
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
      .replace(/\*(.+?)\*/g,'<em>$1</em>')
      .replace(/\n/g,'<br>');
  }

  // ── Init ───────────────────────────────────────────────
  loadConfig();

})();