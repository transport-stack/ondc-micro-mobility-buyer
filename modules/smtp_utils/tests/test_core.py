import unittest
import random
import string
from email.mime.text import MIMEText

from modules.smtp_utils.core import SMTPUtils
from modules.utils import convert_data_to_csv_string, generate_random_csv_attachments


class SMTPTestSuite(unittest.TestCase):
    def setUp(self):
        self.smtp_utils = SMTPUtils()
        self.test_receiver = 'test@test.ac.in'

    @unittest.skip("Only test in production")
    def test_send_basic_email(self):
        subject = 'Basic Email Test'
        body = 'This is a test email for basic SMTP functionality.'
        self.smtp_utils.send_simple_email(self.test_receiver, subject, body)
        print("Test passed: Basic email sent")

    @unittest.skip("Only test in production")
    def test_send_email_with_attachments(self):
        subject = 'Email with Attachments Test'
        body = 'This email contains attachments for testing.'
        attachments = generate_random_csv_attachments(2, 10, 5)
        self.smtp_utils.send_email_with_attachments(self.test_receiver, subject, body, attachments)
        print("Test passed: Email with attachments sent")


# Run the tests
if __name__ == '__main__':
    unittest.main()
