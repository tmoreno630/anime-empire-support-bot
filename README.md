# AI Customer Support Agent

Automated customer support system for Shopify stores using Claude AI to respond to customer emails.

## Features

- ✅ Monitors Outlook inbox every 5 minutes
- ✅ Automatically responds to 60-70% of customer emails
- ✅ Follows strict company policies
- ✅ Flags complex issues for human review
- ✅ Sends Slack notifications for items needing attention
- ✅ Tracks all interactions in SQLite database
- ✅ Cost: ~$10-20/month

## Project Structure

```
customer_support/
├── .env                          # Environment variables (configure this!)
├── .gitignore                    # Git ignore file
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── master_implementation.md      # Detailed setup guide
├── outlook_email_handler.py      # Email integration
├── shopify_integration.py        # Shopify API handler
├── customer_support_agent.py     # AI agent with guidelines
├── slack_notifier.py             # Slack notifications
├── main_support_bot.py           # Main orchestration
├── review_dashboard.py           # CLI dashboard
├── test_setup.py                 # Setup verification
└── support_bot.db                # SQLite database (auto-created)
```

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit [.env](.env) and add your credentials:

```bash
# Required
OUTLOOK_CLIENT_ID=your_azure_client_id
OUTLOOK_CLIENT_SECRET=your_azure_secret
OUTLOOK_TENANT_ID=your_azure_tenant_id
SUPPORT_EMAIL=support@yourstore.com
SHOPIFY_DOMAIN=yourstore.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_token
ANTHROPIC_API_KEY=your_anthropic_key

# Optional
SLACK_WEBHOOK_URL=your_slack_webhook
```

### 3. Test Setup

```bash
python test_setup.py
```

This verifies:
- Environment variables configured
- Outlook authentication working
- Shopify connection working
- Claude API accessible
- Database creation successful

### 4. Run the Bot

```bash
# Run once
python main_support_bot.py

# Or run continuously (checks every 5 minutes)
# Press Ctrl+C to stop
```

### 5. View Review Dashboard

```bash
# View pending reviews
python review_dashboard.py

# View statistics
python review_dashboard.py stats

# Interactive resolve mode
python review_dashboard.py resolve
```

## Setup Guide

For detailed setup instructions including:
- Azure AD configuration
- Shopify API setup
- Anthropic API key
- Slack webhook
- Railway deployment

See [master_implementation.md](master_implementation.md)

## How It Works

1. **Email Monitoring**: Bot checks inbox every 5 minutes for unread emails
2. **Spam Filtering**: Automatically filters out sales/marketing emails
3. **Order Lookup**: Finds order info from Shopify using order number or email
4. **AI Response**: Claude generates polite, policy-compliant response
5. **Human Review**: Complex issues flagged and sent to Slack
6. **Response Sent**: AI reply sent automatically for simple cases
7. **Tracking**: All actions logged in database

## Policies

The AI follows strict policies:

- **No refunds/returns** except defective items or non-delivery
- **Shipping**: 10-14 business days standard
- **Sizing**: Adult sizing, kids fit smalls
- **Address changes**: Only before fulfillment
- **Very polite tone**: Warm, friendly, empathetic

## Monitoring

### Slack Notifications

Receive alerts for:
- Items needing human review
- High priority issues
- System errors

### Review Dashboard

```bash
python review_dashboard.py
```

Shows:
- Pending reviews
- Automation rate
- Recent activity

## Deployment

### Railway (Recommended)

1. Push code to GitHub
2. Create Railway project
3. Connect GitHub repo
4. Add environment variables
5. Deploy!

See [master_implementation.md](master_implementation.md) Part 8 for details.

## Troubleshooting

**Bot not processing emails?**
- Check Railway logs
- Verify environment variables
- Test Outlook authentication

**Getting spam?**
- Update spam keywords in `customer_support_agent.py`

**Wrong responses?**
- Review system prompt in `customer_support_agent.py`
- Adjust tone or policy explanations

**Slack not notifying?**
- Test webhook URL
- Check Slack app permissions

## Cost Breakdown

- **Railway**: $0-5/month (free tier covers most usage)
- **Anthropic API**: $3-5/month (~300 emails)
- **Microsoft/Shopify**: Free tiers
- **Total**: $10-20/month

## Support

For issues or questions, check:
1. [master_implementation.md](master_implementation.md) - detailed guide
2. Railway logs for errors
3. Run `python test_setup.py` to diagnose

## License

Private project for internal use.
