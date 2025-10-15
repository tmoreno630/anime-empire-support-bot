# AI Customer Support Agent - Complete Implementation Guide

**For Claude Code: Follow this guide step-by-step to implement the entire system**

---

## 🎯 Project Overview

Building an AI-powered customer support agent for a Shopify store that:
- Monitors Outlook inbox every 5 minutes
- Responds to customer emails automatically (60-70% automation)
- Follows strict company policies
- Flags complex issues for human review
- Sends Slack notifications for items needing attention
- Costs ~$10-20/month to run

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:
- [ ] Shopify store with admin access
- [ ] Outlook/Microsoft 365 account for support emails
- [ ] Azure account (free tier is fine)
- [ ] Anthropic API access
- [ ] Slack workspace admin access
- [ ] GitHub account
- [ ] Railway.app account (sign up with GitHub)

---

## 🗂️ Project Structure

```
support-bot/
├── .env                          # Environment variables (DO NOT COMMIT)
├── .gitignore                    # Git ignore file
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
├── SETUP_GUIDE.md               # Detailed setup instructions
├── outlook_email_handler.py     # Email integration
├── shopify_integration.py       # Shopify API handler
├── customer_support_agent.py    # AI agent with guidelines
├── slack_notifier.py            # Slack notifications (NEW)
├── main_support_bot.py          # Main orchestration
├── review_dashboard.py          # CLI dashboard
├── test_setup.py                # Setup verification
└── support_bot.db               # SQLite database (auto-created)
```

---

## PART 1: AZURE AD SETUP (Outlook Access)

### Step 1.1: Create Azure AD App Registration

1. Go to https://portal.azure.com/
2. Sign in with your Microsoft account
3. Search for "Azure Active Directory" in the top search bar
4. Click on **Azure Active Directory** from results

### Step 1.2: Register New Application

1. In the left sidebar, click **App registrations**
2. Click **+ New registration** at the top
3. Fill in the form:
   - **Name**: `Support Bot Email Handler`
   - **Supported account types**: Select "Accounts in this organizational directory only (Single tenant)"
   - **Redirect URI**: Leave blank (not needed for this app)
4. Click **Register**

### Step 1.3: Note Your IDs

After registration, you'll see the Overview page. **SAVE THESE VALUES**:

```
Application (client) ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Directory (tenant) ID:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Copy these to a secure note. You'll add them to `.env` later.

### Step 1.4: Create Client Secret

1. In the left sidebar, click **Certificates & secrets**
2. Click **+ New client secret**
3. Fill in:
   - **Description**: `Support Bot Secret`
   - **Expires**: 24 months (or your preference)
4. Click **Add**
5. **IMMEDIATELY COPY THE VALUE** - you won't see it again!
   - It looks like: `abc123~DEF456.ghi789JKL`

```
Client Secret Value: abc123~DEF456.ghi789JKL
```

### Step 1.5: Configure API Permissions

1. In the left sidebar, click **API permissions**
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (NOT Delegated)
5. Search for and add these permissions:
   - **Mail.Read** - Read mail in all mailboxes
   - **Mail.ReadWrite** - Read and write mail in all mailboxes  
   - **Mail.Send** - Send mail as any user
6. Click **Add permissions**

### Step 1.6: Grant Admin Consent

**CRITICAL STEP:**

1. After adding permissions, you'll see them listed but marked "Not granted"
2. Click the **Grant admin consent for [Your Organization]** button
3. Click **Yes** in the confirmation dialog
4. All permissions should now show a green checkmark ✅

### Step 1.7: Verify Settings

Your API permissions should look like this:
```
✅ Mail.Read              - Application - Granted for [Org]
✅ Mail.ReadWrite         - Application - Granted for [Org]
✅ Mail.Send              - Application - Granted for [Org]
```

**Azure AD Setup Complete!** ✅

---

## PART 2: SHOPIFY ADMIN API SETUP

### Step 2.1: Enable Custom App Development

1. Log into your Shopify admin: `https://yourstore.myshopify.com/admin`
2. Go to **Settings** (bottom left)
3. Click **Apps and sales channels**
4. Click **Develop apps** (near the top)
5. If prompted, click **Allow custom app development**

### Step 2.2: Create Custom App

1. Click **Create an app**
2. App name: `Support Bot`
3. App developer: Select yourself
4. Click **Create app**

### Step 2.3: Configure Admin API Scopes

