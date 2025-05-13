"""create_users_table

Revision ID: 1_create_users
Revises: 8d0ba4d5b8c6
Create Date: 2025-04-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1_create_users'
down_revision: Union[str, None] = '8d0ba4d5b8c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('username', sa.String(), unique=True, index=True),
        sa.Column('password', sa.String()),
        sa.Column('email', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
    )


def downgrade() -> None:
    op.drop_table('users')
