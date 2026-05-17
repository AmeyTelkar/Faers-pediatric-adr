"""Add gnn_checkpoints table

Revision ID: 002
Create Date: 2025-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # GNN training checkpoints metadata
    op.create_table(
        "gnn_checkpoints",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("age_group", sa.String(15), nullable=False),
        sa.Column("val_auc", sa.Numeric),
        sa.Column("test_auc", sa.Numeric),
        sa.Column("epochs", sa.Integer),
        sa.Column("n_drugs", sa.Integer),
        sa.Column("n_adrs", sa.Integer),
        sa.Column("n_edges", sa.Integer),
        sa.Column("checkpoint_path", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Add missing columns to signal_cache if they don't exist
    # (signal_cache was created in 001, we add columns that 001 missed)
    try:
        op.add_column("signal_cache", sa.Column("n10", sa.Integer))
    except Exception:
        pass
    try:
        op.add_column("signal_cache", sa.Column("n01", sa.Integer))
    except Exception:
        pass
    try:
        op.add_column("signal_cache", sa.Column("n00", sa.Integer))
    except Exception:
        pass
    try:
        op.add_column("signal_cache", sa.Column("is_signal", sa.Boolean, server_default="false"))
    except Exception:
        pass


def downgrade():
    op.drop_table("gnn_checkpoints")
