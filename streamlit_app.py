"""Nex: the Blennex Design brand assistant (Streamlit front-end).

Deploy free on Streamlit Community Cloud (share.streamlit.io):
add GROQ_API_KEY under the app's Settings -> Secrets.

Run locally:
    export GROQ_API_KEY=...
    streamlit run streamlit_app.py
"""

import os

import streamlit as st

# Streamlit Cloud keeps keys in st.secrets; copy them into the environment so
# the shared chat engine (which reads os.environ) finds them. Be forgiving
# about how the secret was typed: any capitalisation, a few common names, or
# nested under a [groq] section.
def _load_secrets():
    try:
        flat = {}
        for k, v in st.secrets.items():
            if isinstance(v, (str, int, float)):
                flat[k.strip().upper()] = str(v)
            elif hasattr(v, "items"):  # a [section]
                for k2, v2 in v.items():
                    flat[f"{k.strip().upper()}_{k2.strip().upper()}"] = str(v2)
    except Exception:
        return  # no secrets file locally: fall back to real environment variables
    aliases = {
        "GROQ_API_KEY": ["GROQ_API_KEY", "GROQ_KEY", "GROQ_APIKEY", "GROQ_API_KEY_", "API_KEY", "GROQ_GROQ_API_KEY"],
        "BLENNEX_CONTACT": ["BLENNEX_CONTACT"],
        "GROQ_MODEL": ["GROQ_MODEL"],
    }
    for target, names in aliases.items():
        # Streamlit also copies root-level secrets into os.environ as typed
        # (spaces/quotes included), so always prefer the cleaned value.
        for n in names:
            val = flat.get(n, "").strip().strip('"').strip("'").strip()
            if val:
                if target == "GROQ_API_KEY":
                    # API keys never contain whitespace; drop any spaces, line
                    # breaks or invisible characters picked up while pasting.
                    val = "".join(ch for ch in val if ch.isprintable() and not ch.isspace())
                os.environ[target] = val
                break


_load_secrets()


def _log_key_fingerprint():
    """Log a safe fingerprint of the key (never the key itself) to help debug
    'Invalid API Key' errors from the app logs."""
    import logging

    key = os.environ.get("GROQ_API_KEY", "")
    log = logging.getLogger("blennex-bot")
    if not key:
        log.error("GROQ_API_KEY is not set (add it under Settings -> Secrets)")
        return
    hint = ""
    if not key.startswith("gsk_"):
        hint = (" WARNING: Groq keys start with 'gsk_'. This looks like a different provider's key"
                " (e.g. 'xai-' is Grok/xAI, 'sk-' is OpenAI, 'AIza' is Google) or a placeholder.")
    log.warning("GROQ_API_KEY loaded: %d characters, starts '%s', ends '%s'.%s",
                len(key), key[:4], key[-4:], hint)


if "_bx_key_logged" not in st.session_state:
    st.session_state["_bx_key_logged"] = True
    _log_key_fingerprint()

from chatbot import MAX_INPUT_CHARS, respond  # noqa: E402  (needs the env set first)
from prompts import EXAMPLE_QUESTIONS, WELCOME_MESSAGE  # noqa: E402

st.set_page_config(page_title="Blennex Design · Brand Assistant", page_icon="📦", layout="centered")

# ---------------------------------------------------------------------------
# Look & feel
# ---------------------------------------------------------------------------
# Widget mode (?widget=1) is the compact chat inside the floating panel on the
# Blennex website. ?theme=dark|light matches the site's colour theme.
WIDGET = st.query_params.get("widget") == "1"
THEME = "dark" if st.query_params.get("theme") == "dark" else "light"

# Blennex website palette (public/index.html brand tokens)
PALETTES = {
    "dark": dict(bg="#131211", surface="#1C1A19", fg="#EEEAE4", muted="#A9A39B", line="#34302D",
                 accent="#D3A6AA", on_fg="#131211", user_bg="#262321"),
    "light": dict(bg="#F5F3EF", surface="#FFFFFF", fg="#151412", muted="#5D5953", line="#DCD7CF",
                  accent="#8C5F63", on_fg="#EEEAE4", user_bg="#EAE6DF"),
}
C = PALETTES[THEME]

