"""
Daily Summary Email
Sends a summary of bot activity for the previous day
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict
import pytz
from outlook_email_handler import OutlookEmailHandler


class DailySummary:
    def __init__(self, db_path: str, email_handler: OutlookEmailHandler):
        self.db_path = db_path
        self.email_handler = email_handler

    def get_daily_stats(self) -> Dict:
        """
        Get statistics for the last 24 hours
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get timestamp for 24 hours ago
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()

        # Total emails processed
        cursor.execute('''
            SELECT COUNT(*) FROM processed_emails
            WHERE processed_at >= ?
        ''', (yesterday,))
        total_emails = cursor.fetchone()[0]

        # AI responses sent
        cursor.execute('''
            SELECT COUNT(*) FROM processed_emails
            WHERE processed_at >= ? AND response_sent = 1
        ''', (yesterday,))
        responses_sent = cursor.fetchone()[0]

        # Spam filtered (using intent field)
        cursor.execute('''
            SELECT COUNT(*) FROM processed_emails
            WHERE processed_at >= ? AND intent = 'spam'
        ''', (yesterday,))
        spam_filtered = cursor.fetchone()[0]

        # Items flagged for human review in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) FROM human_review_queue
            WHERE created_at >= ?
        ''', (yesterday,))
        flagged_count = cursor.fetchone()[0]

        # Total pending reviews (unresolved)
        cursor.execute('''
            SELECT COUNT(*) FROM human_review_queue
            WHERE status = 'pending'
        ''')
        pending_reviews = cursor.fetchone()[0]

        # Get pending review details
        cursor.execute('''
            SELECT order_number, customer_email, reason, priority, created_at
            FROM human_review_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at DESC
            LIMIT 10
        ''')
        pending_items = cursor.fetchall()

        conn.close()

        # Calculate automation rate
        if total_emails > 0:
            automation_rate = (responses_sent / total_emails) * 100
        else:
            automation_rate = 0

        return {
            'total_emails': total_emails,
            'responses_sent': responses_sent,
            'spam_filtered': spam_filtered,
            'flagged_count': flagged_count,
            'pending_reviews': pending_reviews,
            'automation_rate': automation_rate,
            'pending_items': pending_items,
            'report_date': datetime.now().strftime('%B %d, %Y')
        }

    def generate_summary_html(self, stats: Dict) -> str:
        """
        Generate HTML email for daily summary
        """
        # Priority emoji map
        priority_emoji = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }

        # Build pending items list
        pending_html = ''
        if stats['pending_items']:
            pending_html = '<h3>Pending Reviews:</h3><ul>'
            for item in stats['pending_items']:
                order_num, email, reason, priority, created = item
                emoji = priority_emoji.get(priority, '🟡')
                pending_html += f'<li>{emoji} <strong>Order #{order_num}</strong> - {email}<br><small>{reason}</small></li>'
            pending_html += '</ul>'
        else:
            pending_html = '<p style="color: #28a745;">✅ No pending reviews - all caught up!</p>'

        html = f'''
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .stats {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 0 0 10px 10px;
                    margin-bottom: 20px;
                }}
                .stat-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid #dee2e6;
                }}
                .stat-label {{
                    font-weight: bold;
                }}
                .stat-value {{
                    font-size: 1.2em;
                    color: #667eea;
                }}
                .automation-rate {{
                    font-size: 2em;
                    color: #28a745;
                    text-align: center;
                    margin: 20px 0;
                }}
                ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                li {{
                    padding: 10px;
                    margin: 5px 0;
                    background: white;
                    border-left: 3px solid #667eea;
                }}
                .footer {{
                    text-align: center;
                    color: #6c757d;
                    font-size: 0.9em;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Daily Support Bot Summary</h1>
                    <p>{stats['report_date']}</p>
                </div>

                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">📧 Total Emails Processed</span>
                        <span class="stat-value">{stats['total_emails']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">✅ AI Responses Sent</span>
                        <span class="stat-value">{stats['responses_sent']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">🚫 Spam Filtered</span>
                        <span class="stat-value">{stats['spam_filtered']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">🚩 Flagged for Review (24h)</span>
                        <span class="stat-value">{stats['flagged_count']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">📋 Pending Reviews (Total)</span>
                        <span class="stat-value">{stats['pending_reviews']}</span>
                    </div>
                </div>

                <div class="automation-rate">
                    📈 Automation Rate: {stats['automation_rate']:.1f}%
                </div>

                {pending_html}

                <div class="footer">
                    <p>This summary covers the last 24 hours of bot activity.</p>
                    <p>Powered by Anime Empire Support Bot</p>
                </div>
            </div>
        </body>
        </html>
        '''

        return html

    def send_daily_summary(self, recipient_email: str) -> bool:
        """
        Generate and send daily summary email
        """
        try:
            # Get stats
            stats = self.get_daily_stats()

            # Generate HTML
            html_body = self.generate_summary_html(stats)

            # Send email
            subject = f"📊 Daily Support Bot Summary - {stats['report_date']}"

            success = self.email_handler.send_reply(
                to_email=recipient_email,
                subject=subject,
                body=html_body
            )

            if success:
                print(f"✅ Daily summary sent to {recipient_email}")
            else:
                print(f"❌ Failed to send daily summary")

            return success

        except Exception as e:
            print(f"Error sending daily summary: {e}")
            return False


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Initialize email handler
    email_handler = OutlookEmailHandler(
        client_id=os.getenv('OUTLOOK_CLIENT_ID'),
        client_secret=os.getenv('OUTLOOK_CLIENT_SECRET'),
        tenant_id=os.getenv('OUTLOOK_TENANT_ID'),
        support_email=os.getenv('SUPPORT_EMAIL')
    )

    # Initialize daily summary
    summary = DailySummary(
        db_path=os.getenv('DB_PATH', 'support_bot.db'),
        email_handler=email_handler
    )

    # Send test summary
    recipient = os.getenv('SUMMARY_EMAIL', 't.moreno1170@gmail.com')
    summary.send_daily_summary(recipient)
