import os
import discord
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Import Local Memory Skill
from skills.memory import init_db, save_fact, get_memories

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize Gemini Client
client_ai = genai.Client(api_key=GEMINI_KEY)

# Initialize Discord Client
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

def load_identity():
    try:
        with open('identity.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "You are Freebot, a professional assistant for Dr. Fahad Umer."

# Ensure Database is ready
init_db()

@discord_client.event
async def on_ready():
    print(f'✅ Freebot Stable (Lite + Search) Online: {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user: return
    
    msg_text = message.content.strip()
    user_id = str(message.author.id)

    # --- MANUAL MEMORY COMMANDS ---
    if msg_text.lower().startswith("remember "):
        fact = msg_text[9:].strip()
        save_fact(user_id, fact)
        return await message.reply(f"🧠 Memory Locked: **{fact}**")

    if msg_text.lower() == "check brain":
        facts = get_memories(user_id)
        return await message.reply("**Current Stored Memory:**\n" + "\n".join([f"• {f}" for f in facts]) if facts else "Memory is currently empty.")

    # --- AI RESPONSE LOGIC ---
    async with message.channel.typing():
        try:
            # 1. Gather Identity & Stored Facts
            identity = load_identity()
            memories = "\n".join(get_memories(user_id))
            
            # 2. Build System Instruction
            system_instruction = f"{identity}\n\nUSER FACTS FROM DATABASE:\n{memories}"
            
            # 3. Prepare Content (Text + Attachments)
            content_parts = [msg_text] if msg_text else ["Hello!"]
            for attachment in message.attachments:
                file_path = f"temp_{attachment.filename}"
                await attachment.save(file_path)
                with open(file_path, "rb") as f:
                    content_parts.append(types.Part.from_bytes(
                        data=f.read(), 
                        mime_type=attachment.content_type
                    ))
                os.remove(file_path)

            # 4. Generate Response with Search Grounding
            # (Simplified call to avoid tool-conflict 400 errors)
            response = client_ai.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=content_parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )

            full_response = response.text if response.text else "I have processed your request."
            
            # 5. Split for Discord 2000 char limit
            for i in range(0, len(full_response), 2000):
                await message.reply(full_response[i:i+2000])

        except Exception as e:
            print(f"❌ API Error: {e}")
            await message.reply(f"⚠️ Service interruption. Please try again. ({str(e)[:50]})")

discord_client.run(DISCORD_TOKEN)
