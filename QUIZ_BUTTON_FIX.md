# Start Quiz Button - Troubleshooting Guide

## ✅ What I Fixed

Added better error handling to the Start Quiz button:
1. **Console logging** - Shows "Start Quiz button clicked" in browser console
2. **Error display** - Shows red error box if the quiz fails to start
3. **Error messages** - Displays the actual error message
4. **Sign-in link** - If not logged in, provides a link to sign in page

## 🔍 Common Issues & Solutions

### Issue 1: Not Logged In ⚠️
**Symptom**: Button does nothing or shows "Failed to start quiz"  
**Cause**: The aptitude quiz requires authentication  
**Solution**: You must be logged in to take the quiz

**How to fix**:
1. Go to: http://localhost:3001/en/auth/signin
2. Sign in with your account
3. Return to: http://localhost:3001/en/aptitude
4. Click "Start Quiz 🚀"

### Issue 2: No Quiz Questions in Database
**Symptom**: Error says "NO_QUESTIONS_AVAILABLE"  
**Status**: ✅ **VERIFIED - 20 questions exist in database**

### Issue 3: API Not Running
**Symptom**: Network error or timeout  
**Solution**: Make sure backend is running

**Check backend**:
```powershell
# Terminal 1 - Backend should show:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Test backend:
```powershell
# Should return questions endpoint info
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/docs"
```

### Issue 4: Frontend Not Updated
**Symptom**: Old button still showing  
**Solution**: 
1. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear .next cache and restart:
```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

## 🧪 How to Test the Button

### 1. Open Browser Console
Press F12 (Windows) or Cmd+Option+I (Mac) to open Developer Tools

### 2. Go to the Quiz Page
http://localhost:3001/en/aptitude

### 3. Click "Start Quiz 🚀"
Watch the console for:
- ✅ "Start Quiz button clicked" - Button works!
- ✅ "Quiz started successfully: {data}" - API call succeeded!
- ❌ "Failed to start quiz: {error}" - See error details

### 4. Check for Errors
If button doesn't work, you'll see one of these:

#### Error: "Unauthorized" or 401
```
Failed to start quiz: Unauthorized
```
**Fix**: Sign in at http://localhost:3001/en/auth/signin

#### Error: "Network Error"
```
Failed to start quiz: Network Error
```
**Fix**: Check if backend is running on port 8000

#### Error: "NO_QUESTIONS_AVAILABLE"
```
Failed to start quiz: NO_QUESTIONS_AVAILABLE
```
**Fix**: Already fixed - 20 questions exist in database ✅

## 📋 Pre-Flight Checklist

Before testing, verify:

✅ **Backend running**: 
```powershell
# Should see: INFO:     Uvicorn running on http://0.0.0.0:8000
cd backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ **Frontend running**:
```powershell
# Should see: ▲ Next.js ready on http://localhost:3001
cd frontend
npm run dev
```

✅ **Database has questions**:
```powershell
# Should show: Found 20 quiz questions
cd backend
.venv\Scripts\Activate.ps1
python check_quiz_questions.py
```

✅ **You're signed in**:
- Go to http://localhost:3001/en/auth/signin
- Create account or sign in
- Verify email if needed (check backend logs for verification link)

## 🎯 What the Button Should Do

When working correctly:

1. **Click "Start Quiz 🚀"**
2. Button text changes to "Loading…"
3. Button becomes disabled (grayed out)
4. API call to `/api/v1/aptitude/questions`
5. Questions load from backend
6. Page shows first question with 5-point scale
7. Progress bar shows "Question 1 of 20"

## 🐛 Debugging Commands

### Check if API is accessible:
```powershell
# Should return 401 (Unauthorized) or session data
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/aptitude/questions"
```

### Check backend logs:
Look at the backend terminal (Terminal 1) for:
```
INFO:     POST /api/v1/auth/signin 200 OK
INFO:     GET /api/v1/aptitude/questions 200 OK
```

### Check frontend logs:
Look at the frontend terminal (Terminal 4) for:
```
GET /en/aptitude 200 in 500ms
```

### Check browser console:
Press F12, go to Console tab, look for:
```
Start Quiz button clicked
Quiz started successfully: {session_id: "...", questions: [...]}
```

## ✅ Updated Files

1. **`frontend/src/app/[locale]/(workspace)/aptitude/page.tsx`**
   - Added console.log when button is clicked
   - Added onError handler with alert
   - Shows error message in red box below button
   - Added "Go to sign in" link if error occurs

## 🔧 Quick Fix Script

If nothing works, run this to reset everything:

```powershell
# Stop frontend
# Ctrl+C in the frontend terminal

# Clean and restart frontend
cd frontend
Remove-Item -Recurse -Force .next
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
npm run dev

# In browser:
# 1. Clear cache: Ctrl+Shift+Delete, check "Cached images and files"
# 2. Hard refresh: Ctrl+Shift+R
# 3. Go to http://localhost:3001/en/auth/signin
# 4. Sign in
# 5. Go to http://localhost:3001/en/aptitude
# 6. Click "Start Quiz 🚀"
```

## 💡 Most Likely Issue

**You need to be signed in!** 

The `/api/v1/aptitude/questions` endpoint requires authentication (see `token=Depends(get_token_payload)` in the router).

**Quick test**:
1. Open browser to http://localhost:3001/en/auth/signin
2. Sign in with email and password
3. Go to http://localhost:3001/en/aptitude
4. Click "Start Quiz 🚀"
5. Should load questions immediately!

## 📞 Still Not Working?

If the button still doesn't work after signing in:

1. Open browser console (F12)
2. Click the button
3. Take a screenshot of:
   - The console errors
   - The Network tab (filter by "aptitude")
   - The error message on the page
4. Check backend terminal for errors

The error message will tell us exactly what's wrong!
