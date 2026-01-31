# 📂 FREEBOT SYSTEM MANIFEST - v1.0 (Public Safe)

## 🏢 1. Project Overview
* **Purpose:** Professional Research & Dental AI Assistant for Dr. Fahad Umer (AKU).
* **Hosting:** Linux VM (e2-micro) on GCP.
* **Philosophy:** "Free Always" - Uses Gemini 2.0 Flash Free Tier.

## 🛠 2. Security Configuration
> ⚠️ **CRITICAL:** These files are in `.gitignore` and must NEVER be pushed to GitHub.
* `.env`: Contains `DISCORD_TOKEN` and `GEMINI_API_KEY`.
* `freebot_memory.db`: Contains private user facts and history.

## 🛠 3. Environment Setup
1. **Directory:** `/home/geminimoltbot/freebot/`
2. **Python:** 3.10+ in `venv`
3. **Libraries:** `discord.py`, `google-genai`, `python-dotenv`, `Pillow`

## 💻 4. Core Bot Logic (bot.py)
* **Identity:** Loads from `identity.txt`.
* **Memory:** SQLite3 stores conversation facts.
* **Multimodal:** Handles text, image attachments, and voice notes (`.ogg`).
* **Search:** Uses Google Search tool for real-time dental research.

## ⚡ 5. Recovery Cheat Sheet
* **Check Logs:** `sudo journalctl -u freebot.service -f`
* **Restart:** `sudo systemctl restart freebot.service`
* **Sync Code:** `git add bot.py identity.txt && git commit -m "update" && git push origin main`
