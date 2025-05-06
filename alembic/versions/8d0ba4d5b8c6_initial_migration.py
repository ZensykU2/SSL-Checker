"""Initial migration

Revision ID: 8d0ba4d5b8c6
Revises: 
Create Date: 2025-05-02 10:39:43.923768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d0ba4d5b8c6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(), unique=True, index=True),
        sa.Column('password', sa.String()),
        sa.Column('email', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
    )

    op.create_table(
        'websites',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('url', sa.String(), nullable=False, index=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('threshold_days', sa.Integer(), nullable=False),
        sa.Column('next_warning', sa.DateTime(), default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.UniqueConstraint('url', 'user_id', name='unique_user_website'),
    )

    op.create_table(
        'check_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('website_id', sa.Integer(), sa.ForeignKey('websites.id'), nullable=False),
        sa.Column('checked_at', sa.DateTime(), default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('remaining_days', sa.Integer()),
        sa.Column('email_sent', sa.Boolean(), default=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('check_logs')
    op.drop_table('websites')
    op.drop_table('users')
