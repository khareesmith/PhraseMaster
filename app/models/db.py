from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User
from app.models.submission import Submission
from app.models.challenge import Challenge
from app.models.leaderboard import LeaderboardEntry
import os
from datetime import datetime
from typing import Optional

# Database URL configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create PostgreSQL engine with best practices
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=1800)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Function to create a database connection
def get_db_connection():
    """
    Create a session to the PostgreSQL database.

    Returns:
        Session: The database session object.
    """
    try:
        session = Session()
        return session
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
    
# Function to get a user by email
def get_user_by_email(session, email: str) -> Optional[User]:
    """
    Retrieve a user from the database by email.

    Args:
        session (Session): The database session object.
        email (str): The email of the user to retrieve.

    Returns:
        Result: The user row if found, otherwise None.
    """
    try:
        return session.query(User).filter_by(email=email).first()
    except Exception as e:
        print(f"Database operation error: {e}")
        return None

# Function to create a new user
def create_user(session, email: str, name: str, total_votes: int = 0) -> None:
    """
    Create a new user in the database.

    Args:
        session (Session): The database session object.
        email (str): The email of the new user.
        name (str): The name of the new user.

    Returns:
        None
    """
    try:
        new_user = User(email=email, name=name, total_votes=total_votes)
        session.add(new_user)
        session.commit()
    except Exception as e:
        print(f"Database operation error: {e}")
        session.rollback()

#Function to insert a submission
def insert_submission(session, user_id: int, username: str, date: datetime, user_phrase: str, category: str, challenge_id: str, challenge: str, initial_score: int, scored_first=False, final_submission=True) -> None:
    """
    Adds a new submission into the database.

    Args:
        session (Session): The database session object.
        user_id (int): The user_id of the user submitting the phrase.
        username (str): The username of the user submitting the phrase.
        date (str): The date of the submission.
        user_phrase (str): The submitted phrase.
        category (str): The category of the challenge.
        challenge_id (str): The ID of the challenge.
        challenge (str): The original prompt of the challenge.
        initial_score (int): The initial score of the submission.
        scored_first (bool): Whether the user chose to score first before submitting.
        final_submission (bool): Whether this is the final submission or a preliminary scoring.

    Returns:
        None
    """
    try:
        new_submission = Submission(
            user_id=user_id, username=username, date=date, user_phrase=user_phrase,
            category=category, challenge_id=challenge_id, challenge=challenge, initial_score=initial_score,
            scored_first=scored_first, final_submission=final_submission
        )
        session.add(new_submission)
        session.commit()
    except Exception as e:
        print(f"Database operation error: {e}")
        session.rollback()
        raise

# Function to update a username
def update_username(session, user_id: int, new_username: str) -> None:
    """
    Update the username of a user in the database.

    Args:
        session (Session): The database session object.
        user_id (int): The ID of the user.
        new_username (str): The new username.

    Returns:
        None
    """
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            user.name = new_username
            session.query(Submission).filter_by(user_id=user_id).update({"username": new_username})
            session.commit()
    except Exception as e:
        print(f"Database operation error: {e}")
        session.rollback()
    finally:
        session.close()

# Function to check if a phrase has already been submitted
def phrase_already_submitted(session, user_id: int, category: str, date: datetime) -> bool:
    """
    Check if a phrase has already been submitted by a user for a given category and date.

    Args:
        session (Session): The database session object.
        user_id (int): The ID of the user.
        category (str): The category of the challenge.
        date (str): The date of the challenge.

    Returns:
        bool: True if the phrase has already been submitted, False otherwise.
    """
    try:
        result = session.query(Submission).filter_by(
            user_id=user_id, category=category, date=date
        ).first()
        return result is not None
    except Exception as e:
        print(f"Database operation error: {e}")
        return False
        
def create_tables():
    Base.metadata.create_all(engine)

def drop_tables():
    Base.metadata.drop_all(engine)

# Uncomment these lines if you want to recreate the tables
# drop_tables()
create_tables()

__all__ = ['User', 'Submission', 'Challenge', 'LeaderboardEntry', 'get_db_connection', 'get_user_by_email', 'create_user', 'insert_submission', 'update_username', 'phrase_already_submitted']