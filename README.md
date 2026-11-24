# Nex: Blennex Design Brand Assistant

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/KashifKhan777/Blennex-Chatbot)

A domain-focused chatbot for **Blennex Design**: brand identity, packaging and label
design, and 3D product visualization for product-based brands (beauty, skincare,
haircare, wellness).

- **LLM API:** Groq (`openai/gpt-oss-120b`, with automatic fallback to `gpt-oss-20b` and `qwen3.8-27b`)
- **UI / hosting:** Gradio, deployed on Render (free tier)
- **Behaviour:** defined by the system prompt in `prompts.py` (role, context, knowledge, rules)

## Model configuration

| Parameter | Value | Why |
|---|---|---|
| `temperature` | **0.4** | The bot speaks for a real business. Facts (services, process, values) must stay consistent, and it must not improvise prices or claims. Values near 0 sound robotic and repetitive; above ~0.8 the model starts to embellish. 0.4 is grounded but still conversational. |
| `max_tokens` | **600** | The prompt targets answers of about 250 words (~350 tokens). 600 leaves room for a detailed answer when asked, without cutting off mid-sentence, while capping latency and cost. |
| History | last 8 exchanges | Keeps conversational memory while staying inside Groq free-tier token limits. |

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
python app.py
```

## Deploy (Render, free)

1. Click **Deploy to Render** above (or go to `https://render.com/deploy?repo=https://github.com/KashifKhan777/Blennex-Chatbot`).
2. Sign in to Render; it reads `render.yaml` and asks for **`GROQ_API_KEY`**. Paste your Groq key there.
3. Click **Apply**. After the build (~2-3 min) you get a public URL like `https://blennex-brand-assistant.onrender.com`.

Free instances sleep after 15 minutes without traffic; the first visit after that takes ~30-50 seconds to wake up.

### Embed on the Blennex website

```html
<iframe src="https://blennex-brand-assistant.onrender.com" width="100%" height="720"
        style="border:0;border-radius:12px" title="Blennex brand assistant"></iframe>
```

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (entered in Render at deploy time; never commit it) |
| `BLENNEX_CONTACT` | no | Where the bot sends leads, e.g. `hello@blennex.com` |
| `GROQ_MODEL` | no | Override the primary model |
