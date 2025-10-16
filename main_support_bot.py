"""
Main Support Bot Orchestrator
Coordinates email handling, AI responses, and Slack notifications
"""

import os
import time
import sqlite3
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

from outlook_email_handler import OutlookEmailHandler
from shopify_integration import ShopifyIntegration
from customer_support_agent import CustomerSupportAgent
from slack_notifier import SlackNotifier
from daily_summary import DailySummary
import pytz

class SupportBot:
    def __init__(self, config: Dict):
        self.config = config
        self.db_path = config.get('db_path', 'support_bot.db')

        self.email_handler = OutlookEmailHandler(
            client_id=config['outlook_client_id'],
            client_secret=config['outlook_client_secret'],
            tenant_id=config['outlook_tenant_id'],
            support_email=config['support_email']
        )

        self.shopify = ShopifyIntegration(
            shop_domain=config['shopify_domain'],
            access_token=config['shopify_access_token']
        )

        self.ai_agent = CustomerSupportAgent(
            api_key=config['anthropic_api_key']
        )

        slack_url = config.get('slack_webhook_url')
        self.slack = SlackNotifier(slack_url) if slack_url else None

        self.check_interval = config.get('check_interval_minutes', 5)

        # Daily summary configuration
        self.summary_email = config.get('summary_email')
        self.summary_hour = config.get('summary_hour', 8)  # 8 AM
        self.summary_timezone = pytz.timezone(config.get('summary_timezone', 'America/Chicago'))  # CST
        self.last_summary_date = None

        # Initialize daily summary
        self.daily_summary = DailySummary(self.db_path, self.email_handler) if self.summary_email else None

        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                email_id TEXT PRIMARY KEY,
                customer_email TEXT,
                subject TEXT,
                processed_at TEXT,
                response_sent BOOLEAN,
                flagged_for_review BOOLEAN,
                order_number TEXT,
                intent TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS human_review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT,
                order_number TEXT,
                customer_email TEXT,
                reason TEXT,
                priority TEXT,
                created_at TEXT,
                resolved_at TEXT,
                resolved_by TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        conn.commit()
        conn.close()

        print(f"✅ Database initialized: {self.db_path}")

    def is_email_processed(self, email_id: str) -> bool:
        """Check if email was already processed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT email_id FROM processed_emails WHERE email_id = ?', (email_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_email_processed(self, email_id: str, customer_email: str, subject: str,
                            response_sent: bool, flagged: bool, order_number: str = None,
                            intent: str = None):
        """Mark email as processed in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO processed_emails
            (email_id, customer_email, subject, processed_at, response_sent,
             flagged_for_review, order_number, intent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (email_id, customer_email, subject, datetime.now().isoformat(),
              response_sent, flagged, order_number, intent))

        conn.commit()
        conn.close()

    def add_to_review_queue(self, email_id: str, order_number: str,
                           customer_email: str, reason: str, priority: str = 'medium'):
        """Add email to human review queue and notify via Slack"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO human_review_queue (
                email_id, order_number, customer_email, reason, priority, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (email_id, order_number, customer_email, reason, priority, datetime.now().isoformat()))

        conn.commit()
        conn.close()

        print(f"⚠️  FLAGGED FOR REVIEW: {reason} - Order #{order_number}")

        if self.slack:
            self.slack.notify_human_review_needed(
                order_number=order_number,
                customer_email=customer_email,
                reason=reason,
                priority=priority
            )

    def process_email(self, email: Dict) -> bool:
        """
        Process a single email
        Returns True if processed successfully
        """
        email_id = email['id']

        if self.is_email_processed(email_id):
            print(f"⏭️  Skipping already processed email: {email['subject']}")
            return True

        print(f"\n📧 Processing: {email['subject']}")
        print(f"   From: {email['from_name']} <{email['from_email']}>")

        customer_email = email['from_email']
        customer_name = email['from_name'] or 'Valued Customer'
        email_subject = email['subject']
        email_body = email['body']

        is_blocked, block_reason = self.ai_agent.is_blocked_sender(customer_email, customer_name)
        if is_blocked:
            print(f"   🚫 BLOCKED: {block_reason}")
            self.mark_email_processed(email_id, customer_email, email_subject,
                                     False, False, None, 'blocked_sender')
            self.email_handler.mark_as_read(email_id)
            return True

        order_number = self.ai_agent.extract_order_number(email_subject + " " + email_body)
        order_context = None

        if order_number:
            print(f"   🔍 Found order number: #{order_number}")
            order_context = self.shopify.find_order_by_number(order_number)

            if not order_context:
                orders = self.shopify.find_order_by_email(customer_email)
                if orders:
                    order_context = orders[0]
                    order_number = order_context['order_number']
                    print(f"   📦 Matched by email to order #{order_number}")
        else:
            orders = self.shopify.find_order_by_email(customer_email, limit=1)
            if orders:
                order_context = orders[0]
                order_number = order_context['order_number']
                print(f"   📦 Found order by email: #{order_number}")

        ai_response = self.ai_agent.generate_response(
            customer_email=customer_email,
            customer_name=customer_name,
            email_subject=email_subject,
            email_body=email_body,
            order_context=order_context
        )

        if ai_response['type'] == 'spam':
            print(f"   🗑️  SPAM: {ai_response['reason']}")
            self.mark_email_processed(email_id, customer_email, email_subject,
                                     False, False, order_number, 'spam')
            self.email_handler.mark_as_read(email_id)
            return True

        if ai_response['flag_for_human']:
            print(f"   🚩 Flagged for review: {ai_response['human_review_reason']}")

            priority = 'high' if 'overdue' in ai_response['human_review_reason'].lower() else 'medium'

            self.add_to_review_queue(
                email_id=email_id,
                order_number=order_number or 'N/A',
                customer_email=customer_email,
                reason=ai_response['human_review_reason'],
                priority=priority
            )

            self.mark_email_processed(email_id, customer_email, email_subject,
                                     False, True, order_number, ai_response.get('intent'))
            self.email_handler.mark_as_read(email_id)
            return True

        if ai_response['should_send'] and ai_response['response']:
            reply_subject = email_subject if email_subject.startswith('RE:') else f"RE: {email_subject}"

            success = self.email_handler.send_reply(
                to_email=customer_email,
                subject=reply_subject,
                body=ai_response['response'],
                original_message_id=email_id
            )

            if success:
                print(f"   ✅ AI response sent")
                self.email_handler.mark_as_read(email_id)
                self.mark_email_processed(email_id, customer_email, email_subject,
                                         True, False, order_number, ai_response.get('intent'))
                return True
            else:
                print(f"   ❌ Failed to send response")
                return False

        return True

    def run_once(self):
        """Run one cycle of email processing"""
        print(f"\n{'='*60}")
        print(f"🤖 Support Bot Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        if not self.email_handler.authenticate():
            print("❌ Failed to authenticate with Outlook")
            if self.slack:
                self.slack.notify_error("Failed to authenticate with Outlook")
            return

        emails = self.email_handler.get_unread_emails(limit=10)
        print(f"\n📬 Found {len(emails)} unread emails")

        if not emails:
            print("✅ No new emails to process")
            return

        processed = 0
        for email in emails:
            try:
                if self.process_email(email):
                    processed += 1
            except Exception as e:
                print(f"❌ Error processing email: {e}")
                if self.slack:
                    self.slack.notify_error(
                        error_message=str(e),
                        context=f"Email: {email.get('subject', 'Unknown')}"
                    )

        print(f"\n✅ Processed {processed}/{len(emails)} emails")

    def check_and_send_daily_summary(self):
        """Check if it's time to send daily summary and send if needed"""
        if not self.daily_summary or not self.summary_email:
            return

        # Get current time in configured timezone
        now = datetime.now(self.summary_timezone)
        current_date = now.date()
        current_hour = now.hour

        # Check if we should send summary
        # Send at configured hour, but only once per day
        if current_hour == self.summary_hour and self.last_summary_date != current_date:
            print(f"\n📊 Sending daily summary to {self.summary_email}...")
            try:
                success = self.daily_summary.send_daily_summary(self.summary_email)
                if success:
                    self.last_summary_date = current_date
                    print("✅ Daily summary sent successfully")
                else:
                    print("❌ Failed to send daily summary")
            except Exception as e:
                print(f"❌ Error sending daily summary: {e}")
                if self.slack:
                    self.slack.notify_error(
                        error_message=str(e),
                        context="Daily summary error"
                    )

    def run_continuous(self):
        """Run bot continuously with configured interval"""
        print("="*60)
        print("🤖 Support Bot Started")
        print(f"Check interval: {self.check_interval} minutes")
        print(f"Database: {self.db_path}")
        print("="*60)

        while True:
            try:
                self.run_once()
                self.check_and_send_daily_summary()
                print(f"\n💤 Sleeping for {self.check_interval} minutes...")
                time.sleep(self.check_interval * 60)

            except KeyboardInterrupt:
                print("\n\n👋 Support Bot stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in main loop: {e}")
                if self.slack:
                    self.slack.notify_error(
                        error_message=str(e),
                        context="Main loop error"
                    )
                time.sleep(60)


