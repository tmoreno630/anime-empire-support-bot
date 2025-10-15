"""
Test Setup Script
Verifies all API connections and environment variables
"""

import os
from dotenv import load_dotenv

def test_environment_variables():
    """Check if all required environment variables are set"""
    print("\n" + "="*60)
    print("🔧 Testing Environment Variables")
    print("="*60)

    required_vars = [
        'OUTLOOK_CLIENT_ID',
        'OUTLOOK_CLIENT_SECRET',
        'OUTLOOK_TENANT_ID',
        'SUPPORT_EMAIL',
        'SHOPIFY_DOMAIN',
        'SHOPIFY_ACCESS_TOKEN',
        'ANTHROPIC_API_KEY'
    ]

    optional_vars = [
        'SLACK_WEBHOOK_URL',
        'DB_PATH',
        'CHECK_INTERVAL_MINUTES'
    ]

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Missing or not configured")
            all_good = False

    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value and value != f"your_{var.lower()}_here":
            print(f"✅ {var}: Set")
        else:
            print(f"⚠️  {var}: Not set (optional)")

    return all_good


def test_outlook_connection():
    """Test Outlook/Microsoft Graph API connection"""
    print("\n" + "="*60)
    print("📧 Testing Outlook Connection")
    print("="*60)

    try:
        from outlook_email_handler import OutlookEmailHandler

        handler = OutlookEmailHandler(
            client_id=os.getenv('OUTLOOK_CLIENT_ID'),
            client_secret=os.getenv('OUTLOOK_CLIENT_SECRET'),
            tenant_id=os.getenv('OUTLOOK_TENANT_ID'),
            support_email=os.getenv('SUPPORT_EMAIL')
        )

        if handler.authenticate():
            print("✅ Outlook authentication successful")

            emails = handler.get_unread_emails(limit=1)
            print(f"✅ Successfully fetched emails (found {len(emails)} unread)")
            return True
        else:
            print("❌ Outlook authentication failed")
            print("   Check your client ID, secret, and tenant ID")
            print("   Verify admin consent was granted in Azure AD")
            return False

    except Exception as e:
        print(f"❌ Outlook connection error: {e}")
        return False


def test_shopify_connection():
    """Test Shopify API connection"""
    print("\n" + "="*60)
    print("🛍️  Testing Shopify Connection")
    print("="*60)

    try:
        from shopify_integration import ShopifyIntegration

        shopify = ShopifyIntegration(
            shop_domain=os.getenv('SHOPIFY_DOMAIN'),
            access_token=os.getenv('SHOPIFY_ACCESS_TOKEN')
        )

        result = shopify._make_request('orders.json?limit=1')

        if result:
            print("✅ Shopify connection successful")
            if 'orders' in result:
                print(f"✅ Successfully fetched orders (found {len(result['orders'])})")
            return True
        else:
            print("❌ Shopify connection failed")
            print("   Check your shop domain and access token")
            print("   Verify API scopes are configured correctly")
            return False

    except Exception as e:
        print(f"❌ Shopify connection error: {e}")
        return False


def test_anthropic_api():
    """Test Anthropic API connection"""
    print("\n" + "="*60)
    print("🤖 Testing Anthropic API")
    print("="*60)

    try:
        from customer_support_agent import CustomerSupportAgent

        agent = CustomerSupportAgent(api_key=os.getenv('ANTHROPIC_API_KEY'))

        test_response = agent.generate_response(
            customer_email="test@example.com",
            customer_name="Test Customer",
            email_subject="Test",
            email_body="This is a test message"
        )

        if test_response and test_response.get('response'):
            print("✅ Anthropic API connection successful")
            print("✅ AI agent generated test response")
            return True
        else:
            print("❌ Anthropic API connection failed")
            print("   Check your API key")
            return False

    except Exception as e:
        print(f"❌ Anthropic API error: {e}")
        return False


def test_slack_webhook():
    """Test Slack webhook (optional)"""
    print("\n" + "="*60)
    print("💬 Testing Slack Webhook (Optional)")
    print("="*60)

    slack_url = os.getenv('SLACK_WEBHOOK_URL')

    if not slack_url or slack_url == "your_slack_webhook_url_here":
        print("⚠️  Slack webhook not configured (optional)")
        return None

    try:
        from slack_notifier import SlackNotifier

        notifier = SlackNotifier(slack_url)

        success = notifier.send_notification(
            title="🧪 Test Notification",
            message="Support bot setup test",
            color="#36A64F",
            fields=[
                {
                    "title": "Status",
                    "value": "Testing connection",
                    "short": True
                }
            ]
        )

        if success:
            print("✅ Slack webhook working")
            print("   Check your Slack channel for test notification")
            return True
        else:
            print("❌ Slack webhook failed")
            print("   Check your webhook URL")
            return False

    except Exception as e:
        print(f"❌ Slack webhook error: {e}")
        return False


def test_database():
    """Test database creation"""
    print("\n" + "="*60)
    print("💾 Testing Database")
    print("="*60)

    try:
        import sqlite3

        db_path = os.getenv('DB_PATH', 'support_bot.db')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                test_value TEXT
            )
        ''')

        cursor.execute("INSERT INTO test_table (test_value) VALUES (?)", ("test",))
        conn.commit()

        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()

        cursor.execute("DROP TABLE test_table")
        conn.commit()
        conn.close()

        if result:
            print(f"✅ Database working: {db_path}")
            return True
        else:
            print("❌ Database test failed")
            return False

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Run all tests"""
    load_dotenv()

    print("\n" + "="*60)
    print("🧪 SUPPORT BOT SETUP TEST")
    print("="*60)

    results = {}

    results['env_vars'] = test_environment_variables()

    if not results['env_vars']:
        print("\n❌ Environment variables not configured properly")
        print("Please check your .env file")
        return

    results['outlook'] = test_outlook_connection()
    results['shopify'] = test_shopify_connection()
    results['anthropic'] = test_anthropic_api()
    results['slack'] = test_slack_webhook()
    results['database'] = test_database()

    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  SKIP"

        print(f"{status}: {test_name.replace('_', ' ').title()}")

    critical_tests = ['env_vars', 'outlook', 'shopify', 'anthropic', 'database']
    critical_passed = all(results.get(test) for test in critical_tests)

    print("\n" + "="*60)

    if critical_passed:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("Your support bot is ready to run.")
        print("\nNext steps:")
        print("1. Run: python main_support_bot.py")
        print("2. Send a test email to your support address")
        print("3. Check for automated response")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please fix the issues above before running the bot.")

    print("="*60 + "\n")


if __name__ == "__main__":
    main()
