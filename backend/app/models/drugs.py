from sqlalchemy import Column, BigInteger, Integer, String, Text, ForeignKey, Index
from app.database import Base


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False, index=True)
    caseid = Column(BigInteger, nullable=False)
    drug_seq = Column(Integer, nullable=False)
    role_cod = Column(String(2), index=True)
    drugname_original = Column(Text)
    drugname_normalized = Column(Text, index=True)
    rxcui = Column(String(20))
    route = Column(String(50))
    dose_amt = Column(String(20))
    dose_unit = Column(String(20))
    dose_form = Column(String(50))
    dose_freq = Column(String(20))
    dechal = Column(String(1))
    rechal = Column(String(1))
    source_quarter = Column(String(6), nullable=False)
