"""
Test email filtering to verify blocked senders are caught
"""

from customer_support_agent import CustomerSupportAgent
import os
from dotenv import load_dotenv

load_dotenv()

agent = CustomerSupportAgent(api_key=os.getenv('ANTHROPIC_API_KEY'))

test_cases = [
    {
        'email': 'noreply@aliexpress.com',
        'name': 'AliExpress',
        'should_block': True,
        'description': 'AliExpress notification'
    },
    {
        'email': 'notifications@shopify.com',
        'name': 'Shopify',
        'should_block': True,
        'description': 'Shopify notification'
    },
    {
        'email': 'no-reply@myshopify.com',
        'name': 'Your Store',
        'should_block': True,
        'description': 'Shopify store notification'
    },
    {
        'email': 'sales@somemarketingcompany.com',
        'name': 'Sales Team',
        'should_block': True,
        'description': 'Sales email'
    },
    {
        'email': 'marketing@agency.com',
        'name': 'Marketing Agency',
        'should_block': True,
        'description': 'Marketing email'
    },
    {
        'email': 'customer@gmail.com',
        'name': 'John Doe',
        'should_block': False,
        'description': 'Real customer email'
    },
    {
        'email': 'jane.smith@yahoo.com',
        'name': 'Jane Smith',
        'should_block': False,
        'description': 'Real customer email'
    }
]

print("="*60)
print("EMAIL FILTERING TEST")
print("="*60)

passed = 0
failed = 0

for test in test_cases:
    is_blocked, reason = agent.is_blocked_sender(test['email'], test['name'])
    expected = test['should_block']

    status = "✅ PASS" if is_blocked == expected else "❌ FAIL"

    if is_blocked == expected:
        passed += 1
    else:
        failed += 1

    print(f"\n{status} - {test['description']}")
    print(f"   Email: {test['email']}")
    print(f"   Name: {test['name']}")
    print(f"   Expected: {'BLOCK' if expected else 'ALLOW'}")
    print(f"   Result: {'BLOCKED' if is_blocked else 'ALLOWED'}")
    if is_blocked:
        print(f"   Reason: {reason}")

print("\n" + "="*60)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("="*60)
