"""add user.anthropic_api_key

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("user", sa.Column("anthropic_api_key", sa.String(120), nullable=True))


def downgrade():
    op.drop_column("user", "anthropic_api_key")
