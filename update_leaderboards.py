import os
import sys
import logging
from datetime import date, timedelta
from sqlalchemy.exc import SQLAlchemyError

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.utils.get_leaderboard import update_daily_leaderboard
from app.models.db import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_all_leaderboards(target_date=None):
    """
    Update leaderboards for all categories for a specific date.
    If no date is provided, it updates for yesterday.
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)
    
    categories = ['tiny_story', 'scene_description', 'specific_word', 'rhyming_phrase', 
                    'emotion', 'dialogue', 'idiom', 'slogan', 'movie_quote']
    
    app = create_app()
    with app.app_context():
        session = get_db_connection()
        try:
            for category in categories:
                logger.info(f"Updating leaderboard for category: {category}, date: {target_date}")
                update_daily_leaderboard(category, target_date)
            logger.info("All leaderboards updated successfully")
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {str(e)}")
            session.rollback()
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
        finally:
            session.close()

if __name__ == "__main__":
    # Check if a date argument is provided
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            logger.error("Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
    else:
        target_date = None
    
    update_all_leaderboards(target_date)