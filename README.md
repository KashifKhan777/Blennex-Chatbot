# Nex: Blennex Design Brand Assistant


A domain-focused chatbot for **Blennex Design**: brand identity, packaging and label
design, and 3D product visualization for product-based brands (beauty, skincare,
haircare, wellness).

- **LLM API:** Groq (`openai/gpt-oss-120b`, with automatic fallback to `gpt-oss-20b` and `qwen3.8-27b`)
- **UI / hosting:** Streamlit on Streamlit Community Cloud (free, no card). A Gradio version (`app.py`) is included for Colab/local use.
- **Behaviour:** defined by the system prompt in `prompts.py` (role, context, knowledge, rules)

## Model configuration

| Parameter | Value | Why |
|---|---|---|
| `temperature` | **0.4** | The bot speaks for a real business. Facts (services, process, values) must stay consistent, and it must not improvise prices or claims. Values near 0 sound robotic and repetitive; above ~0.8 the model starts to embellish. 0.4 is grounded but still conversational. |
| `max_tokens` | **350** | The prompt asks for 2-4 sentences (~40-80 words). 350 covers that, GPT-OSS's brief reasoning tokens, and a longer answer when asked, without cutting off mid-sentence. |
| History | last 6 exchanges | Keeps conversational memory while staying inside Groq free-tier token limits. |
| System prompt | ~905 tokens | Resent every message, so kept compact (was ~1,910). |

## Reliability

- Streams responses token by token.
- Retries network, timeout and server errors with exponential backoff (max 3).
- On rate limits or a retired model, falls back to another Groq model.
- Auth/missing-key errors show a friendly message instead of crashing.
- Empty and over-long inputs (>2000 chars) are rejected politely.

## Run locally

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
streamlit run streamlit_app.py     # Streamlit UI
python app.py                      # or the Gradio UI
```

## Files

| File | Purpose |
|---|---|
| `prompts.py` | System prompt (role, context, Blennex knowledge, rules) |
| `knowledge/Blennex_DNA_Client_Safe.docx` | Client-safe Blennex knowledge document the prompt's facts are condensed from |
| `chatbot.py` | Chat engine: model config, memory, streaming, failure handling |
| `streamlit_app.py` | Streamlit UI (the deployed app) |
| `app.py` | Gradio UI (local / Colab / Render) |
| `widget/blennex-widget.js` | Floating chat button for the website |
| `Blennex_Chatbot_Assignment.ipynb` | Colab notebook walkthrough with test outputs |

## Deploy (Streamlit Community Cloud, free, no card)

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository `KashifKhan777/blennex-chatbot`, branch `main`, main file `streamlit_app.py`.
4. Optionally pick a custom subdomain, e.g. `blennex-chatbot`.
5. **Advanced settings → Secrets**, paste:
   ```toml
   GROQ_API_KEY = "your-groq-key"
   ```
6. Click **Deploy**. The app is live in ~2-3 minutes.

Free apps sleep after several days without visitors; the first visitor then clicks "Yes, get this app back up" and waits ~30 s.

### Add the floating chat button to the Blennex website

Paste this **one line** before `</body>` (or in your site builder's footer / custom-code box).
Replace the `data-url` with your Streamlit app link:

```html
<script src="https://cdn.jsdelivr.net/gh/KashifKhan777/Blennex-Chatbot@main/widget/blennex-widget.js"
        data-url="https://blennex-chatbot-kashifkhan.streamlit.app" defer></script>
```

This adds a round chat button at the bottom right, a small greeting bubble, and a compact chat
panel (full-screen on phones). Options (add to the same tag):
`data-color="#2a2622"`, `data-accent="#c9a97a"`, `data-position="left"`,
`data-greeting="..."` (empty string turns the bubble off), `data-delay="4"` (seconds).

Open the chat from any of your own buttons or links with `onclick="BlennexChat.open()"`.
Preview: `widget/demo.html`.

### Alternative: Render

`render.yaml` is included for a one-click Render deploy (`python app.py`), if your Render account allows free services without a card.

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (Streamlit **Secrets** / Render env var; never commit it) |
| `BLENNEX_CONTACT` | no | Override where the bot sends leads (default: Contact page, hello@blennexdesign.com, WhatsApp) |
| `GROQ_MODEL` | no | Override the primary model |
