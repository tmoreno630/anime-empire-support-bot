"""
Slack Integration for Notifications
Sends alerts to Slack for items needing human review
"""

import requests
from typing import Dict, Optional
from datetime import datetime

class SlackNotifier:
    def __init__(self, webhook_url: str):
        """
        Initialize Slack notifier

        Args:
            webhook_url: Slack incoming webhook URL
        """
        self.webhook_url = webhook_url

    def send_notification(self, title: str, message: str,
                         color: str = "#FFD700",
                         fields: Optional[list] = None) -> bool:
        """
        Send a notification to Slack

        Args:
            title: Notification title
            message: Main message text
            color: Hex color for message sidebar (default: gold)
            fields: List of field dicts with 'title' and 'value'

        Returns:
            True if sent successfully
        """
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": fields or [],
                    "footer": "Support Bot",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Slack notification: {e}")
            return False

    def notify_human_review_needed(self, order_number: str,
                                   customer_email: str,
                                   reason: str,
                                   priority: str = "medium") -> bool:
        """
        Send notification for item needing human review
        """
        color_map = {
            'high': '#FF0000',
            'medium': '#FFD700',
            'low': '#36A64F'
        }

        priority_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        fields = [
            {
                "title": "Order Number",
                "value": f"#{order_number}",
                "short": True
            },
            {
                "title": "Priority",
                "value": f"{priority_emoji.get(priority, '🟡')} {priority.upper()}",
                "short": True
            },
            {
                "title": "Customer",
                "value": customer_email,
                "short": False
            },
            {
                "title": "Reason",
                "value": reason,
                "short": False
            }
        ]

        return self.send_notification(
            title="🚩 Human Review Needed",
            message="A customer support email requires your attention",
            color=color_map.get(priority, '#FFD700'),
            fields=fields
        )

    def notify_error(self, error_message: str, context: str = "") -> bool:
        """
        Send error notification
        """
        fields = [
            {
                "title": "Error",
                "value": error_message,
                "short": False
            }
        ]

        if context:
            fields.append({
                "title": "Context",
                "value": context,
                "short": False
            })

        return self.send_notification(
            title="❌ Support Bot Error",
            message="An error occurred in the support bot",
            color="#FF0000",
            fields=fields
        )

    def notify_daily_summary(self, stats: Dict) -> bool:
        """
        Send daily summary notification
        """
        fields = [
            {
                "title": "Emails Processed",
                "value": str(stats.get('total_emails', 0)),
                "short": True
            },
            {
                "title": "AI Responses Sent",
                "value": str(stats.get('responses_sent', 0)),
                "short": True
            },
            {
                "title": "Automation Rate",
                "value": f"{stats.get('automation_rate', 0):.1f}%",
                "short": True
            },
            {
                "title": "Pending Reviews",
                "value": str(stats.get('pending_reviews', 0)),
                "short": True
            },
            {
                "title": "Spam Filtered",
                "value": str(stats.get('spam', 0)),
                "short": True
            }
        ]

        return self.send_notification(
            title="📊 Daily Support Summary",
            message="Here's how your support bot performed today",
            color="#36A64F",
            fields=fields
        )


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    notifier = SlackNotifier(os.getenv('SLACK_WEBHOOK_URL'))

    print("Testing Slack notification...")
    success = notifier.notify_human_review_needed(
        order_number="1234",
        customer_email="customer@example.com",
        reason="Package not received - 10 days overdue",
        priority="high"
    )

    if success:
        print("✅ Slack notification sent successfully")
    else:
        print("❌ Failed to send Slack notification")
