"""Initial schema — all FAERS tables

Revision ID: 001
Create Date: 2025-01-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Upload sessions
    op.create_table(
        "upload_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("quarter", sa.String(6), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("files_uploaded", postgresql.ARRAY(sa.Text), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("row_stats", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Demographics
    op.create_table(
        "demographics",
        sa.Column("primaryid", sa.BigInteger, primary_key=True),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("caseversion", sa.Integer, nullable=False),
        sa.Column("i_f_code", sa.String(1)),
        sa.Column("event_dt", sa.Date),
        sa.Column("fda_dt", sa.Date),
        sa.Column("rept_cod", sa.String(10)),
        sa.Column("age_raw", sa.Numeric),
        sa.Column("age_cod", sa.String(5)),
        sa.Column("age_years", sa.Numeric),
        sa.Column("age_group", sa.String(20)),
        sa.Column("is_age_imputed", sa.Boolean, server_default="false"),
        sa.Column("sex", sa.String(1)),
        sa.Column("weight_kg", sa.Numeric),
        sa.Column("occp_cod", sa.String(5)),
        sa.Column("reporter_country", sa.String(5)),
        sa.Column("occr_country", sa.String(5)),
        sa.Column("event_dt_partial", sa.Boolean, server_default="false"),
        sa.Column("source_quarter", sa.String(6), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                   sa.ForeignKey("upload_sessions.session_id")),
    )
    op.create_index("idx_demo_age_group", "demographics", ["age_group"])
    op.create_index("idx_demo_quarter", "demographics", ["source_quarter"])
    op.create_index("idx_demo_caseid", "demographics", ["caseid"])

    # Drugs
    op.create_table(
        "drugs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("drug_seq", sa.Integer, nullable=False),
        sa.Column("role_cod", sa.String(2)),
        sa.Column("drugname_original", sa.Text),
        sa.Column("drugname_normalized", sa.Text),
        sa.Column("rxcui", sa.String(20)),
        sa.Column("route", sa.String(50)),
        sa.Column("dose_amt", sa.String(20)),
        sa.Column("dose_unit", sa.String(20)),
        sa.Column("dose_form", sa.String(50)),
        sa.Column("dose_freq", sa.String(20)),
        sa.Column("dechal", sa.String(1)),
        sa.Column("rechal", sa.String(1)),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )
    op.create_index("idx_drugs_primaryid", "drugs", ["primaryid"])
    op.create_index("idx_drugs_normalized", "drugs", ["drugname_normalized"])
    op.create_index("idx_drugs_role", "drugs", ["role_cod"])

    # Reactions
    op.create_table(
        "reactions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("pt_term", sa.Text, nullable=False),
        sa.Column("drug_rec_act", sa.Text),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )
    op.create_index("idx_reac_primaryid", "reactions", ["primaryid"])
    op.create_index("idx_reac_pt", "reactions", ["pt_term"])

    # Outcomes
    op.create_table(
        "outcomes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("outc_cod", sa.String(2), nullable=False),
        sa.Column("severity_score", sa.Integer, nullable=False),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )

    # Report sources
    op.create_table(
        "report_sources",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("rpsr_cod", sa.String(5)),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )

    # Therapy
    op.create_table(
        "therapy",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("dsg_drug_seq", sa.Integer),
        sa.Column("start_dt", sa.Date),
        sa.Column("end_dt", sa.Date),
        sa.Column("duration_days", sa.Numeric),
        sa.Column("start_dt_partial", sa.Boolean, server_default="false"),
        sa.Column("end_dt_partial", sa.Boolean, server_default="false"),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )

    # Indications
    op.create_table(
        "indications",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("primaryid", sa.BigInteger, sa.ForeignKey("demographics.primaryid"), nullable=False),
        sa.Column("caseid", sa.BigInteger, nullable=False),
        sa.Column("drug_seq", sa.Integer),
        sa.Column("indi_pt", sa.Text),
        sa.Column("source_quarter", sa.String(6), nullable=False),
    )

    # Drug normalization cache
    op.create_table(
        "drug_norm_cache",
        sa.Column("drugname_original_lower", sa.Text, primary_key=True),
        sa.Column("drugname_normalized", sa.Text),
        sa.Column("rxcui", sa.String(20)),
        sa.Column("lookup_source", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Signal cache
    op.create_table(
        "signal_cache",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("drugname_normalized", sa.Text, nullable=False),
        sa.Column("pt_term", sa.Text, nullable=False),
        sa.Column("age_group", sa.String(20), nullable=False),
        sa.Column("n11", sa.Integer, nullable=False),
        sa.Column("n1x", sa.Integer, nullable=False),
        sa.Column("nx1", sa.Integer, nullable=False),
        sa.Column("nxx", sa.Integer, nullable=False),
        sa.Column("prr", sa.Numeric),
        sa.Column("prr_ci_lower", sa.Numeric),
        sa.Column("prr_chi2", sa.Numeric),
        sa.Column("ror", sa.Numeric),
        sa.Column("ror_ci_lower", sa.Numeric),
        sa.Column("ror_ci_upper", sa.Numeric),
        sa.Column("ic", sa.Numeric),
        sa.Column("ic025", sa.Numeric),
        sa.Column("ebgm", sa.Numeric),
        sa.Column("eb05", sa.Numeric),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_quarters", postgresql.ARRAY(sa.Text), nullable=False),
        sa.UniqueConstraint("drugname_normalized", "pt_term", "age_group",
                            name="uix_signal_drug_adr_age"),
    )
    op.create_index("idx_signal_drug", "signal_cache", ["drugname_normalized"])
    op.create_index("idx_signal_adr", "signal_cache", ["pt_term"])
    op.create_index("idx_signal_age_group", "signal_cache", ["age_group"])


def downgrade():
    op.drop_table("signal_cache")
    op.drop_table("drug_norm_cache")
    op.drop_table("indications")
    op.drop_table("therapy")
    op.drop_table("report_sources")
    op.drop_table("outcomes")
    op.drop_table("reactions")
    op.drop_table("drugs")
    op.drop_table("demographics")
    op.drop_table("upload_sessions")