1. Click **Configure Admin API scopes**
2. Scroll down and check these boxes:
   - ✅ **read_orders** - Read orders
   - ✅ **write_orders** - Modify orders  
   - ✅ **read_customers** - Read customer data
   - ✅ **read_fulfillments** - Read fulfillments and shipments
3. Click **Save** at the bottom

### Step 2.4: Install App and Get Token

1. Click the **API credentials** tab
2. Click **Install app** button
3. Click **Install** in the confirmation modal
4. You'll see the **Admin API access token**
5. Click **Reveal token once** and **COPY IT IMMEDIATELY**

```
Admin API Access Token: shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**IMPORTANT**: This token is shown only once. Store it securely.

### Step 2.5: Note Your Store Domain

Your Shopify domain is: `yourstore.myshopify.com`

**Shopify Setup Complete!** ✅

---

## PART 3: ANTHROPIC API KEY

### Step 3.1: Get API Key

1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Click **API Keys** in left sidebar
4. Click **Create Key**
5. Name it: `Support Bot`
6. Copy the key (starts with `sk-ant-`)

```
Anthropic API Key: sk-ant-apiXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Anthropic Setup Complete!** ✅

---

## PART 4: SLACK INTEGRATION SETUP

### Step 4.1: Create Slack Webhook

1. Go to https://api.slack.com/apps
2. Click **Create New App**
3. Select **From scratch**
4. App Name: `Support Bot Alerts`
5. Pick your workspace
6. Click **Create App**

### Step 4.2: Enable Incoming Webhooks

1. In the left sidebar, click **Incoming Webhooks**
2. Toggle **Activate Incoming Webhooks** to ON
3. Scroll down and click **Add New Webhook to Workspace**
4. Select the channel where you want notifications (e.g., `#support-alerts`)
5. Click **Allow**

### Step 4.3: Copy Webhook URL

You'll see your webhook URL:
```
Webhook URL: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

Copy this URL - you'll add it to `.env`

**Slack Setup Complete!** ✅

---

## PART 5: PROJECT SETUP

### Step 5.1: Initialize Project

```bash
# Create project directory
mkdir support-bot
cd support-bot

# Initialize git
git init

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 5.2: Create .gitignore

Create `.gitignore` file:

```
# Environment variables
.env
.env.local

# Python
venv/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
```

### Step 5.3: Create requirements.txt

Create `requirements.txt`:

```
anthropic>=0.39.0
requests>=2.31.0
python-dotenv>=1.0.0
python-dateutil>=2.8.2
pytz>=2024.1
beautifulsoup4>=4.12.0
lxml>=5.0.0
```

### Step 5.4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5.5: Create .env File

Create `.env` file with your credentials:

```bash
# Outlook Configuration
OUTLOOK_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTLOOK_CLIENT_SECRET=abc123~DEF456.ghi789JKL
OUTLOOK_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SUPPORT_EMAIL=support@yourstore.com

# Shopify Configuration
SHOPIFY_DOMAIN=yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-apiXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

# Optional: Database path
DB_PATH=support_bot.db

# Optional: Check interval (minutes)
CHECK_INTERVAL_MINUTES=5
```

**Replace all the `xxx` values with your actual credentials from the previous steps.**

---

## PART 6: CREATE PROJECT FILES

### File 1: outlook_email_handler.py

**Claude Code: Create this file with the content from the earlier artifact `outlook_email_handler.py`**

Key features:
- Microsoft Graph API authentication
- Fetch unread emails
- Send replies
- Mark emails as read
- Get attachments

### File 2: shopify_integration.py

**Claude Code: Create this file with the content from the earlier artifact `shopify_integration.py`**

Key features:
- Find orders by email or order number
- Get order status and tracking info
- Update shipping addresses
- Check fulfillment status

### File 3: slack_notifier.py (NEW)

**Claude Code: Create this NEW file:**

```python
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
            'high': '#FF0000',    # Red
            'medium': '#FFD700',  # Gold
            'low': '#36A64F'      # Green
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


# Usage example
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    notifier = SlackNotifier(os.getenv('SLACK_WEBHOOK_URL'))
    
    # Test notification
    notifier.notify_human_review_needed(
        order_number="1234",
        customer_email="customer@example.com",
        reason="Package not received - 10 days overdue",
        priority="high"
    )
```

### File 4: customer_support_agent.py (UPDATED - More Polite Tone)

**Claude Code: Create this file with UPDATED system prompt for very polite tone:**

