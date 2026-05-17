from sqlalchemy import Column, BigInteger, Integer, String, Date, Numeric, Boolean, ForeignKey
from app.database import Base


class Therapy(Base):
    __tablename__ = "therapy"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False)
    caseid = Column(BigInteger, nullable=False)
    dsg_drug_seq = Column(Integer)
    start_dt = Column(Date)
    end_dt = Column(Date)
    duration_days = Column(Numeric)
    start_dt_partial = Column(Boolean, default=False)
    end_dt_partial = Column(Boolean, default=False)
    source_quarter = Column(String(6), nullable=False)
