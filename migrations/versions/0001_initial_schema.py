"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-03

"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(120), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("plan", sa.String(20), server_default="trial"),
        sa.Column("trial_ends", sa.DateTime()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("last_login_at", sa.DateTime()),
        sa.Column("trial_warned_at", sa.DateTime()),
        sa.Column("reset_token", sa.String(64), index=True),
        sa.Column("reset_token_expires", sa.DateTime()),
        sa.Column("subscription_end", sa.DateTime()),
        sa.Column("subscription_warned_at", sa.DateTime()),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.false()),
        sa.Column("onboarded_at", sa.DateTime()),
        sa.Column("profile_nome", sa.String(120)),
        sa.Column("profile_escritorio", sa.String(120)),
        sa.Column("profile_cargo", sa.String(80)),
    )

    op.create_table(
        "generation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("tool", sa.String(60), nullable=False),
        sa.Column("titulo", sa.String(150)),
        sa.Column("campos_json", sa.Text()),
        sa.Column("resultado", sa.Text(), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), server_default=sa.false()),
        sa.Column("feedback", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), index=True),
    )

    op.create_table(
        "template",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("tool", sa.String(60), nullable=False, index=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("campos_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade():
    op.drop_table("template")
    op.drop_table("generation")
    op.drop_table("user")