```python
"""
AI Customer Support Agent using Claude API
Implements specific support guidelines with very polite and kind tone
"""

import anthropic
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class CustomerSupportAgent:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
        
    def build_system_prompt(self) -> str:
        """Build the system prompt with very polite and kind tone"""
        return """You are a warm, friendly, and exceptionally polite customer support agent for a Shopify clothing store. Your primary goal is to make every customer feel valued, heard, and cared for while following company policies.

TONE & COMMUNICATION STYLE:
- Be VERY polite, kind, and empathetic in every response
- Use warm, friendly language that makes customers feel appreciated
- Always thank customers for reaching out and for their patience
- Express genuine understanding and care for their situation
- Use phrases like "I completely understand," "I'm so sorry for any inconvenience," "I'd be more than happy to help"
- End responses with warm closings like "Please don't hesitate to reach out if you need anything else!" or "We're here to help anytime!"
- Even when delivering policy-based denials, be compassionate and offer alternatives when possible
- Never be curt or robotic - write as a caring human

CRITICAL POLICIES - FOLLOW EXACTLY:

1. REFUNDS & RETURNS POLICY:
   - All sales are FINAL. We do NOT offer refunds or returns.
   - ONLY TWO EXCEPTIONS (be kind but firm):
     a) Defective products: "We'd be more than happy to send you a replacement! Could you please send us some clear photos of the issue? We want to make sure we get you the perfect replacement."
     b) Non-delivery with proof: "I'm so sorry your package hasn't arrived! We'll absolutely send you a replacement once we confirm with the tracking information that it was returned to sender or delivered to the wrong address."
   
   - For sizing issues: "I completely understand how frustrating sizing issues can be! Unfortunately, due to our policy, we're unable to accept returns or exchanges for sizing. However, I'd love to help you find the perfect fit for your next order! Our items are based on adult sizing, though kids should fit into smalls. Is there anything else I can help you with?"

2. ITEMS NOT RECEIVED:
   - If within expected delivery window (order date + 14 days): 
     "I completely understand your concern! Your package is still within our typical 10-14 day shipping window. According to our tracking, it's currently [status]. I'm confident it will arrive soon, but please don't hesitate to reach out if you have any other questions!"
   
   - If 7+ days past expected delivery: 
     "I'm so sorry for this delay! This is definitely taking longer than expected. Let me flag this for our team to review right away, and we'll get back to you within 24 hours with a solution. Thank you so much for your patience!"
     FLAG: "NEEDS_HUMAN_REVIEW: Not received - Order #[number] - [X] days overdue"

3. SHIPPING QUESTIONS:
   - "Our standard shipping typically takes 10-14 business days, though occasionally it can take up to 3 weeks depending on your location. We truly appreciate your patience!"
   - For tracking: "I'd be happy to check on that for you! According to the tracking information, your package is currently [status]. It should arrive by [date]. Please let me know if you have any other questions!"
   - If unfulfilled: "I see your order hasn't shipped yet. Let me flag this for immediate attention, and our team will follow up with you shortly!"
     FLAG: "NEEDS_HUMAN_REVIEW: Unfulfilled - Order #[number]"

4. ADDRESS CHANGES:
   - If not yet shipped: "Absolutely! I'd be more than happy to update your shipping address for you. Let me take care of that right away!"
     USE TOOL: update_address
   
   - If already shipped: "I completely understand the situation, and I wish I could help! Unfortunately, since your package has already been shipped, we're unable to redirect it or send a replacement. I'm so sorry for any inconvenience this may cause. Is there anything else I can assist you with?"

5. SPAM FILTER:
   - IGNORE sales rep emails (marketing, SEO, ads, etc.)
   - ONLY respond to customer order inquiries
   - If spam: Return "SPAM_DETECTED: [brief reason]"

6. GENERAL QUESTIONS:
   - "All of our clothing is based on adult sizing, though kids should fit comfortably into smalls!"
   - "Shipping typically takes 10-14 business days, though it can occasionally take up to 3 weeks depending on your location."
   - Always be patient and thorough in explanations

EXAMPLE RESPONSES:

Bad (too robotic): "We don't accept returns. Shipping is 10-14 days."

Good (very polite): "Thank you so much for reaching out! I completely understand your concern about the fit. Unfortunately, we're unable to accept returns or exchanges due to our policy. However, I'd love to help you find the perfect size for any future orders! Please don't hesitate to reach out if you need sizing guidance. We're here to help!"

RESPONSE FORMAT:
- Complete, warm, friendly customer-facing response (default)
- If escalation needed: Start with "NEEDS_HUMAN_REVIEW: [reason]" then draft a kind response
- If spam: "SPAM_DETECTED: [reason]"
- If address update: "ACTION_REQUIRED: update_address" with details

Remember: You represent the brand. Every interaction should leave the customer feeling valued and cared for, even when you cannot fulfill their exact request. Be genuinely helpful, kind, and professional."""

    def classify_email_intent(self, email_body: str, subject: str) -> Dict:
        """Classify the email to determine intent and filter spam"""
        email_lower = (email_body + " " + subject).lower()
        
        # Spam patterns
        spam_keywords = [
            'seo service', 'boost your sales', 'increase traffic', 
            'marketing service', 'grow your business', 'website optimization',
            'google ranking', 'social media marketing', 'advertising opportunity',
            'partner with us', 'collaboration opportunity', 'influencer',
            'backlinks', 'web design', 'app development', 'consulting'
        ]
        
        if any(keyword in email_lower for keyword in spam_keywords):
            return {
                'is_spam': True,
                'intent': 'spam',
                'confidence': 0.9
            }
        
        # Customer intent patterns
        intents = {
            'tracking': ['where is my order', 'tracking', 'shipped', 'delivery', 'havent received', 'not arrived'],
            'return_refund': ['return', 'refund', 'money back', 'send back', 'exchange'],
            'defective': ['defective', 'broken', 'damaged', 'wrong item', 'missing', 'torn'],
            'address_change': ['change address', 'wrong address', 'update address', 'different address', 'ship to'],
            'sizing': ['too small', 'too big', 'doesnt fit', 'wrong size', 'size issue', 'fit'],
            'general': ['question', 'info', 'how long', 'when will', 'sizing', 'kids']
        }
        
        detected_intents = []
        for intent_type, keywords in intents.items():
            if any(keyword in email_lower for keyword in keywords):
                detected_intents.append(intent_type)
        
        return {
            'is_spam': False,
            'intent': detected_intents[0] if detected_intents else 'general',
            'all_intents': detected_intents,
            'confidence': 0.7
        }
    
    def extract_order_number(self, text: str) -> Optional[str]:
        """Extract order number from email text"""
        patterns = [
            r'#(\d{4,6})',
            r'order\s*#?\s*(\d{4,6})',
            r'\b(\d{4,6})\b'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def calculate_days_since_expected(self, order_context: Dict) -> int:
        """Calculate days since expected delivery"""
        if not order_context or not order_context.get('expected_delivery_max'):
            return 0
        
        try:
            expected = datetime.fromisoformat(order_context['expected_delivery_max'].replace('Z', '+00:00'))
            days_past = (datetime.now(expected.tzinfo) - expected).days
            return max(0, days_past)
        except:
            return 0
    
    def generate_response(self, customer_email: str, customer_name: str,
                         email_subject: str, email_body: str, 
                         order_context: Optional[Dict] = None) -> Dict:
        """
        Generate AI response using Claude with all context
        
        Returns:
            Dictionary with response text, actions needed, and flags
        """
        
        # Classify the email
        classification = self.classify_email_intent(email_body, email_subject)
        
        if classification['is_spam']:
            return {
                'type': 'spam',
                'should_send': False,
                'response': None,
                'flag_for_human': False,
                'reason': 'Spam detected - sales/marketing email'
            }
        
        # Build context for Claude
        context_parts = [
            f"Customer Name: {customer_name}",
            f"Customer Email: {customer_email}",
            f"Subject: {email_subject}",
            f"Customer Message:\n{email_body}\n",
        ]
        
        if order_context:
            context_parts.append("\nORDER INFORMATION:")
            context_parts.append(f"Order Number: {order_context.get('order_number')}")
            context_parts.append(f"Order Date: {order_context.get('created_at')}")
            context_parts.append(f"Status: {order_context.get('fulfillment_status')}")
            context_parts.append(f"Financial Status: {order_context.get('financial_status')}")
            
            if order_context.get('tracking_info'):
                context_parts.append("\nTRACKING INFORMATION:")
                for tracking in order_context['tracking_info']:
                    context_parts.append(f"  Tracking #: {tracking['number']}")
                    context_parts.append(f"  Carrier: {tracking['company']}")
                    if tracking.get('url'):
                        context_parts.append(f"  Track here: {tracking['url']}")
                    if tracking.get('status'):
                        context_parts.append(f"  Status: {tracking['status']}")
            
            # Calculate days since expected delivery
            days_past = self.calculate_days_since_expected(order_context)
            if days_past > 0:
                context_parts.append(f"\nNOTE: Package is {days_past} days past expected delivery")
            
            context_parts.append("\nORDERED ITEMS:")
            for item in order_context.get('line_items', []):
                context_parts.append(f"  - {item['name']} (Qty: {item['quantity']})")
        
        user_message = "\n".join(context_parts)
        
        # Call Claude API
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.build_system_prompt(),
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            response_text = message.content[0].text
            
            # Parse response for flags and actions
            needs_human = response_text.startswith("NEEDS_HUMAN_REVIEW:")
            is_spam = response_text.startswith("SPAM_DETECTED:")
            needs_action = "ACTION_REQUIRED:" in response_text
            
            if needs_human:
                reason_line = response_text.split('\n')[0]
                reason = reason_line.replace("NEEDS_HUMAN_REVIEW:", "").strip()
                response_text = response_text.replace(reason_line, "").strip()
            else:
                reason = None
            
            return {
                'type': 'customer_inquiry',
                'response': response_text,
                'should_send': not needs_human and not is_spam,
                'flag_for_human': needs_human,
                'human_review_reason': reason,
                'needs_action': needs_action,
                'intent': classification['intent']
            }
            
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {
                'type': 'error',
                'response': None,
                'should_send': False,
                'flag_for_human': True,
                'human_review_reason': f"AI error: {str(e)}"
            }
```

