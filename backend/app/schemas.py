"""
Pydantic Schemas
Request/response validation models.
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, EmailStr
import re
from typing import Optional


class LeadCreate(BaseModel):
    """
    Schema for creating a new lead from public form.
    
    NOTE: API key is passed via Authorization header, NOT request body.
    This prevents API key exposure in logs and browser.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Client's full name")
    email: EmailStr = Field(..., description="Client's email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    service_type: Optional[str] = Field("General IT", max_length=100, description="Type of service requested")
    message: Optional[str] = Field(None, max_length=2000, description="Inquiry message")
    turnstile_token: str = Field(..., description="Cloudflare Turnstile token for spam prevention")
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize name - remove HTML/script tags."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        v = v.strip()
        # Remove any HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Remove control characters
        v = re.sub(r'[\x00-\x1F\x7F]', '', v)
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number."""
        if not v or not v.strip():
            raise ValueError('Phone cannot be empty')
        v = v.strip()
        # Remove common phone formatting characters, keep only digits and +
        v = re.sub(r'[\s\-\(\)\.]', '', v)
        # Validate - must be 10-15 digits, optionally starting with +
        if not re.match(r'^\+?\d{10,15}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize message - remove dangerous content."""
        if v is None:
            return None
        v = v.strip()
        # Remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        # Remove control characters
        v = re.sub(r'[\x00-\x1F\x7F]', '', v)
        # Enforce max length
        v = v[:2000]
        return v if v else None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "919876543210",
                "message": "I'm interested in IT support services",
                "turnstile_token": "1x00000000000000000000AA"
            }
        }
    }


class LeadResponse(BaseModel):
    """
    Schema for lead response (excludes sensitive data).
    """
    id: int
    name: str
    email: str
    phone: str
    service_type: Optional[str]
    message: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class LeadStats(BaseModel):
    """Schema for lead statistics."""
    total: int
    today: int
    week: int


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema for success responses."""
    message: str
    lead_id: Optional[int] = None
