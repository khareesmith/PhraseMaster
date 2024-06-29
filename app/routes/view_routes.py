from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from datetime import datetime, timedelta
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError
from sqlalchemy.sql import text
from app.models.db import get_db_connection, User, Submission
from app.utils.vote import get_user_votes, increment_user_vote, reset_daily_votes, MAX_VOTES_PER_CATEGORY, format_category_name
import bleach

# Create a Blueprint for the view routes
view_bp = Blueprint('view', __name__)

@view_bp.before_request
def before_request():
    # This will reset votes daily. You might want to optimize this to run only once per day.
    reset_daily_votes()

# Route to the index page
@view_bp.route('/')
def index():
    """
    Render the index page.
    """
    return render_template('main/index.html')

# Route to the voting page
@view_bp.route('/vote/', methods=['GET', 'POST'])
def vote():
    """
    Render the voting page and handle vote submissions.

    If a GET request is received, fetch two random submissions for the given category and display them for voting.
    If a POST request is received, update the vote count for the selected submission.

    Returns:
        - A rendered template for the voting page on GET requests.
        - A redirect to the voting page on POST requests.
        - An error message if there are not enough submissions to vote on.
    """
    session_db = get_db_connection()
    category = request.args.get('category')
    formatted_category = format_category_name(category)
    username = request.args.get('username')
    
    # Default values for non-logged-in users
    user = None
    votes_used = 0
    votes_remaining = MAX_VOTES_PER_CATEGORY
    progress_class = ''
    progress_width = 0
    
    # Fetch the user object
    if 'user' in session:
        user_id = session['user']['id']
        user = session_db.query(User).filter_by(id=user_id).first()
        
        if user:
            votes_used = get_user_votes(user, category)
            votes_remaining = MAX_VOTES_PER_CATEGORY - votes_used   
            
            if votes_remaining == 0:
                progress_class = 'danger'
                progress_width = 100
            elif votes_remaining <= 2:
                progress_class = 'warning'
                progress_width = (votes_used / MAX_VOTES_PER_CATEGORY) * 100
            else:
                progress_class = ''
                progress_width = (votes_used / MAX_VOTES_PER_CATEGORY) * 100
    
    if request.method == 'POST':
        
        # Check if the user is logged in
        if 'user' not in session:
            flash("You must be logged in to vote.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash("Invalid CSRF token.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Handle the vote submission
        voted_submission_id = request.form.get('submission_id')
        voted_submission_id = bleach.clean(voted_submission_id)
    
        # Check if the user is trying to vote on their own submission
        submission_owner = session_db.execute(
            text('SELECT username FROM submissions WHERE id = :id'),
            {'id': voted_submission_id}
        ).scalar()
        
        if submission_owner == session['user']['name']:
            flash("You cannot vote for your own submission.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Check if the user has reached the voting limit for this category
        votes_today = get_user_votes(user, category)
        
        if votes_today is None:
            flash("An error occurred while retrieving your vote count.", "error")
            return redirect(url_for('view.vote', category=category))
        
        if votes_today >= MAX_VOTES_PER_CATEGORY:
            flash(f"You have reached your voting limit for the {formatted_category} category.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Update the vote count for the selected submission
        try:
            session_db.execute(
                text('UPDATE submissions SET votes = votes + 1 WHERE id = :id'),
                {'id': voted_submission_id}
            )
            
            # Increment the user's votes for this category and update the voting streak
            remaining_votes = increment_user_vote(user, category, session_db)
            
            if remaining_votes is None:
                raise Exception("Failed to increment user vote")

            session_db.commit()
            
            if remaining_votes > 0:
                flash(f"Vote successful! You have {remaining_votes} vote{'s' if remaining_votes != 1 else ''} left for the {formatted_category} category.", "success")
            else:
                flash(f"Vote successful! You have used all your votes for the {formatted_category} category today.", "success")
                
            return redirect(url_for('view.vote', category=category))
        except Exception as e:
            session_db.rollback()
            flash("An error occurred while casting your vote.", "error")
            print(f"Error details: {str(e)}")
            return render_template('main/error.html', error_message=f"An error occurred: {str(e)}")
        finally:
            session_db.close()

    # Handle GET request: Fetch the category from the query parameters
    if category:
        try:
            # Calculate the date for the previous day
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_date = yesterday.date()
            
            # Fetch two random submissions from the previous day for the given category
            submissions_result = session_db.execute(
                text('''
                    SELECT id, username, category, challenge, user_phrase, votes 
                    FROM submissions 
                    WHERE category = :category 
                    AND DATE(date) = :yesterday_date
                    ORDER BY RANDOM() 
                    LIMIT 2
                '''),
                {'category': category, 'yesterday_date': yesterday_date}
            ).fetchall()
            
            submissions = [{column: value for column, value in zip(['id', 'username', 'category', 'challenge', 'user_phrase', 'votes'], submission)} for submission in submissions_result]
            
            # Check if there are enough submissions to vote on
            if len(submissions) < 2:
                return render_template('main/error.html', error_message='Not enough submissions to vote on.')
                
            # Fetch the leaderboard for the category
            leaderboard_result = session_db.execute(
                text('''
                    SELECT username, SUM(votes) as total_votes
                    FROM submissions
                    WHERE category = :category
                    GROUP BY username
                    ORDER BY total_votes DESC
                    LIMIT 10
                '''),
                {'category': category}
            ).fetchall()

            leaderboard = [{column: value for column, value in zip(['username', 'total_votes'], entry)} for entry in leaderboard_result]
            
            return render_template('votes/vote.html', 
                        submission1=submissions[0],
                        submission2=submissions[1],
                        leaderboard=leaderboard,
                        username=username,
                        category=category,
                        formatted_category=formatted_category,
                        votes_used=votes_used,
                        votes_remaining=votes_remaining,
                        max_votes=MAX_VOTES_PER_CATEGORY,
                        progress_class=progress_class,
                        progress_width=progress_width,
                        user=user)

        # Handle exceptions
        except Exception as e:
            return render_template('main/error.html', error_message=f"An error occurred: {e}")
        finally:
            session_db.close()

    return redirect(url_for('view.index'))

# Profile view route
@view_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Display the user's profile."""
    user = session.get('user')
    if not user:
        return redirect(url_for('auth.login'))

    session_db = get_db_connection()
    try:
        user_obj = session_db.query(User).filter_by(id=user['id']).first()
        
        # Get user's streaks
        streaks = {
            'login': user_obj.login_streak,
            'submission': user_obj.submission_streak,
            'voting': user_obj.voting_streak
        }

        # Get user's best submission
        best_submission = session_db.query(Submission)\
            .filter_by(user_id=user['id'])\
            .order_by(Submission.votes.desc())\
            .first()

        return render_template('profile/profile.html', 
                            user=user, 
                            streaks=streaks, 
                            best_submission=best_submission)
    finally:
        session_db.close()

# Route to the confirm email page
@view_bp.route('/confirm_email', methods=['GET'])
def confirm_email():
    """
    Render the confirm email page.
    """
    return render_template('auth/confirm_email.html')
