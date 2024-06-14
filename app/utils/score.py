# Description: This file contains the function to calculate the initial score of a phrase based on the evaluation criteria provided by the scoring system prompt. The function sends the phrase, category, and original prompt to the OpenAI API for evaluation and extracts the score from the response. If the score extraction fails, it defaults to 0. The extracted score and feedback are returned to the caller.

from openai import OpenAI
from flask import current_app

# Initialize the OpenAI client
client = OpenAI()

# Function to calculate the initial score of a phrase
def calculate_initial_score(phrase, category, original_prompt):
    scoring_system_prompt = [
        {
            "role": "system",
            "content": 
            """
            You are an expert in creative writing and phrase evaluation. You will be given a phrase, the category it belongs to, and the original prompt. Your task is to evaluate how well the phrase meets the criteria of the prompt and category.

            Categories and their criteria:

            * Tiny Story:
            ** Criteria: Engaging narrative, creativity, coherence, adherence to prompt.
            
            * Scene Description:
            ** Criteria: Vivid imagery, detail, relevance to prompt.
            
            * Specific Word:
            ** Criteria: Meaningful incorporation of the word, creativity, natural usage.
            
            * Rhyme:
            ** Criteria: Adherence to form (rhyme or structure), creative language.

            * Emotion:
            ** Criteria: Effective evocation of the specified emotion, vivid language.

            * Dialogue:
            ** Criteria: Natural conversation flow, relevance to prompt, character development (if applicable).

            * Idiom:
            ** Criteria: Clever use of the idiom, originality, adherence to prompt.

            * Slogan:
            ** Criteria: Catchiness, memorability, relevance to product/service/cause.

            * Movie Quote:
            * Criteria: Adherence to genre conventions, originality, entertainment value.

            Evaluation Format:
            * Strengths: Briefly mention the phrase's most successful elements in bullet point format (2-4 bullets maximum).
            * Weaknesses: Briefly mention areas where the phrase could be improved in bullet point format (2-3 bullets maximum).
            * Score: Provide a score out of 10, where 10 is the highest and 0 is the lowest. Use the format "Score: X" (replace X with the numerical score).

            Example:
            * Phrase: The moon winked at the stars as they danced across the night sky.
            * Category: Scene Description
            * Prompt: Create a phrase that describes a starry night.

            Evaluation:

            Strengths:
            Vivid imagery
            Creative use of personification
            
            Weaknesses:
            Could benefit from more specific details (e.g., types of stars, moon phases)

            Score: 8
            
            Important Notes:
            * Your feedback should be concise, focused, and easily digestible.
            * Help users understand the phrase's strengths and areas for improvement.
            * Be objective and fair in your assessment, considering both strengths and weaknesses.
            * The numerical score should reflect your overall judgment of the phrase's quality and effectiveness within its category and prompt.
            * Do not include any dashes or other characters in the lists in the Strength and Weakness sections. Have the heading and then immediately list the items on separate lines.
            """
        },
        {
            "role": "user",
            "content": f"Please evaluate this phrase: '{phrase}'\n\nOriginal Prompt: {original_prompt}\n\nCategory: {category}."
        }
    ]

    client.api_key = current_app.config['OPENAI_API_KEY']
    response = client.chat.completions.create(
        model="gpt-4o", # Use the GPT-4o model for scoring
        messages=scoring_system_prompt,
        temperature=0.6, # Lower temperature for more conservative responses
    )

    feedback = response.choices[0].message.content
    
    try:
        score_str = feedback.split("Score:")[1].split("/")[0].strip()
        score = int(score_str)
    except (IndexError, ValueError):
        # Handle cases where GPT doesn't provide a score in the expected format
        score = 0  # Default to 0 if score extraction fails
        print("Warning: Could not extract score from feedback.")
    return score, feedback