BASE_CSS = f"""
<style>
:root {{ --bx-bg:{C['bg']}; --bx-surface:{C['surface']}; --bx-fg:{C['fg']}; --bx-muted:{C['muted']};
        --bx-line:{C['line']}; --bx-accent:{C['accent']}; --bx-on-fg:{C['on_fg']}; --bx-user:{C['user_bg']}; }}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stBottom"],
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] {{ background: var(--bx-bg) !important; }}
.stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stApp strong {{ color: var(--bx-fg); }}
.stApp {{ font-family: 'Inter','Helvetica Neue',Helvetica,Arial,sans-serif; letter-spacing:-.006em;
         -webkit-font-smoothing: antialiased; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ display:none !important; }}
a, .stApp a {{ color: var(--bx-accent) !important; text-decoration-thickness: 1px; text-underline-offset: 2px; }}

/* messages: no avatars; assistant = plain text, user = soft bubble on the right */
[data-testid="stChatMessage"] {{ background: transparent !important; padding: 0 !important; gap: 0 !important;
  margin: 0 0 1.1rem 0; animation: bxIn .45s cubic-bezier(.16,1,.3,1) both; }}
[data-testid="stChatMessage"] > div:first-child:not([data-testid="stChatMessageContent"]),
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {{ display:none !important; }}
[data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li {{
  font-size: 15px; line-height: 1.62; color: var(--bx-fg); }}
[data-testid="stChatMessageContent"] p {{ margin-bottom: .55em; }}
[data-testid="stChatMessageContent"] ul, [data-testid="stChatMessageContent"] ol {{ padding-left: 1.15em; margin: .2em 0 .6em; }}
[data-testid="stChatMessageContent"] li {{ margin: .15em 0; }}
[data-testid="stChatMessageContent"] li::marker {{ color: var(--bx-accent); }}
[data-testid="stChatMessageContent"] strong {{ font-weight: 600; }}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {{ justify-content: flex-end; }}
[data-testid="stChatMessageContent"][aria-label="Chat message from user"] {{
  flex: 0 1 auto !important; width: auto !important; max-width: 84%; margin: 0 0 0 auto !important;
  background: var(--bx-user); border-radius: 18px 18px 6px 18px; padding: .6rem .95rem !important; }}
[aria-label="Chat message from user"] * {{ margin-top: 0 !important; margin-bottom: 0 !important; }}
[aria-label="Chat message from user"] [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}

/* suggestion chips, like the "What do you need?" chips on the site */
.stButton > button {{ background: transparent !important; color: var(--bx-fg) !important;
  border: 0 !important; box-shadow: inset 0 0 0 1px var(--bx-line) !important; border-radius: 999px !important;
  min-height: 40px; padding: .45rem 1rem !important; justify-content: flex-start !important; text-align: left;
  font-size: 14px; font-weight: 400; transition: box-shadow .3s, background .3s, color .3s; }}
.stButton > button p {{ font-size: 14px !important; color: inherit !important; line-height: 1.35; }}
.stButton > button, .stButton > button * {{ white-space: normal !important; overflow: visible !important;
  text-overflow: clip !important; height: auto; }}
.stButton > button:hover {{ box-shadow: inset 0 0 0 1px var(--bx-accent) !important; color: var(--bx-fg) !important; }}
.stButton > button:active {{ background: var(--bx-fg) !important; color: var(--bx-on-fg) !important; }}
.stButton > button:focus-visible {{ outline: 2px solid var(--bx-accent) !important; outline-offset: 2px; }}

/* message box */
[data-testid="stChatInput"] {{ background: var(--bx-surface) !important; border: 1px solid var(--bx-line) !important;
  border-radius: 22px !important; box-shadow: none !important; transition: border-color .3s; }}
[data-testid="stChatInput"]:focus-within {{ border-color: var(--bx-accent) !important; }}
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea {{ background: transparent !important; }}
[data-testid="stChatInput"] > div {{ border: 0 !important; box-shadow: none !important; outline: none !important; }}
[data-testid="stChatInput"] textarea {{ color: var(--bx-fg) !important; caret-color: var(--bx-accent); font-size: 15px !important; }}
[data-testid="stChatInput"] textarea::placeholder {{ color: var(--bx-muted) !important; opacity: 1; }}
[data-testid="stChatInputSubmitButton"] {{ background: var(--bx-fg) !important; color: var(--bx-on-fg) !important;
  border-radius: 999px !important; transition: background .3s, opacity .3s; }}
[data-testid="stChatInputSubmitButton"]:hover {{ background: var(--bx-accent) !important; color:#151412 !important; }}
[data-testid="stChatInputSubmitButton"]:disabled {{ opacity: .35; }}
[data-testid="stChatInputSubmitButton"] svg {{ color: inherit !important; fill: currentColor; }}
[data-testid="InputInstructions"] {{ display:none !important; }}

/* empty state */
.bx-hello {{ padding: 0 .1rem .8rem; animation: bxIn .6s cubic-bezier(.16,1,.3,1) both; }}
.bx-eyebrow {{ display:flex; align-items:center; gap:.6em; font-size: 11px; font-weight: 500; letter-spacing: .28em;
  text-transform: uppercase; color: var(--bx-muted); margin-bottom: .8rem; }}
.bx-eyebrow::before {{ content:""; width:6px; height:6px; border-radius:50%; background: var(--bx-accent); }}
.bx-title {{ font-size: 28px; font-weight: 500; letter-spacing: -.045em; line-height: 1.08; margin: 0 0 .6rem;
  color: var(--bx-fg); }}
.bx-title em {{ font-style: italic; font-weight: 300; color: var(--bx-accent); }}
.bx-hello p {{ font-size: 15px; line-height: 1.6; color: var(--bx-muted) !important; margin: 0; max-width: 34ch; }}
.bx-label {{ font-size: 13px; color: var(--bx-muted) !important; margin: .4rem 0 .5rem; }}

/* "thinking" dots while the first words arrive */
.bx-typing {{ display:inline-flex; gap:5px; padding:.5rem 0; }}
.bx-typing i {{ width:6px; height:6px; border-radius:50%; background: var(--bx-muted); animation: bxDot 1.2s infinite ease-in-out; }}
.bx-typing i:nth-child(2) {{ animation-delay: .15s; }} .bx-typing i:nth-child(3) {{ animation-delay: .3s; }}
@keyframes bxDot {{ 0%, 80%, 100% {{ opacity:.25; transform: translateY(0); }} 40% {{ opacity:1; transform: translateY(-3px); }} }}
@keyframes bxIn {{ from {{ opacity:0; transform: translateY(8px); }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}
</style>
"""

