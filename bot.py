import discord
import os
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Standard intents for reading messages
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            user_id TEXT,
            fact TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_fact(user_id, fact):
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO memories VALUES (?, ?, ?)', (str(user_id), fact, datetime.now()))
    conn.commit()
    conn.close()

def get_memories(user_id):
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fact FROM memories WHERE user_id = ?', (str(user_id),))
    facts = cursor.fetchall()
    conn.close()
    return [f[0] for f in facts]

def delete_memory(user_id, keyword):
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM memories WHERE user_id = ? AND fact LIKE ?', (str(user_id), f'%{keyword}%'))
    conn.commit()
    conn.close()

# --- BOT EVENTS ---

@client.event
async def on_ready():
    print(f'Freebot is online without prefixes as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower()

    # 1. NATURAL TRIGGER: REMEMBER
    if content.startswith("remember ") or content.startswith("freebot, remember "):
        fact = message.content.split("emember ", 1)[1]
        save_fact(message.author.id, fact)
        await message.channel.send(f"✨ I've added that to my records: {fact}")
        return

    # 2. NATURAL TRIGGER: BRAIN/RECALL
    if "what do you remember" in content or "check brain" in content:
        facts = get_memories(message.author.id)
        if not facts:
            await message.channel.send("My records are empty for you.")
        else:
            memory_list = "\n".join([f"• {f}" for f in facts])
            await message.channel.send(f"**Here is what I know about you:**\n{memory_list}")
        return

    # 3. NATURAL TRIGGER: FORGET
    if content.startswith("forget "):
        keyword = content.replace("forget ", "")
        delete_memory(message.author.id, keyword)
        await message.channel.send(f"🗑️ I've cleared any memories related to: {keyword}")
        return

    # 4. GENERAL CHAT (With Memory & Multimodal)
    user_memories = get_memories(message.author.id)
    context = f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if user_memories:
        context += "Stored User Facts:\n" + "\n".join(user_memories)

    async with message.channel.typing():
        try:
            content_parts = [f"Context:\n{context}\n\nUser: {message.content}"]
            
            if message.attachments:
                for attachment in message.attachments:
                    # Check for Images or Audio
                    mime = attachment.content_type or ""
                    if any(x in mime for x in ['image', 'audio']):
                        file_data = await attachment.read()
                        content_parts.append({'mime_type': mime, 'data': file_data})
                        
                        # Auto-describe and save to memory
                        desc_resp = model.generate_content(["Describe this briefly for my memory DB:", {'mime_type': mime, 'data': file_data}])
                        save_fact(message.author.id, f"Seen/Heard: {desc_resp.text}")

            response = model.generate_content(content_parts)
            text = response.text
            
            for i in range(0, len(text), 2000):
                await message.channel.send(text[i:i+2000])
                
        except Exception as e:
            await message.channel.send(f"⚠️ System Error: {e}")

client.run(TOKEN)        
