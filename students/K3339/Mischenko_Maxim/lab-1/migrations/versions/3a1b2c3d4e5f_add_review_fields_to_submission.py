"""add_review_fields_to_submission

Revision ID: 3a1b2c3d4e5f
Revises: 8aeac767bcc0
Create Date: 2026-06-06 15:38:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '8aeac767bcc0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add review fields to submission table
    op.add_column('submission', sa.Column('score', sa.Float(), nullable=True))
    op.add_column('submission', sa.Column('reviewer_id', sa.Integer(), nullable=True))
    op.add_column('submission', sa.Column('review_comment', sa.String(), nullable=True))
    op.add_column('submission', sa.Column('reviewed_at', sa.String(), nullable=True))
    op.add_column('submission', sa.Column('status', sa.String(), nullable=False, server_default=sa.text("'pending'")))
    
    # Add foreign key constraint for reviewer
    op.create_foreign_key(
        'fk_submission_reviewer_user',
        'submission', 'user',
        ['reviewer_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key first
    op.drop_constraint('fk_submission_reviewer_user', 'submission', type_='foreignkey')
    
    # Drop columns
    op.drop_column('submission', 'status')
    op.drop_column('submission', 'reviewed_at')
    op.drop_column('submission', 'review_comment')
    op.drop_column('submission', 'reviewer_id')
    op.drop_column('submission', 'score')