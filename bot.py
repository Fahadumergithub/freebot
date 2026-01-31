import os
import discord
import sqlite3
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import skills safely - if they fail, the bot stays up
try:
    from skills.google_drive import log_to_sheet
except ImportError:
    log_to_sheet = None

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

client_ai = genai.Client(api_key=GEMINI_KEY)
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

def load_identity():
    try:
        with open('identity.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "You are Freebot, a professional assistant for Dr. Fahad Umer."

def init_db():
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS memories (user_id TEXT, fact TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

def save_fact(user_id, fact):
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('INSERT INTO memories VALUES (?, ?, ?)', (str(user_id), fact, datetime.datetime.now()))
    conn.commit()
    conn.close()

def get_memories(user_id):
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('SELECT fact FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15', (str(user_id),))
    facts = [row[0] for row in c.fetchall()]
    conn.close()
    return facts

init_db()

@discord_client.event
async def on_ready():
    print(f'✅ Stable Multimodal Agent Online: {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user: return
    
    msg_text = message.content.strip()
    user_id = str(message.author.id)

    # 1. Traditional Commands (Working Backup)
    if msg_text.lower().startswith("remember "):
        fact = msg_text[9:].strip()
        save_fact(user_id, fact)
        return await message.reply(f"🧠 Memory Locked: **{fact}**")

    if msg_text.lower() == "check brain":
        facts = get_memories(user_id)
        return await message.reply("**Memory:**\n" + "\n".join([f"• {f}" for f in facts]) if facts else "Memory empty.")

    async with message.channel.typing():
        try:
            # 2. Process Content (Multimodal)
            content_parts = [msg_text] if msg_text else ["Analyze attached media."]
            for attachment in message.attachments:
                file_path = f"temp_{attachment.filename}"
                await attachment.save(file_path)
                with open(file_path, "rb") as f:
                    content_parts.append(types.Part.from_bytes(data=f.read(), mime_type=attachment.content_type))
                os.remove(file_path)

            # 3. Contextual Prompting
            identity = load_identity()
            memories = "\n".join(get_memories(user_id))
            system_prompt = f"{identity}\n\nUSER FACTS:\n{memories}\n\nRespond professionally. Use tools for logging if requested."

            # 4. Gemini 2.0 Flash Execution
            active_tools = [types.Tool(google_search=types.GoogleSearch())]
            if log_to_sheet:
                active_tools.append(log_to_sheet)

            response = client_ai.models.generate_content(
                model='gemini-2.0-flash',
                contents=content_parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=active_tools
                )
            )

            await message.reply(response.text)
        except Exception as e:
            print(f"❌ Error: {e}")
            await message.reply(f"⚠️ Service Alert: {e}")

discord_client.run(DISCORD_TOKEN)
