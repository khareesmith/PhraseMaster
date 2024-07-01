"""Add LeaderboardEntry model

Revision ID: 88b17198dffa
Revises: f64c8544603d
Create Date: 2024-07-01 12:08:26.958360

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '88b17198dffa'
down_revision = 'f64c8544603d'
branch_labels = None
depends_on = None

def upgrade():
    # Check if daily_challenges table exists before trying to drop it
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    if 'daily_challenges' in inspector.get_table_names():
        # First, drop the foreign key constraint if it exists
        if 'submissions_challenge_id_fkey' in [fk['name'] for fk in inspector.get_foreign_keys('submissions')]:
            op.drop_constraint('submissions_challenge_id_fkey', 'submissions', type_='foreignkey')
        
        # Now we can safely drop the daily_challenges table
        op.drop_table('daily_challenges')

    # Check if leaderboard_entries table already exists
    if 'leaderboard_entries' not in inspector.get_table_names():
        # Create leaderboard_entries table only if it doesn't exist
        op.create_table('leaderboard_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    # Drop the leaderboard_entries table
    op.drop_table('leaderboard_entries')
    
    # Recreate the daily_challenges table
    op.create_table('daily_challenges',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('challenge_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('original_challenge', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='daily_challenges_pkey'),
    sa.UniqueConstraint('challenge_id', name='daily_challenges_challenge_id_key')
    )
    
    # Recreate the foreign key constraint
    op.create_foreign_key('submissions_challenge_id_fkey', 'submissions', 'daily_challenges', ['challenge_id'], ['challenge_id'])