WIDGET_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"],
[data-testid="stHeader"], [data-testid="stToolbar"] { display:none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 1.25rem 1.25rem 4.5rem !important; max-width: 100% !important; }
[data-testid="stBottomBlockContainer"] { padding: .5rem 1rem 1rem !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: .5rem; }
.stButton { margin: 0 !important; }
::-webkit-scrollbar { width: 8px; } ::-webkit-scrollbar-thumb { background: var(--bx-line); border-radius: 8px; }
</style>
"""

PAGE_CSS = """
<style>
.bx-header { text-align:center; padding: .5rem 0 1.25rem; }
.bx-header h1 { font-weight:500; letter-spacing:-.045em; margin-bottom:.2rem; font-size:2.4rem; color: var(--bx-fg); }
.bx-header p { color: var(--bx-muted) !important; margin-top:0; }
</style>
"""

st.markdown(BASE_CSS + (WIDGET_CSS if WIDGET else PAGE_CSS), unsafe_allow_html=True)
TYPING = '<span class="bx-typing"><i></i><i></i><i></i></span>'

if not WIDGET:
    st.markdown(
        '<div class="bx-header"><h1>Blennex Design</h1>'
        "<p>Brand identity · Packaging &amp; labels · 3D product visualization</p></div>",
        unsafe_allow_html=True,
    )

# Conversation memory lives in the browser session: one history per visitor.
if "history" not in st.session_state:
    st.session_state.history = []

if not WIDGET:
    with st.sidebar:
        st.markdown("### About Nex")
        st.markdown(
            "Nex is the AI brand assistant for **Blennex Design**: strategic brand systems "
            "for product-based brands in beauty, skincare, haircare and wellness."
        )
        if st.button("Start a new conversation", use_container_width=True):
            st.session_state.history = []
            st.rerun()
        st.caption("Nex is an AI assistant and can make mistakes. For quotes and project details, please contact the Blennex team.")

# Empty state: greeting + suggestion chips
pending = None
was_empty = not st.session_state.history
if was_empty:
    if WIDGET:
        st.markdown(
            '<div class="bx-hello"><div class="bx-eyebrow">Blennex Design</div>'
            "<div class=\"bx-title\">Let's talk about your <em>brand</em>.</div>"
            "<p>Ask about brand identity, packaging and labels, or 3D product visuals.</p></div>"
            '<div class="bx-label">Popular questions</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant"):
            st.markdown(WELCOME_MESSAGE)
    questions = EXAMPLE_QUESTIONS[:3] if WIDGET else EXAMPLE_QUESTIONS
    cols = st.columns(1 if WIDGET else 2)
    for i, q in enumerate(questions):
        if cols[i % len(cols)].button(q, key=f"ex{i}", use_container_width=not WIDGET):
            pending = q

# Replay the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

typed = st.chat_input(
    "Message Nex…" if WIDGET else "Ask about your brand, packaging, or how Blennex works…",
    max_chars=MAX_INPUT_CHARS,
)
user_msg = typed or pending

if user_msg:
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant"):
        box = st.empty()
        box.markdown(TYPING, unsafe_allow_html=True)
        reply = ""
        for reply in respond(user_msg, st.session_state.history):  # streams progressively longer text
            box.markdown(reply + " ▍")
        box.markdown(reply)
    st.session_state.history += [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": reply},
    ]
    if was_empty:
        st.rerun()  # clear the welcome screen and suggestions once the chat has started
