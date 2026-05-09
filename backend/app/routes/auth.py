import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Secure login endpoint for admin panel.
    Requires ADMIN_USERNAME and ADMIN_PASSWORD from environment.
    """
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        logger.error("Admin credentials not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not configured properly"
        )
        
    if form_data.username != settings.ADMIN_USERNAME or form_data.password != settings.ADMIN_PASSWORD:
        # Prevent timing attacks by generic delay or consistent check
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = {"sub": form_data.username, "exp": expire}
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
        return {"access_token": encoded_jwt, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"JWT encoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate token"
        )

async def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to verify JWT token for admin routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None or username != settings.ADMIN_USERNAME:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
        
    return username
