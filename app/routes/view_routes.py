from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import validate_csrf
from wtforms.validators import ValidationError
from sqlalchemy.sql import text
from ..models.db import get_db_connection
import bleach

view_bp = Blueprint('view', __name__)

@view_bp.route('/')
def index():
    """
    Render the index page.
    """
    return render_template('main/index.html')

@view_bp.route('/vote/', methods=['GET', 'POST'])
def vote():
    """
    Render the voting page and handle vote submissions.

    If a GET request is received, fetch two random submissions for the given category and display them for voting.
    If a POST request is received, update the vote count for the selected submission.

    Returns:
        - A rendered template for the voting page on GET requests.
        - A redirection to the index page on successful vote submission.
        - An error message if there are not enough submissions to vote on.
    """
    session_db = get_db_connection()
    category = request.args.get('category')
    username = request.args.get('username')
    
    if request.method == 'POST':
        
        # Validate CSRF token
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            flash("Invalid CSRF token.", "error")
            return redirect(url_for('view.vote', category=category))
        
        if 'user' not in session:
            flash("You must be logged in to vote.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Handle the vote submission
        voted_submission_id = request.form.get('submission_id')
        voted_submission_id = bleach.clean(voted_submission_id)
    
        # Check if the user is trying to vote on their own submission
        submission_owner = session_db.execute(
            text('SELECT username FROM submissions WHERE id = :id'),
            {'id': voted_submission_id}
        ).scalar()  # Fetches the first column of the first row
        

        if submission_owner == session['user']['name']:
            flash("You cannot vote for your own submission.", "error")
            return redirect(url_for('view.vote', category=category))
        
        # Update the vote count for the selected submission
        try:
            session_db.execute(
                text('UPDATE submissions SET votes = votes + 1 WHERE id = :id'),
                {'id': voted_submission_id}
            )
            session_db.commit()
            flash("Vote successful!", "success")
            return redirect(url_for('view.vote', category=category))
        except Exception as e:
            session_db.rollback()
            flash("An error occurred while casting your vote.", "error")
            return render_template('main/error.html', error_message=f"An error occurred: {e}")
        finally:
            session_db.close()

    # Handle GET request: Fetch the category from the query parameters
    if category:
        try:
            challenge_result = session_db.execute(
                text('SELECT challenge_id FROM daily_challenges WHERE category = :category ORDER BY date DESC LIMIT 1'),
                {'category': category}
            ).fetchone()
            
            if challenge_result == None:
                return render_template('main/error.html', error_message='There are no submissions in this category today. Go submit something!')

            if challenge_result:
                challenge_id = challenge_result[0]  # Accessing the first element in the tuple directly
                submissions_result = session_db.execute(
                    text('''
                        SELECT id, username, category, challenge, user_phrase, votes FROM submissions 
                        WHERE challenge_id = :challenge_id 
                        ORDER BY RANDOM() 
                        LIMIT 2
                    '''),
                    {'challenge_id': challenge_id}
                ).fetchall()
                submissions = [{column: value for column, value in zip(['id', 'username', 'category', 'challenge', 'user_phrase', 'votes'], submission)} for submission in submissions_result]

                if len(submissions) < 2:
                    return render_template('main/error.html', error_message='Not enough submissions to vote on.')
                
                leaderboard_result = session_db.execute(
                    text('''
                        SELECT username, SUM(initial_score + votes) AS total_score
                        FROM submissions
                        WHERE category = :category
                        GROUP BY username
                        ORDER BY total_score DESC
                        LIMIT 10
                    '''),
                    {'category': category}
                ).fetchall()

                leaderboard = [{column: value for column, value in zip(['username', 'total_score'], entry)} for entry in leaderboard_result]
                
                return render_template('votes/vote.html', submission1=submissions[0], submission2=submissions[1], leaderboard=leaderboard, username=username)

        except Exception as e:
            return render_template('main/error.html', error_message=f"An error occurred: {e}")
        finally:
            session_db.close()

    return redirect(url_for('view.index'))

@view_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Display the user's profile."""
    user = session.get('user')
    if not user:
        return redirect(url_for('auth.login'))

    return render_template('profile/profile.html', user=user)

@view_bp.route('/confirm_email', methods=['GET'])
def confirm_email():
    """
    Render the confirm email page.
    """
    return render_template('auth/confirm_email.html')
