from datetime import datetime, date, timedelta
from sqlalchemy import and_
from app.models.db import User, get_db_connection
from app.utils.streaks import update_voting_streak
from sqlalchemy.orm.attributes import flag_modified
import logging

logger = logging.getLogger(__name__)

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
    try:
        today = date.today()
        voting_date = (today - timedelta(days=1)).isoformat()  # Use yesterday's date for voting
        logger.debug(f"Voting date: {voting_date}")
        
        if not user.votes_per_category:
            user.votes_per_category = {}
        
        # Ensure the voting_date exists in votes_per_category
        if voting_date not in user.votes_per_category:
            user.votes_per_category[voting_date] = {}
        
        logger.debug(f"User's votes_per_category: {user.votes_per_category}")
        
        current_votes = user.votes_per_category[voting_date].get(category, 0)
        logger.debug(f"Current votes for {category}: {current_votes}")
        
        if current_votes >= MAX_VOTES_PER_CATEGORY:
            return 0

        user.votes_per_category[voting_date][category] = current_votes + 1
        user.daily_votes = sum(user.votes_per_category[voting_date].values())
        user.last_vote_date = datetime.now()

        logger.debug(f"Updated votes_per_category: {user.votes_per_category}")
        logger.debug(f"Updated daily_votes: {user.daily_votes}")
        logger.debug(f"Updated last_vote_date: {user.last_vote_date}")

        flag_modified(user, "votes_per_category")
        flag_modified(user, "daily_votes")
        flag_modified(user, "last_vote_date")
        
        update_voting_streak(user, session_db)
        
        session_db.add(user)
        session_db.commit()
        
        remaining_votes = MAX_VOTES_PER_CATEGORY - user.votes_per_category[voting_date][category]
        return max(remaining_votes, 0)
    except Exception as e:
        logger.error(f"Error in increment_user_vote: {str(e)}", exc_info=True)
        raise

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