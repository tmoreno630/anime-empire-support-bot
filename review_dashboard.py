"""
Human Review Dashboard
CLI tool to view and manage emails flagged for human review
"""

import sqlite3
import sys
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv

class ReviewDashboard:
    def __init__(self, db_path: str = 'support_bot.db'):
        self.db_path = db_path

    def get_pending_reviews(self) -> List[Dict]:
        """Get all pending items in review queue"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM human_review_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
        ''')

        reviews = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return reviews

    def get_review_stats(self) -> Dict:
        """Get statistics about reviews"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM human_review_queue WHERE status = "pending"')
        pending = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM human_review_queue WHERE status = "resolved"')
        resolved = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM processed_emails WHERE response_sent = 1')
        automated = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM processed_emails')
        total = cursor.fetchone()[0]

        conn.close()

        automation_rate = (automated / total * 100) if total > 0 else 0

        return {
            'pending': pending,
            'resolved': resolved,
            'automated_responses': automated,
            'total_emails': total,
            'automation_rate': automation_rate
        }

    def mark_resolved(self, review_id: int, resolved_by: str = 'manual'):
        """Mark a review item as resolved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE human_review_queue
            SET status = 'resolved',
                resolved_at = ?,
                resolved_by = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), resolved_by, review_id))

        conn.commit()
        conn.close()

        print(f"✅ Review #{review_id} marked as resolved")

    def display_dashboard(self):
        """Display the review dashboard"""
        stats = self.get_review_stats()
        reviews = self.get_pending_reviews()

        print("\n" + "="*70)
        print("🔍 HUMAN REVIEW DASHBOARD")
        print("="*70)

        print("\n📊 STATISTICS")
        print("-"*70)
        print(f"Total Emails Processed:    {stats['total_emails']}")
        print(f"Automated Responses:       {stats['automated_responses']}")
        print(f"Automation Rate:           {stats['automation_rate']:.1f}%")
        print(f"Items Pending Review:      {stats['pending']}")
        print(f"Items Resolved:            {stats['resolved']}")

        if not reviews:
            print("\n" + "="*70)
            print("✅ No items pending review!")
            print("="*70 + "\n")
            return

        print("\n🚩 PENDING REVIEWS")
        print("-"*70)

        for review in reviews:
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }

            emoji = priority_emoji.get(review['priority'], '🟡')
            created = datetime.fromisoformat(review['created_at'])
            age = (datetime.now() - created).total_seconds() / 3600

            print(f"\n{emoji} Review ID: {review['id']} | Priority: {review['priority'].upper()}")
            print(f"   Order:     #{review['order_number']}")
            print(f"   Customer:  {review['customer_email']}")
            print(f"   Reason:    {review['reason']}")
            print(f"   Created:   {created.strftime('%Y-%m-%d %H:%M')} ({age:.1f}h ago)")

        print("\n" + "="*70)
        print(f"Total: {len(reviews)} item(s) need attention")
        print("="*70 + "\n")

    def get_email_details(self, review_id: int) -> Dict:
        """Get full details for a review item"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM human_review_queue WHERE id = ?', (review_id,))
        review = cursor.fetchone()

        if not review:
            conn.close()
            return None

        review_dict = dict(review)
        email_id = review_dict['email_id']

        cursor.execute('SELECT * FROM processed_emails WHERE email_id = ?', (email_id,))
        email = cursor.fetchone()

        conn.close()

        if email:
            review_dict['email_details'] = dict(email)

        return review_dict

    def interactive_mode(self):
        """Run interactive mode for resolving reviews"""
        while True:
            self.display_dashboard()

            reviews = self.get_pending_reviews()

            if not reviews:
                break

            print("Commands:")
            print("  [number] - View details for review ID")
            print("  r [number] - Mark review ID as resolved")
            print("  q - Quit")

            choice = input("\nEnter command: ").strip().lower()

            if choice == 'q':
                break

            if choice.startswith('r '):
                try:
                    review_id = int(choice.split()[1])
                    self.mark_resolved(review_id)
                    input("\nPress Enter to continue...")
                except (ValueError, IndexError):
                    print("❌ Invalid review ID")
                    input("\nPress Enter to continue...")

            elif choice.isdigit():
                review_id = int(choice)
                details = self.get_email_details(review_id)

                if details:
                    print("\n" + "="*70)
                    print(f"📧 REVIEW DETAILS - ID #{review_id}")
                    print("="*70)
                    print(f"Order:    #{details['order_number']}")
                    print(f"Customer: {details['customer_email']}")
                    print(f"Reason:   {details['reason']}")
                    print(f"Priority: {details['priority']}")
                    print(f"Created:  {details['created_at']}")

                    if 'email_details' in details:
                        print(f"\nSubject:  {details['email_details']['subject']}")

                    print("="*70)
                    input("\nPress Enter to continue...")
                else:
                    print("❌ Review not found")
                    input("\nPress Enter to continue...")

            else:
                print("❌ Invalid command")
                input("\nPress Enter to continue...")


def main():
    load_dotenv()
    db_path = os.getenv('DB_PATH', 'support_bot.db')

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Run the support bot at least once to create the database")
        return

    dashboard = ReviewDashboard(db_path)

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'stats':
            stats = dashboard.get_review_stats()
            print(f"\n📊 Statistics:")
            print(f"   Total emails: {stats['total_emails']}")
            print(f"   Automated: {stats['automated_responses']}")
            print(f"   Automation rate: {stats['automation_rate']:.1f}%")
            print(f"   Pending reviews: {stats['pending']}")
            print(f"   Resolved: {stats['resolved']}\n")

        elif command == 'resolve':
            dashboard.interactive_mode()

        else:
            print(f"Unknown command: {command}")
            print("Available commands: stats, resolve")

    else:
        dashboard.display_dashboard()


if __name__ == "__main__":
    main()
