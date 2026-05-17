import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.database import Base


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quarter = Column(String(6), nullable=False)
    year = Column(Integer, nullable=False)
    files_uploaded = Column(ARRAY(Text), nullable=False)
    status = Column(String(20), default="pending")
    row_stats = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
