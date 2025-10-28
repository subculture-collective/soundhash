# Email Notification System

Comprehensive email notification system with templates, preferences, transactional emails, and marketing automation.

## Features

- ✉️ **Transactional Emails**: Welcome, password reset, payment receipts, API key notifications
- 📊 **Product Emails**: Match notifications, processing updates, quota warnings
- 📣 **Marketing Emails**: Feature announcements, tips & tricks, case studies
- 🔔 **Admin Emails**: Security alerts, system notifications, reports
- 🎨 **Customizable Templates**: Jinja2-based templates with branding
- 📈 **Analytics**: Track opens, clicks, and email performance
- ⚙️ **User Preferences**: Fine-grained control over email types
- 🔄 **Digest Emails**: Daily and weekly activity summaries
- 🤖 **Marketing Automation**: Onboarding workflows, re-engagement campaigns
- 🧪 **A/B Testing**: Test different email variants
- 🌍 **Multi-language Support**: Template localization
- 🚫 **Unsubscribe Management**: Easy opt-out system

## Configuration

### Environment Variables

```bash
# Enable/disable email system
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid  # or 'ses'

# SendGrid Configuration
SENDGRID_API_KEY=your_api_key_here
SENDGRID_FROM_EMAIL=noreply@soundhash.io
SENDGRID_FROM_NAME=SoundHash

# AWS SES Configuration (alternative)
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY=your_access_key
AWS_SES_SECRET_KEY=your_secret_key
AWS_SES_FROM_EMAIL=noreply@soundhash.io

# Email Templates
EMAIL_TEMPLATES_DIR=./templates/email

# Email Tracking
EMAIL_TRACK_OPENS=true
EMAIL_TRACK_CLICKS=true
EMAIL_UNSUBSCRIBE_URL=http://localhost:8000/api/email/unsubscribe

# Digest Settings
DIGEST_DAILY_ENABLED=true
DIGEST_DAILY_TIME=09:00
DIGEST_WEEKLY_ENABLED=true
DIGEST_WEEKLY_DAY=1  # Monday=1, Sunday=7
DIGEST_WEEKLY_TIME=09:00
```

## Email Types

### Transactional Emails

Always sent (cannot be disabled):
- Welcome email when user signs up
- Password reset requests
- Security alerts
- API key generation notifications

```python
from src.email import send_welcome_email, send_password_reset_email

# Send welcome email
await send_welcome_email(
    user_email="user@example.com",
    username="johndoe",
    user_id=1
)

# Send password reset
await send_password_reset_email(
    user_email="user@example.com",
    username="johndoe",
    reset_token="abc123",
    user_id=1
)
```

### Product Emails

Can be disabled by users:
- Audio match found
- Processing job completed
- Quota warnings
- API usage alerts

```python
from src.email import send_match_found_email, send_quota_warning_email

# Send match notification
await send_match_found_email(
    user_email="user@example.com",
    username="johndoe",
    match_video_title="Awesome Song",
    match_video_url="https://youtube.com/watch?v=xxx",
    similarity_score=0.95,
    user_id=1
)

# Send quota warning
await send_quota_warning_email(
    user_email="user@example.com",
    username="johndoe",
    quota_type="API requests",
    usage_percentage=85.0,
    user_id=1
)
```

### Marketing Emails

Can be disabled by users:
- Feature announcements
- Tips & tricks
- Case studies
- Product updates

```python
from src.email.automation import marketing_automation

# Send feature announcement
await marketing_automation.send_feature_announcement(
    feature_name="WebSocket Streaming",
    feature_description="Real-time audio fingerprinting",
    feature_url="https://soundhash.io/features/streaming"
)
```

### Digest Emails

Automated daily/weekly summaries:

```python
from src.email.digest import send_daily_digests, send_weekly_digests

# Send daily digests to all users
results = await send_daily_digests()
print(f"Sent: {results['sent']}, Skipped: {results['skipped']}")

# Send weekly digests
results = await send_weekly_digests()
```

## API Endpoints

### Get Email Preferences

```bash
GET /api/v1/email/preferences
Authorization: Bearer <token>
```

Response:
```json
{
  "id": 1,
  "user_id": 1,
  "receive_match_found": true,
  "receive_processing_complete": true,
  "receive_quota_warnings": true,
  "receive_feature_announcements": true,
  "receive_daily_digest": false,
  "receive_weekly_digest": true,
  "preferred_language": "en",
  "unsubscribed_at": null
}
```

### Update Email Preferences

```bash
PUT /api/v1/email/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "receive_match_found": false,
  "receive_daily_digest": true,
  "preferred_language": "en"
}
```

### Unsubscribe from All Emails

```bash
POST /api/v1/email/unsubscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "optional_unsubscribe_token"
}
```

### Get Email Logs

```bash
GET /api/v1/email/logs?category=product&limit=50
Authorization: Bearer <token>
```

### Campaign Management (Admin Only)

```bash
# List campaigns
GET /api/v1/email/campaigns?status=scheduled

# Create campaign
POST /api/v1/email/campaigns
{
  "name": "Feature Launch Campaign",
  "template_name": "feature_announcement",
  "category": "marketing",
  "target_segment": "all_users",
  "scheduled_at": "2025-11-01T09:00:00Z"
}

# Get campaign details
GET /api/v1/email/campaigns/{campaign_id}
```

## Email Templates

### Template Structure

Templates are stored in `templates/email/` directory:

```
templates/email/
├── README.md
├── welcome_en.html
├── welcome_en_subject.txt
├── password_reset_en.html
├── password_reset_en_subject.txt
├── match_found_en.html
└── ...
```

### Template Variables

