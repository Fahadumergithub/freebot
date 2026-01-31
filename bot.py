import os
import discord
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Skills
from skills.memory import init_db, save_fact, get_memories
from skills.google_drive import log_to_sheet

load_dotenv()
client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

init_db()

@discord_client.event
async def on_ready():
    print(f'✅ Conversational Agent Online: {discord_client.user}')

@discord_client.event
async def on_message(message):
    if message.author == discord_client.user: return
    
    user_id = str(message.author.id)
    msg_text = message.content.strip()

    async with message.channel.typing():
        try:
            # 1. Prepare Content (Handles Multimodal)
            content_parts = [msg_text] if msg_text else ["Analyze this."]
            for attachment in message.attachments:
                file_path = f"temp_{attachment.filename}"
                await attachment.save(file_path)
                with open(file_path, "rb") as f:
                    content_parts.append(types.Part.from_bytes(data=f.read(), mime_type=attachment.content_type))
                os.remove(file_path)

            # 2. Context & Tools
            user_facts = "\n".join(get_memories(user_id))
            system_prompt = f"You are Dr. Umer's assistant. Use user facts: {user_facts}. Use tools if asked to log/save info."

            # 3. Generate with AUTOMATIC Tool Use
            response = client_ai.models.generate_content(
                model='gemini-2.0-flash',
                contents=content_parts,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[log_to_sheet, types.Tool(google_search=types.GoogleSearch())]
                )
            )

            await message.reply(response.text)
        except Exception as e:
            await message.reply(f"⚠️ Error: {e}")

discord_client.run(os.getenv("DISCORD_TOKEN"))
