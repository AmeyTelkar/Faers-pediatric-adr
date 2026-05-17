from sqlalchemy import Column, BigInteger, Integer, String, Text, ForeignKey
from app.database import Base


class Indication(Base):
    __tablename__ = "indications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False)
    caseid = Column(BigInteger, nullable=False)
    drug_seq = Column(Integer)
    indi_pt = Column(Text)
    source_quarter = Column(String(6), nullable=False)
