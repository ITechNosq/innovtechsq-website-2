"""
Innovtechnosq - Automated Service Request (SR) Email System
Senior Full-Stack Implementation using SMTP
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Handles automated professional communications for Innovtechnosq.
    Configure GMAIL_USER and GMAIL_APP_PASSWORD in your .env file.
    """
    
    def __init__(self):
        # These settings are pulled from backend/app/core/config.py which reads the .env
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.is_configured = bool(self.user and self.password)

    def send_auto_responder(self, client_name: str, client_email: str, sr_id: str):
        """
        Sends a premium HTML confirmation email to the client immediately upon SR submission.
        """
        if not self.is_configured:
            logger.warning("[EMAIL] System not configured. Skipping auto-responder.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Confirmation: Service Request {sr_id} Received - Innovtechnosq"
            msg["From"] = f"Innovtechnosq Support <{self.user}>"
            msg["To"] = client_email

            # Professional HTML Template
            html_content = f"""
            <html>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 40px;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;">
                    <div style="background: #3b82f6; padding: 30px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: -0.5px;">Innovtechnosq</h1>
                    </div>
                    <div style="padding: 40px;">
                        <h2 style="color: #0f172a; margin-top: 0;">Hello {client_name},</h2>
                        <p>Thank you for choosing <strong>Innovtechnosq</strong>. We have successfully logged your Service Request.</p>
                        
                        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 20px; margin: 25px 0; text-align: center;">
                            <span style="display: block; font-size: 12px; color: #3b82f6; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">Service Request ID</span>
                            <span style="font-size: 28px; font-weight: 800; color: #1e3a8a;">{sr_id}</span>
                        </div>

                        <p><strong>What's next?</strong></p>
                        <ul style="padding-left: 20px; color: #475569;">
                            <li>A senior technical engineer is reviewing your requirements.</li>
                            <li>You will receive a call or email within 30-60 minutes.</li>
                            <li>A custom solution proposal will be prepared for your business.</li>
                        </ul>

                        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                            <p style="font-size: 14px; color: #64748b; margin-bottom: 8px;">Need urgent assistance?</p>
                            <a href="tel:+918595237962" style="color: #3b82f6; font-weight: 600; text-decoration: none; margin-right: 20px;">📞 Call +91 85952 37962</a>
                            <a href="https://wa.me/918595237962" style="color: #22c55e; font-weight: 600; text-decoration: none;">💬 WhatsApp</a>
                        </div>
                    </div>
                    <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8;">
                        &copy; 2024 Innovtechnosq Pvt Ltd. All rights reserved.<br>
                        Premium IT | Security | Networking Solutions
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(f"[EMAIL] SR {sr_id} confirmation sent to {client_email}")
            return True

        except Exception as e:
            logger.error(f"[EMAIL] Failed to send SR confirmation: {e}")
            return False

# Singleton instance to be used by the API routes
email_service = EmailService()

def get_lead_notification_service():
    """Compatibility factory for lead routes."""
    return email_service

def get_admin_email():
    """Compatibility getter for admin email."""
    return settings.ADMIN_EMAIL
