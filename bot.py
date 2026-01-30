import os
import discord
import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Load credentials
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# 2. Initialize Gemini Client
gemini = genai.Client(api_key=GEMINI_KEY)

def split_message(text, limit=2000):
    """Splits text into chunks of 2000 characters for Discord."""
    return [text[i:i + limit] for i in range(0, len(text), limit)]

class Freebot(discord.Client):
    async def on_ready(self):
        print(f'✅ Freebot is online as {self.user}')

    async def on_message(self, message):
        # Don't reply to self
        if message.author == self.user:
            return

        async with message.channel.typing():
            try:
                # Get dynamic time for the system instruction
                now = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
                
                # Enable Internet Search
                search_tool = types.Tool(google_search=types.GoogleSearch())

                # Generate content with 2.5 Flash-Lite (Most stable 2026 free model)
                response = gemini.models.generate_content(
                    model='gemini-2.5-flash-lite', 
                    contents=message.content,
                    config=types.GenerateContentConfig(
                        tools=[search_tool],
                        system_instruction=f"You are Freebot. Current time is {now}. Use Google Search for live facts."
                    )
                )
                
                if response.text:
                    chunks = split_message(response.text)
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    # Sometimes search results return no direct text, but have candidates
                    await message.reply("I found some info but couldn't summarize it. Try asking differently!")
                    
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("⚠️ Brain fog! Check the terminal logs for the error.")

# 3. Start Bot
intents = discord.Intents.default()
intents.message_content = True 

client = Freebot(intents=intents)
client.run(DISCORD_TOKEN)
