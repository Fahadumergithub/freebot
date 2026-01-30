import discord
from discord.ext import commands
import os
import sqlite3
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = os.getenv("DISCORD_TOKEN")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")

genai.configure(api_key=GENAI_API_KEY)
# Using the 2026 Stable Flash-Lite model
model = genai.GenerativeModel('gemini-2.5-flash-lite')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- DATABASE SETUP ---
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
    cursor.execute('INSERT INTO memories VALUES (?, ?, ?)', 
                   (str(user_id), fact, datetime.now()))
    conn.commit()
    conn.close()

def get_memories(user_id):
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fact FROM memories WHERE user_id = ?', (str(user_id),))
    facts = cursor.fetchall()
    conn.close()
    return [f[0] for f in facts]

# --- BOT COMMANDS ---

@bot.event
async def on_ready():
    print(f'Freebot is live and remembering as {bot.user}')

@bot.command()
async def remember(ctx, *, arg):
    save_fact(ctx.author.id, arg)
    await ctx.send(f"✅ Fact stored in my lite-DB: {arg}")

@bot.command()
async def forget(ctx, *, arg):
    conn = sqlite3.connect('freebot_memory.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM memories WHERE user_id = ? AND fact LIKE ?', 
                   (str(ctx.author.id), f'%{arg}%'))
    conn.commit()
    conn.close()
    await ctx.send(f"🗑️ Memory deleted: {arg}")

@bot.command()
async def brain(ctx):
    facts = get_memories(ctx.author.id)
    if not facts:
        await ctx.send("I don't have any saved facts about you yet.")
    else:
        memory_list = "\n".join([f"- {f}" for f in facts])
        await ctx.send(f"**My internal records for you:**\n{memory_list}")

# --- MAIN CHAT LOGIC ---

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    user_memories = get_memories(message.author.id)
    context = f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    if user_memories:
        context += "Past facts about this user:\n" + "\n".join(user_memories)

    async with message.channel.typing():
        try:
            content_parts = [f"Context:\n{context}\n\nUser Message: {message.content}"]
            
            # MULTIMODAL HANDLING
            if message.attachments:
                for attachment in message.attachments:
                    # Check for Images or Audio
                    is_image = any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp'])
                    is_audio = any(attachment.filename.lower().endswith(ext) for ext in ['mp3', 'wav', 'ogg'])
                    
                    if is_image or is_audio:
                        file_data = await attachment.read()
                        content_parts.append({'mime_type': attachment.content_type, 'data': file_data})
                        
                        # Ask Gemini to describe the file for the DB
                        desc_prompt = "Briefly describe this file so I can remember it later. Start with 'FILE_DESCRIPTION: '"
                        desc_resp = model.generate_content([desc_prompt, {'mime_type': attachment.content_type, 'data': file_data}])
                        
                        # Save description to SQLite
                        save_fact(message.author.id, desc_resp.text.replace("FILE_DESCRIPTION: ", ""))

            # Generate final response
            response = model.generate_content(content_parts)
            text = response.text
            
            for i in range(0, len(text), 2000):
                await message.channel.send(text[i:i+2000])
                
        except Exception as e:
            await message.channel.send(f"⚠️ System Error: {e}")

bot.run(TOKEN)
