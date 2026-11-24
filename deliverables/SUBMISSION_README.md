# Nex: Blennex Design Brand Assistant (Assignment Submission)

A domain-specific chatbot (brand identity, packaging & label design, 3D product visualization for
physical-product brands) built with the **Groq API**, deployed publicly, and embedded on the Blennex Design website.

## Links
| | |
|---|---|
| **Live chatbot (public)** | https://blennex-chatbot-kashifkhan.streamlit.app |
| **Open the notebook in Colab** | https://colab.research.google.com/github/KashifKhan777/Blennex-Chatbot/blob/main/Blennex_Chatbot_Assignment.ipynb |
| **Source code** | https://github.com/KashifKhan777/Blennex-Chatbot |
| **On the website** | blennexdesign.com → "Ask Nex" button (bottom-right) |

## What's in this package
| File | What it is |
|---|---|
| `Blennex_Chatbot_Assignment.ipynb` | Google Colab notebook: setup, system prompt, model configuration (with justification), engine with memory and error handling, tests with saved outputs, Gradio public link |
| `Blennex_Chatbot_Project_Report.pdf` | 11-page project report: design, configuration, deployment, test results, screenshots, challenges, full system prompt |
| `screenshots/` | Final interface screenshots (website widget, memory, pricing honesty, off-topic refusal, poor-fit decline, mobile, standalone app) |
| `source_code/` | `prompts.py` (system prompt), `chatbot.py` (engine), `streamlit_app.py` (deployed UI), `app.py` (Gradio UI), `requirements.txt`, `.streamlit/config.toml`, `widget/` (website chat button), `knowledge/` (client-safe knowledge document) |

## Requirements covered
- **Domain focus:** stays on brand design; off-topic questions are declined politely and redirected
- **System prompt:** Role (persona, expertise, tone) + Context (audience, scope, constraints, background knowledge)
- **Model configuration:** temperature **0.4**, max tokens **350**, both justified in the notebook (Section 3) and the report (Section 03)
- **LLM API:** Groq (`openai/gpt-oss-120b`, with automatic fallbacks)
- **Working code:** runs end to end, handles API failures gracefully, keeps conversation history (last 6 exchanges)
- **Deployment:** public Streamlit Community Cloud link plus the website integration

## Run the notebook
1. Open it in Colab (link above). Add `GROQ_API_KEY` under 🔑 **Secrets** (free key at console.groq.com; it starts with `gsk_`) and enable *Notebook access*.
2. **Runtime → Run all.** Section 6 prints a public Gradio link to chat with the bot.
