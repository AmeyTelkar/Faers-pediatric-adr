from sqlalchemy import Column, BigInteger, Integer, String, Numeric, Boolean, Date, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Demographic(Base):
    __tablename__ = "demographics"

    primaryid = Column(BigInteger, primary_key=True)
    caseid = Column(BigInteger, nullable=False, index=True)
    caseversion = Column(Integer, nullable=False)
    i_f_code = Column(String(1))
    event_dt = Column(Date)
    fda_dt = Column(Date)
    rept_cod = Column(String(10))
    age_raw = Column(Numeric)
    age_cod = Column(String(5))
    age_years = Column(Numeric)
    age_group = Column(String(20), index=True)
    is_age_imputed = Column(Boolean, default=False)
    sex = Column(String(1))
    weight_kg = Column(Numeric)
    occp_cod = Column(String(5))
    reporter_country = Column(String(5))
    occr_country = Column(String(5))
    event_dt_partial = Column(Boolean, default=False)
    source_quarter = Column(String(6), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("upload_sessions.session_id"))
