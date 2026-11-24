---
title: Blennex Design Brand Assistant
emoji: 📦
colorFrom: gray
colorTo: yellow
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
short_description: Brand identity, packaging & 3D visualization assistant
---

# Nex: Blennex Design Brand Assistant

A domain-focused chatbot for **Blennex Design**: brand identity, packaging and label
design, and 3D product visualization for product-based brands (beauty, skincare,
haircare, wellness).

- **LLM API:** Groq (`openai/gpt-oss-120b`, with automatic fallback to `gpt-oss-20b` and `qwen3.8-27b`)
- **UI / hosting:** Gradio on Hugging Face Spaces
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

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Groq API key (add as a **Secret** on Hugging Face Spaces) |
| `BLENNEX_CONTACT` | no | Where the bot sends leads, e.g. `hello@blennex.com` |
| `GROQ_MODEL` | no | Override the primary model |
