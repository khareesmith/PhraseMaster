from sqlalchemy import Column, BigInteger, String, Text, Date, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from .base import Base

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
        scored_first: Whether the submission was scored first.
        final_submission: Whether the submission is the final submission.
        
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
    
    scored_first = Column(Boolean, default=False)
    final_submission = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="submissions")
    daily_challenge = relationship("Challenge", back_populates="submissions")