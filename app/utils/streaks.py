# Helper functions to update user streaks in the database like login streak, submission streak, and voting streak.
from datetime import datetime, timedelta
from app.models.db import User, get_db_connection
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def update_login_streak(user: User, session):
    """
    Update the login streak of the user. This function should be called whenever a user logs in. If the user has logged in yesterday, the login streak is incremented by 1. If the user has not logged in yesterday, the login streak is reset to 1.
    
    Args:
        user (User): The user whose login streak is to be updated.
        session: The SQLAlchemy session object.
    
    Returns:
        None
    """
    
    try:
        today = datetime.now().date()
        last_login_date = user.last_login_date.date() if isinstance(user.last_login_date, datetime) else user.last_login_date
        logger.debug(f"Last login date: {last_login_date}, Today: {today}")
        if last_login_date == today - timedelta(days=1):
            user.login_streak += 1
            logger.debug(f"Incrementing login streak: {user.login_streak} for user: {user.name}")
        elif last_login_date < today - timedelta(days=1):
            user.login_streak = 1
            logger.debug("Resetting login streak to 1")
        user.last_login_date = datetime.now()
        session.commit()
    except Exception as e:
        logger.error(f"Error updating login streak: {e}")

def update_submission_streak(user: User, session):
    """
    Update the submission streak of the user. This function should be called whenever a user submits a post. If the user has submitted a post yesterday, the submission streak is incremented by 1. If the user has not submitted a post yesterday, the submission streak is reset to 1.
    
    Args:
        user (User): The user whose submission streak is to be updated.
        session: The SQLAlchemy session object.
    
    Returns:
        None
    """
    
    try:
        today = datetime.now().date()
        last_submission_date = user.last_submission_date.date() if isinstance(user.last_submission_date, datetime) else user.last_submission_date
        logger.debug(f"Last submission date: {last_submission_date}, Today: {today}")
        if last_submission_date == today - timedelta(days=1):
            user.submission_streak += 1
            logger.debug(f"Incrementing submission streak: {user.submission_streak}")
        elif last_submission_date < today - timedelta(days=1):
            user.submission_streak = 1
            logger.debug("Resetting submission streak to 1")
        user.last_submission_date = datetime.now()
        session.commit()
    except Exception as e:
        logger.error(f"Error updating submission streak: {e}")

def update_voting_streak(user: User, session):
    """
    Update the voting streak of the user. This function should be called whenever a user votes on a post. If the user has voted yesterday, the voting streak is incremented by 1. If the user has not voted yesterday, the voting streak is reset to 1.
    
    Args:
        user (User): The user whose submission streak is to be updated.
        session: The SQLAlchemy session object.
    
    Returns:
        None
    """
    
    try:
        today = datetime.now().date()
        last_voting_date = user.last_voting_date.date() if isinstance(user.last_voting_date, datetime) else user.last_voting_date
        logger.debug(f"Last voting date: {last_voting_date}, Today: {today}")
        if last_voting_date == today - timedelta(days=1):
            user.voting_streak += 1
            logger.debug(f"Incrementing voting streak: {user.voting_streak}")
        elif last_voting_date < today - timedelta(days=1):
            user.voting_streak = 1
            logger.debug("Resetting voting streak to 1")
        user.last_voting_date = datetime.now()
        session.commit()
    except Exception as e:
        logger.error(f"Error updating submission streak: {e}")
