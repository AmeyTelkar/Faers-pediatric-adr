from sqlalchemy import Column, BigInteger, String, ForeignKey
from app.database import Base


class ReportSource(Base):
    __tablename__ = "report_sources"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    primaryid = Column(BigInteger, ForeignKey("demographics.primaryid"), nullable=False)
    caseid = Column(BigInteger, nullable=False)
    rpsr_cod = Column(String(5))
    source_quarter = Column(String(6), nullable=False)
