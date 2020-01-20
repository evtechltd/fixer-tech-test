"""Initial migration

Revision ID: 47e9c5263376
Revises:
Create Date: 2020-01-20 11:49:29.393930

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "47e9c5263376"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("currency", "date", name="uq_currency_date"),
    )
    op.create_index(op.f("ix_rate_currency"), "rate", ["currency"], unique=False)
    op.create_index(op.f("ix_rate_date"), "rate", ["date"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_rate_date"), table_name="rate")
    op.drop_index(op.f("ix_rate_currency"), table_name="rate")
    op.drop_table("rate")
