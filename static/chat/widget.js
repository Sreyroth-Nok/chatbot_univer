/*
 * University AI Chatbot – website chat widget (US-07).
 *
 * Add to any page:
 *   <script src="https://YOUR-SERVER/static/chat/widget.js"
 *           data-api="https://YOUR-SERVER" data-title="University AI Chatbot" defer></script>
 * The university website's address must be listed in CORS_ALLOWED_ORIGINS.
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var API = ((script && script.dataset.api) || "").replace(/\/$/, "");
  var TITLE = (script && script.dataset.title) || "University AI Chatbot";

  var TEXT = {
    welcome: "សួស្តី! Hello! Ask me about courses, fees, schedules or services. / សូមសួរខ្ញុំអំពីមុខវិជ្ជា ថ្លៃសិក្សា កាលវិភាគ ឬសេវាកម្ម។",
    placeholder: "Type your question… / វាយសំណួររបស់អ្នក…",
    error: "Sorry, something went wrong. Please try again. / សូមអភ័យទោស សូមព្យាយាមម្តងទៀត។",
    helpful: "Helpful?",
    thanks: "Thanks!",
    sources: "Source: "
  };

  function sessionId() {
    var key = "uniChatbotSession";
    try {
      var id = localStorage.getItem(key);
      if (!id) {
        id = "web-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem(key, id);
      }
      return id;
    } catch (e) {
      // Private browsing or blocked storage: keep one id for this page view
      if (!window.__uniChatbotSession) {
        window.__uniChatbotSession = "web-" + Math.random().toString(36).slice(2);
      }
      return window.__uniChatbotSession;
    }
  }

  var css = [
    ".ucb-btn{position:fixed;right:20px;bottom:20px;width:60px;height:60px;border-radius:50%;border:none;",
    "background:#1f4e78;color:#fff;font-size:26px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25);z-index:2147483000}",
    ".ucb-panel{position:fixed;right:20px;bottom:92px;width:min(370px,calc(100vw - 24px));height:min(540px,calc(100vh - 120px));",
    "background:#fff;color:#1d1d1f;border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,.25);display:none;flex-direction:column;",
    "overflow:hidden;z-index:2147483000;font-family:'Noto Sans Khmer','Khmer OS',system-ui,-apple-system,'Segoe UI',Arial,sans-serif;font-size:14px}",
    ".ucb-panel.open{display:flex}",
    ".ucb-head{background:#1f4e78;color:#fff;padding:12px 14px;font-weight:600;display:flex;justify-content:space-between;align-items:center}",
    ".ucb-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1}",
    ".ucb-msgs{flex:1;overflow-y:auto;padding:12px;background:#f4f6f9;display:flex;flex-direction:column;gap:8px}",
    ".ucb-msg{max-width:85%;padding:9px 12px;border-radius:12px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word}",
    ".ucb-bot{background:#fff;align-self:flex-start;border:1px solid #e3e6ea}",
    ".ucb-user{background:#1f4e78;color:#fff;align-self:flex-end}",
    ".ucb-meta{font-size:12px;color:#6b7280;margin-top:6px}",
    ".ucb-rate{margin-top:6px;font-size:12px;color:#6b7280;display:flex;gap:6px;align-items:center}",
    ".ucb-rate button{border:1px solid #d0d5dc;background:#fff;border-radius:6px;cursor:pointer;padding:2px 8px;font-size:14px}",
    ".ucb-form{display:flex;border-top:1px solid #e3e6ea;background:#fff}",
    ".ucb-input{flex:1;border:none;padding:12px;font:inherit;outline:none;min-width:0;background:transparent;color:inherit}",
    ".ucb-send{border:none;background:#1f4e78;color:#fff;padding:0 16px;cursor:pointer;font-weight:600}",
    ".ucb-send:disabled{opacity:.5;cursor:default}",
    "@media (max-width:480px){.ucb-panel{right:12px;bottom:84px}.ucb-btn{right:12px;bottom:12px}}"
  ].join("");

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text; // textContent: never inject HTML
    return node;
  }

  function init() {
    var style = el("style");
    style.textContent = css;
    document.head.appendChild(style);

    var button = el("button", "ucb-btn", "💬");
    button.setAttribute("aria-label", "Open chat");
    var panel = el("div", "ucb-panel");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", TITLE);

    var head = el("div", "ucb-head");
    head.appendChild(el("span", "", TITLE));
    var close = el("button", "ucb-close", "×");
    close.setAttribute("aria-label", "Close chat");
    head.appendChild(close);

    var msgs = el("div", "ucb-msgs");
    msgs.setAttribute("aria-live", "polite");
    var form = el("form", "ucb-form");
    var input = el("input", "ucb-input");
    input.placeholder = TEXT.placeholder;
    input.maxLength = 1000;
    var send = el("button", "ucb-send", "Send");
    send.type = "submit";
    form.appendChild(input);
    form.appendChild(send);

    panel.appendChild(head);
    panel.appendChild(msgs);
    panel.appendChild(form);
    document.body.appendChild(panel);
    document.body.appendChild(button);

    function addMessage(text, who) {
      var m = el("div", "ucb-msg " + (who === "user" ? "ucb-user" : "ucb-bot"), text);
      msgs.appendChild(m);
      msgs.scrollTop = msgs.scrollHeight;
      return m;
    }

    function addRating(msgNode, logId) {
      var row = el("div", "ucb-rate", TEXT.helpful);
      [["👍", 1], ["👎", -1]].forEach(function (pair) {
        var b = el("button", "", pair[0]);
        b.type = "button";
        b.onclick = function () {
          fetch(API + "/api/chat/" + logId + "/feedback/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rating: pair[1], session_id: sessionId() })
          }).catch(function () {});
          row.textContent = TEXT.thanks;
        };
        row.appendChild(b);
      });
      msgNode.appendChild(row);
    }

    addMessage(TEXT.welcome, "bot");

    function toggle(open) {
      panel.classList.toggle("open", open);
      if (open) input.focus();
    }
    button.onclick = function () { toggle(!panel.classList.contains("open")); };
    close.onclick = function () { toggle(false); };

    form.onsubmit = function (e) {
      e.preventDefault();
      var text = input.value.trim();
      if (!text) return;
      addMessage(text, "user");
      input.value = "";
      send.disabled = true;
      var typing = addMessage("…", "bot");

      fetch(API + "/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId() })
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          typing.remove();
          if (!res.ok) { addMessage(res.data.error || TEXT.error, "bot"); return; }
          var d = res.data;
          var m = addMessage(d.answer, "bot");
          if (d.sources && d.sources.length) {
            m.appendChild(el("div", "ucb-meta", TEXT.sources + d.sources.map(function (s) { return s.title; }).join(", ")));
          }
          if (!d.escalated) addRating(m, d.log_id);
        })
        .catch(function () { typing.remove(); addMessage(TEXT.error, "bot"); })
        .finally(function () { send.disabled = false; input.focus(); });
    };
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
