"""
Database Models
SQLAlchemy models for the Lead table.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Lead(Base):
    """
    Lead model representing a form submission/contact request.
    
    Attributes:
        id: Primary key
        name: Client's name
        phone: Contact phone number
        message: Inquiry message
        created_at: Submission timestamp
    """
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)
    service_type = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name='{self.name}', phone='{self.phone}')>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excludes sensitive data)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "service_type": self.service_type,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
