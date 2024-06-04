from sqlalchemy import create_engine, Column, Integer, String, Text, Date, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

# SQLAlchemy base model
Base = declarative_base()

# Create a PostgreSQL engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    total_votes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    submissions = relationship("Submission", back_populates="user")

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(BigInteger, primary_key=True)
    date = Column(Date, nullable=False)
    category = Column(String, nullable=False)
    challenge_id = Column(String, ForeignKey('daily_challenges.challenge_id'), nullable=False)
    challenge = Column(Text, nullable=False)
    user_phrase = Column(Text, nullable=True)  # Allow NULL values
    username = Column(String, nullable=True)
    initial_score = Column(Integer, nullable=True)
    votes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    user = relationship("User", back_populates="submissions")

# Define the Challenge model
class Challenge(Base):
    __tablename__ = 'daily_challenges'
    id = Column(BigInteger, primary_key=True)
    challenge_id = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    original_challenge = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    
def get_db_connection():
    """
    Create a session to the PostgreSQL database.

    Returns:
        Session: The database session object.
    """
    try:
        session = Session()
        return session
    except SQLAlchemyError as e:
        print(f"Database connection error: {e}")
        return None

def test_db_connection():
    try:
        session = Session()
        print("Database connection was successful!")
        session.close()
    except SQLAlchemyError as e:
        print(f"Error connecting to the database: {e}")

def get_user_by_email(session, email):
    """
    Retrieve a user from the database by email.

    Args:
        session (Session): The database session object.
        email (str): The email of the user to retrieve.

    Returns:
        Result: The user row if found, otherwise None.
    """
    try:
        result = session.execute(text('SELECT * FROM users WHERE email = :email'), {'email': email}).fetchone()
        return result
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
        return None

def create_user(session, email, name, total_votes=0):
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
        session.execute(text('INSERT INTO users (email, name, total_votes) VALUES (:email, :name, :total_votes)'), {'email': email, 'name': name, 'total_votes': total_votes})
        session.commit()
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")

def insert_submission(session, username, date, user_phrase, category, challenge_id, challenge, initial_score):
    """
    Insert a new submission into the database.

    Args:
        session (Session): The database session object.
        username (str): The username of the user submitting the phrase.
        date (str): The date of the submission.
        user_phrase (str): The submitted phrase.
        category (str): The category of the challenge.
        challenge_id (str): The ID of the challenge.
        challenge (str): The original prompt of the challenge.
        initial_score (int): The initial score of the submission.

    Returns:
        None
    """
    try:
        session.execute(text("""
            INSERT INTO submissions (username, date, user_phrase, category, challenge_id, challenge, initial_score) 
            VALUES (:username, :date, :user_phrase, :category, :challenge_id, :challenge, :initial_score)
        """), {
            'username': username, 'date': date, 'user_phrase': user_phrase, 
            'category': category, 'challenge_id': challenge_id, 
            'challenge': challenge, 'initial_score': initial_score
        })
        session.commit()
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
    finally:
        session.close()

def phrase_already_submitted(session, username, category, date):
    try:
        result = session.execute(text('SELECT username FROM submissions WHERE username = :username AND category = :category AND date = :date'), {'username': username, 'category': category, 'date': date}).fetchone()
        return result is not None
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
        return False
    finally:
        session.close()
        
# Function to create tables if they do not exist
def create_tables():
    Base.metadata.create_all(engine)

# Call this function initially to create tables if they don't exist
create_tables()