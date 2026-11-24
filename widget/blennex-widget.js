/*!
 * Blennex Design: floating chat widget for "Nex", the brand assistant.
 *
 * Add ONE line before </body> on your website:
 *
 *   <script src="https://cdn.jsdelivr.net/gh/KashifKhan777/Blennex-Chatbot@main/widget/blennex-widget.js"
 *           data-url="https://blennex-chatbot.streamlit.app" defer></script>
 *
 * Optional attributes on the same <script> tag:
 *   data-url       your Streamlit app link (required)
 *   data-color     button / header color          (default #2a2622)
 *   data-accent    small accent color             (default #c9a97a)
 *   data-greeting  text in the little bubble       ("" to turn it off)
 *   data-position  "right" or "left"              (default right)
 *   data-delay     seconds before the bubble shows (default 4)
 */
(function () {
  "use strict";
  if (window.__blennexWidget) return; // never load twice
  window.__blennexWidget = true;

  var script = document.currentScript || document.querySelector("script[data-url][src*='blennex-widget']");
  var cfg = function (name, fallback) {
    var v = script && script.getAttribute("data-" + name);
    return v === null || v === undefined ? fallback : v;
  };

  var APP_URL = String(cfg("url", "https://blennex-chatbot.streamlit.app")).replace(/\/+$/, "");
  var COLOR = cfg("color", "#2a2622");
  var ACCENT = cfg("accent", "#c9a97a");
  var GREETING = cfg("greeting", "Hi! Questions about your brand or packaging? Ask Nex.");
  var SIDE = cfg("position", "right") === "left" ? "left" : "right";
  var DELAY = parseFloat(cfg("delay", "4")) * 1000;
  var IFRAME_SRC = APP_URL + "/?embed=true&widget=1";

  var store = {
    get: function (k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) {} }
  };

  var ICON_CHAT =
    '<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M12 3C6.5 3 2 6.9 2 11.6c0 2.3 1.1 4.4 2.9 6L4 21.4c-.1.4.3.7.7.5l4.2-2c1 .3 2 .4 3.1.4 5.5 0 10-3.9 10-8.7S17.5 3 12 3Zm-4.5 10a1.4 1.4 0 1 1 0-2.8 1.4 1.4 0 0 1 0 2.8Zm4.5 0a1.4 1.4 0 1 1 0-2.8 1.4 1.4 0 0 1 0 2.8Zm4.5 0a1.4 1.4 0 1 1 0-2.8 1.4 1.4 0 0 1 0 2.8Z"/></svg>';
  var ICON_CLOSE =
    '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" d="M6 6l12 12M18 6 6 18"/></svg>';
  var ICON_RESTART =
    '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5"/></svg>';

  var css = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}",
    ".launcher{position:fixed;bottom:22px;" + SIDE + ":22px;width:60px;height:60px;border-radius:50%;border:0;cursor:pointer;",
    "  background:" + COLOR + ";color:#fff;display:flex;align-items:center;justify-content:center;",
    "  box-shadow:0 8px 24px rgba(0,0,0,.28);transition:transform .2s ease,box-shadow .2s ease;z-index:2147483000}",
    ".launcher:hover{transform:scale(1.06);box-shadow:0 10px 28px rgba(0,0,0,.34)}",
    ".launcher:focus-visible,.hbtn:focus-visible,.bubble-x:focus-visible{outline:3px solid " + ACCENT + ";outline-offset:2px}",
    ".launcher .dot{position:absolute;top:3px;" + SIDE + ":3px;width:13px;height:13px;border-radius:50%;background:" + ACCENT + ";border:2px solid #fff}",
    ".launcher.open .dot{display:none}",
    ".bubble{position:fixed;bottom:94px;" + SIDE + ":22px;max-width:250px;background:#fff;color:#2a2622;border-radius:14px;",
    "  padding:12px 32px 12px 14px;font-size:14px;line-height:1.45;box-shadow:0 8px 28px rgba(0,0,0,.18);cursor:pointer;",
    "  opacity:0;transform:translateY(8px);transition:opacity .25s ease,transform .25s ease;pointer-events:none;z-index:2147483000}",
    ".bubble.show{opacity:1;transform:none;pointer-events:auto}",
    ".bubble b{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#8a7a68;margin-bottom:2px}",
    ".bubble-x{position:absolute;top:6px;right:6px;width:22px;height:22px;border:0;border-radius:50%;background:transparent;color:#8a7a68;cursor:pointer;font-size:16px;line-height:1}",
    ".bubble-x:hover{background:#f1efeb}",
    ".panel{position:fixed;bottom:94px;" + SIDE + ":22px;width:380px;height:600px;max-height:calc(100vh - 120px);",
    "  background:#faf9f7;border-radius:16px;overflow:hidden;display:flex;flex-direction:column;",
    "  box-shadow:0 16px 48px rgba(0,0,0,.28);opacity:0;transform:translateY(14px) scale(.98);transform-origin:bottom " + SIDE + ";",
    "  transition:opacity .22s ease,transform .22s ease;pointer-events:none;visibility:hidden;z-index:2147483001}",
    ".panel.open{opacity:1;transform:none;pointer-events:auto;visibility:visible}",
    ".head{background:" + COLOR + ";color:#fff;padding:14px 12px 14px 16px;display:flex;align-items:center;gap:12px;flex:none}",
    ".avatar{width:38px;height:38px;border-radius:50%;background:" + ACCENT + ";color:" + COLOR + ";display:flex;align-items:center;justify-content:center;font-weight:700;font-size:17px;flex:none}",
    ".titles{flex:1;min-width:0}",
    ".title{font-weight:600;font-size:15px;letter-spacing:.01em}",
    ".sub{font-size:12px;opacity:.75;margin-top:2px;display:flex;align-items:center;gap:6px}",
    ".sub i{width:7px;height:7px;border-radius:50%;background:#6fcf8e;display:inline-block}",
    ".hbtn{width:34px;height:34px;border:0;border-radius:50%;background:transparent;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;opacity:.85}",
    ".hbtn:hover{background:rgba(255,255,255,.12);opacity:1}",
    ".body{position:relative;flex:1;background:#faf9f7}",
    ".body iframe{position:absolute;inset:0;width:100%;height:100%;border:0;background:#faf9f7}",
    ".loading{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;",
    "  color:#6b5b4b;font-size:14px;text-align:center;padding:24px;background:#faf9f7;transition:opacity .3s ease}",
    ".loading.hide{opacity:0;pointer-events:none}",
    ".spinner{width:30px;height:30px;border-radius:50%;border:3px solid #e6e1da;border-top-color:" + COLOR + ";animation:spin .9s linear infinite}",
    ".loading small{color:#9b8f82;font-size:12px}",
    "@keyframes spin{to{transform:rotate(360deg)}}",
    ".foot{flex:none;font-size:11px;color:#9b8f82;text-align:center;padding:6px 10px 8px;background:#faf9f7;border-top:1px solid #eee9e2}",
    "@media (max-width:480px){",
    "  .panel{left:0;right:0;bottom:0;top:0;width:100%;height:100%;max-height:none;border-radius:0}",
    "  .launcher.open{display:none}",
    "  .bubble{bottom:92px;max-width:calc(100vw - 110px)}",
    "}",
    "@media (prefers-reduced-motion:reduce){.launcher,.bubble,.panel{transition:none}.spinner{animation-duration:2.5s}}"
  ].join("\n");

  var host = document.createElement("div");
  host.id = "blennex-chat-widget";
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;

  root.innerHTML =
    "<style>" + css + "</style>" +
    '<div class="bubble" role="status" aria-live="polite"><b>Blennex Design</b><span class="msg"></span>' +
    '  <button class="bubble-x" aria-label="Dismiss">&times;</button></div>' +
    '<section class="panel" role="dialog" aria-modal="false" aria-label="Chat with Nex, the Blennex Design brand assistant">' +
    '  <header class="head">' +
    '    <div class="avatar" aria-hidden="true">N</div>' +
    '    <div class="titles"><div class="title">Nex · Blennex Design</div>' +
    '      <div class="sub"><i></i>Online · brand assistant</div></div>' +
    '    <button class="hbtn restart" title="Start a new conversation" aria-label="Start a new conversation">' + ICON_RESTART + "</button>" +
    '    <button class="hbtn close" title="Close chat" aria-label="Close chat">' + ICON_CLOSE + "</button>" +
    "  </header>" +
    '  <div class="body"><div class="loading"><div class="spinner"></div><div>Connecting you to Nex…</div>' +
    "    <small>If the assistant has been idle, waking it up can take up to 30 seconds.</small></div></div>" +
    '  <div class="foot">AI assistant · can make mistakes</div>' +
    "</section>" +
    '<button class="launcher" aria-label="Open chat with Nex" aria-expanded="false"><span class="ico">' + ICON_CHAT + '</span><span class="dot"></span></button>';

  var $ = function (sel) { return root.querySelector(sel); };
  var launcher = $(".launcher"), panel = $(".panel"), body = $(".body"), loading = $(".loading");
  var bubble = $(".bubble"), iframe = null, isOpen = false;

  $(".msg").textContent = GREETING;

  function loadIframe() {
    loading.classList.remove("hide");
    if (iframe) iframe.remove();
    iframe = document.createElement("iframe");
    iframe.title = "Nex, Blennex Design brand assistant";
    iframe.allow = "clipboard-write";
    iframe.addEventListener("load", function () {
      // Streamlit needs a moment after "load" to render its first frame.
      setTimeout(function () { loading.classList.add("hide"); }, 900);
    });
    iframe.src = IFRAME_SRC;
    body.appendChild(iframe);
  }

  function hideBubble(remember) {
    bubble.classList.remove("show");
    if (remember) store.set("bx-bubble-dismissed", "1");
  }

  function setOpen(open) {
    isOpen = open;
    panel.classList.toggle("open", open);
    launcher.classList.toggle("open", open);
    launcher.setAttribute("aria-expanded", String(open));
    launcher.setAttribute("aria-label", open ? "Close chat" : "Open chat with Nex");
    $(".ico").innerHTML = open ? ICON_CLOSE : ICON_CHAT;
    if (open) {
      hideBubble(true);
      if (!iframe) loadIframe(); // lazy: the app only loads when someone opens the chat
    }
  }

  launcher.addEventListener("click", function () { setOpen(!isOpen); });
  $(".close").addEventListener("click", function () { setOpen(false); launcher.focus(); });
  $(".restart").addEventListener("click", loadIframe); // fresh page = fresh conversation
  bubble.addEventListener("click", function (e) {
    if (e.target.closest(".bubble-x")) { hideBubble(true); return; }
    setOpen(true);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen) { setOpen(false); launcher.focus(); }
  });

  // Warm the app up in the background shortly after page load, so it's
  // usually awake by the time a visitor opens the chat.
  function warmUp() {
    try { fetch(APP_URL + "/", { mode: "no-cors", cache: "no-store" }).catch(function () {}); } catch (e) {}
  }

  function mount() {
    document.body.appendChild(host);
    if (GREETING && !store.get("bx-bubble-dismissed")) {
      setTimeout(function () { if (!isOpen) bubble.classList.add("show"); }, DELAY);
    }
    setTimeout(warmUp, 1500);
  }

  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);

  // Tiny public API, e.g. a "Chat with us" link: onclick="BlennexChat.open()"
  window.BlennexChat = {
    open: function () { setOpen(true); },
    close: function () { setOpen(false); }
  };
})();
