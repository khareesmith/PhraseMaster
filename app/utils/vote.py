from datetime import datetime, date
from sqlalchemy import and_
from app.models.db import User, get_db_connection
from app.utils.streaks import update_voting_streak
from sqlalchemy.orm.attributes import flag_modified

MAX_VOTES_PER_CATEGORY = 5

def get_user_votes(user, category):
    """
    Get the number of votes a user has made for a specific category.
    
    Args:
        user: The user object to get votes for
        category: The category to get votes for
        
    Returns:
        The number of votes the user has made in the specified category today.
    """
    today = date.today().isoformat()
    if not user.votes_per_category:
        user.votes_per_category = {}
    return user.votes_per_category.get(today, {}).get(category, 0)

def increment_user_vote(user, category, session_db):
    """
    Increment the vote count for a user in a specific category.
    
    Args:
        user: The user object to increment votes for
        category: The category to increment votes for
        session_db: The database session object
    
    Returns:
        Returns the number of remaining votes for that category.
        Returns 0 if the user has reached the maximum number of votes for the category.
    """
    today = date.today().isoformat()
    if not user.votes_per_category:
        user.votes_per_category = {}
    if today not in user.votes_per_category:
        user.votes_per_category[today] = {}

    current_votes = user.votes_per_category[today].get(category, 0)
    if current_votes >= MAX_VOTES_PER_CATEGORY:
        return 0

    user.votes_per_category[today][category] = current_votes + 1
    user.daily_votes = sum(user.votes_per_category[today].values())
    user.last_vote_date = datetime.now()

    flag_modified(user, "votes_per_category")
    flag_modified(user, "daily_votes")
    flag_modified(user, "last_vote_date")
    
    session_db.add(user)
    session_db.commit()  # Commit the changes here
    
    remaining_votes = MAX_VOTES_PER_CATEGORY - user.votes_per_category[today][category]
    return max(remaining_votes, 0)

def format_category_name(category):
    """
    Format the category name for display.
    """
    return " ".join(word.capitalize() for word in category.split('_'))

def reset_daily_votes():
    """
    Reset votes for all users if it's a new day.
    This function should be called once per day, perhaps in a before_request handler.
    """
    session_db = get_db_connection()
    try:
        today = date.today().isoformat()
        users = session_db.query(User).all()
        for user in users:
            if not user.votes_per_category:
                user.votes_per_category = {}
            if today not in user.votes_per_category:
                user.votes_per_category[today] = {}
                user.daily_votes = 0
        session_db.commit()
    finally:
        session_db.close()