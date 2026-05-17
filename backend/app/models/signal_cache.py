from sqlalchemy import Column, BigInteger, String, Text, Numeric, Integer, DateTime, func, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY
from app.database import Base


class SignalCache(Base):
    __tablename__ = "signal_cache"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    drugname_normalized = Column(Text, nullable=False, index=True)
    pt_term = Column(Text, nullable=False, index=True)
    age_group = Column(String(20), nullable=False, index=True)
    n11 = Column(Integer, nullable=False)
    n1x = Column(Integer, nullable=False)
    nx1 = Column(Integer, nullable=False)
    nxx = Column(Integer, nullable=False)
    prr = Column(Numeric)
    prr_ci_lower = Column(Numeric)
    prr_chi2 = Column(Numeric)
    ror = Column(Numeric)
    ror_ci_lower = Column(Numeric)
    ror_ci_upper = Column(Numeric)
    ic = Column(Numeric)
    ic025 = Column(Numeric)
    ebgm = Column(Numeric)
    eb05 = Column(Numeric)
    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    source_quarters = Column(ARRAY(Text), nullable=False)

    __table_args__ = (
        UniqueConstraint("drugname_normalized", "pt_term", "age_group",
                         name="uix_signal_drug_adr_age"),
    )


class DrugNormCache(Base):
    __tablename__ = "drug_norm_cache"

    drugname_original_lower = Column(Text, primary_key=True)
    drugname_normalized = Column(Text)
    rxcui = Column(String(20))
    lookup_source = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
