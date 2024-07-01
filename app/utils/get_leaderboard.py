from datetime import date, timedelta
from sqlalchemy import func
from app.models.db import get_db_connection, User, LeaderboardEntry, Submission

def update_daily_leaderboard(category, target_date=None):
    session = get_db_connection()
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    results = session.query(
        Submission.user_id,
        func.sum(Submission.votes).label('total_votes')
    ).filter(
        Submission.category == category,
        Submission.date == target_date
    ).group_by(Submission.user_id).all()

    for user_id, total_votes in results:
        entry = LeaderboardEntry(
            user_id=user_id,
            category=category,
            score=total_votes,
            date=target_date
        )
        session.merge(entry)
    
    session.commit()
    session.close()

def get_leaderboard(category, start_date, end_date):
    session = get_db_connection()
    results = session.query(
        User.name,  # Get the username
        func.sum(LeaderboardEntry.score).label('total_score')
    ).join(User, User.id == LeaderboardEntry.user_id
    ).filter(
        LeaderboardEntry.category == category,
        LeaderboardEntry.date.between(start_date, end_date)
    ).group_by(User.id, User.name
    ).order_by(func.sum(LeaderboardEntry.score).desc()
    ).limit(10).all()
    
    session.close()
    return [{"username": result.name, "total_score": result.total_score} for result in results]