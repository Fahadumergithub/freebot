import os
import discord
import sqlite3
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. SETUP & CREDENTIALS
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

client_ai = genai.Client(api_key=GEMINI_KEY)
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 2. DATABASE (MEMORY) LOGIC
def init_db():
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memories 
                 (user_id TEXT, fact TEXT, timestamp DATETIME)''')
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
    c.execute('SELECT fact FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10', (str(user_id),))
    facts = [row[0] for row in c.fetchall()]
    conn.close()
    return facts

def delete_memory(user_id, keyword):
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('DELETE FROM memories WHERE user_id = ? AND fact LIKE ?', (str(user_id), f'%{keyword}%'))
    conn.commit()
    conn.close()

init_db()

# 3. HELPER FUNCTIONS
def split_message(text, limit=2000):
    return [text[i:i + limit] for i in range(0, len(text), limit)]

# 4. BOT EVENTS
@discord_client.event
async def on_ready():
    print(f'✅ Freebot Memory-Agent is online as {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return

    content_lower = message.content.lower()
    user_id = message.author.id

    # --- COMMAND: REMEMBER ---
    if content_lower.startswith("remember "):
        fact = message.content[9:]
        save_fact(user_id, fact)
        return await message.reply(f"✨ Memory Stored: {fact}")

    # --- COMMAND: FORGET ---
    if content_lower.startswith("forget "):
        keyword = content_lower[7:]
        delete_memory(user_id, keyword)
        return await message.reply(f"🗑️ Cleared memories matching: {keyword}")

    # --- GENERAL CHAT WITH AI ---
    async with message.channel.typing():
        try:
            # Prepare context
            now = datetime.datetime.now().strftime("%A, %B %d, %Y - %H:%M")
            user_memories = get_memories(user_id)
            memory_str = "\n".join([f"- {m}" for m in user_memories])
            
            # Setup Prompt Parts
            prompt_parts = [
                f"SYSTEM: Current Time: {now}. User Memories:\n{memory_str}\n\n"
                f"User said: {message.content}"
            ]

            # Handle Attachments (Images/Audio)
            if message.attachments:
                for attachment in message.attachments:
                    mime = attachment.content_type or ""
                    if any(x in mime for x in ['image', 'audio', 'video', 'pdf']):
                        file_bytes = await attachment.read()
                        prompt_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=mime))

            # AI Generation with Internet Search
            search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client_ai.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt_parts,
                config=types.GenerateContentConfig(
                    tools=[search_tool],
                    system_instruction="You are Freebot, an advanced AI Agent. You remember user facts and use Google Search for live info."
                )
            )

            # Reply
            if response.text:
                for chunk in split_message(response.text):
                    await message.reply(chunk)
            else:
                await message.reply("I processed that but don't have a text response.")

        except Exception as e:
            print(f"Error: {e}")
            await message.reply(f"⚠️ Agent Error: {e}")

discord_client.run(DISCORD_TOKEN)
