# Deployment Guide — AI HR System

## Overview
- **Backend + Celery + Redis + PostgreSQL** → Railway (free $5/month credit)
- **Next.js Frontend** → Vercel (free forever)
- **Media files** → Cloudinary (25GB free)

---

## Step 1 — Accounts to create first (all free)

1. [railway.app](https://railway.app) — sign up with GitHub
2. [vercel.com](https://vercel.com) — sign up with GitHub
3. [cloudinary.com](https://cloudinary.com) — sign up, then go to Dashboard and note your **Cloud Name**, **API Key**, **API Secret**
4. Push your code to a GitHub repository if you haven't already

---

## Step 2 — Deploy the Backend on Railway

### 2a. Create a new Railway project
1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"** → select your backend repo
3. Railway will detect the `railway.toml` and start building

### 2b. Add PostgreSQL
1. In your Railway project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically injects `DATABASE_URL` into your backend service — nothing else needed

### 2c. Add Redis
1. Click **"+ New"** → **"Database"** → **"Redis"**
2. Railway automatically injects `REDIS_URL` — nothing else needed

### 2d. Set environment variables
1. Click your backend service → **"Variables"** tab
2. Add all variables from `RAILWAY_ENV_VARS.txt` (fill in the real values)
3. For `SECRET_KEY`, generate one here: https://djecrety.ir/

### 2e. Get your backend URL
1. Click your backend service → **"Settings"** → **"Domains"**
2. Click **"Generate Domain"** — you'll get a URL like `https://ai-hr-system.up.railway.app`
3. Copy this URL — you'll need it for Vercel and for `ALLOWED_HOSTS`

---

## Step 3 — Deploy the Celery Worker on Railway

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"** → same repo
2. Go to **Settings** → **"Start Command"** → set it to:
   ```
   celery -A ai_hr_system worker --loglevel=info --concurrency=2
   ```
3. Go to **Variables** → click **"Share variables from"** → select your backend service
   (This copies all env vars automatically — no duplication needed)

---

## Step 4 — Deploy the Frontend on Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your **frontend** GitHub repo
3. Vercel auto-detects Next.js — click **Deploy**
4. After first deploy, go to **Settings** → **Environment Variables** and add:
   ```
   NEXT_PUBLIC_API_URL = https://your-backend.up.railway.app/api
   ```
   (use the Railway URL from Step 2e — with `/api` at the end)
5. Go to **Deployments** → click **"Redeploy"** to pick up the env var

---

## Step 5 — Update Backend CORS

Now that you have the Vercel URL (e.g. `https://ai-hr-system.vercel.app`):

1. Go to Railway → your backend service → Variables
2. Update `CORS_ALLOWED_ORIGINS` to your Vercel URL (no trailing slash)
3. Update `ALLOWED_HOSTS` to your Railway domain
4. Railway auto-redeploys on variable changes

---

## Step 6 — Verify Everything Works

Run these checks in order:

```bash
# 1. Backend health
curl https://your-backend.up.railway.app/api/health/
# Should return: {"status": "ok", "database": "ok"}

# 2. Try registering an HR user via the frontend
# Go to your Vercel URL → Sign Up as HR

# 3. Check Celery is running in Railway logs
# Railway → Celery service → Logs
# Should show: "celery@... ready."
```

---

## Troubleshooting

**Build fails on Railway:**
- Check that `requirements.txt` is in the root of your repo
- View build logs in Railway → your service → **Deployments** tab

**500 error after deploy:**
- Check Railway logs for the actual error
- Most common cause: missing environment variable

**Celery tasks not running:**
- Verify `REDIS_URL` is set in the worker service variables
- Check worker logs for connection errors

**Media files not uploading:**
- Verify all three Cloudinary vars are set correctly
- Test at cloudinary.com dashboard that the credentials work

**CORS errors in browser:**
- Double-check `CORS_ALLOWED_ORIGINS` matches your Vercel URL exactly (no trailing slash, with `https://`)

---

## Free Tier Limits to Know

| Service | Limit | Notes |
|---|---|---|
| Railway | $5 credit/month | Enough for ~500 hrs of light usage |
| Vercel | Unlimited hobby | No meaningful limits for a demo |
| Cloudinary | 25GB storage, 25GB bandwidth/month | More than enough for a demo |
| Railway PostgreSQL | 1GB storage | Fine for demo data |
| Railway Redis | 25MB | Fine for Celery task queue |
