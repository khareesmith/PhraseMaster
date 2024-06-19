from sqlalchemy import create_engine, Column, Integer, String, Text, Date, BigInteger, ForeignKey, Boolean
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
import os, string, random
from datetime import datetime

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
    """
    User model for database.
    
    Attributes:
        id: The user's ID.
        email: The user's email address.
        password_hash: The hashed password.
        password_salt: The salt used to hash the password.
        name: The user's username.
        total_votes: The total number of votes the user has.
        email_verified: Whether the user's email is verified.
        google_user: Whether the user is a Google user.
        submissions: The user's submissions which have a relationship to the Submission model.
        
        login_streak: The user's login streak.
        submission_streak: The user's submission streak.
        voting_streak: The user's voting streak.
        last_login_date: The date of the user's last login.
        last_submission_date: The date of the user's last submission.
        last_voting_date: The date of the user's last vote.
    
    Methods:
        set_password: Set the password for the user by salting and hashing the password. Saves both to the database.
        check_password: Check if the password provided matches the hashed password in the database.
        get_verification_token: Get a verification token for the user.
        generate_random_password: Generate a random password of 12 characters.
        verify_verification_token: Verify the verification token for the user.
    """
    __tablename__ = 'users'
    id = Column(Integer, index=True, primary_key=True)
    email = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=True)
    password_salt = Column(String(64), nullable=True)
    name = Column(String(128), unique=True, nullable=True)
    total_votes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    email_verified = Column(Boolean, nullable=False, default=True, server_default=text("True"))
    google_user = Column(Boolean, nullable=False, default=False, server_default=text("False"))
    submissions = relationship("Submission", back_populates="user")
    
    # Streak fields
    login_streak = Column(Integer, default=0)
    submission_streak = Column(Integer, default=0)
    voting_streak = Column(Integer, default=0)
    last_login_date = Column(Date, default=datetime.now())
    last_submission_date = Column(Date, default=datetime.now())
    last_voting_date = Column(Date, default=datetime.now())
    
    def set_password(self, password):
        """
        Set the password for the user by salting and hashing the password. Saves both to the database.
        
        Args:
            password (str): The password to set.
        
        Returns:
            None
        """
        salt = os.urandom(16).hex()
        self.password_salt = salt
        salted_password = salt + password
        self.password_hash = generate_password_hash(salted_password)
        
    def check_password(self, password):
        """
        Check if the password provided matches the hashed password in the database.
        
        Args:
            password (str): The password to set.
        
        Returns:
            bool: True if the password matches, False otherwise.
        """
        salted_password = self.password_salt + password
        return check_password_hash(self.password_hash, salted_password)
    
    def get_verification_token(self, expires_sec=3600):
        """
        Get the verification token for the user.
        
        Args:
            expires_sec (int): The number of seconds before the token expires.
        
        Returns:
            str: The verification token.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
    def generate_random_password(length=12):
        """
        Generate a random password of 12 characters.
        
        Args:
            length (int): The length of the password.
        
        Returns:
            str: The random password.
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        random_password = ''.join(random.choice(characters) for i in range(length))
        return random_password

    @staticmethod
    def verify_verification_token(token):
        """
        Verify the verification token for the user.
        
        Args:
            token (str): The verification token.
        
        Returns:
            User: The user if the token is valid, otherwise None.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
# Define the Submission model    
class Submission(Base):
    """
    Submission model for the database.
    
    Attributes:
        id: The submission ID.
        date: The date of the submission.
        category: The category of the submission.
        challenge_id: The ID of the challenge.
        challenge: The original challenge prompt.
        user_phrase: The phrase submitted by the user.
        user_id: The ID of the user who submitted the phrase.
        username: The username of the user who submitted the phrase.
        initial_score: The initial score of the submission.
        votes: The number of votes the submission has.
        user: The user who submitted the phrase with a relationship to the User model.
        
    Methods:
        None
    """
    __tablename__ = 'submissions'
    id = Column(BigInteger, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    category = Column(String(64), nullable=False)
    challenge_id = Column(String(128), ForeignKey('daily_challenges.challenge_id'), nullable=False)
    challenge = Column(Text, nullable=False)
    user_phrase = Column(Text, nullable=True, default="")
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    username = Column(String(128), nullable=True)
    initial_score = Column(Integer, nullable=False, default=0, server_default=text("0"))
    votes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    user = relationship("User", back_populates="submissions")

# Define the Challenge model
class Challenge(Base):
    """
    Challenge model for the database.
    
    Attributes:
        id: The challenge ID for the database.
        challenge_id: The unique ID of the challenge.
        category: The category of the challenge.
        original_challenge: The original challenge prompt.
        date: The date of the challenge.
        
    Methods:
        None
    """
    __tablename__ = 'daily_challenges'
    id = Column(BigInteger, primary_key=True)
    challenge_id = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)
    original_challenge = Column(Text, nullable=False)
    date = Column(Date, nullable=False)

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
    except SQLAlchemyError as e:
        print(f"Database connection error: {e}")
        return None

# Function to get a user by email
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

# Function to create a new user
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

#Function to insert a submission
def insert_submission(session, user_id, username, date, user_phrase, category, challenge_id, challenge, initial_score):
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

    Returns:
        None
    """
    try:
        session.execute(text("""
            INSERT INTO submissions (user_id, username, date, user_phrase, category, challenge_id, challenge, initial_score) 
            VALUES (:user_id, :username, :date, :user_phrase, :category, :challenge_id, :challenge, :initial_score)
        """), {
            'user_id': user_id, 'username': username, 'date': date, 'user_phrase': user_phrase, 
            'category': category, 'challenge_id': challenge_id, 
            'challenge': challenge, 'initial_score': initial_score
        })
        session.commit()
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
        session.rollback()
        raise

# Function to update a username
def update_username(session, user_id, new_username):
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
        session.execute(text("UPDATE users SET name = :new_username WHERE id = :user_id"), {'new_username': new_username, 'user_id': user_id})
        session.execute(text("UPDATE submissions SET username = :new_username WHERE user_id = :user_id"), {'new_username': new_username, 'user_id': user_id})
        session.commit()
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
        session.rollback()
    finally:
        session.close()

# Function to check if a phrase has already been submitted
def phrase_already_submitted(session, user_id, category, date):
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
        result = session.execute(text('SELECT user_id FROM submissions WHERE user_id = :user_id AND category = :category AND date = :date'), {'user_id': user_id, 'category': category, 'date': date}).fetchone()
        return result is not None
    except SQLAlchemyError as e:
        print(f"Database operation error: {e}")
        return False
    finally:
        session.close()
        
# Function to create tables if they do not exist
def create_tables():
    Base.metadata.create_all(engine)
    
# Function to drop tables if needed
def drop_tables():
    Base.metadata.drop_all(engine)

# Call these functions initially to drop and create the tables in the database. Comment out the drop_tables() function if you do not want to drop the tables.
# drop_tables()
create_tables()