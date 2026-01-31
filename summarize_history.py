import os
import sqlite3
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
client_ai = genai.Client(api_key=GEMINI_KEY)

DB_PATH = 'freebot_memory.db'

def summarize_and_save():
    if not os.path.exists(DB_PATH):
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Get unique users who chatted today
    c.execute("SELECT DISTINCT user_id FROM memories")
    users = [row[0] for row in c.fetchall()]

    for user_id in users:
        # 2. Get the last 50 messages for this user
        c.execute("SELECT fact FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50", (user_id,))
        recent_messages = [row[0] for row in c.fetchall()]
        
        if not recent_messages:
            continue

        chat_history = "\n".join(recent_messages)

        # 3. Ask Gemini to extract new permanent facts
        prompt = f"""
        Analyze the following recent chat history between a user and an AI.
        Extract any NEW personal facts, preferences, or professional details about the user.
        Format them as short, bulleted "facts".
        If no new facts are found, just return the word "NONE".

        CHAT HISTORY:
        {chat_history}
        """

        try:
            response = client_ai.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
                config={'system_instruction': "You are a memory processor. Extract only core facts."}
            )

            new_facts = response.text.strip()
            if new_facts and new_facts != "NONE":
                # 4. Save extracted facts back to the database
                c.execute("INSERT INTO memories (user_id, fact, timestamp) VALUES (?, ?, datetime('now'))", 
                          (user_id, f"Auto-Learned: {new_facts}",))
                print(f"✅ Auto-learned new facts for user {user_id}")

        except Exception as e:
            print(f"❌ Error processing user {user_id}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    summarize_and_save()
