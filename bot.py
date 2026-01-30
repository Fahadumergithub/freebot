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

def get_memories(user_id):
    conn = sqlite3.connect('freebot_memory.db')
    c = conn.cursor()
    c.execute('SELECT fact FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15', (str(user_id),))
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

@discord_client.event
async def on_ready():
    print(f'✅ Agent Online: {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user: return
    content_lower = message.content.lower()
    user_id = message.author.id

    if content_lower.startswith("remember "):
        fact = message.content[9:]
        save_fact(user_id, fact)
        return await message.reply(f"🧠 Memory Locked: {fact}")

    if content_lower == "check brain":
        facts = get_memories(user_id)
        if not facts: return await message.reply("My memory of you is empty.")
        return await message.reply("**What I know about you:**\n" + "\n".join([f"• {f}" for f in facts]))

    if content_lower.startswith("forget "):
        keyword = content_lower[7:]
        delete_memory(user_id, keyword)
        return await message.reply(f"🗑️ Erased: {keyword}")

    async with message.channel.typing():
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            user_memories = get_memories(user_id)
            memory_context = "\n".join(user_memories) if user_memories else "No previous facts known."
            
            # STRUCTURED PROMPT FOR BETTER RECALL
            prompt = f"""
            <system_context>
            Current Time: {now}
            User ID: {user_id}
            Known Facts About This User:
            {memory_context}
            </system_context>

            <user_request>
            {message.content}
            </user_request>
            
            INSTRUCTIONS: Use the <system_context> to answer accurately. If the user asks who they are or what their name is, look at the 'Known Facts' above.
            """

            search_tool = types.Tool(google_search=types.GoogleSearch())
            response = client_ai.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[search_tool],
                    system_instruction="You are Freebot. You are a helpful AI with a perfect memory of the facts the user tells you to remember."
                )
            )

            text = response.text
            for i in range(0, len(text), 2000):
                await message.reply(text[i:i+2000])

        except Exception as e:
            await message.reply(f"⚠️ Error: {e}")

discord_client.run(DISCORD_TOKEN)
