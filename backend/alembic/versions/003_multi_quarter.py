"""Add multi-quarter support: is_superseded, loaded_quarters, signal quarter_filter

Revision ID: 003
Create Date: 2025-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. Add is_superseded to all 7 data tables ──────────────────────
    for table in [
        "demographics", "drugs", "reactions", "outcomes",
        "therapy", "indications", "report_sources",
    ]:
        op.add_column(table, sa.Column(
            "is_superseded", sa.Boolean, server_default="false", nullable=False,
        ))

    # ── 2. Partial indexes for fast active-only queries ────────────────
    op.create_index(
        "idx_demo_active", "demographics", ["is_superseded"],
        postgresql_where=sa.text("is_superseded = FALSE"),
    )
    op.create_index(
        "idx_drug_active", "drugs", ["is_superseded"],
        postgresql_where=sa.text("is_superseded = FALSE"),
    )
    op.create_index(
        "idx_reac_active", "reactions", ["is_superseded"],
        postgresql_where=sa.text("is_superseded = FALSE"),
    )
    op.create_index(
        "idx_outc_active", "outcomes", ["is_superseded"],
        postgresql_where=sa.text("is_superseded = FALSE"),
    )

    # ── 3. Quarter registry table ──────────────────────────────────────
    op.create_table(
        "loaded_quarters",
        sa.Column("quarter", sa.String(6), primary_key=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("quarter_num", sa.Integer, nullable=False),
        sa.Column("quarter_label", sa.String(30), nullable=False),
        sa.Column("pediatric_rows", sa.Integer),
        sa.Column("drug_rows", sa.Integer),
        sa.Column("reaction_rows", sa.Integer),
        sa.Column("signal_count", sa.Integer, server_default="0"),
        sa.Column("gnn_trained", sa.Boolean, server_default="false"),
        sa.Column("superseded_rows", sa.Integer, server_default="0"),
        sa.Column("loaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("upload_sessions.session_id")),
    )

    # ── 4. Add quarter_filter to signal_cache ──────────────────────────
    op.add_column("signal_cache", sa.Column(
        "quarter_filter", sa.String(50), server_default="ALL",
    ))

    # Update existing unique constraint to include quarter_filter
    # Note: PostgreSQL auto-named this differently from the Alembic name
    op.drop_constraint(
        "signal_cache_drugname_normalized_pt_term_age_group_key",
        "signal_cache", type_="unique",
    )
    op.create_unique_constraint(
        "uix_signal_drug_adr_age_qf", "signal_cache",
        ["drugname_normalized", "pt_term", "age_group", "quarter_filter"],
    )


def downgrade():
    # Restore old unique constraint
    op.drop_constraint("uix_signal_drug_adr_age_qf", "signal_cache", type_="unique")
    op.create_unique_constraint(
        "signal_cache_drugname_normalized_pt_term_age_group_key", "signal_cache",
        ["drugname_normalized", "pt_term", "age_group"],
    )
    op.drop_column("signal_cache", "quarter_filter")

    op.drop_table("loaded_quarters")

    for idx in ["idx_demo_active", "idx_drug_active", "idx_reac_active", "idx_outc_active"]:
        op.drop_index(idx)

    for table in [
        "demographics", "drugs", "reactions", "outcomes",
        "therapy", "indications", "report_sources",
    ]:
        op.drop_column(table, "is_superseded")
