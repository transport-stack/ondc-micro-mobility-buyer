import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=f"envs/.env.smtp")
sender_address = os.getenv("SENDER_EMAIL_ID")
sender_pass = os.getenv("SENDER_EMAIL_PASSWORD")


class SMTPUtils:
    def __init__(self, smtp_server='smtp.gmail.com', smtp_port=587):
        self.sender_address = sender_address
        self.sender_pass = sender_pass
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, receiver_address_to, subject=None, body=None, attachments=None, receiver_address_cc=None):
        try:
            message = MIMEMultipart()
            message['From'] = self.sender_address
            if not receiver_address_to:
                raise Exception("No receiver address provided")
            message['To'] = receiver_address_to
            if receiver_address_cc:
                message['Cc'] = receiver_address_cc
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            if attachments:
                for filename, attachment in attachments.items():
                    message.attach(attachment)

            session = smtplib.SMTP(self.smtp_server, self.smtp_port)
            session.starttls()
            session.login(self.sender_address, self.sender_pass)
            all_recipients = receiver_address_to.split(",") + (
                receiver_address_cc.split(",") if receiver_address_cc else [])

            session.sendmail(self.sender_address, all_recipients, message.as_string())
            session.quit()
        except smtplib.SMTPException as e:
            print(f"SMTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def send_simple_email(self, receiver_address_to, subject, body, receiver_address_cc=None):
        self.send_email(receiver_address_to=receiver_address_to, subject=subject, body=body,
                        receiver_address_cc=receiver_address_cc)

    def send_email_with_attachments(self, receiver_address_to, subject, body, attachments, receiver_address_cc=None):
        self.send_email(receiver_address_to=receiver_address_to, subject=subject, body=body, attachments=attachments,
                        receiver_address_cc=receiver_address_cc)
