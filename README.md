# Freebot: Internet-Aware AI Agent with Persistence

Freebot is a production-grade Discord AI agent designed for the **2026 Gemini ecosystem**. It features long-term memory, real-time web grounding, and is hosted 24/7 on Google Cloud.

## 🚀 Key Features
* **Long-Term Memory:** Uses SQLite3 to remember user facts (e.g., names, preferences). Use `remember [fact]` to store info and `check brain` to view it.
* **Live Web Search:** Integrated Google Search tool for real-time news, weather, and data.
* **Persistent Hosting:** Managed by `systemd` on a GCP VM for 100% uptime.
* **Multimodal Ready:** Capable of processing text and attachments (images/audio) in a single flow.

## 🛠️ Technical Stack
* **Language:** Python 3.10+
* **Core SDK:** `google-genai` (Gemini 2.5 Flash-Lite)
* **Database:** SQLite3 (Local persistence)
* **Infrastructure:** Google Cloud Platform (Compute Engine)

## 📂 Project Structure
* `bot.py`: Main agent logic and database integration.
* `freebot_memory.db`: (Local only) SQLite database file.
* `freebot.service`: Systemd configuration for 24/7 reliability.
* `.env`: Environment variables (API keys).

## 🛡️ Usage
- **Chat:** Just talk to the bot.
- **Memory:** `remember I am a developer`
- **Recall:** `check brain`
- **Reset Memory:** `forget [keyword]`
