"""
Add change_history JSON field to memories table.

Revision ID: 2026_04_06_add_change_history
Revises: 3c16bf7adb99
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# Revision identifiers
revision = '2026_04_06_add_change_history'
down_revision = '3c16bf7adb99'
branch_labels = None
depends_on = None


def upgrade():
    # Add change_history JSON column
    op.add_column('memories', sa.Column('change_history', sa.JSON, nullable=True, server_default='[]'))
    
    # Update existing rows to have empty list instead of NULL
    op.execute(text("""
        UPDATE memories 
        SET change_history = '[]'
        WHERE change_history IS NULL
    """))


def downgrade():
    op.drop_column('memories', 'change_history')
