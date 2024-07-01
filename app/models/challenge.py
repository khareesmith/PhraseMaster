from sqlalchemy import Column, BigInteger, String, Text, Date
from sqlalchemy.orm import relationship
from .base import Base

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
    
    submissions = relationship("Submission", back_populates="daily_challenge")