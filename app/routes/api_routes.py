from flask import Blueprint, jsonify, request, session
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
import bleach

from ..models.db import get_db_connection, phrase_already_submitted, insert_submission
from ..utils.score import calculate_initial_score
from ..utils.auth import login_required
from ..utils.challenge import get_or_create_daily_challenge

# Create a Blueprint for the API routes
api_bp = Blueprint('api', __name__)

# Route to generate a challenge
@api_bp.route('/generate_challenge/<category>', methods=['GET'])

def generate_category_challenge(category):
    
    """
    Generate a challenge for a specific category.
    """
    
    # Initialize variables
    challenge_id = None
    challenge = None
    
    # Validate category
    allowed_categories = ['tiny_story', 'scene_description', 'specific_word', 'rhyming_phrase', 'emotion', 'dialogue', 'idiom', 'slogan', 'movie_quote']
    if category not in allowed_categories:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Sanitize category input
    category = bleach.clean(category)

    try:
        # Get or create a daily challenge for the category
        challenge_id, challenge = get_or_create_daily_challenge(category)
        if challenge_id is None or challenge is None:
            return jsonify({'error': 'Failed to retrieve or create challenge'}), 500
        
        return jsonify({'challenge_id': challenge_id, 'challenge': challenge, 'category': category})
    except Exception as e:
        print('Error creating challenge: %s' % e)
    return jsonify({'error': 'An error occurred while generating the challenge'}), 500

# Route for phrase submission
@api_bp.route('/submit_phrase', methods=['POST'])
@login_required
def submit_phrase():
    
    """
    Submit a phrase for a given challenge.
    """
    session_db = get_db_connection()
    # Get the current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Validate the user phrase and challenge ID
        data = request.get_json()
        required_fields = ['user_phrase', 'challenge_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Check if the user is logged in before phrase submission
        user = session.get('user')
        if not user:
            return jsonify({'error': 'User not logged in'}), 401
        
        # Sanitize user name and challenge ID
        user_id = user.get('id')
        username = bleach.clean(user.get('name'))
        challenge_id = bleach.clean(data['challenge_id'])
        
        # Fetch challenge details from the database
        result = session_db.execute(
            text("SELECT category, original_challenge FROM daily_challenges WHERE challenge_id = :challenge_id"),
            {'challenge_id': challenge_id}
        ).fetchone()
        
        if not result:
            return jsonify({'error': 'Invalid challenge ID'}), 400
        
        # Dictionary unpacking to get the challenge data
        challenge_data = result._asdict()
        user_phrase = data['user_phrase']
        category = challenge_data['category']
        challenge = challenge_data['original_challenge']
        
        # Validate that the phrase is at least 3 characters long
        if len(user_phrase) < 3:
            return jsonify({'error': 'Phrase must be at least 3 characters long.'}), 400
        
        # Check if the user has already submitted a phrase for the category today
        if phrase_already_submitted(session_db, user_id, category, current_date):
            return jsonify({'error': 'You have already submitted a phrase for this category today.'}), 400

        # Calculate the initial score and feedback
        initial_score, feedback = calculate_initial_score(user_phrase, category, challenge)
        # Validate user ID, user phrase, challenge ID, challenge, and category
        if not user_id:
            return jsonify({'error': 'Missing user ID'}), 400
        
        if not user_phrase:
            return jsonify({'error': 'Missing user phrase'}), 400
        
        if not challenge_id:
            return jsonify({'error': 'Missing challenge ID'}), 400
        
        if not challenge:
            return jsonify({'error': 'Missing challenge'}), 400
        
        if not category:
            return jsonify({'error': 'Missing category'}), 400
        
        # Get the current date and insert into the database
        insert_submission(session_db, user_id, username, current_date, user_phrase, category, challenge_id, challenge, initial_score)
    
    # Handle database errors
    except SQLAlchemyError as e:
        session_db.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    
    # Handle key errors
    except KeyError as e:
        session_db.rollback()
        return jsonify({'error': 'KeyError: ' + str(e)}), 400
    
    # Handle all other exceptions
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500
    
    # Close the database session
    finally:
        session_db.close()
    
    # Return feedback in JSON response
    return jsonify({'message': 'Submission successful!', 'feedback': feedback})