from flask import Blueprint, jsonify, request, session
from sqlalchemy import text
from datetime import datetime, date, timedelta
from sqlalchemy.exc import SQLAlchemyError
from app.models.db import get_db_connection, phrase_already_submitted, insert_submission, User
from app.utils.score import calculate_initial_score
from app.utils.auth import login_required, admin_required
from app.utils.get_challenge import get_or_create_daily_challenge
from app.utils.get_leaderboard import get_leaderboard, update_daily_leaderboard
from app.utils.streaks import update_submission_streak
import bleach

# Create a Blueprint for the API routes
api_bp = Blueprint('api', __name__)

session_db = get_db_connection()

# Route to generate a challenge
@api_bp.route('/generate_challenge/<category>', methods=['GET'])
def generate_category_challenge(category):
    
    """
    Generate a challenge for a specific category.
    
    Args:
        category (str): The category for which to generate the challenge.
    
    Returns:
        JSON: The generated challenge, its ID, and the category.
    """
    
    # Initialize variables
    challenge_id = None
    challenge = None
    
    # Validate category
    allowed_categories = ['tiny_story', 'scene_description', 'specific_word', 'rhyming_phrase', 
                        'emotion', 'dialogue', 'idiom', 'slogan', 'movie_quote']
    if category not in allowed_categories:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Sanitize category input
    category = bleach.clean(category)

    try:
        # Get or create a daily challenge for the category
        challenge_id, challenge = get_or_create_daily_challenge(category, session_db)
        if challenge_id is None or challenge is None:
            return jsonify({'error': 'Failed to retrieve or create challenge'}), 500
        
        return jsonify({'challenge_id': challenge_id, 'challenge': challenge, 'category': category})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

# Route for phrase submission
@api_bp.route('/submit_phrase', methods=['POST'])
@login_required
def submit_phrase():
    
    """
    Submit a phrase for a given challenge. The challenge ID and user phrase are required in the request data. The user must be logged in to submit a phrase.
    """
    current_date = datetime.now().date()
    data = request.get_json()
    user = session.get('user')
    user_id = user.get('id')
    challenge_id = data['challenge_id']
    score_first = data.get('score_first', False)
    
    session_key = f'scored_{challenge_id}'
    
    try:
        # Validate the user phrase and challenge ID
        required_fields = ['user_phrase', 'challenge_id']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if the user is logged in before phrase submission
        if not user:
            return jsonify({'error': 'User not logged in'}), 401
        
        # Sanitize user name
        username = bleach.clean(user.get('name'))
        
        # Fetch challenge details from the database
        challenge_data = session_db.execute(
            text("SELECT category, original_challenge FROM daily_challenges WHERE challenge_id = :challenge_id"),
            {'challenge_id': challenge_id}
        ).fetchone()
        
        if not challenge_data:
            return jsonify({'error': 'Invalid challenge ID'}), 400
        
        user_phrase = data['user_phrase']
        category, challenge = challenge_data
        
        # Validate that the phrase is at least 3 characters long
        if len(user_phrase) < 3:
            return jsonify({'error': 'Phrase must be at least 3 characters long.'}), 400
        
        # Check if the user has already submitted a phrase for the category today
        if phrase_already_submitted(session_db, user_id, category, current_date):
            return jsonify({'error': 'You have already submitted a phrase for this category today.'}), 400
        
        previously_scored = session.get(session_key, False)
        
        if score_first and not previously_scored:
            initial_score, feedback = calculate_initial_score(user_phrase, category, challenge)
            session[session_key] = True
            return jsonify({'message': 'Phrase scored', 'feedback': feedback, 'score': initial_score}), 200

        # If we're here, it's a submission (either direct or after scoring)
        if previously_scored:
            # Recalculate score for consistency
            initial_score, _ = calculate_initial_score(user_phrase, category, challenge)
        else:
            initial_score = 0
        
        # Validate user ID, user phrase, challenge ID, challenge, and category
        if not all([user_id, user_phrase, challenge_id, challenge, category]):
            missing = [field for field in ['user ID', 'user phrase', 'challenge ID', 'challenge', 'category'] if not locals()[field.replace(' ', '_')]]
            return jsonify({'error': f"Missing {', '.join(missing)}"}), 400
        
        # Insert submission into database
        insert_submission(session_db, user_id, username, current_date, user_phrase, category, 
                        challenge_id, challenge, initial_score=initial_score, scored_first=score_first)
        
        # Commit the insertion to ensure the user and submission are in the database
        session_db.commit()
        
        # Clear the scoring session for this challenge
        session.pop(session_key, None)
        
        # Fetch the user object for updating the submission streak
        user_obj = session_db.query(User).filter_by(id=user_id).first()
        if user_obj:
            update_submission_streak(user_obj, session_db)
            session_db.commit()
    
        return jsonify({'message': 'Submission successful!'}), 200
        
    # Handle database errors
    except SQLAlchemyError as e:
        session_db.rollback()
        return jsonify({'error': 'Database error: ' + str(e)}), 500
    
    # Handle other exceptions
    except Exception as e:
        session_db.rollback()
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500
    
    # Close the database session
    finally:
        session_db.close()
    
@api_bp.route('/check_previous_score/<challenge_id>', methods=['GET'])
@login_required
def check_previous_score(challenge_id):
    previously_scored = session.get(f'scored_{challenge_id}', False)
    return jsonify({'previously_scored': previously_scored}), 200

@api_bp.route('/leaderboard/<category>/<timeframe>')
def get_leaderboard_api(category, timeframe):
    today = date.today()
    if timeframe == 'daily':
        start_date = end_date = today - timedelta(days=1)
    elif timeframe == 'weekly':
        start_date = today - timedelta(days=7)
        end_date = today - timedelta(days=1)
    elif timeframe == 'monthly':
        start_date = today.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        end_date = today - timedelta(days=1)
    elif timeframe == 'all-time':
        start_date = date(2000, 1, 1)  # Set this to your app's launch date
        end_date = today - timedelta(days=1)
    else:
        return jsonify({'error': 'Invalid timeframe'}), 400

    leaderboard = get_leaderboard(category, start_date, end_date)
    return jsonify(leaderboard)

@api_bp.route('/update_leaderboard/<category>', methods=['POST'])
@login_required
@admin_required
def update_leaderboard_api(category):
    update_daily_leaderboard(category)
    return jsonify({'message': 'Leaderboard updated successfully'})