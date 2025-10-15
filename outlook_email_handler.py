"""
Outlook Email Handler using Microsoft Graph API
Handles authentication, fetching emails, sending replies
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

class OutlookEmailHandler:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str, support_email: str, signature_path: str = 'signature.html'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.support_email = support_email
        self.access_token = None
        self.token_expiry = None
        self.signature_html = self._load_signature(signature_path)

    def _load_signature(self, signature_path: str) -> str:
        """
        Load email signature from HTML file
        """
        try:
            if os.path.exists(signature_path):
                with open(signature_path, 'r') as f:
                    return f.read()
            else:
                print(f"Warning: Signature file not found at {signature_path}")
                return ""
        except Exception as e:
            print(f"Error loading signature: {e}")
            return ""

    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph using client credentials
        Returns True if successful
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return True

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }

        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()

            token_response = response.json()
            self.access_token = token_response['access_token']
            expires_in = token_response.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

            return True

        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_unread_emails(self, limit: int = 10) -> List[Dict]:
        """
        Fetch unread emails from inbox
        Returns list of email dictionaries
        """
        if not self.authenticate():
            return []

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Filter for unread emails only
        url = f"https://graph.microsoft.com/v1.0/users/{self.support_email}/messages"
        params = {
            '$filter': 'isRead eq false',
            '$top': limit,
            '$orderby': 'receivedDateTime desc',
            '$select': 'id,subject,from,receivedDateTime,body,toRecipients,conversationId'
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            emails = response.json().get('value', [])

            processed_emails = []
            for email in emails:
                processed_emails.append({
                    'id': email['id'],
                    'subject': email['subject'],
                    'from_email': email['from']['emailAddress']['address'],
                    'from_name': email['from']['emailAddress'].get('name', ''),
                    'received_time': email['receivedDateTime'],
                    'body': email['body']['content'],
                    'body_type': email['body']['contentType'],
                    'conversation_id': email.get('conversationId', '')
                })

            return processed_emails

        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def send_reply(self, to_email: str, subject: str, body: str,
                   original_message_id: Optional[str] = None) -> bool:
        """
        Send reply email
        If original_message_id provided, sends as reply to that message
        """
        if not self.authenticate():
            return False

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # Append signature to body
        body_with_signature = body + self.signature_html

        # Construct email
        email_msg = {
            'message': {
                'subject': subject if not subject.startswith('RE:') else subject,
                'body': {
                    'contentType': 'HTML',
                    'content': body_with_signature
                },
                'toRecipients': [
                    {
                        'emailAddress': {
                            'address': to_email
                        }
                    }
                ]
            }
        }

        # If replying to specific message, use reply endpoint
        if original_message_id:
            url = f"https://graph.microsoft.com/v1.0/users/{self.support_email}/messages/{original_message_id}/reply"
            email_msg['comment'] = body_with_signature
            email_msg.pop('message')
        else:
            url = f"https://graph.microsoft.com/v1.0/users/{self.support_email}/sendMail"

        try:
            response = requests.post(url, headers=headers, json=email_msg)
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark email as read
        """
        if not self.authenticate():
            return False

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        url = f"https://graph.microsoft.com/v1.0/users/{self.support_email}/messages/{message_id}"
        data = {
            'isRead': True
        }

        try:
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Error marking email as read: {e}")
            return False

    def get_attachments(self, message_id: str) -> List[Dict]:
        """
        Get attachments from an email
        """
        if not self.authenticate():
            return []

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        url = f"https://graph.microsoft.com/v1.0/users/{self.support_email}/messages/{message_id}/attachments"

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            attachments = response.json().get('value', [])
            return attachments

        except Exception as e:
            print(f"Error getting attachments: {e}")
            return []


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    handler = OutlookEmailHandler(
        client_id=os.getenv('OUTLOOK_CLIENT_ID'),
        client_secret=os.getenv('OUTLOOK_CLIENT_SECRET'),
        tenant_id=os.getenv('OUTLOOK_TENANT_ID'),
        support_email=os.getenv('SUPPORT_EMAIL')
    )

    if handler.authenticate():
        print("✅ Authentication successful")
        emails = handler.get_unread_emails(limit=5)
        print(f"📧 Found {len(emails)} unread emails")
    else:
        print("❌ Authentication failed")
