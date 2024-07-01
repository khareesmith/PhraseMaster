from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from sqlalchemy.dialects.postgresql import JSONB
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from .base import Base
from werkzeug.security import generate_password_hash, check_password_hash
import os
import string
import random

# Definition of the User model for the database.
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
        is_admin: Whether the user is an admin.
        
        login_streak: The user's login streak.
        submission_streak: The user's submission streak.
        voting_streak: The user's voting streak.
        last_login_date: The date of the user's last login.
        last_submission_date: The date of the user's last submission.
        last_voting_date: The date of the user's last vote.
        
        daily_votes: The number of votes the user has for the day.
        last_vote_date: The date of the user's last vote.
        
        submissions: The user's submissions which have a relationship to the Submission model.
    
    Methods:
        set_password: Set the password for the user by salting and hashing the password. Saves both to the database.
        check_password: Check if the password provided matches the hashed password in the database.
        get_verification_token: Get a verification token for the user.
        generate_random_password: Generate a random password of 12 characters.
        verify_verification_token: Verify the verification token for the user.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=True)
    password_salt = Column(String(64), nullable=True)
    name = Column(String(128), unique=True, nullable=True)
    total_votes = Column(Integer, nullable=False, default=0, server_default=text("0"))
    email_verified = Column(Boolean, nullable=False, default=True, server_default=text("True"))
    google_user = Column(Boolean, nullable=False, default=False, server_default=text("False"))
    is_admin = Column(Boolean, nullable=False, default=False)
    
    # Streak fields
    login_streak = Column(Integer, default=0)
    submission_streak = Column(Integer, default=0)
    voting_streak = Column(Integer, default=0)
    last_login_date = Column(Date, default=datetime.now)
    last_submission_date = Column(Date, default=datetime.now)
    last_voting_date = Column(Date, default=datetime.now)
    
    # Vote fields
    daily_votes = Column(Integer, default=0)
    last_vote_date = Column(DateTime)
    votes_per_category = Column(JSONB, default={})
    
    submissions = relationship("Submission", back_populates="user")
    
    def set_password(self, password: str) -> None:
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
        
    def check_password(self, password: str) -> bool:
        """
        Check if the password provided matches the hashed password in the database.
        
        Args:
            password (str): The password to set.
        
        Returns:
            bool: True if the password matches, False otherwise.
        """
        salted_password = self.password_salt + password
        return check_password_hash(self.password_hash, salted_password)
    
    def get_verification_token(self, expires_sec: int = 3600) -> str:
        """
        Get the verification token for the user.
        
        Args:
            expires_sec (int): The number of seconds before the token expires.
        
        Returns:
            str: The verification token.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """
        Generate a random password of 12 characters.
        
        Args:
            length (int): The length of the password.
        
        Returns:
            str: The random password.
        """
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(characters) for i in range(length))

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