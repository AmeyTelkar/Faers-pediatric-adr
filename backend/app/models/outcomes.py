from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey
from app.database import Base


class Outcome(Base):
    __tablename__ = "outcomes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False)
    caseid = Column(BigInteger, nullable=False)
    outc_cod = Column(String(2), nullable=False)
    severity_score = Column(Integer, nullable=False)
    source_quarter = Column(String(6), nullable=False)
