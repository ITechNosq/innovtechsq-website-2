import httpx
import logging
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

async def verify_turnstile(token: str, remote_ip: str = None) -> bool:
    """
    Verify Cloudflare Turnstile token.
    """
    if not settings.TURNSTILE_SECRET_KEY:
        logger.warning("TURNSTILE_SECRET_KEY not set, skipping verification")
        return True

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=5.0)
            result = response.json()
            
            if result.get("success"):
                return True
                
            logger.warning(f"Turnstile verification failed: {result}")
            return False
    except Exception as e:
        logger.error(f"Turnstile API error: {e}")
        # Fail open or closed depending on strictness. For lead gen, fail closed to prevent spam, 
        # but if it's an internal error, maybe fail open? Let's fail closed for security.
        return False
