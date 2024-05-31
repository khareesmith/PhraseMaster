from ..models.db import get_db_connection
from openai import OpenAI
from flask import current_app
from datetime import datetime
import pytz
import uuid
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

# System prompt for PhraseMaster
SYSTEM_PROMPT = [{
    "role": "system", 
    "content": """
You are "PhraseMaster," an interactive phrase generator designed for a word game. Your task is to craft creative and engaging phrases that players can complete.

**Format:**

Always begin with "Create a phrase that..." followed by the specific task, falling into one of the categories below.

**Categories:**

* **Tiny Story: A phrase that sparks a miniature narrative.**
    * Example: Create a phrase that tells a tiny story about a lost sock.
    
* **Scene Description: A phrase that paints a vivid picture of a setting or event.**
    * Example: Create a phrase that describes a 13-year-old's birthday party.
    
* **Specific Word: Incorporate a given word into a phrase in a creative way.**
    * Example: Create a phrase that uses the word 'ketchup'.
    
* **Rhyme: A phrase that rhymes with a given word or follows a specific poetic structure.**
    * Example: Create a phrase that rhymes with "moonlight." OR Create a phrase in the form of a limerick.

* **Emotion: Evoke a particular feeling or mood through a phrase.**
    * Example: Create a phrase that expresses joy and excitement.

* **Dialogue:: A story/phrase that is a snippet of a conversation.**
    * Example: Create a phrase that starts a conversation between two friends meeting after a long time.

* **Idiom: Incorporate a common idiom or figure of speech into a phrase with a twist.**
    * Example: Create a phrase that uses the idiom "piece of cake."
    
* **Slogan: Craft a catchy slogan for a product, service, or cause.**
    * Example: Create a slogan for a new brand of eco-friendly sneakers."

* **Movie Quote: Create a new movie quote in the style of a specific movie genre.**
    * Example: Create a phrase in the style of a cheesy action movie one-liner."

**Important Notes:**

* Your output should consist solely of the "Create a phrase..." prompt. DO NOT finish the phrase.
* Do not include additional words like "sure," "okay," or confirmations.
* Be sure the phrases are simple and do not use overly complex words or concepts that users may have to research.
    """
}]

# Function to generate challenges
def generate_challenge(category):

    """
    Generate a challenge based on the specified category.

    Args:
        category (str): The category for which to generate the challenge.

    Returns:
        str: The generated response from OpenAI.
    """
    
    client.api_key = current_app.config['OPENAI_API_KEY']
    response = client.chat.completions.create(
        model="gpt-4o",
        messages= SYSTEM_PROMPT + [{"role": "user", "content": f"Generate a {category} phrase"}],
        temperature=1.75,
        presence_penalty= 1.5
    )

    return response.choices[0].message.content.strip()

def get_or_create_daily_challenge(category):
    session_db = get_db_connection()
    today = datetime.now(pytz.timezone('US/Eastern')).date()  # Ensure we're comparing just the date part
    challenge_id = None
    challenge = None

    try:
        result = session_db.execute(
            text("SELECT original_challenge, date, challenge_id FROM daily_challenges WHERE category = :category ORDER BY date DESC LIMIT 1"),
            {'category': category}
        ).fetchone()
        
        if result:
            challenge_row = result._asdict()
            challenge_date = challenge_row['date']
            challenge_id = challenge_row['challenge_id']

            if challenge_date == today:
                challenge = challenge_row['original_challenge']
            else:
                # Generate new challenge if there is no challenge for today
                challenge = generate_challenge(category)
                challenge_id = str(uuid.uuid4())
                session_db.execute(
                    text("INSERT INTO daily_challenges (challenge_id, category, original_challenge, date) VALUES (:challenge_id, :category, :original_challenge, :date)"),
                    {'challenge_id': challenge_id, 'category': category, 'original_challenge': challenge, 'date': today}
                )
                session_db.commit()
        else:
            # Generate new challenge if the table is empty
            challenge = generate_challenge(category)
            challenge_id = str(uuid.uuid4())
            session_db.execute(
                text("INSERT INTO daily_challenges (challenge_id, category, original_challenge, date) VALUES (:challenge_id, :category, :original_challenge, :date)"),
                {'challenge_id': challenge_id, 'category': category, 'original_challenge': challenge, 'date': today}
            )
            session_db.commit()

    except Exception as e:
        session_db.rollback()
        logging.error(f"Error in get_or_create_daily_challenge: {e}")
        return None, None
    finally:
        session_db.close()

    return challenge_id, challenge