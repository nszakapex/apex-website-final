# The Apex Marketing Group Website

Static website for The Apex Marketing Group, a content-driven marketing agency for local service businesses.

## Main Files

- `index.html` - Home page and contact form.
- `privacy-policy.html` - Public Privacy Policy for website, CRM, and SMS review.
- `terms-and-conditions.html` - Public Terms & Conditions, including SMS Terms.

## Local Preview

Because this is a static site, you can preview it with any local static server:

```bash
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Netlify Deployment

Deploy the repository as a static site:

- Build command: leave blank
- Publish directory: repository root
- Entry page: `index.html`

The site should load from the root path after deployment.

## Twilio A2P 10DLC Notes

Keep these pages publicly accessible for Twilio A2P 10DLC campaign review and SMS compliance:

- `https://theapexmarketinggroup.com/privacy-policy.html`
- `https://theapexmarketinggroup.com/terms-and-conditions.html`

Use the live Privacy Policy and Terms & Conditions URLs when registering SMS campaigns.

## Security

Do not commit secrets, API keys, CRM tokens, Twilio credentials, webhook secrets, or private customer data to this repository.
