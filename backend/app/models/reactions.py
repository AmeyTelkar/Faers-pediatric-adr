from sqlalchemy import Column, BigInteger, String, Text, ForeignKey, Index
from app.database import Base


class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False, index=True)
    caseid = Column(BigInteger, nullable=False)
    pt_term = Column(Text, nullable=False, index=True)
    drug_rec_act = Column(Text)
    source_quarter = Column(String(6), nullable=False)
