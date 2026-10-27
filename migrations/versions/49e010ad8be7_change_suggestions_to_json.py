"""change suggestions to json

Revision ID: 49e010ad8be7
Revises: 3773fafab7f6
Create Date: 2026-09-14 10:15:09.504071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49e010ad8be7'
down_revision: Union[str, Sequence[str], None] = '3773fafab7f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "grammar_issues",
        "suggestions",
        existing_type=sa.TEXT(),
        type_=sa.JSON(),
        existing_nullable=False,
        postgresql_using="suggestions::json"
    )


def downgrade() -> None:
    op.alter_column(
        "grammar_issues",
        "suggestions",
        existing_type=sa.JSON(),
        type_=sa.TEXT(),
        existing_nullable=False,
        postgresql_using="suggestions::text"
    )