# Supabase Setup Guide for CashPilot AI

## Step 1: Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up / Login
3. Click **"New Project"**
4. Fill in:
   - **Project Name**: CashPilot-AI
   - **Database Password**: (generate strong password)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Free (sufficient for development)
5. Click **"Create new project"**
6. Wait 2-3 minutes for setup

---

## Step 2: Get Your Credentials

Once project is ready:

1. Go to **Project Settings** (gear icon on left sidebar)
2. Click **API** tab
3. Copy these values:

```
Project URL: https://xxxxx.supabase.co
anon/public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... (keep secret!)
```

4. Add to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 3: Create Database Schema

1. In Supabase dashboard, click **SQL Editor** (left sidebar)
2. Click **"New query"**
3. Copy and paste the SQL from `supabase/schema.sql`
4. Click **"Run"**
5. Verify tables created in **Table Editor**

---

## Step 4: Enable Realtime

1. Go to **Database** → **Replication**
2. Enable replication for these tables:
   - `conversations`
   - `messages`
3. Click **"Save"**

---

## Step 5: Configure Authentication

1. Go to **Authentication** → **Providers**
2. Enable **Email** provider
3. (Optional) Enable social providers:
   - Google OAuth
   - GitHub OAuth
4. Go to **Authentication** → **Policies**
5. Policies are already set up in schema.sql

---

## Step 6: Test Connection

Run this test:

```bash
cd C:\CashPilot_AI
.venv\Scripts\activate
python test_supabase.py
```

You should see:
```
✓ Connected to Supabase successfully!
✓ Database schema verified
```

---

## Your Project is Ready! 🎉

Now run the application:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Visit: http://localhost:8000/docs
