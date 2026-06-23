# MarketMind API Keys & Credentials Setup

This document explains how Aidan retrieves credentials for future MarketMind
integrations. It is a **setup guide only**. No real keys appear here, and no
integration in the current codebase calls any external service.

## Core principles

MarketMind credential handling is, in order:

1. **Sandbox-first** — use test/sandbox keys before touching production.
2. **Read-only-first** — request read scopes before any write scope.
3. **Least-privilege-first** — request only the scopes a slice actually needs.
4. **Approval-gated** — any key that can move money, publish, message, refund,
   order inventory, or change account settings is high/critical risk and stays
   behind approval gates (see `APPROVAL_POLICY.md`) before use.

## Hard rules (never break these)

- **Never** commit real credentials. `.env` is gitignored; only `.env.example`
  (placeholder names) is tracked.
- **Never** paste real keys into chat, issues, PRs, or logs.
- **Never** store secrets in source code.
- Real credentials live in: a local `.env`, GitHub Actions secrets, a cloud
  secret manager, or the hosting provider's secret store — never the repo.
- Separate **sandbox vs production** and **read-only vs draft-write vs
  live-write** credentials.
- Any key-check/validation command must confirm presence/format and **mask the
  value** (e.g. print `sk_live_****…last4`), never the secret itself.
- Tests use **fake/example keys only**.

## Risk classification of credentials

| Capability the key enables | Risk | Gate before use |
|---|---|---|
| Read-only analytics / catalog reads | Low | Logged, auto-allowed |
| Draft creation (unpublished product/page) | Medium | Draft-only, no external send |
| Payments, refunds, publishing, ads, inventory orders, customer/supplier messaging, account changes | High/Critical | **Explicit approval required; blocked by default** |

---

## 1. Stripe

- Start in **sandbox/test mode**. Live keys are **not needed** until
  approval-gated payment actions exist.
- Prefer **restricted API keys** over the unrestricted secret key for any new
  integration — scope them to only the resources MarketMind reads.
- Payment Link creation stays **disabled** until explicitly approved.

Retrieve from the [Stripe Dashboard](https://docs.stripe.com/keys):
Developers → API keys (toggle **Test mode**); create a **Restricted key** and
grant only the needed permissions. Webhook secret: Developers → Webhooks.

Variables:
```
STRIPE_PUBLISHABLE_KEY
STRIPE_RESTRICTED_KEY
STRIPE_WEBHOOK_SECRET
```

## 2. Shopify

- Use a **development store** first.
- Admin API requires an **access token** and explicit **scopes**; request only
  what's needed and **start read-only** (`read_products`, `read_orders`).
- Product publishing, price changes, inventory changes, and order actions
  require approval gates.

Retrieve from the Shopify admin: Settings → Apps and sales channels → Develop
apps → create app → configure Admin API scopes → install → reveal the Admin API
access token. See the
[Admin API reference](https://shopify.dev/docs/api/admin-graphql/latest).

Variables:
```
SHOPIFY_STORE_DOMAIN
SHOPIFY_ADMIN_ACCESS_TOKEN
SHOPIFY_API_VERSION
```

## 3. eBay

- Use the **eBay Developer Program sandbox** first.
- eBay APIs use **OAuth access tokens and scopes**; sandbox and production have
  separate keysets.
- Listing creation and order actions require approval gates.

Retrieve from the [eBay Developer Program](https://developer.ebay.com/api-docs/static/oauth-tokens.html):
create an application keyset (Sandbox first), configure the OAuth redirect URI
(RuName), then run the OAuth flow to obtain tokens.

Variables:
```
EBAY_CLIENT_ID
EBAY_CLIENT_SECRET
EBAY_REDIRECT_URI
EBAY_ENVIRONMENT   # sandbox | production
```

## 4. Amazon SP-API

- Treat Amazon as **later-stage** — setup is the most complex.
- Requires developer/app registration and an authorization workflow; do **not**
  implement production Amazon actions in early slices.

Retrieve via [SP-API authorization docs](https://developer-docs.amazon.com/sp-api/docs/authorizing-selling-partner-api-applications):
register as a developer, create the SP-API app, complete the authorization
workflow to obtain a refresh token.

Variables:
```
AMAZON_SP_API_CLIENT_ID
AMAZON_SP_API_CLIENT_SECRET
AMAZON_SP_API_REFRESH_TOKEN
AMAZON_SP_API_REGION   # na | eu | fe
```

## 5. TikTok Shop / Meta / Google Ads / shipping providers

Placeholder sections only — do not wire these until the repo contains approved
requirements. **No ad spend, campaign launch, or budget change without approval
gates.** Start any analytics access as import/read-only.

Variables (read-only/import first):
```
META_ADS_ACCESS_TOKEN
TIKTOK_ADS_ACCESS_TOKEN
GOOGLE_ADS_DEVELOPER_TOKEN
```

## 5b. Gmail (supplier outreach drafts — approval-gated)

- **Off by default.** `contact_supplier` exports a local `.txt` draft until
  `MARKETMIND_GMAIL_ENABLED=true`.
- **Simulate first:** keep `MARKETMIND_GMAIL_DRY_RUN=true` (default) to exercise
  the approval + execute path without calling Google.
- **Live drafts** create an inbox draft via `users.drafts.create` — the operator
  still reviews and sends manually. Requires:
  - `MARKETMIND_GMAIL_DRY_RUN=false`
  - `MARKETMIND_ENABLE_LIVE_WRITES=true`
  - OAuth desktop/web app credentials with Gmail compose scope
- Check readiness without printing secrets:
  `python scripts/check_operator_readiness.py` (Gmail + commerce + preflight), or
  `python scripts/check_gmail_config.py` for Gmail only.

Variables:
```
MARKETMIND_GMAIL_ENABLED
MARKETMIND_GMAIL_DRY_RUN
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
GMAIL_OPERATOR_EMAIL
```

## 6. Secret handling checklist

```
[ ] .env is gitignored; only .env.example is committed
[ ] .env.example contains placeholder names only
[ ] No secret appears in source code
[ ] Logs mask secrets (print masked, never raw)
[ ] Tests use fake/example keys only
[ ] Key-check commands validate presence/format without printing values
[ ] Sandbox and production credentials are separate
[ ] Read-only, draft-write, and live-write credentials are separate
[ ] High/critical-risk keys remain behind approval gates (APPROVAL_POLICY.md)
```

## References

- Stripe keys: https://docs.stripe.com/keys
- Shopify Admin API: https://shopify.dev/docs/api/admin-graphql/latest
- eBay OAuth tokens: https://developer.ebay.com/api-docs/static/oauth-tokens.html
- Amazon SP-API authorization: https://developer-docs.amazon.com/sp-api/docs/authorizing-selling-partner-api-applications