All templates have access to base variables:
- `app_name`: "SoundHash"
- `app_url`: Application base URL
- `support_email`: Support email address
- `unsubscribe_url`: Unsubscribe URL
- `current_year`: Current year

Template-specific variables are passed via context.

### Creating New Templates

1. Create HTML template: `template_name_en.html`
2. Create subject: `template_name_en_subject.txt`
3. Optionally create plain text: `template_name_en.txt`
4. Use template in code:

```python
from src.email.service import email_service

await email_service.send_template_email(
    recipient_email="user@example.com",
    template_name="your_template",
    context={"custom_var": "value"},
    user_id=1
)
```

### Multi-language Support

Create language-specific templates:
- `welcome_en.html` (English)
- `welcome_es.html` (Spanish)
- `welcome_fr.html` (French)

System automatically uses user's preferred language or falls back to English.

## Marketing Automation

### Onboarding Workflow

Automatic email sequence for new users:
- Day 0: Welcome (transactional)
- Day 1: Getting started guide
- Day 3: Tips & tricks
- Day 7: Feature highlights

```python
from src.email.automation import marketing_automation

# Run for specific user
await marketing_automation.run_onboarding_workflow(user_id=1)
```

### Re-engagement Campaign

Automatically re-engage inactive users (30+ days):

```python
# Find and email inactive users
sent_count = await marketing_automation.run_re_engagement_workflow()
```

### Tips Series

Send educational content series:

```python
tip_content = {
    "title": "Improving Match Accuracy",
    "content": "Use longer audio segments for better matches...",
    "example": "Minimum 5 seconds recommended"
}

sent_count = await marketing_automation.run_tips_series(
    tip_number=1,
    tip_content=tip_content
)
```

## Analytics & Tracking

### Tracking Pixel (Opens)

Automatically embedded in HTML emails:
```html
<img src="https://api.soundhash.io/api/v1/email/tracking/open/123" 
     width="1" height="1" />
```

### Click Tracking

Links are automatically wrapped:
```html
<a href="https://api.soundhash.io/api/v1/email/tracking/click/123?redirect_url=...">
  Click here
</a>
```

### Analytics Dashboard

View email performance:
- Open rates by template
- Click-through rates
- Campaign performance
- User engagement metrics

## A/B Testing

Create template variants:

```python
from src.database.models import EmailTemplate

# Create variant A
template_a = EmailTemplate(
    name="feature_announcement",
    variant="A",
    subject="New Feature: {{ feature_name }}",
    html_body="...",
    category="marketing"
)

# Create variant B
template_b = EmailTemplate(
    name="feature_announcement",
    variant="B",
    subject="Exciting Update: {{ feature_name }}",
    html_body="...",
    category="marketing"
)
```

Campaign will automatically split traffic based on `ab_test_split_percentage`.

## Database Schema

### Email Preferences

Stores user email preferences per user.

### Email Templates

Stores email templates with variants for A/B testing.

### Email Logs

Tracks all sent emails with delivery status and engagement metrics.

### Email Campaigns

Manages marketing campaigns with scheduling and analytics.

## Security & Compliance

- **Unsubscribe**: Required unsubscribe link in all marketing emails
- **Preferences**: Users control what emails they receive
- **GDPR Compliant**: User data handling and deletion
- **Rate Limiting**: Prevents email spam
- **Authentication**: Secure API endpoints
- **Encryption**: All email communication over TLS

## Monitoring & Debugging

### Check Email Service Status

```python
from src.email.service import email_service

print(f"Email enabled: {email_service.enabled}")
print(f"Provider: {email_service.provider}")
```

### View Recent Logs

```bash
# API endpoint
GET /api/v1/email/logs?limit=100

# Database query
SELECT * FROM email_logs 
WHERE created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;
```

### Test Email Sending

```python
from src.email.service import email_service

# Send test email
result = await email_service.send_email(
    recipient_email="test@example.com",
    subject="Test Email",
    html_body="<p>This is a test</p>",
    category="admin"
)

print(f"Success: {result}")
```

## Troubleshooting

### Emails Not Sending

1. Check `EMAIL_ENABLED=true` in configuration
2. Verify provider API keys are correct
3. Check email logs for errors
4. Verify recipient hasn't unsubscribed
5. Check provider dashboard for issues

### Tracking Not Working

1. Ensure `EMAIL_TRACK_OPENS=true`
2. Check tracking URLs are accessible
3. Verify email logs are being updated
4. Test with non-image-blocking email clients

### Templates Not Rendering

1. Verify template files exist
2. Check template syntax (Jinja2)
3. Ensure all required variables are provided
4. Check language fallback (en)

## Best Practices

1. **Always provide plain text alternative** for HTML emails
2. **Test templates** across multiple email clients
3. **Monitor bounce rates** and clean email lists
4. **Respect user preferences** - never override
5. **Use transactional emails sparingly** - only for critical notifications
6. **A/B test** marketing emails for better engagement
7. **Segment users** for targeted campaigns
8. **Track and analyze** email performance metrics
9. **Keep emails mobile-friendly** - responsive design
10. **Include clear call-to-action** in marketing emails

## Migration

Run database migration to create email tables:

```bash
alembic upgrade head
```

This creates:
- `email_preferences`
- `email_templates`
- `email_logs`
- `email_campaigns`

## Contributing

When adding new email types:

1. Create template files
2. Add helper function in `src/email/transactional.py`
3. Update email preferences model if needed
4. Add tests
5. Update documentation

## Support

For issues or questions:
- Email: support@soundhash.io
- Documentation: https://docs.soundhash.io/email
- GitHub Issues: https://github.com/subculture-collective/soundhash/issues
