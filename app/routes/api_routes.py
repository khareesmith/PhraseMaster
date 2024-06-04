from flask import Blueprint, jsonify, request, session
from datetime import datetime
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

from ..models.db import get_db_connection, phrase_already_submitted, insert_submission
from ..utils.score import calculate_initial_score
from ..utils.login_req import login_required
from ..utils.challenge import generate_challenge, get_or_create_daily_challenge

api_bp = Blueprint('api', __name__)

# Route to generate a challenge
@api_bp.route('/generate_challenge/<category>', methods=['GET'])

def generate_category_challenge(category):
    
    """
    Generate a challenge for a specific category.
    """
    
    challenge_id = None
    challenge = None  # Ensure variables are initialized
    
    # Validate category
    allowed_categories = ['tiny_story', 'scene_description', 'specific_word', 'rhyming_phrase', 'emotion', 'dialogue', 'idiom', 'slogan', 'movie_quote']
    if category not in allowed_categories:
        return jsonify({'error': 'Invalid category'}), 400

    try:
        challenge_id, challenge = get_or_create_daily_challenge(category)
        if challenge_id is None or challenge is None:
            return jsonify({'error': 'Failed to retrieve or create challenge'}), 500
        
        return jsonify({'challenge_id': challenge_id, 'challenge': challenge, 'category': category})
    except Exception as e:
        print('Error creating challenge: %s' % e)
    return jsonify({'error': 'An error occurred while generating the challenge'}), 500

# Route to generate random challenge. Currently unused
@api_bp.route('/generate_challenge/random', methods=['GET'])
def generate_random_challenge():
    from random import choice
    category = choice(['tiny_story', 'scene_description', 'specific_word', 'rhyming_phrase', 'emotion', 'dialogue', 'idiom', 'slogan', 'movie_quote'])
    challenge = generate_challenge(category)
    challenge_id = str(uuid.uuid4())  # Generate a unique ID
    return jsonify({'challenge_id': challenge_id, 'challenge': challenge, 'category': category})

# Route for phrase submission
@api_bp.route('/submit_phrase', methods=['POST'])
@login_required
def submit_phrase():
    
    """
    Submit a phrase for a given challenge.
    """

    session_db = get_db_connection()
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        data = request.get_json()
        required_fields = ['username', 'user_phrase', 'challenge_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        username = session.get('user', {}).get('name')
        challenge_id = data['challenge_id']
        
        # Fetch challenge details from the database
        result = session_db.execute(
            text("SELECT category, original_challenge FROM daily_challenges WHERE challenge_id = :challenge_id"),
            {'challenge_id': challenge_id}
        ).fetchone()
        challenge_data = result._asdict()
        user_phrase = data['user_phrase']
        category = challenge_data['category']
        challenge = challenge_data['original_challenge']
        
        if len(user_phrase) < 3:
            return jsonify({'error': 'Phrase must be at least 3 characters long.'}), 400
        
        if phrase_already_submitted(session_db, username, category, current_date):
            return jsonify({'error': 'You have already submitted a phrase for this category today.'}), 400

        initial_score, feedback = calculate_initial_score(user_phrase, category, challenge)
        
        if not username or not user_phrase or not challenge_id or not challenge or not category:
            return jsonify({'error': 'Missing data'}), 400
        
        # Get the current date and insert into the database
        insert_submission(session_db, username, current_date, user_phrase, category, challenge_id, challenge, initial_score)
    
    except SQLAlchemyError as e:
        session_db.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    
    except KeyError as e:
        session_db.rollback()
        return jsonify({'error': 'KeyError: ' + str(e)}), 400
    
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500
        
    finally:
        session_db.close()
    
    return jsonify({'message': 'Submission successful!', 'feedback': feedback})  # Return feedback in JSON response