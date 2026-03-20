/**
 * Restaurant Agent Chat Widget
 * Embeddable via: <script src="/static/widget.js" data-tenant-id="demo" data-restaurant-name="My Restaurant" data-theme-color="#e85d26"></script>
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Config — read from script tag data attributes
  // ---------------------------------------------------------------------------
  const scriptTag =
    document.currentScript ||
    (function () {
      const scripts = document.querySelectorAll("script[data-tenant-id]");
      return scripts[scripts.length - 1];
    })();

  const CONFIG = {
    tenantId: scriptTag ? scriptTag.getAttribute("data-tenant-id") || "demo" : "demo",
    restaurantName: scriptTag
      ? scriptTag.getAttribute("data-restaurant-name") || "Restaurant"
      : "Restaurant",
    themeColor: scriptTag
      ? scriptTag.getAttribute("data-theme-color") || "#e85d26"
      : "#e85d26",
    apiBase: scriptTag ? scriptTag.getAttribute("data-api-base") || "" : "",
  };

  // ---------------------------------------------------------------------------
  // Session — persisted in sessionStorage
  // ---------------------------------------------------------------------------
  const SESSION_KEY = "ra_widget_session_" + CONFIG.tenantId;

  function getSessionId() {
    let sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid) {
      sid = "ws-" + Math.random().toString(36).slice(2, 11) + "-" + Date.now();
      sessionStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
  }

  // ---------------------------------------------------------------------------
  // Styles — injected into <head>
  // ---------------------------------------------------------------------------
  function injectStyles() {
    const css = `
      #ra-widget-btn {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        background: ${CONFIG.themeColor};
        color: #fff;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        transition: transform 0.2s;
      }
      #ra-widget-btn:hover { transform: scale(1.08); }

      #ra-widget-panel {
        position: fixed;
        bottom: 92px;
        right: 24px;
        width: 360px;
        max-width: calc(100vw - 48px);
        height: 520px;
        max-height: calc(100vh - 120px);
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        z-index: 99998;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 14px;
      }
      #ra-widget-panel.ra-hidden { display: none !important; }

      #ra-widget-header {
        background: ${CONFIG.themeColor};
        color: #fff;
        padding: 14px 16px;
        font-weight: 600;
        font-size: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-shrink: 0;
      }
      #ra-widget-header span { opacity: 0.85; font-size: 12px; font-weight: 400; }
      #ra-widget-close {
        background: transparent;
        border: none;
        color: #fff;
        font-size: 20px;
        cursor: pointer;
        padding: 0 4px;
        line-height: 1;
      }

      #ra-widget-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .ra-msg {
        max-width: 80%;
        padding: 10px 13px;
        border-radius: 12px;
        line-height: 1.45;
        word-wrap: break-word;
      }
      .ra-msg-user {
        align-self: flex-end;
        background: ${CONFIG.themeColor};
        color: #fff;
        border-bottom-right-radius: 4px;
      }
      .ra-msg-agent {
        align-self: flex-start;
        background: #f1f1f1;
        color: #222;
        border-bottom-left-radius: 4px;
      }
      .ra-msg-typing {
        align-self: flex-start;
        background: #f1f1f1;
        color: #888;
        font-style: italic;
        border-bottom-left-radius: 4px;
        padding: 10px 13px;
        border-radius: 12px;
      }

      #ra-widget-input-row {
        display: flex;
        padding: 10px 12px;
        gap: 8px;
        border-top: 1px solid #eee;
        flex-shrink: 0;
      }
      #ra-widget-input {
        flex: 1;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        outline: none;
        resize: none;
        font-family: inherit;
        line-height: 1.4;
      }
      #ra-widget-input:focus { border-color: ${CONFIG.themeColor}; }
      #ra-widget-send {
        background: ${CONFIG.themeColor};
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 14px;
        cursor: pointer;
        flex-shrink: 0;
        font-weight: 600;
      }
      #ra-widget-send:disabled { opacity: 0.5; cursor: not-allowed; }

      @media (max-width: 480px) {
        #ra-widget-panel {
          bottom: 0;
          right: 0;
          width: 100vw;
          max-width: 100vw;
          height: 100dvh;
          max-height: 100dvh;
          border-radius: 0;
        }
        #ra-widget-btn { bottom: 16px; right: 16px; }
      }
    `;
    const style = document.createElement("style");
    style.id = "ra-widget-styles";
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ---------------------------------------------------------------------------
  // DOM — build widget markup
  // ---------------------------------------------------------------------------
  function buildWidget() {
    // Floating button
    const btn = document.createElement("button");
    btn.id = "ra-widget-btn";
    btn.setAttribute("aria-label", "Open chat");
    btn.innerHTML =
      '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

    // Panel
    const panel = document.createElement("div");
    panel.id = "ra-widget-panel";
    panel.classList.add("ra-hidden");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", CONFIG.restaurantName + " chat");

    panel.innerHTML = `
      <div id="ra-widget-header">
        <div>
          <div>${CONFIG.restaurantName}</div>
          <span>Ask me about our menu!</span>
        </div>
        <button id="ra-widget-close" aria-label="Close chat">&times;</button>
      </div>
      <div id="ra-widget-messages" role="log" aria-live="polite"></div>
      <div id="ra-widget-input-row">
        <textarea
          id="ra-widget-input"
          rows="1"
          placeholder="Ask about dishes, allergies, specials…"
          aria-label="Your message"
        ></textarea>
        <button id="ra-widget-send">Send</button>
      </div>
    `;

    document.body.appendChild(btn);
    document.body.appendChild(panel);
    return { btn, panel };
  }

  // ---------------------------------------------------------------------------
  // Chat logic
  // ---------------------------------------------------------------------------
  function appendMessage(container, text, role) {
    const div = document.createElement("div");
    div.className = "ra-msg ra-msg-" + role;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showTyping(container) {
    const div = document.createElement("div");
    div.className = "ra-msg-typing";
    div.id = "ra-widget-typing";
    div.textContent = "Typing…";
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function removeTyping() {
    const el = document.getElementById("ra-widget-typing");
    if (el) el.remove();
  }

  async function sendMessage(text, sessionId, messagesEl, sendBtn, inputEl) {
    sendBtn.disabled = true;
    appendMessage(messagesEl, text, "user");
    const typing = showTyping(messagesEl);

    try {
      const res = await fetch(CONFIG.apiBase + "/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": CONFIG.tenantId,
        },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });

      removeTyping();

      if (!res.ok) {
        appendMessage(messagesEl, "Sorry, something went wrong. Please try again.", "agent");
        return;
      }

      const data = await res.json();
      const reply = data.response || data.message || "I'm not sure about that.";
      appendMessage(messagesEl, reply, "agent");
    } catch (_err) {
      removeTyping();
      appendMessage(messagesEl, "Unable to reach the restaurant agent. Please check your connection.", "agent");
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------
  function init() {
    injectStyles();
    const { btn, panel } = buildWidget();

    const messagesEl = document.getElementById("ra-widget-messages");
    const inputEl = document.getElementById("ra-widget-input");
    const sendBtn = document.getElementById("ra-widget-send");
    const closeBtn = document.getElementById("ra-widget-close");

    const sessionId = getSessionId();
    let greeted = false;

    function openPanel() {
      panel.classList.remove("ra-hidden");
      btn.setAttribute("aria-expanded", "true");
      inputEl.focus();

      if (!greeted) {
        greeted = true;
        appendMessage(
          messagesEl,
          "Hi! I'm the " + CONFIG.restaurantName + " assistant. Ask me about our menu, specials, or dietary requirements!",
          "agent"
        );
      }
    }

    function closePanel() {
      panel.classList.add("ra-hidden");
      btn.setAttribute("aria-expanded", "false");
      btn.focus();
    }

    btn.addEventListener("click", function () {
      if (panel.classList.contains("ra-hidden")) {
        openPanel();
      } else {
        closePanel();
      }
    });

    closeBtn.addEventListener("click", closePanel);

    // Auto-grow textarea
    inputEl.addEventListener("input", function () {
      this.style.height = "auto";
      this.style.height = Math.min(this.scrollHeight, 100) + "px";
    });

    // Send on Enter (Shift+Enter = newline)
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });

    sendBtn.addEventListener("click", handleSend);

    function handleSend() {
      const text = inputEl.value.trim();
      if (!text || sendBtn.disabled) return;
      inputEl.value = "";
      inputEl.style.height = "auto";
      sendMessage(text, sessionId, messagesEl, sendBtn, inputEl);
    }

    // Close on Escape
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.classList.contains("ra-hidden")) {
        closePanel();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