### File 5: main_support_bot.py (UPDATED - with Slack)

**Claude Code: Update the main orchestrator to include Slack notifications:**

Add to imports:
```python
from slack_notifier import SlackNotifier
```

Update the `__init__` method to include:
```python
# Initialize Slack notifier if webhook URL provided
slack_url = config.get('slack_webhook_url')
self.slack = SlackNotifier(slack_url) if slack_url else None
```

Update the `add_to_review_queue` method to include Slack notification:
```python
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
    
    # Send Slack notification
    if self.slack:
        self.slack.notify_human_review_needed(
            order_number=order_number,
            customer_email=customer_email,
            reason=reason,
            priority=priority
        )
```

### File 6: test_setup.py

**Claude Code: Create this file from the earlier artifact `test_setup.py`**

### File 7: review_dashboard.py

**Claude Code: Create this file from the earlier artifact `review_dashboard.py`**

---

## PART 7: TESTING LOCALLY

### Step 7.1: Verify Setup

```bash
# Run the test script
python test_setup.py
```

This should verify:
- ✅ All environment variables set
- ✅ Outlook authentication works
- ✅ Shopify connection works
- ✅ Claude API accessible
- ✅ Database created

### Step 7.2: Test Slack Integration

```bash
# Test Slack notification
python slack_notifier.py
```

