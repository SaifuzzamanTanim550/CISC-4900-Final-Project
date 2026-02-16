from src.services.email_service import send_stock_out_email

subject = "Test email from inventory system"
body = "If you are reading this, Gmail SMTP is working."

send_stock_out_email(subject, body)

print("Email sent successfully")
