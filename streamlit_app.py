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
                os.environ[target] = val
                break


_load_secrets()

from chatbot import MAX_INPUT_CHARS, respond  # noqa: E402  (needs the env set first)
from prompts import EXAMPLE_QUESTIONS, WELCOME_MESSAGE  # noqa: E402

st.set_page_config(page_title="Blennex Design · Brand Assistant", page_icon="📦", layout="centered")

# Widget mode (?widget=1): compact layout for the floating chat panel on the
# Blennex website. The panel itself shows the brand header, so we hide ours.
WIDGET = st.query_params.get("widget") == "1"

if WIDGET:
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
          [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer { display:none !important; }
          .block-container { padding: 0.75rem 0.9rem 4.5rem !important; max-width: 100% !important; }
          [data-testid="stChatMessage"] { padding: 0.35rem 0; gap: 0.5rem; }
          [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li { font-size: 0.92rem; line-height: 1.5; }
          .stButton button { font-size: 0.85rem; padding: 0.35rem 0.7rem; min-height: 0; text-align: left; justify-content: flex-start; }
          [data-testid="stBottomBlockContainer"] { padding: 0.5rem 0.75rem 0.75rem !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <style>
      .bx-header { text-align:center; padding: 0.5rem 0 0.25rem; }
      .bx-header h1 { font-weight:600; letter-spacing:0.05em; margin-bottom:0.1rem; font-size:2rem; }
      .bx-header p { opacity:0.7; margin-top:0; }
      .bx-note { text-align:center; opacity:0.6; font-size:0.8rem; }
      #MainMenu, footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)
if not WIDGET:
    st.markdown(
        """
        <div class="bx-header">
          <h1>BLENNEX DESIGN</h1>
          <p>Brand identity · Packaging &amp; labels · 3D product visualization</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Conversation memory lives in the browser session: one history per visitor.
if "history" not in st.session_state:
    st.session_state.history = []

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

# Welcome message + clickable example questions on an empty chat
pending = None
if not st.session_state.history:
    with st.chat_message("assistant", avatar="🟫"):
        st.markdown(WELCOME_MESSAGE)
    # Narrow panel: one column, fewer suggestions. Full page: two columns.
    questions = EXAMPLE_QUESTIONS[:4] if WIDGET else EXAMPLE_QUESTIONS
    cols = st.columns(1 if WIDGET else 2)
    for i, q in enumerate(questions):
        if cols[i % len(cols)].button(q, key=f"ex{i}", use_container_width=True):
            pending = q

# Replay the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"], avatar="🟫" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

typed = st.chat_input("Ask about your brand or packaging…" if WIDGET else "Ask about your brand, packaging, or how Blennex works…", max_chars=MAX_INPUT_CHARS)
user_msg = typed or pending

if user_msg:
    with st.chat_message("user"):
        st.markdown(user_msg)
    with st.chat_message("assistant", avatar="🟫"):
        box = st.empty()
        reply = ""
        for reply in respond(user_msg, st.session_state.history):  # streams progressively longer text
            box.markdown(reply + " ▌")
        box.markdown(reply)
    st.session_state.history += [
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": reply},
    ]
    if pending:
        st.rerun()  # hide the example buttons once the chat has started
