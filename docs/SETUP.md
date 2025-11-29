# ReeferShield – Setup Guide

## 1. Create Supabase project

1. Go to Supabase and create a new project.
2. Copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL` and `BACKEND_SUPABASE_URL`
   - anon public key → `SUPABASE_ANON_KEY`
   - service role key → `SUPABASE_SERVICE_ROLE_KEY` and `BACKEND_SUPABASE_SERVICE_ROLE_KEY`
3. Open SQL editor and run `supabase_schema.sql` from this repo.

## 2. Stripe

1. Create two Products:
   - `ReeferShield Base` – recurring $49/month
   - `ReeferShield Truck` – recurring $29/month per truck
2. For each product, create a Price with a 14‑day trial.
3. Copy the Price IDs into:
   - `NEXT_PUBLIC_STRIPE_PRICE_ID_BASE`
   - `NEXT_PUBLIC_STRIPE_PRICE_ID_PER_TRUCK`
4. In Stripe, create a webhook endpoint pointing to your **frontend** deployment:
   - `https://YOUR_FRONTEND_DOMAIN/api/stripe/webhook`
   - Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `checkout.session.completed`.
5. Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`.
6. Set `STRIPE_SECRET_KEY` to your secret API key.
7. (Optional) Configure a Billing Portal and put the URL in `STRIPE_BILLING_PORTAL_URL`.

## 3. Telematics (Samsara, Motive, Geotab)

Create developer applications for each provider:

- **Samsara**
  - OAuth redirect URL: `https://YOUR_BACKEND_DOMAIN/auth/samsara/callback`
- **Motive**
  - OAuth redirect URL: `https://YOUR_BACKEND_DOMAIN/auth/motive/callback`
- **Geotab**
  - OAuth redirect URL: `https://YOUR_BACKEND_DOMAIN/auth/geotab/callback`

Fill in:

- `SAMSARA_CLIENT_ID`, `SAMSARA_CLIENT_SECRET`, `SAMSARA_OAUTH_REDIRECT_URI`
- `MOTIVE_CLIENT_ID`, `MOTIVE_CLIENT_SECRET`, `MOTIVE_OAUTH_REDIRECT_URI`
- `GEOTAB_CLIENT_ID`, `GEOTAB_CLIENT_SECRET`, `GEOTAB_OAUTH_REDIRECT_URI`

In each provider’s console, add webhook / data forwarding URLs that point to:

- `https://YOUR_BACKEND_DOMAIN/webhooks/samsara`
- `https://YOUR_BACKEND_DOMAIN/webhooks/motive`
- `https://YOUR_BACKEND_DOMAIN/webhooks/geotab`

## 4. IPFS (web3.storage)

1. Sign up at web3.storage or nft.storage.
2. Create an API token and put it in `WEB3_STORAGE_TOKEN`.

## 5. Polygon + Alchemy/Infura

1. Create a Polygon mainnet project in Alchemy or Infura.
2. Copy the HTTPS RPC URL into `POLYGON_RPC_URL_PRIMARY`.
3. (Optional) Add another provider to `POLYGON_RPC_URL_FALLBACK`.
4. Create a wallet for ReeferShield and fund it with a small amount of MATIC.
5. Set `POLYGON_PRIVATE_KEY` to that wallet’s private key (never commit this file).
6. Deploy a simple contract that exposes a function like:

   `function recordCertificate(bytes32 cidHash, string calldata cid, uint256 timestamp) external;`

7. Put the deployed contract address into `POLYGON_CERT_CONTRACT_ADDRESS`.

## 6. Email (Resend)

1. Sign up at Resend.
2. Create an API key → `RESEND_API_KEY`.
3. Add and verify your domain, then pick a from email → `FROM_EMAIL`.

## 7. FastAPI backend (Railway / Fly.io)

### Railway

1. Create a new Railway project from this repo.
2. Set root directory to `backend`.
3. Add environment variables from `.env.example`.
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port 8000`.

### Fly.io

1. Install `flyctl`.
2. `cd backend`
3. `fly launch` (accept defaults, set app name).
4. Deploy with `fly deploy`.

## 8. Next.js frontend (Vercel)

### One‑click deploy

Create a GitHub repo with this code, then in `README.md` you already have:

```md
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_GITHUB_USERNAME/reefershield&root-directory=web)
```

Clicking that from GitHub will preconfigure Vercel.

### Manual

1. Create new Vercel project, import from GitHub.
2. Set root directory to `web`.
3. Framework: Next.js.
4. Add environment variables as in `.env.example`.
5. Deploy.

## 9. Daily digest

Configure a cron job (Railway cron, Fly.io scheduled task, or an external scheduler) to hit:

- `GET https://YOUR_BACKEND_DOMAIN/cron/daily-digest`

once per day.

## 10. Local development

```bash
# Web
cd web
npm install
npm run dev

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
