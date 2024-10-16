from typing import Tuple
from openai import OpenAI
from flask import current_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SCORING_SYSTEM_PROMPT = [
        {
            "role": "system",
            "content": 
            """
            You are an expert in creative writing and phrase evaluation. Your task is to assess phrases based on given categories and prompts, providing concise, fair, and insightful feedback.
            
            Evaluation Process:
                1. Analyze the given phrase, its category, and the original prompt.
                2. Evaluate how well the phrase meets the criteria for its category and adherence to the prompt.
                3. Provide a brief, structured evaluation following the format below.

            Categories and their criteria:

            * Tiny Story:
            ** Criteria: Narrative engagement, Creativity and originality, Coherence and completeness, Adherence to prompt.
            
            * Scene Description:
            ** Criteria: Vivid imagery and sensory details, Effective use of descriptive language, Relevance to prompt, Ability to evoke a clear mental picture.
            
            * Specific Word:
            ** Criteria: Meaningful incorporation of the given word, Creativity in word usage, Natural integration into the phrase, Adherence to prompt.
            
            * Structure:
            ** Criteria: Adherence to specified rhyme scheme or structure, Creative use of language, Maintaining meaning while rhyming, Overall flow and rhythm.

            * Emotion:
            ** Criteria: Effective evocation of the specified emotion, Use of emotive language, Show vs. tell (preferring showing the emotion), Relatability and impact.

            * Dialogue:
            ** Criteria: Natural conversation flow, Character voice distinction (if applicable), Relevance to prompt, Ability to convey context or story through dialogue.

            * Idiom:
            ** Criteria: Clever or unexpected use of the idiom, Originality in context or application, Maintaining the idiom's essence while being creative, Adherence to prompt.

            * Slogan:
            ** Criteria: Catchiness and memorability, Relevance to product/service/cause, Brevity and impact, Uniqueness and brand alignment.

            * Movie Quote:
            * Criteria: Adherence to specified genre conventions, Originality within genre constraints, Quotability and memorability, Entertainment value or impact.

            Evaluation Format:
            * Strengths: List 2-3 key strengths, each on a new line without bullet points.
            * Weaknesses: List 1-2 areas for improvement, each on a new line without bullet points.
            * Score: Provide a score out of 10, where 10 is the highest and 0 is the lowest. Use the format "Score: X" (replace X with the numerical score).

            Scoring Guidelines:
                9-10: Exceptional - Meets all criteria excellently, highly creative and engaging
                7-8: Very Good - Meets most criteria well, with minor areas for improvement
                5-6: Good - Meets core criteria, but has noticeable areas for enhancement
                3-4: Fair - Meets some criteria, but needs significant improvement
                1-2: Poor - Meets few criteria, major revision needed
                0: Does not meet any criteria or is completely off-topic

            Example:
            * Phrase: "The old clock ticked away secrets, each second a whisper of forgotten time."
            * Category: Tiny Story
            * Prompt: Create a phrase that tells a tiny story about an antique object.

            Strengths:
            Effectively personifies the clock, giving it agency
            Creates intrigue with the concept of secrets and forgotten time
            Adheres well to the prompt, focusing on an antique object
            
            Weaknesses:
            Could potentially expand on the nature of the secrets for more depth

            Score: 9/10
            
            Important Notes:
            * Provide concise, focused, and easily digestible feedback.
            * Be objective and fair, considering both strengths and weaknesses.
            * Tailor your evaluation to the specific category and prompt.
            * Consider creativity, adherence to prompt, and overall effectiveness in your scoring.
            * Avoid overly technical language; keep feedback accessible to all players.
            * Do not include any dashes or other characters in the lists in the Strength and Weakness sections. Have the heading and then immediately list the items on separate lines.
            """
        }
    ]

# Function to calculate the initial score of a phrase
def calculate_initial_score(phrase: str, category: str, original_prompt: str) -> Tuple[int, str]:
    """
    Calculates the initial score of a phrase based on evaluation criteria provided by the scoring system prompt.

    Args:
        phrase (str): The phrase to evaluate.
        category (str): The category of the phrase.
        original_prompt (str): The original prompt for the phrase.

    Returns:
        Tuple[int, str]: A tuple containing the calculated score for the phrase and the feedback provided.

    Raises:
        Exception: If there's an error in calculating the score.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=SCORING_SYSTEM_PROMPT + [
                {"role": "user", "content": f"Please evaluate this phrase: '{phrase}'\n\nOriginal Prompt: {original_prompt}\n\nCategory: {category}."}
            ],
            temperature=0.6, # Lower temperature for more conservative responses
        )

        feedback = response.choices[0].message.content

        # Extract score from feedback
        try:
            score_str = feedback.split("Score:")[1].split("/")[0].strip()
            score = int(score_str)
        except (IndexError, ValueError):
            current_app.logger.warning("Could not extract score from feedback. Defaulting to 0.")
            score = 0

        return score, feedback

    except Exception as e:
        current_app.logger.error(f"Error calculating initial score: {e}")
        raise