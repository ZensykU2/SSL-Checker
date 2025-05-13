"""create_websites_and_logs

Revision ID: 2_create_websites_logs
Revises: 1_create_users
Create Date: 2025-04-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2_create_websites_logs'
down_revision: Union[str, None] = '1_create_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'websites',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('url', sa.String(), nullable=False, index=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('threshold_days', sa.Integer(), nullable=False),
        sa.Column('next_warning', sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.UniqueConstraint('url', 'user_id', name='unique_user_website'),
    )

    op.create_table(
        'check_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('website_id', sa.Integer(), sa.ForeignKey('websites.id'), nullable=False),
        sa.Column('checked_at', sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('remaining_days', sa.Integer()),
        sa.Column('email_sent', sa.Boolean(), default=False),
    )


def downgrade() -> None:
    op.drop_table('check_logs')
    op.drop_table('websites')
