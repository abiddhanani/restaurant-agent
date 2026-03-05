/**
 * Restaurant Agent Widget
 * Drop-in embeddable chat widget.
 * Usage: <script src="widget.js" data-api-key="YOUR_KEY" data-endpoint="https://your-agent.com"></script>
 */
(function() {
  const script = document.currentScript;
  const apiKey = script.getAttribute('data-api-key');
  const endpoint = script.getAttribute('data-endpoint') || 'http://localhost:8000';
  let sessionId = null;

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #ra-widget-btn {
      position: fixed; bottom: 24px; right: 24px;
      width: 56px; height: 56px; border-radius: 50%;
      background: #000; color: #fff; font-size: 24px;
      border: none; cursor: pointer; z-index: 9999;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    #ra-widget-window {
      display: none; position: fixed;
      bottom: 96px; right: 24px;
      width: 360px; height: 500px;
      background: #fff; border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.2);
      z-index: 9998; flex-direction: column;
      font-family: system-ui, sans-serif;
    }
    #ra-widget-window.open { display: flex; }
    #ra-header {
      padding: 16px; background: #000; color: #fff;
      border-radius: 16px 16px 0 0; font-weight: 600;
    }
    #ra-messages {
      flex: 1; overflow-y: auto; padding: 16px;
      display: flex; flex-direction: column; gap: 8px;
    }
    .ra-msg { padding: 10px 14px; border-radius: 12px; max-width: 80%; font-size: 14px; }
    .ra-msg.user { background: #000; color: #fff; align-self: flex-end; }
    .ra-msg.assistant { background: #f0f0f0; align-self: flex-start; }
    #ra-input-row {
      display: flex; padding: 12px; gap: 8px;
      border-top: 1px solid #eee;
    }
    #ra-input {
      flex: 1; padding: 8px 12px; border: 1px solid #ddd;
      border-radius: 20px; outline: none; font-size: 14px;
    }
    #ra-send {
      padding: 8px 16px; background: #000; color: #fff;
      border: none; border-radius: 20px; cursor: pointer; font-size: 14px;
    }
  `;
  document.head.appendChild(style);

  // Build DOM
  const btn = document.createElement('button');
  btn.id = 'ra-widget-btn';
  btn.textContent = '🍽️';

  const win = document.createElement('div');
  win.id = 'ra-widget-window';
  win.innerHTML = `
    <div id="ra-header">What can I help you find?</div>
    <div id="ra-messages"></div>
    <div id="ra-input-row">
      <input id="ra-input" placeholder="Ask about dishes..." />
      <button id="ra-send">Send</button>
    </div>
  `;

  document.body.appendChild(btn);
  document.body.appendChild(win);

  btn.onclick = () => win.classList.toggle('open');

  async function sendMessage(text) {
    addMessage('user', text);
    const res = await fetch(`${endpoint}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
    const data = await res.json();
    sessionId = data.session_id;
    addMessage('assistant', data.response);
  }

  function addMessage(role, content) {
    const msgs = document.getElementById('ra-messages');
    const div = document.createElement('div');
    div.className = `ra-msg ${role}`;
    div.textContent = content;
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
  }

  document.getElementById('ra-send').onclick = () => {
    const input = document.getElementById('ra-input');
    if (input.value.trim()) { sendMessage(input.value.trim()); input.value = ''; }
  };

  document.getElementById('ra-input').onkeydown = (e) => {
    if (e.key === 'Enter') document.getElementById('ra-send').click();
  };
})();
