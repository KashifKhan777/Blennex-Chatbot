"""Nex: the Blennex Design brand assistant.

A domain-focused chatbot (brand identity, packaging and 3D product
visualization for product-based brands) built on the Groq API and served
with Gradio.

Run locally:
    export GROQ_API_KEY=...
    python app.py
"""

import logging
import os
import time

import gradio as gr
from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Groq,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from prompts import CONTACT, EXAMPLE_QUESTIONS, SYSTEM_PROMPT, WELCOME_MESSAGE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("blennex-bot")

# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------
# Primary model, plus fallbacks used if the primary is rate-limited, down or
# retired (Groq retires models regularly; Llama 3.3 70B was removed in 2026).
# GPT-OSS 120B follows the "stay on topic / don't invent prices" rules most
# reliably of the models Groq offers; the other two are fast backups.
PRIMARY_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
FALLBACK_MODELS = [m for m in ["openai/gpt-oss-20b", "qwen/qwen3.8-27b"] if m != PRIMARY_MODEL]


def model_kwargs(model):
    """Reasoning models think before answering. Keep that short so replies are
    fast and the thinking does not eat into the max_tokens answer budget."""
    if model.startswith("openai/gpt-oss"):
        return {"reasoning_effort": "low"}
    if model.startswith("qwen/"):
        return {"reasoning_format": "hidden"}
    return {}


# TEMPERATURE = 0.4
#   The bot represents a real business, so facts (services, process, values)
#   must stay consistent and it must not "get creative" with prices or claims.
#   0.0 to 0.2 sounds robotic and repeats the same phrasing; above ~0.8 it
#   starts to embellish. 0.4 keeps answers grounded but still conversational.
TEMPERATURE = 0.4

# MAX_TOKENS = 600
#   The system prompt asks for answers of about 250 words (~350 tokens).
#   600 leaves headroom for a detailed answer when the user asks for one
#   (for example "walk me through your full process") without cutting it off
#   mid-sentence, while capping cost and latency and stopping runaway output.
MAX_TOKENS = 600

# Memory: keep the last N user/assistant exchanges. Older turns are dropped so
# the prompt stays well within Groq's free-tier tokens-per-minute limits.
MAX_HISTORY_TURNS = 8

MAX_INPUT_CHARS = 2000
REQUEST_TIMEOUT_S = 30
MAX_RETRIES = 3
RATE_LIMIT_WAIT_S = 12

_client = None


def get_client():
    """Create the Groq client lazily so the UI still loads if the key is missing."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            return None
        # max_retries=0: we do our own retry/backoff below so we control the messaging.
        _client = Groq(api_key=api_key, timeout=REQUEST_TIMEOUT_S, max_retries=0)
    return _client


# ---------------------------------------------------------------------------
# Conversation memory
# ---------------------------------------------------------------------------
def _content_to_text(content):
    """Gradio messages can hold a string or a list of content parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict) and content.get("type") == "text":
        return content.get("text", "")
    return ""


def build_messages(message, history):
    """System prompt + the last MAX_HISTORY_TURNS exchanges + the new message."""
    past = []
    for item in history or []:
        if isinstance(item, dict):
            role, text = item.get("role"), _content_to_text(item.get("content"))
            if role in ("user", "assistant") and text.strip():
                past.append({"role": role, "content": text})
        elif isinstance(item, (list, tuple)) and len(item) == 2:  # legacy [user, bot] pairs
            user_text, bot_text = item
            if user_text:
                past.append({"role": "user", "content": _content_to_text(user_text)})
            if bot_text:
                past.append({"role": "assistant", "content": _content_to_text(bot_text)})

    past = past[-MAX_HISTORY_TURNS * 2:]
    # The API expects the conversation to start with a user turn after the system prompt.
    while past and past[0]["role"] != "user":
        past.pop(0)

    return [{"role": "system", "content": SYSTEM_PROMPT}, *past, {"role": "user", "content": message}]


# ---------------------------------------------------------------------------
# Chat handler with graceful failure handling
# ---------------------------------------------------------------------------
FRIENDLY_ERRORS = {
    "no_key": (
        "The assistant isn't configured yet (missing API key). "
        f"In the meantime, you can reach the Blennex team via {CONTACT}."
    ),
    "auth": (
        "I can't connect to my language service right now (authentication problem). "
        f"Please reach the Blennex team directly via {CONTACT}."
    ),
    "rate": "I'm getting a lot of questions right now. Please wait a few seconds and send your message again.",
    "network": "I'm having trouble reaching my language service. Please try again in a moment.",
    "unknown": (
        "Something went wrong on my side. Please try again, or contact the Blennex team "
        f"via {CONTACT}."
    ),
}


