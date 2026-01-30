# Freebot: Internet-Aware Discord AI Agent

A production-grade Discord bot powered by the **Gemini 2.5 Flash-Lite** model. Freebot isn't just a chatbot; it's a grounded agent that knows the current time, weather, and live news through Google Search integration.

## 🚀 Key Features
* **Always Live:** Managed by `systemd` on a GCP VM for 24/7 uptime.
* **Web Grounding:** Real-time access to the internet via Google Search tools.
* **Time Sensitive:** Awareness of current date and time for accurate scheduling and context.
* **Auto-Splitting:** Handles long AI responses by intelligently chunking messages for Discord.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **AI SDK:** `google-genai` (2026 Production Version)
* **Discord API:** `discord.py`
* **Deployment:** Google Cloud Platform (VM Instance)

## 📂 Project Structure
* `bot.py`: Core logic and AI tool integration.
* `.env`: (Hidden) API keys and Discord tokens.
* `freebot.service`: Linux service configuration for 24/7 operation.
* `.gitignore`: Prevents sensitive keys from being leaked to GitHub.

## 🤖 Future Roadmap (True Agent Status)
* **Multi-Model Routing:** Integration with Claude 3.5 for complex logic tasks.
* **Tool-Use:** Enabling the bot to read uploaded PDFs and CSV files.
* **Persistent Memory:** Long-term RAG (Retrieval-Augmented Generation) for user-specific history.
