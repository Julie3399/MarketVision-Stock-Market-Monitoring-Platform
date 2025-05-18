from typing import Dict
import smtplib
from email.mime.text import MIMEText

class AlertService:
    def __init__(self):
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password'
        }
    
    def send_email_alert(self, symbol: str, alert_type: str, data: Dict):
        msg = MIMEText(f"Stock {symbol} triggered {alert_type} alert\nDetailed data: {str(data)}")
        msg['Subject'] = f"Stock Alert - {symbol}"
        msg['From'] = self.email_config['username']
        msg['To'] = self.email_config['username']
        
        with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
            server.starttls()
            server.login(self.email_config['username'], self.email_config['password'])
            server.send_message(msg)