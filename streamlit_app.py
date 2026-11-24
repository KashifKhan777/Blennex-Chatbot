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
# the shared chat engine (which reads os.environ) finds them.
try:
    for _key in ("GROQ_API_KEY", "BLENNEX_CONTACT", "GROQ_MODEL"):
        if _key in st.secrets and not os.environ.get(_key):
            os.environ[_key] = str(st.secrets[_key])
except Exception:
    pass  # no secrets file locally: fall back to real environment variables

from chatbot import MAX_INPUT_CHARS, respond  # noqa: E402  (needs the env set first)
from prompts import EXAMPLE_QUESTIONS, WELCOME_MESSAGE  # noqa: E402

st.set_page_config(page_title="Blennex Design · Brand Assistant", page_icon="📦", layout="centered")

st.markdown(
    """
    <style>
      .bx-header { text-align:center; padding: 0.5rem 0 0.25rem; }
      .bx-header h1 { font-weight:600; letter-spacing:0.05em; margin-bottom:0.1rem; font-size:2rem; }
      .bx-header p { opacity:0.7; margin-top:0; }
      .bx-note { text-align:center; opacity:0.6; font-size:0.8rem; }
      #MainMenu, footer { visibility:hidden; }
    </style>
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
    cols = st.columns(2)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if cols[i % 2].button(q, key=f"ex{i}", use_container_width=True):
            pending = q

# Replay the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"], avatar="🟫" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

typed = st.chat_input("Ask about your brand, packaging, or how Blennex works…", max_chars=MAX_INPUT_CHARS)
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