def main():
    load_dotenv()

    config = {
        'outlook_client_id': os.getenv('OUTLOOK_CLIENT_ID'),
        'outlook_client_secret': os.getenv('OUTLOOK_CLIENT_SECRET'),
        'outlook_tenant_id': os.getenv('OUTLOOK_TENANT_ID'),
        'support_email': os.getenv('SUPPORT_EMAIL'),
        'shopify_domain': os.getenv('SHOPIFY_DOMAIN'),
        'shopify_access_token': os.getenv('SHOPIFY_ACCESS_TOKEN'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
        'db_path': os.getenv('DB_PATH', 'support_bot.db'),
        'check_interval_minutes': int(os.getenv('CHECK_INTERVAL_MINUTES', '5')),
        'summary_email': os.getenv('SUMMARY_EMAIL'),
        'summary_hour': int(os.getenv('SUMMARY_HOUR', '8')),
        'summary_timezone': os.getenv('SUMMARY_TIMEZONE', 'America/Chicago')
    }

    required = ['outlook_client_id', 'outlook_client_secret', 'outlook_tenant_id',
                'support_email', 'shopify_domain', 'shopify_access_token', 'anthropic_api_key']

    missing = [key for key in required if not config[key]]
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        return

    bot = SupportBot(config)
    bot.run_continuous()


if __name__ == "__main__":
    main()
