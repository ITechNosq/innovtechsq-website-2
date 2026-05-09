import asyncio
import logging
import sys
import os

# Ensure backend directory is in path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.email_service import get_email_service
from app.core.config import get_email_config

# Configure logging to see output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestEmailReply")

def test_automated_reply(target_email: str):
    logger.info("=========================================")
    logger.info(f"Initiating Automated Reply Test for: {target_email}")
    logger.info("=========================================")
    
    config = get_email_config()
    if not config.get("user") or not config.get("password"):
        logger.warning("SMTP credentials (SMTP_USER / SMTP_PASSWORD) are NOT configured in .env!")
        logger.warning("Falling back to MockEmailService. The email will NOT be sent over the internet, but the backend logic will execute successfully.")
    else:
        logger.info(f"SMTP is configured for user: {config.get('user')}. Attempting to send real email...")
    
    email_service = get_email_service()
    
    # Simulate the automated reply
    success = email_service.send_auto_responder_email(
        lead_name="InnovTech Test User",
        lead_email=target_email,
        lead_phone="+91 0000000000",
        lead_message="Testing the automated reply system."
    )
    
    if success:
        logger.info("✅ SUCCESS: The automated reply logic executed immediately without errors!")
    else:
        logger.error("❌ FAILED: There was an issue executing the automated reply.")
        
    logger.info("=========================================")

if __name__ == "__main__":
    test_automated_reply("innovtechnosq@gmail.com")
