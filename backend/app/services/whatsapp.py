"""
WhatsApp Service Integration
This requires a 3rd party API like Twilio or Meta's official WhatsApp Business API.
"""
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        # In a real app, these would come from settings (.env)
        self.twilio_account_sid = ""
        self.twilio_auth_token = ""
        self.from_number = "whatsapp:+14155238886" # Twilio sandbox number
        self.to_number = "whatsapp:+918595237962" # Admin number
        
        self._enabled = bool(self.twilio_account_sid and self.twilio_auth_token)

    async def send_whatsapp_notification(self, lead_name: str, lead_phone: str) -> bool:
        """
        Send a WhatsApp message to the admin when a new lead is captured.
        """
        if not self._enabled:
            logger.warning("[WhatsApp] API Keys missing. WhatsApp cannot work without API credentials (e.g., Twilio).")
            return False

        message_body = f"🚀 New Lead: {lead_name}\n📞 Phone: {lead_phone}\nPlease check the admin dashboard."

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        data = {
            "From": self.from_number,
            "To": self.to_number,
            "Body": message_body
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    data=data,
                    auth=(self.twilio_account_sid, self.twilio_auth_token)
                )
                
                if response.status_code in (200, 201):
                    logger.info("✅ WhatsApp notification sent successfully.")
                    return True
                else:
                    logger.error(f"❌ Failed to send WhatsApp: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ WhatsApp API Error: {e}")
            return False

whatsapp_service = WhatsAppService()
