"""Nex: the Blennex Design brand assistant (Gradio front-end).

Run locally:
    export GROQ_API_KEY=...
    python app.py
"""

import os

import gradio as gr

from chatbot import MAX_INPUT_CHARS, respond
from prompts import EXAMPLE_QUESTIONS, WELCOME_MESSAGE


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
