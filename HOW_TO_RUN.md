# 🚀 FAMPATH - Quick Start Guide

## ⚡ FASTEST WAY TO START (One Click!)

1. **Double-click this file:**
   ```
   START_ALL_SERVERS.bat
   ```

2. **Wait 15 seconds** for both servers to start

3. **Open your browser** to:
   ```
   http://localhost:3000
   ```

That''s it! ✅

---

## 📊 Check if Servers Are Running

**Double-click:**
```
CHECK_STATUS.bat
```

It will tell you if backend and frontend are running.

---

## 🛑 How to Stop

Close both Command Prompt windows titled:
- "FamPath Backend"
- "FamPath Frontend"

Or press `CTRL+C` in each window.

---

## 🔧 Manual Start (If Needed)

### Backend Only:
```
cd backend
START_BACKEND.bat
```

### Frontend Only:
```
cd frontend
START_FRONTEND.bat
```

---

## ✅ Expected Output

### Backend Window Should Show:
```
INFO:     Application startup complete.
```

### Frontend Window Should Show:
```
✓ Ready in 2.5s
```

---

## 🆘 Troubleshooting

### Problem: Port already in use

**Check what''s running:**
```
CHECK_STATUS.bat
```

**Kill port 8000:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <number> /F
```

**Kill port 3000:**
```cmd
netstat -ano | findstr :3000
taskkill /PID <number> /F
```

---

## 📁 Project Structure

```
rajitha/
├── START_ALL_SERVERS.bat  ← ONE-CLICK START
├── CHECK_STATUS.bat       ← Check if running
├── backend/
│   └── START_BACKEND.bat
└── frontend/
    └── START_FRONTEND.bat
```

---

## 🌐 Important URLs

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Main Application |
| http://localhost:3000/en/sign-in | Sign In Page |
| http://localhost:3000/en/sign-up | Register Page |
| http://localhost:8000/docs | API Documentation |
| http://localhost:8000/health | Health Check |

---

## 🎯 First Time Setup

1. Run `START_ALL_SERVERS.bat`
2. Wait for both servers to start
3. Go to http://localhost:3000/en/sign-up
4. Create an account
5. Check console for verification (dev mode - no email needed)

---

**Need Help?** Check the console output in both server windows!
