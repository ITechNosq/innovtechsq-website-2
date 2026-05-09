"""
Lead Routes - SECURED
All endpoints require authentication.

Security:
- Client API key for lead submission (via Authorization header)
- Admin API key for admin endpoints
- Rate limiting per IP
- Input validation and sanitization
- Secure error handling (no internal details leaked)
"""
from datetime import datetime, timedelta
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models import Lead
from app.schemas import (
    LeadCreate, LeadResponse, LeadStats, SuccessResponse, ErrorResponse
)
from app.core.config import settings
from app.core.rate_limiter import check_ip_rate_limit, check_email_rate_limit
from app.services.email_service import get_lead_notification_service, get_admin_email
from app.services.turnstile import verify_turnstile
from app.routes.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


# ============== PAGINATION ==============

def get_pagination_params(
    skip: int = 0,
    limit: int = None
) -> tuple[int, int]:
    """
    Get sanitized pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Max records to return
        
    Returns:
        Tuple of (skip, limit)
    """
    # Sanitize skip
    try:
        skip = max(0, int(skip))
    except (ValueError, TypeError):
        skip = 0
    
    # Sanitize and cap limit
    default_limit = settings.DEFAULT_PAGE_SIZE
    max_limit = settings.MAX_PAGE_SIZE
    
    try:
        limit = int(limit) if limit else default_limit
    except (ValueError, TypeError):
        limit = default_limit
    
    limit = min(max(1, limit), max_limit)
    
    return skip, limit


# ============== ROUTES ==============

@router.post(
    "",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Create a new lead from form submission.
    
    SECURITY:
    - CAPTCHA (Turnstile) verification
    - Rate limited per IP
    - Input validated and sanitized
    
    Request Body:
        name: Client's full name (required)
        email: Client's email address (required)
        phone: Phone number (required)
        message: Inquiry message (optional)
        turnstile_token: Cloudflare Turnstile token (required)
    """
    client_ip = request.client.host if request.client else "unknown"
    request_id = str(uuid.uuid4())[:8]
    
    # 1. Rate limiting (IP)
    allowed, rate_info = check_ip_rate_limit(client_ip)
    if not allowed:
        logger.warning(f"Rate limit exceeded for IP {client_ip} [req={request_id}]")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
        
    # 2. Rate limiting (Email)
    email_allowed, _ = check_email_rate_limit(lead.email)
    if not email_allowed:
        logger.warning(f"Rate limit exceeded for Email {lead.email} [req={request_id}]")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests for this email. Please try again later."
        )
        
    # 3. CAPTCHA verification
    is_valid_bot = await verify_turnstile(lead.turnstile_token, client_ip)
    if not is_valid_bot:
        logger.warning(f"Turnstile verification failed for {client_ip} [req={request_id}]")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot verification failed. Please try again."
        )
    
    # 4. Check for duplicate (within time window)
    window_start = datetime.now() - timedelta(hours=settings.DUPLICATE_WINDOW_HOURS)
    existing = db.query(Lead).filter(
        or_(Lead.phone == lead.phone, Lead.email == lead.email),
        Lead.created_at >= window_start
    ).first()
    
    if existing:
        logger.info(f"Duplicate lead detected: {lead.phone} [req={request_id}]")
        return SuccessResponse(
            message="Lead already captured",
            lead_id=existing.id
        )
    
    try:
        # 5. Create lead
        db_lead = Lead(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            message=lead.message
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        
        logger.info(f"Lead created: ID={db_lead.id}, email={lead.email} [req={request_id}]")
        
        # 6. Send email notifications via BackgroundTasks (non-blocking)
        admin_email = get_admin_email()
        email_service = get_lead_notification_service()
        
        if admin_email:
            background_tasks.add_task(
                email_service.send_lead_notification,
                lead_name=lead.name,
                lead_phone=lead.phone,
                lead_message=lead.message or "",
                to_email=admin_email
            )
            
        background_tasks.add_task(
            email_service.send_auto_responder_email,
            lead_name=lead.name,
            lead_email=lead.email,
            lead_phone=lead.phone,
            lead_message=lead.message or ""
        )
        
        return SuccessResponse(
            message="Lead captured successfully",
            lead_id=db_lead.id
        )
        
    except Exception as e:
        db.rollback()
        # Log internally but return generic message
        logger.error(f"Failed to create lead [req={request_id}]: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process request"
        )


@router.get(
    "",
    response_model=list[LeadResponse],
    responses={401: {"model": ErrorResponse}}
)
async def get_leads(
    skip: int = 0,
    limit: int = None,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
) -> list[LeadResponse]:
    """
    Get all leads (ADMIN ONLY).
    
    SECURITY:
    - Requires valid JWT token in Authorization header
    
    Query Parameters:
        skip: Number of records to skip (default: 0)
        limit: Max records to return (default: 20, max: 100)
    """
    skip, limit = get_pagination_params(skip, limit)
    
    leads = db.query(Lead).order_by(
        Lead.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return leads


@router.get("/stats", response_model=LeadStats)
async def get_lead_stats(
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
) -> LeadStats:
    """
    Get lead statistics (ADMIN ONLY).
    
    SECURITY:
    - Requires valid JWT token in Authorization header
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    
    # Total leads
    total = db.query(func.count(Lead.id)).scalar() or 0
    
    # Today's leads
    today = db.query(func.count(Lead.id)).filter(
        Lead.created_at >= today_start
    ).scalar() or 0
    
    # This week's leads
    week = db.query(func.count(Lead.id)).filter(
        Lead.created_at >= week_start
    ).scalar() or 0
    
    return LeadStats(total=total, today=today, week=week)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    admin: str = Depends(get_current_admin)
) -> LeadResponse:
    """
    Get a single lead by ID (ADMIN ONLY).
    
    SECURITY:
    - Requires valid JWT token in Authorization header
    """
    # Validate lead_id
    if lead_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid lead ID"
        )
    
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return lead
