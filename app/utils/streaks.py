from datetime import datetime, timedelta
from app.models.db import User
from sqlalchemy.orm import Session
import logging
from typing import Callable

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def update_streak(user: User, session: Session, streak_type: str) -> None:
    """
    Generic function to update user streaks (login, submission, voting).

    Args:
        user (User): The user whose streak is to be updated.
        session (Session): The SQLAlchemy session object.
        streak_type (str): The type of streak to update ('login', 'submission', or 'voting').

    Raises:
        ValueError: If an invalid streak_type is provided.
    """
    streak_attributes = {
        'login': ('last_login_date', 'login_streak'),
        'submission': ('last_submission_date', 'submission_streak'),
        'voting': ('last_voting_date', 'voting_streak')
    }

    if streak_type not in streak_attributes:
        raise ValueError(f"Invalid streak_type: {streak_type}")

    last_date_attr, streak_attr = streak_attributes[streak_type]

    try:
        today = datetime.now().date()
        last_date = getattr(user, last_date_attr)
        last_date = last_date.date() if isinstance(last_date, datetime) else last_date
        
        logger.debug(f"Last {streak_type} date: {last_date}, Today: {today}")

        if last_date == today - timedelta(days=1):
            setattr(user, streak_attr, getattr(user, streak_attr) + 1)
            logger.debug(f"Incrementing {streak_type} streak: {getattr(user, streak_attr)}")
        elif last_date < today - timedelta(days=1):
            setattr(user, streak_attr, 1)
            logger.debug(f"Resetting {streak_type} streak to 1")

        setattr(user, last_date_attr, datetime.now())
        session.commit()
    except Exception as e:
        logger.error(f"Error updating {streak_type} streak: {e}")
        session.rollback()

update_login_streak: Callable[[User, Session], None] = lambda user, session: update_streak(user, session, 'login')
update_submission_streak: Callable[[User, Session], None] = lambda user, session: update_streak(user, session, 'submission')
update_voting_streak: Callable[[User, Session], None] = lambda user, session: update_streak(user, session, 'voting')