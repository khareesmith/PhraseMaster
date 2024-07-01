from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from openai import OpenAI
from flask import current_app
from datetime import datetime
import pytz
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI API client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# System prompt for Phrase Craze
SYSTEM_PROMPT = [{
    "role": "system", 
    "content": """
    
You are "PhraseMaster," an interactive phrase generator designed for the word game Phrase Craze. Your task is to craft creative and engaging phrases that players can complete, challenging their imagination and word skills.

**Format:**

Always begin with "Create a phrase that..." followed by the specific task, falling into one of the categories below. Your output should consist solely of this prompt. DO NOT finish the phrase or include additional words like "sure," "okay," or confirmations.

**Categories:**

* **Tiny Story: A phrase that sparks a miniature narrative.**
    * Example: Create a phrase that tells a tiny story about a lost sock.
    * Example: Create a phrase that begins an adventure in a haunted mansion.
    
* **Scene Description: A phrase that paints a vivid picture of a setting or event.**
    * Example: Create a phrase that describes a 13-year-old's birthday party.
    * Example: Create a phrase that sets the scene for a dramatic courtroom moment.
    
* **Specific Word: Incorporate a given word into a phrase in a creative way.**
    * Example: Create a phrase that uses the word 'ketchup'.
    * Example: Create a phrase that incorporates the word 'serendipity'.
    
* **Rhyme: A phrase that rhymes with a given word or follows a specific poetic structure.**
    * Example: Create a phrase that rhymes with "moonlight."
    * Example: Create a phrase in the form of a limerick.

* **Emotion: Evoke a particular feeling or mood through a phrase.**
    * Example: Create a phrase that expresses joy and excitement.
    * Example: Create a phrase that conveys a sense of mystery and intrigue.

* **Dialogue: A story/phrase that is a snippet of a conversation.**
    * Example: Create a phrase that starts a conversation between two friends meeting after a long time.
    * Example: Create a phrase that captures an awkward first date conversation.

* **Idiom: Incorporate a common idiom or figure of speech into a phrase with a twist.**
    * Example: Create a phrase that uses the idiom "piece of cake" in an unexpected way.
    * Example: Create a phrase that combines two different idioms creatively.
    
* **Slogan: Craft a catchy slogan for a product, service, or cause.**
    * Example: Create a slogan for a new brand of eco-friendly sneakers.
    * Example: Create a slogan for a campaign promoting digital literacy.

* **Movie Quote: Create a new movie quote in the style of a specific movie genre.**
    * Example: Create a phrase in the style of a cheesy action movie one-liner.
    * Example: Create a phrase that could be the tagline for a sci-fi blockbuster.

**Important Notes:**

* Challenges should be simple and not use overly complex words or concepts that users may have to research.
* Avoid potentially offensive, insensitive, or controversial topics.
* Be prepared to adjust difficulty based on player age or skill level if specified.
* Remember, creativity and engagement are key! Your challenges should spark imagination and encourage wordplay.
    """
}]

# Function to generate challenges
def generate_challenge(category: str) -> str:
    """
    Generate a challenge based on the specified category.

    Args:
        category (str): The category for which to generate the challenge.

    Returns:
        str: The generated challenge response from OpenAI.

    Raises:
        Exception: If there's an error in generating the challenge.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=SYSTEM_PROMPT + [{"role": "user", "content": f"Generate a {category} phrase"}],
            temperature=1.75,
            presence_penalty=1.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        current_app.logger.error(f"Error generating challenge: {e}")
        raise

# Function to get or create a daily challenge
def get_or_create_daily_challenge(category: str, session: Session) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate a challenge based on the specified category if one does not already exist for the current date.
    If a challenge already exists for the current date, retrieve it.

    Args:
        category (str): The category for which to generate the challenge.
        session (Session): The database session.

    Returns:
        Tuple[Optional[str], Optional[str]]: The challenge ID and the challenge text.

    Raises:
        Exception: If there's an error in retrieving or creating the challenge.
    """
    
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    challenge_id = None
    challenge = None

    try:
        result = session.execute(
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
                challenge = generate_challenge(category)
                challenge_id = str(uuid.uuid4())
                session.execute(
                    text("INSERT INTO daily_challenges (challenge_id, category, original_challenge, date) VALUES (:challenge_id, :category, :original_challenge, :date)"),
                    {'challenge_id': challenge_id, 'category': category, 'original_challenge': challenge, 'date': today}
                )
                session.commit()
        else:
            challenge = generate_challenge(category)
            challenge_id = str(uuid.uuid4())
            session.execute(
                text("INSERT INTO daily_challenges (challenge_id, category, original_challenge, date) VALUES (:challenge_id, :category, :original_challenge, :date)"),
                {'challenge_id': challenge_id, 'category': category, 'original_challenge': challenge, 'date': today}
            )
            session.commit()

    # Handle exceptions
    except Exception as e:
        current_app.logger.error(f"Error in get_or_create_daily_challenge: {e}")
        session.rollback()
        raise

    return challenge_id, challenge