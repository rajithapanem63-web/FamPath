# Deploy FamPath to Render

## Step-by-Step Deployment Guide

### Prerequisites
- GitHub account (already done ✅)
- Render account (create at https://render.com)
- Your GitHub repository: https://github.com/rajithapanem63-web/FamPath

---

## Part 1: Push Updated Files to GitHub

```powershell
cd c:\Users\jakat\OneDrive\Desktop\rajitha
git add render.yaml backend/requirements.txt DEPLOY_TO_RENDER.md
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## Part 2: Deploy on Render (Web Dashboard)

### Option A: One-Click Deploy (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign up/Login with GitHub

2. **Connect Your Repository**
   - Click **"New +"** → **"Blueprint"**
   - Connect your GitHub account
   - Select repository: `rajithapanem63-web/FamPath`
   - Click **"Connect"**

3. **Render will automatically:**
   - Read `render.yaml`
   - Create PostgreSQL database
   - Create backend service
   - Create frontend service
   - Set up environment variables

4. **Wait for deployment** (5-10 minutes)
   - Backend will be at: `https://fampath-backend.onrender.com`
   - Frontend will be at: `https://fampath-frontend.onrender.com`

---

### Option B: Manual Deploy (Alternative)

If you prefer manual setup:

#### 1. Create Database
- Click **"New +"** → **"PostgreSQL"**
- Name: `fampath-db`
- Database: `fampath`
- User: `fampath_user`
- Plan: **Free**
- Click **"Create Database"**
- Copy the **Internal Database URL** (starts with `postgresql://`)

#### 2. Create Backend Service
- Click **"New +"** → **"Web Service"**
- Connect repository: `rajithapanem63-web/FamPath`
- Name: `fampath-backend`
- Region: **Oregon (US West)**
- Branch: `main`
- Root Directory: `backend`
- Runtime: **Python 3**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Plan: **Free**

**Environment Variables:**
```
APP_ENV=production
APP_VERSION=0.1.0
DATABASE_URL=<paste Internal Database URL here>
SECRET_KEY=<generate random 64 char string>
CORS_ORIGINS=https://fampath-frontend.onrender.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_EMAIL=noreply@fampath.dev
SMTP_FROM_NAME=FamPath
```

Click **"Create Web Service"**

#### 3. Create Frontend Service
- Click **"New +"** → **"Web Service"**
- Connect repository: `rajithapanem63-web/FamPath`
- Name: `fampath-frontend`
- Region: **Oregon (US West)**
- Branch: `main`
- Root Directory: `frontend`
- Runtime: **Node**
- Build Command: `npm install && npm run build`
- Start Command: `npm start`
- Plan: **Free**

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://fampath-backend.onrender.com
NODE_ENV=production
```

Click **"Create Web Service"**

---

## Part 3: Update CORS After Deployment

Once frontend is deployed, update backend CORS:

1. Go to backend service on Render
2. Click **"Environment"**
3. Update `CORS_ORIGINS` to actual frontend URL
4. Click **"Save Changes"**
5. Backend will auto-redeploy

---

## Part 4: Verify Deployment

### Test Backend
```
https://fampath-backend.onrender.com/health
```
Should return: `{"status":"ok","version":"0.1.0","env":"production"}`

### Test Frontend
```
https://fampath-frontend.onrender.com
```
Should show the FamPath homepage

---

## Important Notes

### Free Tier Limitations
- Services **spin down after 15 min** of inactivity
- First request after sleep takes **30-60 seconds**
- Database has **1GB storage limit**
- 750 hours/month free (enough for 1 service 24/7)

### Keep Services Active (Optional)
Use a service like **UptimeRobot** (free) to ping your app every 5 minutes:
- https://uptimerobot.com
- Add monitor: `https://fampath-backend.onrender.com/health`
- Monitor every 5 minutes

### Database Migrations
First deploy will auto-create tables. For future schema changes:
```bash
# Run migrations on Render Shell
cd backend
alembic upgrade head
```

### View Logs
- Go to service → **"Logs"** tab
- View real-time logs for debugging

---

## Troubleshooting

### Backend won't start
1. Check logs for errors
2. Verify DATABASE_URL is set
3. Ensure requirements.txt is correct

### Frontend can't reach backend
1. Check NEXT_PUBLIC_API_URL is correct
2. Verify backend CORS_ORIGINS includes frontend URL
3. Test backend /health endpoint directly

### Database connection error
1. Verify DATABASE_URL format
2. Check if database is running
3. Ensure backend uses asyncpg driver

---

## Cost Estimate

- **Free Tier:** $0/month
  - PostgreSQL: Free (1GB)
  - Backend: Free (750 hours)
  - Frontend: Free (750 hours)

- **Starter Tier:** $7-14/month
  - Always-on services
  - No sleep time
  - Better performance

---

## Your Deployed URLs (after deployment)

- **Frontend:** https://fampath-frontend.onrender.com
- **Backend API:** https://fampath-backend.onrender.com
- **API Docs:** https://fampath-backend.onrender.com/docs

---

## Next Steps After Deployment

1. ✅ Test registration and login
2. ✅ Create a demo account
3. ✅ Test all features (quiz, prediction, cost calculator)
4. ✅ Share the frontend URL!

**Good luck with your deployment!** 🚀