You should receive a test notification in your Slack channel.

### Step 7.3: Send Test Email

1. Send a test email to your support address
2. In the email, mention an order number
3. Run the bot once:

```bash
python main_support_bot.py
```

4. Check if you received a reply
5. Check Slack for notifications (if flagged)

### Step 7.4: Review Dashboard

```bash
# Check the dashboard
python review_dashboard.py

# Resolve items if needed
python review_dashboard.py resolve
```

---

## PART 8: RAILWAY DEPLOYMENT

### Step 8.1: Prepare for Deployment

1. Make sure all files are committed to git:

```bash
git add .
git commit -m "Initial support bot implementation"
```

2. Push to GitHub:

```bash
# Create new repo on GitHub, then:
git remote add origin https://github.com/yourusername/support-bot.git
git branch -M main
git push -u origin main
```

### Step 8.2: Create Railway Project

1. Go to https://railway.app/
2. Click **Sign in with GitHub**
3. Authorize Railway
4. Click **New Project**
5. Select **Deploy from GitHub repo**
6. Choose your `support-bot` repository
7. Click **Deploy Now**

### Step 8.3: Add Environment Variables

1. After deployment, click on your project
2. Click on the **Variables** tab
3. Click **Raw Editor**
4. Paste all your environment variables:

```
OUTLOOK_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTLOOK_CLIENT_SECRET=abc123~DEF456.ghi789JKL
OUTLOOK_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SUPPORT_EMAIL=support@yourstore.com
SHOPIFY_DOMAIN=yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-apiXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
CHECK_INTERVAL_MINUTES=5
```

5. Click **Update Variables**

