/*!
 * Blennex Design: floating chat widget for "Nex", the brand assistant.
 *
 * Add ONE line before </body> on your website:
 *
 *   <script src="/blennex-widget.js" data-url="https://blennex-chatbot-kashifkhan.streamlit.app"
 *           data-default-theme="dark" defer></script>
 *
 * Optional attributes on the same <script> tag:
 *   data-url            your Streamlit app link (required)
 *   data-default-theme  "dark" or "light": theme when <html> has no data-theme (default light)
 *   data-greeting       text in the small bubble ("" turns it off)
 *   data-position       "right" or "left" (default right)
 *   data-delay          seconds before the bubble shows (default 4)
 *   data-crop           px hidden at the bottom of the app to keep Streamlit's
 *                       "Built with Streamlit" bar out of view (default 36, 0 = off)
 *
 * The panel can be resized by dragging its free edge or corner, or toggled
 * wide with the expand button. Size is remembered per visitor.
 * Open it from your own buttons with: onclick="BlennexChat.open()"
 */
(function () {
  "use strict";
  if (window.__blennexWidget) return;
  window.__blennexWidget = true;

  var script = document.currentScript || document.querySelector("script[src*='blennex-widget']");
  var cfg = function (name, fallback) {
    var v = script && script.getAttribute("data-" + name);
    return v === null || v === undefined ? fallback : v;
  };

  var APP_URL = String(cfg("url", "https://blennex-chatbot-kashifkhan.streamlit.app")).replace(/\/+$/, "");
  var DEFAULT_THEME = cfg("default-theme", "light") === "dark" ? "dark" : "light";
  var GREETING = cfg("greeting", "Questions about your brand or packaging? Ask Nex.");
  var SIDE = cfg("position", "right") === "left" ? "left" : "right";
  var OTHER = SIDE === "right" ? "left" : "right";
  var DELAY = parseFloat(cfg("delay", "4")) * 1000;
  var CROP = Math.max(0, parseInt(cfg("crop", "36"), 10) || 0);

  // Panel size limits (px)
  var MIN_W = 340, MIN_H = 440, COMPACT = { w: 400, h: 640 }, WIDE_W = 720;
  var GAP = 22; // distance from the screen edge

  // Blennex website palette, so the panel matches the site in both themes
  var PALETTES = {
    dark:  { bg: "#131211", surface: "#1C1A19", raised: "#242120", fg: "#EEEAE4", muted: "#A9A39B",
             line: "#34302D", accent: "#D3A6AA", onfg: "#131211", shadow: "rgba(0,0,0,.55)" },
    light: { bg: "#F5F3EF", surface: "#FFFFFF", raised: "#ECE8E2", fg: "#151412", muted: "#5D5953",
             line: "#DCD7CF", accent: "#8C5F63", onfg: "#EEEAE4", shadow: "rgba(21,20,18,.22)" }
  };

  var store = {
    get: function (k, s) { try { return (s ? sessionStorage : localStorage).getItem(k); } catch (e) { return null; } },
    set: function (k, v, s) { try { (s ? sessionStorage : localStorage).setItem(k, v); } catch (e) {} }
  };

  function siteTheme() {
    var t = document.documentElement.getAttribute("data-theme");
    return t === "dark" || t === "light" ? t : DEFAULT_THEME;
  }

  var I = {
    chat: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" d="M20 12.2c0 4-3.6 7.3-8 7.3-1.1 0-2.2-.2-3.1-.6L4.5 20l1.2-3.4A6.9 6.9 0 0 1 4 12.2C4 8.1 7.6 4.9 12 4.9s8 3.2 8 7.3Z"/></svg>',
    close: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" d="M6 6l12 12M18 6 6 18"/></svg>',
    restart: '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M4 12a8 8 0 1 0 2.4-5.7M4 4v4.5h4.5"/></svg>',
    expand: '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>',
    shrink: '<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" d="M20 10h-6V4M4 14h6v6M14 10l7-7M10 14l-7 7"/></svg>'
  };

  var EASE = "cubic-bezier(.16,1,.3,1)";
  var css = [
    ":host{all:initial}",
    "*{box-sizing:border-box;font-family:Inter,'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}",
    "button{font:inherit;color:inherit;background:none;border:0;cursor:pointer;padding:0}",
    ":focus-visible{outline:2px solid var(--accent);outline-offset:2px}",

    /* launcher: a pill like the site's buttons */
    ".launcher{position:fixed;bottom:" + GAP + "px;" + SIDE + ":" + GAP + "px;z-index:2147483000;height:52px;padding:0 22px 0 18px;",
    "  display:inline-flex;align-items:center;gap:10px;border-radius:999px;background:var(--fg);color:var(--onfg);",
    "  font-size:15px;font-weight:500;letter-spacing:-.006em;box-shadow:0 10px 30px var(--shadow);",
    "  transition:background .3s,color .3s,transform .4s " + EASE + ",opacity .3s,box-shadow .3s}",
    ".launcher:hover{background:var(--accent);color:#151412;transform:translateY(-2px)}",
    ".launcher .dot{width:7px;height:7px;border-radius:50%;background:var(--accent);transition:background .3s}",
    ".launcher:hover .dot{background:#151412}",
    ".launcher.hidden{opacity:0;transform:translateY(12px) scale(.96);pointer-events:none}",

    /* greeting bubble */
    ".bubble{position:fixed;bottom:" + (GAP + 64) + "px;" + SIDE + ":" + GAP + "px;z-index:2147483000;max-width:270px;",
    "  background:var(--surface);color:var(--fg);border-radius:16px;padding:14px 38px 14px 16px;font-size:14px;line-height:1.5;",
    "  box-shadow:0 0 0 1px var(--line),0 14px 36px var(--shadow);cursor:pointer;",
    "  opacity:0;transform:translateY(8px);transition:opacity .4s " + EASE + ",transform .5s " + EASE + ";pointer-events:none}",
    ".bubble.show{opacity:1;transform:none;pointer-events:auto}",
    ".bubble b{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:500;letter-spacing:.24em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}",
    ".bubble b::before{content:'';width:6px;height:6px;border-radius:50%;background:var(--accent)}",
    ".bubble-x{position:absolute;top:8px;right:8px;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;color:var(--muted);transition:background .2s,color .2s}",
    ".bubble-x:hover{background:var(--raised);color:var(--fg)}",

    /* panel */
    ".panel{position:fixed;bottom:" + GAP + "px;" + SIDE + ":" + GAP + "px;z-index:2147483001;",
    "  width:var(--w," + COMPACT.w + "px);height:var(--h," + COMPACT.h + "px);",
    "  max-width:calc(100vw - " + GAP * 2 + "px);max-height:calc(100vh - " + GAP * 2 + "px);",
    "  background:var(--bg);color:var(--fg);border-radius:22px;overflow:hidden;display:flex;flex-direction:column;",
    "  box-shadow:0 0 0 1px var(--line),0 24px 70px var(--shadow);",
    "  opacity:0;visibility:hidden;transform:translateY(16px) scale(.97);transform-origin:bottom " + SIDE + ";pointer-events:none;",
    "  transition:opacity .35s " + EASE + ",transform .5s " + EASE + ",visibility 0s linear .5s,width .45s " + EASE + ",height .45s " + EASE + "}",
    ".panel.open{opacity:1;visibility:visible;transform:none;pointer-events:auto;",
    "  transition:opacity .35s " + EASE + ",transform .5s " + EASE + ",visibility 0s,width .45s " + EASE + ",height .45s " + EASE + "}",
    ".panel.dragging{transition:none!important;user-select:none}",
    ".panel.dragging iframe{pointer-events:none}",

    /* header */
    ".head{flex:none;display:flex;align-items:center;gap:12px;padding:14px 12px 14px 20px;border-bottom:1px solid var(--line)}",
    ".mark{width:34px;height:34px;border-radius:50%;background:var(--raised);display:grid;place-items:center;flex:none;position:relative}",
    ".mark svg{width:18px;height:auto;color:var(--fg)}",
    ".mark::after{content:'';position:absolute;right:-1px;bottom:-1px;width:10px;height:10px;border-radius:50%;background:#6FCF8E;box-shadow:0 0 0 2px var(--bg)}",
    ".titles{flex:1;min-width:0;line-height:1.25}",
    ".title{font-size:15px;font-weight:500;letter-spacing:-.01em}",
    ".sub{font-size:12.5px;color:var(--muted);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".hbtn{width:36px;height:36px;border-radius:50%;display:grid;place-items:center;color:var(--muted);transition:background .25s,color .25s}",
    ".hbtn:hover{background:var(--raised);color:var(--fg)}",

    /* body */
    ".body{position:relative;flex:1;overflow:hidden;background:var(--bg)}",
    ".body iframe{position:absolute;top:0;left:0;width:100%;height:calc(100% + " + CROP + "px);border:0;background:var(--bg);",
    "  opacity:0;transition:opacity .5s " + EASE + "}",
    ".body iframe.ready{opacity:1}",
    ".loading{position:absolute;inset:0;padding:26px 22px;display:flex;flex-direction:column;gap:12px;transition:opacity .4s}",
    ".loading.hide{opacity:0;pointer-events:none}",
    ".sk{border-radius:10px;background:linear-gradient(90deg,var(--surface) 0%,var(--raised) 50%,var(--surface) 100%);background-size:200% 100%;animation:sh 1.4s linear infinite}",
    "@keyframes sh{to{background-position:-200% 0}}",
    ".wake{margin-top:auto;font-size:13px;color:var(--muted);opacity:0;transition:opacity .4s}",
    ".wake.show{opacity:1}",
    ".foot{flex:none;font-size:11.5px;color:var(--muted);text-align:center;padding:8px 12px 10px;border-top:1px solid var(--line);letter-spacing:.01em}",

    /* resize handles on the free edges */
    ".rz{position:absolute;z-index:3;touch-action:none}",
    ".rz-x{top:56px;bottom:0;" + OTHER + ":0;width:10px;cursor:ew-resize}",
    ".rz-y{top:0;left:56px;right:56px;height:8px;cursor:ns-resize}",
    ".rz-c{top:0;" + OTHER + ":0;width:18px;height:18px;cursor:" + (SIDE === "right" ? "nwse" : "nesw") + "-resize}",
    ".rz-x::after{content:'';position:absolute;top:50%;" + OTHER + ":3px;width:4px;height:44px;margin-top:-22px;border-radius:4px;background:var(--line);opacity:0;transition:opacity .25s,background .25s}",
    ".panel:hover .rz-x::after{opacity:1}",
    ".rz-x:hover::after,.panel.dragging .rz-x::after{background:var(--accent);opacity:1}",

    /* phones: full screen */
    "@media (max-width:560px){",
    "  .panel{left:0!important;right:0!important;bottom:0;top:0;width:100%!important;height:100%!important;max-width:none;max-height:none;border-radius:0}",
    "  .rz,.hbtn.size{display:none}",
    "  .launcher{bottom:16px;" + SIDE + ":16px}",
    "  .bubble{bottom:80px;" + SIDE + ":16px;max-width:calc(100vw - 32px)}",
    "}",
    "@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}"
  ].join("\n");

  var host = document.createElement("div");
  host.id = "blennex-chat-widget";
  var root = host.attachShadow ? host.attachShadow({ mode: "open" }) : host;
  var BLX_MARK = '<svg viewBox="0 0 266 326" aria-hidden="true"><path fill="currentColor" d="M0 0V326H168C233.2 326 265.6 288 265.6 236.8C265.6 198.4 246 169.6 211.6 156.8V156C236.4 142.4 250.8 117.6 250.8 85.6C250.8 35.6 218.8 0 155.2 0H0ZM141.6 128H80.8V74.8H141.6C165.2 74.8 171.2 86.8 171.2 101.6C171.2 116 163.2 128 141.6 128ZM151.6 251.2H80.8V192.8H151.6C172.4 192.8 183.2 206.4 183.2 222.4C183.2 238.4 175.2 251.2 151.6 251.2Z"/></svg>';

  root.innerHTML =
    "<style>" + css + "</style>" +
    '<div class="bubble" role="status" aria-live="polite"><b>Blennex Design</b><span class="msg"></span>' +
    '<button class="bubble-x" aria-label="Dismiss">' + I.close + "</button></div>" +
    '<section class="panel" role="dialog" aria-label="Chat with Nex, the Blennex Design assistant">' +
    '  <div class="rz rz-x" data-rz="x" aria-hidden="true"></div><div class="rz rz-y" data-rz="y" aria-hidden="true"></div><div class="rz rz-c" data-rz="xy" aria-hidden="true"></div>' +
    '  <header class="head"><div class="mark">' + BLX_MARK + "</div>" +
    '    <div class="titles"><div class="title">Nex</div><div class="sub">Blennex Design</div></div>' +
    '    <button class="hbtn size" title="Expand" aria-label="Expand chat">' + I.expand + "</button>" +
    '    <button class="hbtn restart" title="New conversation" aria-label="Start a new conversation">' + I.restart + "</button>" +
    '    <button class="hbtn close" title="Close" aria-label="Close chat">' + I.close + "</button></header>" +
    '  <div class="body"><div class="loading" aria-label="Loading">' +
    '    <div class="sk" style="width:34%;height:10px"></div><div class="sk" style="width:82%;height:26px;margin-top:6px"></div>' +
    '    <div class="sk" style="width:64%;height:26px"></div><div class="sk" style="width:90%;height:12px;margin-top:8px"></div>' +
    '    <div class="sk" style="width:58%;height:40px;margin-top:18px;border-radius:999px"></div><div class="sk" style="width:72%;height:40px;border-radius:999px"></div>' +
    '    <div class="wake">Waking Nex up. This can take up to 30 seconds after a quiet spell.</div></div></div>' +
    '  <div class="foot">AI assistant · can make mistakes</div>' +
    "</section>" +
    '<button class="launcher" aria-label="Open chat with Nex" aria-expanded="false">' + I.chat + '<span>Ask Nex</span><span class="dot"></span></button>';

  var $ = function (s) { return root.querySelector(s); };
  var launcher = $(".launcher"), panel = $(".panel"), body = $(".body"), loading = $(".loading");
  var bubble = $(".bubble"), sizeBtn = $(".size"), wake = $(".wake");
  var iframe = null, isOpen = false, chatTheme = null, wakeTimer = 0;
  $(".msg").textContent = GREETING;

  /* ---------- theme ---------- */
  function paint(theme) {
    var p = PALETTES[theme];
    for (var k in p) host.style.setProperty("--" + k, p[k]);
  }
  // The launcher and bubble follow the site immediately. The open panel keeps
  // the theme its conversation started with (so a theme switch never wipes a
  // chat); a new conversation picks up the current site theme.
  function syncTheme() { paint(iframe ? chatTheme : siteTheme()); }
  new MutationObserver(syncTheme).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  /* ---------- size ---------- */
  function vw() { return window.innerWidth; }
  function vh() { return window.innerHeight; }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  var size = (function () {
    try { var s = JSON.parse(store.get("bx-chat-size") || "null"); if (s && s.w && s.h) return s; } catch (e) {}
    return { w: COMPACT.w, h: COMPACT.h };
  })();
  function applySize(save) {
    size.w = clamp(size.w, MIN_W, Math.max(MIN_W, vw() - GAP * 2));
    size.h = clamp(size.h, MIN_H, Math.max(MIN_H, vh() - GAP * 2));
    panel.style.setProperty("--w", size.w + "px");
    panel.style.setProperty("--h", size.h + "px");
    var wide = size.w >= WIDE_W - 10;
    sizeBtn.innerHTML = wide ? I.shrink : I.expand;
    sizeBtn.title = wide ? "Make smaller" : "Expand";
    sizeBtn.setAttribute("aria-label", wide ? "Make chat smaller" : "Expand chat");
    if (save) store.set("bx-chat-size", JSON.stringify(size));
  }
  sizeBtn.addEventListener("click", function () {
    if (size.w >= WIDE_W - 10) { size.w = COMPACT.w; size.h = COMPACT.h; }
    else { size.w = WIDE_W; size.h = vh() - GAP * 2; }
    applySize(true);
  });
  window.addEventListener("resize", function () { applySize(false); });

  // drag to resize (pointer events cover mouse, pen and touch)
  root.querySelectorAll(".rz").forEach(function (h) {
    h.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      var mode = h.getAttribute("data-rz"), sx = e.clientX, sy = e.clientY, w0 = size.w, h0 = size.h;
      var dir = SIDE === "right" ? -1 : 1; // dragging away from the anchored side grows the panel
      panel.classList.add("dragging");
      h.setPointerCapture(e.pointerId);
      function move(ev) {
        if (mode.indexOf("x") > -1) size.w = w0 + (ev.clientX - sx) * dir;
        if (mode.indexOf("y") > -1) size.h = h0 - (ev.clientY - sy);
        applySize(false);
      }
      function up() {
        panel.classList.remove("dragging");
        h.removeEventListener("pointermove", move);
        h.removeEventListener("pointerup", up);
        h.removeEventListener("pointercancel", up);
        applySize(true);
      }
      h.addEventListener("pointermove", move);
      h.addEventListener("pointerup", up);
      h.addEventListener("pointercancel", up);
    });
    h.addEventListener("dblclick", function () { size.w = COMPACT.w; size.h = COMPACT.h; applySize(true); });
  });

  /* ---------- chat frame ---------- */
  function loadIframe() {
    chatTheme = siteTheme();
    paint(chatTheme);
    loading.classList.remove("hide");
    wake.classList.remove("show");
    clearTimeout(wakeTimer);
    wakeTimer = setTimeout(function () { wake.classList.add("show"); }, 4000);
    if (iframe) iframe.remove();
    var f = document.createElement("iframe");
    f.title = "Nex, Blennex Design brand assistant";
    f.allow = "clipboard-write";
    f.addEventListener("load", function () {
      // Streamlit needs a moment after "load" to paint its first frame
      setTimeout(function () {
        if (f !== iframe) return;
        f.classList.add("ready");
        loading.classList.add("hide");
        clearTimeout(wakeTimer);
      }, 1100);
    });
    f.src = APP_URL + "/?embed=true&widget=1&theme=" + chatTheme;
    iframe = f;
    body.appendChild(f);
  }

  function hideBubble(remember) {
    bubble.classList.remove("show");
    if (remember) store.set("bx-bubble-dismissed", "1", true);
  }

  function setOpen(open) {
    isOpen = open;
    panel.classList.toggle("open", open);
    launcher.classList.toggle("hidden", open);
    launcher.setAttribute("aria-expanded", String(open));
    if (open) {
      hideBubble(true);
      if (!iframe) loadIframe();
      else paint(chatTheme);
      setTimeout(function () { $(".close").focus({ preventScroll: true }); }, 350);
    } else {
      syncTheme();
    }
  }

  launcher.addEventListener("click", function () { setOpen(true); });
  $(".close").addEventListener("click", function () { setOpen(false); launcher.focus({ preventScroll: true }); });
  $(".restart").addEventListener("click", loadIframe);
  bubble.addEventListener("click", function (e) {
    if (e.target.closest(".bubble-x")) { hideBubble(true); return; }
    setOpen(true);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && isOpen) { setOpen(false); launcher.focus({ preventScroll: true }); }
  });

  // Wake the app in the background so it's usually ready when someone opens the chat.
  function warmUp() {
    try { fetch(APP_URL + "/", { mode: "no-cors", cache: "no-store" }).catch(function () {}); } catch (e) {}
  }

  function mount() {
    paint(siteTheme());
    applySize(false);
    document.body.appendChild(host);
    if (GREETING && !store.get("bx-bubble-dismissed", true)) {
      setTimeout(function () { if (!isOpen) bubble.classList.add("show"); }, DELAY);
    }
    setTimeout(warmUp, 1500);
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);

  window.BlennexChat = {
    open: function () { setOpen(true); },
    close: function () { setOpen(false); }
  };
})();
