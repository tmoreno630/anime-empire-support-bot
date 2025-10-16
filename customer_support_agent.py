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
   - If tracking shows DELIVERED but customer says not received:
     "I completely understand your concern, and I'm so sorry you haven't received your package! According to the tracking information, the package shows as delivered. In cases where the tracking confirms delivery, we recommend contacting the shipping carrier directly, as they can provide specific details about the exact delivery location and assist with any delivery issues."

     IMPORTANT: Always include carrier-specific information from the order's tracking_info when available:
     - Mention the carrier name (USPS, UPS, FedEx, DHL, etc.)
     - Include the tracking number
     - Provide the tracking URL if available
     Example: "The package was shipped via USPS with tracking number 9400123456789. You can track it or contact USPS directly at [tracking URL]."

     (Do NOT offer replacement or refund - direct them to the carrier)

   - If within expected delivery window (order date + 14 days):
     "I completely understand your concern! Your package is still within our typical 10-14 day shipping window. According to our tracking, it's currently [status]. I'm confident it will arrive soon, but please don't hesitate to reach out if you have any other questions!"

   - If 7+ days past expected delivery AND not showing as delivered:
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

    def is_blocked_sender(self, sender_email: str, sender_name: str = '') -> Tuple[bool, str]:
        """
        Check if sender should be blocked (non-customer emails)
        Returns (is_blocked, reason)
        """
        sender_email = sender_email.lower()
        sender_name = sender_name.lower()

        blocked_domains = [
            'aliexpress.com',
            'shopify.com',
            'myshopify.com',
            'noreply',
            'no-reply',
            'donotreply',
            'notifications@',
            'marketing@',
            'sales@',
            'support@shopify',
            'alerts@'
        ]

        blocked_keywords = [
            'aliexpress',
            'shopify notification',
            'shopify alert',
            'automatic notification',
            'system notification'
        ]

        for domain in blocked_domains:
            if domain in sender_email:
                return (True, f'Blocked domain: {domain}')

        for keyword in blocked_keywords:
            if keyword in sender_name or keyword in sender_email:
                return (True, f'Blocked keyword: {keyword}')

        return (False, '')

    def classify_email_intent(self, email_body: str, subject: str) -> Dict:
        """Classify the email to determine intent and filter spam"""
        email_lower = (email_body + " " + subject).lower()

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

        classification = self.classify_email_intent(email_body, email_subject)

        if classification['is_spam']:
            return {
                'type': 'spam',
                'should_send': False,
                'response': None,
                'flag_for_human': False,
                'reason': 'Spam detected - sales/marketing email'
            }

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

            days_past = self.calculate_days_since_expected(order_context)
            if days_past > 0:
                context_parts.append(f"\nNOTE: Package is {days_past} days past expected delivery")

            context_parts.append("\nORDERED ITEMS:")
            for item in order_context.get('line_items', []):
                context_parts.append(f"  - {item['name']} (Qty: {item['quantity']})")

        user_message = "\n".join(context_parts)

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


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    agent = CustomerSupportAgent(api_key=os.getenv('ANTHROPIC_API_KEY'))

    test_email = """
    Hi, I ordered a shirt (order #1234) two weeks ago and it still hasn't arrived.
    Can you help me track it down?
    """

    result = agent.generate_response(
        customer_email="test@example.com",
        customer_name="Test Customer",
        email_subject="Where is my order?",
        email_body=test_email
    )

    print("Response:", result)
