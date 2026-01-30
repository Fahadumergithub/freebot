import os
import discord
import sqlite3
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

client_ai = genai.Client(api_key=GEMINI_KEY)
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

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
    print(f"💾 DATABASE SAVE SUCCESS: {fact}")

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
    print(f'✅ Agent Online: {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user: return
    
    msg_text = message.content.strip()
    content_lower = msg_text.lower()
    user_id = str(message.author.id)

    # TRIGGER: REMEMBER (Case Insensitive)
    if content_lower.startswith("remember "):
        fact_to_save = msg_text[9:].strip()
        save_fact(user_id, fact_to_save)
        return await message.reply(f"🧠 Memory Locked: **{fact_to_save}**")

    # TRIGGER: CHECK BRAIN
    if content_lower == "check brain":
        facts = get_memories(user_id)
        if not facts: return await message.reply("My memory of you is currently empty.")
        return await message.reply("**Here is what I know about you:**\n" + "\n".join([f"• {f}" for f in facts]))

    async with message.channel.typing():
        try:
            user_memories = get_memories(user_id)
            memory_context = "\n".join(user_memories) if user_memories else "No personal facts known."
            
            prompt = f"""
            <user_facts>
            {memory_context}
            </user_facts>

            User Message: {message.content}
            """

            search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client_ai.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool],
                    system_instruction="You are Freebot. You have a long-term memory. Use the <user_facts> to address the user correctly."
                )
            )

            await message.reply(response.text)
        except Exception as e:
            await message.reply(f"⚠️ Error: {e}")

discord_client.run(DISCORD_TOKEN)
