"""
Email sending utility for feedback form using SMTP
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import streamlit as st
from logger import get_logger

logger = get_logger(__name__)


def send_feedback_email(name: str, email: str, message: str) -> tuple[bool, str]:
    """
    Send feedback email via SMTP
    
    Args:
        name: User's name (sanitized)
        email: User's email (sanitized)
        message: Feedback message (sanitized)
        
    Returns:
        (success: bool, message: str)
    """
    try:
        # Load SMTP config from Streamlit secrets
        mail_config = st.secrets.get("mail", {})
        
        if not mail_config:
            logger.error("Mail configuration not found in secrets")
            return False, "Email configuration not found"
        
        # Extract config
        host = mail_config.get("HOST")
        port = mail_config.get("PORT", 587)
        username = mail_config.get("USERNAME")
        password = mail_config.get("PASSWORD")
        from_addr = mail_config.get("FROM")
        to_addr = mail_config.get("TO")
        use_ssl = mail_config.get("USE_SSL", False)
        use_tls = mail_config.get("USE_TLS", True)
        timeout = mail_config.get("TIMEOUT_SECONDS", 30)  # Increased from 10 to 30
        
        # Validate required fields
        if not all([host, username, password, from_addr, to_addr]):
            logger.error("Missing required mail configuration")
            return False, "Email configuration incomplete"
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "HoopsInsight Feedback"
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Reply-To"] = email if email and "@" in email else from_addr
        
        # Create email body
        text_body = f"""
New Feedback from HoopsInsight

From: {name}
Email: {email}

Message:
{message}

---
Sent from aeo-insights.com
"""
        
        html_body = f"""
<html>
<body>
<h2>New Feedback from HoopsInsight</h2>
<p><strong>From:</strong> {name}</p>
<p><strong>Email:</strong> {email}</p>
<p><strong>Message:</strong></p>
<p style="white-space: pre-wrap;">{message}</p>
<hr>
<p style="color: #888; font-size: 12px;">Sent from aeo-insights.com</p>
</body>
</html>
"""
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email with retry logic
        max_retries = 2
        for attempt in range(max_retries):
            try:
                if use_ssl and port == 465:
                    # SSL connection (port 465)
                    logger.info(f"Attempting SSL connection to {host}:{port} (attempt {attempt+1}/{max_retries})")
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as server:
                        logger.info("Connected, logging in...")
                        server.login(username, password)
                        logger.info("Logged in, sending message...")
                        server.send_message(msg)
                        logger.info(f"Feedback email sent successfully from {name}")
                        return True, "Email sent successfully"
                else:
                    # STARTTLS connection (port 587)
                    logger.info(f"Attempting STARTTLS connection to {host}:{port} (attempt {attempt+1}/{max_retries})")
                    with smtplib.SMTP(host, port, timeout=timeout) as server:
                        logger.info("Connected, sending EHLO...")
                        server.ehlo()
                        if use_tls:
                            logger.info("Starting TLS...")
                            context = ssl.create_default_context()
                            server.starttls(context=context)
                            server.ehlo()
                        logger.info("Logging in...")
                        server.login(username, password)
                        logger.info("Sending message...")
                        server.send_message(msg)
                        logger.info(f"Feedback email sent successfully from {name}")
                        return True, "Email sent successfully"
            except (TimeoutError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt+1} failed, retrying: {e}")
                    continue
                else:
                    raise  # Re-raise on last attempt
                
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False, "Authentication failed - check email credentials"
    except smtplib.SMTPServerDisconnected as e:
        logger.error(f"SMTP server disconnected: {e}")
        return False, "Server disconnected - check SMTP settings or try again"
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False, f"Email server error: {str(e)}"
    except (TimeoutError, OSError) as e:
        logger.error(f"SMTP connection timeout or network error: {e}")
        return False, "Connection timeout - check network or try again later"
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}", exc_info=True)
        return False, "Failed to send email - please try again later"


def test_email_connection() -> tuple[bool, str]:
    """
    Test SMTP connection without sending email
    
    Returns:
        (success: bool, message: str)
    """
    try:
        mail_config = st.secrets.get("mail", {})
        
        if not mail_config:
            return False, "Mail configuration not found"
        
        host = mail_config.get("HOST")
        port = mail_config.get("PORT", 587)
        username = mail_config.get("USERNAME")
        password = mail_config.get("PASSWORD")
        use_ssl = mail_config.get("USE_SSL", False)
        use_tls = mail_config.get("USE_TLS", True)
        timeout = mail_config.get("TIMEOUT_SECONDS", 10)
        
        if not all([host, username, password]):
            return False, "Missing required configuration"
        
        # Test connection
        if use_ssl and port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as server:
                server.login(username, password)
                return True, "Connection successful"
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as server:
                server.ehlo()
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(username, password)
                return True, "Connection successful"
                
    except Exception as e:
        logger.error(f"Email connection test failed: {e}")
        return False, str(e)

