from datetime import datetime
from sqlalchemy import Column, Enum, Integer, String, DateTime
from database import Base


# Define the Video model
class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    original_location = Column(String)
    compressed_location = Column(String)
    thumbnail_location = Column(String)
    file_type = Column(String)
    status = Column(Enum('pending', 'complete', 'failed', name="processing_status"), default="pending")
