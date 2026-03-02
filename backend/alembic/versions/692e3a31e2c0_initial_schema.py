"""initial schema

Revision ID: 692e3a31e2c0
Revises:
Create Date: 2026-03-01 23:36:29.827316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '692e3a31e2c0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cameras',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('has_ptz', sa.Boolean(), nullable=True),
        sa.Column('has_recording', sa.Boolean(), nullable=True),
        sa.Column('recording_segment_seconds', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ip_address'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cameras')