def respond(message, history):
    """Stream a reply. Yields progressively longer strings for Gradio."""
    message = (message or "").strip()
    if not message:
        yield "Please type a question about your brand, packaging, or Blennex Design."
        return
    if len(message) > MAX_INPUT_CHARS:
        yield (f"That message is a bit long for me ({len(message)} characters). "
               f"Could you shorten it to under {MAX_INPUT_CHARS} characters?")
        return

    client = get_client()
    if client is None:
        log.error("GROQ_API_KEY is not set")
        yield FRIENDLY_ERRORS["no_key"]
        return

    messages = build_messages(message, history)
    models = [PRIMARY_MODEL, *FALLBACK_MODELS]
    model_idx = 0
    transient_failures = 0
    waited_for_rate_limit = False
    error_key = "unknown"

    while transient_failures < MAX_RETRIES:
        if model_idx >= len(models):
            # Every model is rate-limited (Groq free tier: tokens per minute).
            # Quotas refill within seconds, so wait once and start over.
            if error_key == "rate" and not waited_for_rate_limit:
                waited_for_rate_limit = True
                yield "_Lots of questions right now. One moment…_"
                time.sleep(RATE_LIMIT_WAIT_S)
                model_idx = 0
                continue
            break
        model = models[model_idx]
        partial = ""
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=True,
                **model_kwargs(model),
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    partial += delta
                    yield partial
            if partial:
                return
            log.warning("Empty response from %s", model)
            error_key = "unknown"
            model_idx += 1
        except (AuthenticationError, PermissionDeniedError) as e:
            log.error("Auth error: %s", e)
            yield FRIENDLY_ERRORS["auth"]
            return
        except (NotFoundError, BadRequestError) as e:
            # Usually a retired/unknown model name: move to the next model.
            log.warning("Model %s rejected the request (%s); trying fallback", model, e)
            model_idx += 1
            error_key = "unknown"
            continue
        except RateLimitError as e:
            log.warning("Rate limited on %s: %s", model, e)
            error_key = "rate"
            # Different models have separate quotas on Groq, so try the next one.
            model_idx += 1
            time.sleep(1)
            continue
        except (APIConnectionError, APITimeoutError, InternalServerError) as e:
            transient_failures += 1
            log.warning("Transient error on %s (attempt %d): %s", model, transient_failures, e)
            error_key = "network"
            if partial:
                # Stream broke mid-answer: keep what the user already saw.
                yield partial + "\n\n_(The connection dropped. Please ask again if you'd like the rest.)_"
                return
            time.sleep(min(2 ** transient_failures, 8))
            continue
        except Exception as e:  # never crash the UI
            log.exception("Unexpected error: %s", e)
            error_key = "unknown"
            break

    yield FRIENDLY_ERRORS[error_key]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
CSS = """
.gradio-container { max-width: 860px !important; margin: 0 auto !important; }
#bx-header { text-align: center; padding: 8px 0 0; }
#bx-header h1 { font-weight: 600; letter-spacing: 0.04em; margin-bottom: 4px; }
#bx-header p { opacity: 0.75; margin-top: 0; }
footer { display: none !important; }
"""

THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.stone,
    neutral_hue=gr.themes.colors.stone,
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
)

with gr.Blocks(title="Blennex Design · Brand Assistant") as demo:
    gr.HTML(
        "<div id='bx-header'><h1>BLENNEX DESIGN</h1>"
        "<p>Brand identity · Packaging &amp; labels · 3D product visualization</p></div>"
    )
    gr.ChatInterface(
        fn=respond,
        chatbot=gr.Chatbot(
            height=520,
            placeholder=WELCOME_MESSAGE,
            show_label=False,
        ),
        textbox=gr.Textbox(
            placeholder="Ask about your brand, packaging, or how Blennex works…",
            max_length=MAX_INPUT_CHARS,
            submit_btn=True,
        ),
        examples=EXAMPLE_QUESTIONS,
        run_examples_on_click=True,
        cache_examples=False,
        fill_height=True,
        concurrency_limit=8,
    )
    gr.Markdown(
        "<center><small>Nex is an AI assistant and can make mistakes. "
        "For quotes and project details, please contact the Blennex team.</small></center>"
    )


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=8).launch(
        theme=THEME,
        css=CSS,
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.environ.get("PORT", os.environ.get("GRADIO_SERVER_PORT", 7860))),
        share=os.environ.get("GRADIO_SHARE", "").lower() == "true",
    )
