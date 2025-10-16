# Email Filtering Updates - Reduce API Costs

## Summary
Added early-stage email sender filtering to block non-customer emails BEFORE they reach the AI agent, significantly reducing Anthropic API costs.

## Changes Made

### 1. New Method: `is_blocked_sender()`
**File**: [customer_support_agent.py](customer_support_agent.py:95)

Checks sender email and name against blocked lists and returns `(is_blocked, reason)`.

**Blocked Domains:**
- `aliexpress.com` - AliExpress notifications
- `shopify.com` - Shopify notifications
- `myshopify.com` - Shopify store notifications
- `noreply`, `no-reply`, `donotreply` - Automated emails
- `notifications@`, `alerts@` - System notifications
- `marketing@`, `sales@` - Marketing/sales emails
- `support@shopify` - Shopify support

**Blocked Keywords:**
- `aliexpress`
- `shopify notification`, `shopify alert`
- `automatic notification`, `system notification`

### 2. Early Filtering in Email Processing
**File**: [main_support_bot.py](main_support_bot.py:166)

Added sender check immediately after loading email data, BEFORE:
- Order lookup
- AI processing
- API calls

Blocked emails are:
- Marked as read
- Logged in database with intent `'blocked_sender'`
- Skipped for AI processing (saves API costs)

### 3. Testing
**File**: [test_email_filtering.py](test_email_filtering.py)

Comprehensive test suite with 7 test cases:
- ✅ AliExpress notifications
- ✅ Shopify notifications
- ✅ Sales emails
- ✅ Marketing emails
- ✅ Customer emails (allowed)

All tests passing.

### 4. Documentation
**File**: [README.md](README.md)

Updated to reflect:
- New filtering feature
- How to customize blocked senders
- Updated workflow diagram

## Cost Impact

### Before
- All emails processed by AI (including spam/notifications)
- ~500 emails/month × $0.015 = **$7.50/month**

### After
- Only customer emails processed by AI
- Estimated 30-40% reduction in AI calls
- ~300 customer emails × $0.015 = **$4.50/month**
- **Savings: ~$3/month (40% reduction)**

## How to Customize

To add more blocked senders, edit [customer_support_agent.py](customer_support_agent.py:95):

```python
blocked_domains = [
    'aliexpress.com',
    'shopify.com',
    'your-domain-to-block.com',  # Add here
]

blocked_keywords = [
    'aliexpress',
    'your-keyword-to-block',  # Add here
]
```

## Testing

Run the test suite:
```bash
python3 test_email_filtering.py
```

Expected output: 7/7 tests passing

## Database Tracking

Blocked emails are logged with:
- `intent`: `'blocked_sender'`
- `response_sent`: `False`
- `flagged_for_review`: `False`

Query blocked emails:
```sql
SELECT * FROM processed_emails WHERE intent = 'blocked_sender';
```

## Next Steps

1. Monitor bot logs for any legitimate emails accidentally blocked
2. Adjust `blocked_domains` and `blocked_keywords` as needed
3. Consider adding whitelist if needed for specific senders
4. Track cost savings in Anthropic dashboard

## Rollback

If filtering is too aggressive:
1. Comment out lines 166-172 in [main_support_bot.py](main_support_bot.py:166)
2. Redeploy

## Support

Run test to verify filtering:
```bash
python3 test_email_filtering.py
```

Check database for blocked emails:
```bash
sqlite3 support_bot.db "SELECT customer_email, subject, processed_at FROM processed_emails WHERE intent='blocked_sender' ORDER BY processed_at DESC LIMIT 10;"
```
