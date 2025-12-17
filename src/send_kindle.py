"""
Send EPUB files to Kindle via Gmail SMTP.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path


def get_gmail_credentials() -> tuple[str, str]:
    """Get Gmail credentials from environment variables."""
    address = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not address:
        raise ValueError("GMAIL_ADDRESS environment variable is not set")
    if not password:
        raise ValueError("GMAIL_APP_PASSWORD environment variable is not set")
    
    return address, password


def get_kindle_emails() -> list[str]:
    """Get Kindle email addresses from environment variable."""
    emails_str = os.getenv("KINDLE_EMAILS", "")
    if not emails_str:
        raise ValueError("KINDLE_EMAILS environment variable is not set")
    
    return [email.strip() for email in emails_str.split(",") if email.strip()]


def send_to_kindle(epub_path: str, kindle_emails: list[str] = None) -> bool:
    """
    Send an EPUB file to Kindle email addresses.
    
    Args:
        epub_path: Path to the EPUB file
        kindle_emails: List of Kindle email addresses. If None, reads from env.
        
    Returns:
        True if sent successfully, False otherwise
    """
    # Get credentials and recipients
    gmail_address, gmail_password = get_gmail_credentials()
    
    if kindle_emails is None:
        kindle_emails = get_kindle_emails()
    
    if not kindle_emails:
        print("No Kindle email addresses configured")
        return False
    
    # Verify the file exists
    epub_file = Path(epub_path)
    if not epub_file.exists():
        print(f"EPUB file not found: {epub_path}")
        return False
    
    # Create the email
    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = ", ".join(kindle_emails)
    msg["Subject"] = f"HN Daily - {epub_file.stem}"
    
    # Add body text
    body = "Your daily Hacker News digest is attached."
    msg.attach(MIMEText(body, "plain"))
    
    # Attach the EPUB file
    with open(epub_path, "rb") as f:
        attachment = MIMEBase("application", "epub+zip")
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition",
            f"attachment; filename={epub_file.name}"
        )
        msg.attach(attachment)
    
    # Send the email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.send_message(msg)
        return True
        
    except smtplib.SMTPException as e:
        print(f"Failed to send emails")
        return False


if __name__ == "__main__":
    # Test module (requires proper .env setup)
    print("To test this module, ensure .env is configured with:")
    print("  GMAIL_ADDRESS=your-email@gmail.com")
    print("  GMAIL_APP_PASSWORD=your-app-password")
    print("  KINDLE_EMAILS=kindle@kindle.com")
    print("\nThen create a test EPUB and call send_to_kindle('path/to/test.epub')")