### Step 8.4: Configure Start Command

Railway needs to know how to run your app:

1. In your project root, create `Procfile` (no extension):

```
worker: python main_support_bot.py
```

2. Commit and push:

```bash
git add Procfile
git commit -m "Add Procfile for Railway"
git push
```

Railway will automatically redeploy.

### Step 8.5: Monitor Deployment

1. Click on **Deployments** tab
2. Watch the build logs
3. Once deployed, click on **View Logs**
4. You should see: "🤖 Support Bot Started"

### Step 8.6: Verify It's Working

1. Send a test email to your support address
2. Wait 5 minutes (or your CHECK_INTERVAL)
3. Check your email for the AI response
4. Check Slack for any notifications
5. View Railway logs to see processing

---

## PART 9: MONITORING & MAINTENANCE

### Daily Monitoring

**Check Slack notifications** for items needing review

**Or run dashboard remotely:**
```bash
# If you want to check status
railway run python review_dashboard.py
```

### Weekly Tasks

1. Review flagged emails and mark as resolved
2. Check Railway logs for any errors
3. Verify response quality

### Monthly Tasks

1. Review automation rate and stats
2. Update guidelines if policies change
3. Analyze common questions
4. Update system prompt if needed

### Troubleshooting

**Bot not processing emails?**
- Check Railway logs for errors
- Verify environment variables
- Test Outlook authentication
- Check if support email is correct

**Getting spam?**
- Update spam keywords in `classify_email_intent()`
- Review flagged spam to improve detection

**Wrong responses?**
- Review the system prompt
- Add more specific examples
- Adjust tone or policy explanations

**Slack not notifying?**
- Test webhook URL manually
- Check Slack app permissions
- Verify webhook isn't expired

---

## PART 10: COST MONITORING

### Track Your Costs

**Railway:** Check your usage at https://railway.app/account/usage
- Free tier: $5/month credit
- After that: Pay-as-you-go

**Anthropic:** Check usage at https://console.anthropic.com/settings/usage
- ~10 emails/day = ~300/month
- Sonnet 4.5: ~$3-5/month

**Total Expected: $10-20/month** ✅

---

## PART 11: CUSTOMIZATION & SCALING

### Increase Email Volume

If you get more than 20 emails/day:
1. Decrease `CHECK_INTERVAL_MINUTES` to 3
2. Consider PostgreSQL instead of SQLite
3. Monitor API costs

### Add More Features

**Want SMS notifications?**
- Add Twilio integration similar to Slack

**Want to track response time?**
- Add timestamps and calculate SLA metrics

**Want analytics dashboard?**
- Create a simple web dashboard with Flask

**Want email templates?**
- Add common response templates to the system prompt

---

## ✅ CHECKLIST

Use this to track your progress:

**Setup Phase:**
- [ ] Azure AD app created with client ID, secret, tenant ID
- [ ] API permissions granted and admin consent given
- [ ] Shopify custom app created with Admin API token
- [ ] Anthropic API key obtained
- [ ] Slack webhook created
- [ ] Project files created
- [ ] `.env` file configured with all credentials
- [ ] Dependencies installed
- [ ] Local tests passed

**Deployment Phase:**
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables added to Railway
- [ ] Procfile created
- [ ] Bot deployed and running
- [ ] Test email sent and responded to
- [ ] Slack notification received
- [ ] Dashboard accessible

**Maintenance Phase:**
- [ ] Daily Slack monitoring setup
- [ ] Weekly review scheduled
- [ ] Cost monitoring configured
- [ ] Backup strategy for database

---

## 🎉 SUCCESS!

Once all checks are complete, your AI customer support agent is live and saving you hours each week!

**Expected Results:**
- 60-70% of emails handled automatically
- Instant responses (vs hours of manual work)
- Consistent, polite, policy-compliant responses
- Real-time Slack alerts for important issues
- Complete audit trail in database

**Next Steps:**
1. Monitor for first week closely
2. Refine tone/responses as needed
3. Track automation rate
4. Celebrate your free time! 🎊

---

## 📞 SUPPORT

If you run into issues:

1. Check Railway logs first
2. Run `test_setup.py` to verify connections
3. Review this guide step-by-step
4. Check `.env` file for typos
5. Verify all API permissions granted

Most common issues are:
- Missing admin consent in Azure (Step 1.6)
- Wrong API scopes in Shopify
- Typos in environment variables
- Expired API tokens

Good luck! 🚀
