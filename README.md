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
streamlit run streamlit_app.py     # Streamlit UI
python app.py                      # or the Gradio UI
```

## Files

| File | Purpose |
|---|---|
| `prompts.py` | System prompt (role, context, Blennex knowledge, rules) |
| `chatbot.py` | Chat engine: model config, memory, streaming, failure handling |
| `streamlit_app.py` | Streamlit UI (the deployed app) |
| `app.py` | Gradio UI (local / Colab / Render) |
| `Blennex_Chatbot_Assignment.ipynb` | Colab notebook walkthrough with test outputs |

## Deploy (Streamlit Community Cloud, free, no card)

1. Go to **https://share.streamlit.io** and sign in with GitHub.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository `KashifKhan777/blennex-chatbot`, branch `main`, main file `streamlit_app.py`.
4. Optionally pick a custom subdomain, e.g. `blennex-chatbot` → `https://blennex-chatbot.streamlit.app`.
5. **Advanced settings → Secrets**, paste:
   ```toml
   GROQ_API_KEY = "your-groq-key"
   ```
6. Click **Deploy**. The app is live in ~2-3 minutes.

Free apps sleep after several days without visitors; the first visitor then clicks "Yes, get this app back up" and waits ~30 s.

### Embed on the Blennex website

```html
<iframe src="https://blennex-chatbot.streamlit.app/?embed=true" width="100%" height="720"
        style="border:0;border-radius:12px" title="Blennex brand assistant"></iframe>
```

### Alternative: Render

`render.yaml` is included for a one-click Render deploy (`python app.py`), if your Render account allows free services without a card.

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (Streamlit **Secrets** / Render env var; never commit it) |
| `BLENNEX_CONTACT` | no | Where the bot sends leads, e.g. `hello@blennex.com` |
| `GROQ_MODEL` | no | Override the primary model |
