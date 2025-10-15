"""
Test script to run bot once
"""

import os
from dotenv import load_dotenv
from outlook_email_handler import OutlookEmailHandler
from shopify_integration import ShopifyIntegration
from customer_support_agent import CustomerSupportAgent
from slack_notifier import SlackNotifier

load_dotenv()

print("\n" + "="*60)
print("🤖 RUNNING SUPPORT BOT (ONE TIME)")
print("="*60 + "\n")

# Initialize components
email_handler = OutlookEmailHandler(
    client_id=os.getenv('OUTLOOK_CLIENT_ID'),
    client_secret=os.getenv('OUTLOOK_CLIENT_SECRET'),
    tenant_id=os.getenv('OUTLOOK_TENANT_ID'),
    support_email=os.getenv('SUPPORT_EMAIL')
)

shopify = ShopifyIntegration(
    shop_domain=os.getenv('SHOPIFY_DOMAIN'),
    access_token=os.getenv('SHOPIFY_ACCESS_TOKEN')
)

ai_agent = CustomerSupportAgent(
    api_key=os.getenv('ANTHROPIC_API_KEY')
)

slack_url = os.getenv('SLACK_WEBHOOK_URL')
slack = SlackNotifier(slack_url) if slack_url else None

# Authenticate
print("🔐 Authenticating with Outlook...")
if not email_handler.authenticate():
    print("❌ Authentication failed")
    exit(1)
print("✅ Authenticated\n")

# Get unread emails
print("📧 Fetching unread emails...")
emails = email_handler.get_unread_emails(limit=5)
print(f"✅ Found {len(emails)} unread email(s)\n")

if not emails:
    print("📭 No unread emails to process")
    exit(0)

# Process first email
for i, email in enumerate(emails, 1):
    print(f"\n{'='*60}")
    print(f"📨 EMAIL #{i}")
    print(f"{'='*60}")
    print(f"From: {email['from_name']} <{email['from_email']}>")
    print(f"Subject: {email['subject']}")
    print(f"Received: {email['received_time']}")
    print(f"\nBody Preview: {email['body'][:200]}...")

    # Classify email
    classification = ai_agent.classify_email_intent(email['body'], email['subject'])
    print(f"\n🔍 Classification: {classification['intent']}")

    if classification['is_spam']:
        print("🚫 Marked as SPAM - skipping")
        email_handler.mark_as_read(email['id'])
        continue

    # Try to find order info
    print("\n🛍️  Looking up order information...")
    order_number = ai_agent.extract_order_number(email['body'] + " " + email['subject'])

    order_context = None
    if order_number:
        print(f"   Found order number: #{order_number}")
        order_context = shopify.find_order_by_number(order_number)
        if order_context:
            print(f"   ✅ Order found - Status: {order_context.get('fulfillment_status')}")
        else:
            print(f"   ⚠️  Order not found, trying email lookup...")
            orders = shopify.find_order_by_email(email['from_email'])
            if orders:
                order_context = orders[0]
                print(f"   ✅ Found order #{order_context.get('order_number')}")
    else:
        print("   No order number found, searching by email...")
        orders = shopify.find_order_by_email(email['from_email'])
        if orders:
            order_context = orders[0]
            print(f"   ✅ Found order #{order_context.get('order_number')}")
        else:
            print("   ⚠️  No orders found")

    # Generate AI response
    print("\n🤖 Generating AI response...")
    response = ai_agent.generate_response(
        customer_email=email['from_email'],
        customer_name=email['from_name'],
        email_subject=email['subject'],
        email_body=email['body'],
        order_context=order_context
    )

    print(f"\n{'='*60}")
    print("📝 AI RESPONSE")
    print(f"{'='*60}")
    print(f"Type: {response['type']}")
    print(f"Should Send: {response['should_send']}")
    print(f"Flag for Human: {response['flag_for_human']}")

    if response.get('human_review_reason'):
        print(f"Reason: {response['human_review_reason']}")

    if response.get('response'):
        print(f"\nResponse Text:\n{response['response'][:500]}...")

    # Take action
    if response['flag_for_human']:
        print(f"\n🚩 FLAGGED FOR HUMAN REVIEW")
        if slack:
            slack.notify_human_review_needed(
                order_number=order_context.get('order_number', 'Unknown') if order_context else 'Unknown',
                customer_email=email['from_email'],
                reason=response['human_review_reason'],
                priority='high'
            )
            print("   ✅ Slack notification sent")

    elif response['should_send'] and response.get('response'):
        print(f"\n📤 SENDING REPLY...")
        subject = f"RE: {email['subject']}" if not email['subject'].startswith('RE:') else email['subject']

        sent = email_handler.send_reply(
            to_email=email['from_email'],
            subject=subject,
            body=response['response'],
            original_message_id=email['id']
        )

        if sent:
            print("   ✅ Reply sent successfully")
            email_handler.mark_as_read(email['id'])
            print("   ✅ Marked as read")
        else:
            print("   ❌ Failed to send reply")
    else:
        print("\n⏸️  No action taken (spam or error)")

    print(f"\n{'='*60}\n")

print("\n✅ Processing complete!")
