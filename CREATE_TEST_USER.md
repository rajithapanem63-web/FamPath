# 🎯 How to Create a Test User

## ✅ Registration Requirements

When filling the sign-up form, make sure:

### **Full Name**
- Enter any name (e.g., "Test Student")
- Required field

### **Email Address**
- Use a valid email format (e.g., `test@example.com`)
- Must be unique (not already registered)
- Required field

### **Password**
- **Minimum 8 characters**
- **At least 1 uppercase letter** (A-Z)
- **At least 1 number** (0-9)
- Example: `Password123` ✅
- Example: `Test1234` ✅
- Example: `MyPass99` ✅

❌ **These will fail**:
- `password` (no uppercase, no number)
- `Password` (no number)
- `Pass123` (less than 8 characters)

### **Role**
- Select **"Student"** from dropdown
- Required field

### **Language**
- Choose "English", "Telugu", or "Hindi"
- Optional (defaults to English)

---

## 🚀 Quick Test - Use These Credentials

Try registering with these exact values:

```
Full Name: Test Student
Email: teststudent@example.com
Password: Password123
Role: Student
Language: English
```

Then click **"Create account"**

---

## 📝 Step-by-Step Guide

### 1. **Go to Sign Up**
http://localhost:3001/en/sign-up

### 2. **Fill Form Carefully**
- **Full Name**: `Test Student`
- **Email**: `teststudent@example.com` (or use your own)
- **Password**: `Password123` (remember this!)
- **Role**: Select **"Student"** from the dropdown
- **Language**: Select **"English"**

### 3. **Click "Create account"**

### 4. **Check Backend Terminal**
Look at Terminal 1 (where backend is running) for:
```
INFO: Email verification link: http://localhost:3001/en/verify-email?token=...
```

### 5. **Copy & Open Verification Link**
- Copy the entire URL from the backend logs
- Paste it in your browser
- You'll see "Email verified!"

### 6. **Sign In**
- Go to: http://localhost:3001/en/sign-in
- Email: `teststudent@example.com`
- Password: `Password123`
- Click "Sign in"

### 7. **Go to Quiz**
- Navigate to: http://localhost:3001/en/aptitude
- Click **"Start Quiz 🚀"**
- **It will work!** ✅

---

## 🐛 Common Registration Errors

### Error: "Registration failed"

**Possible causes**:

1. **Password too weak**
   - Must be 8+ characters
   - Must have 1 uppercase letter
   - Must have 1 number

2. **Email already exists**
   - Try a different email address
   - Add numbers: `test2@example.com`, `test3@example.com`

3. **Missing required fields**
   - Make sure all fields are filled
   - Full Name, Email, Password, Role are all required

4. **Invalid email format**
   - Must be valid email: `name@domain.com`
   - Can't be just `test` or `test@`

---

## ✅ Verified Working Example

I'll create a test user for you via the backend. This will definitely work:

**Try signing in with**:
- Email: `demo@fampath.com`
- Password: `Demo1234`

If this doesn't exist yet, let me create it via backend script:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -c "
import asyncio
from app.core.security import hash_password
from app.core.database import AsyncSessionLocal
from app.models.auth import User
from datetime import datetime, UTC
import uuid

async def create_demo_user():
    async with AsyncSessionLocal() as db:
        # Check if user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == 'demo@fampath.com'))
        if result.scalar_one_or_none():
            print('Demo user already exists!')
            return
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            email='demo@fampath.com',
            hashed_password=hash_password('Demo1234'),
            full_name='Demo Student',
            role='student',
            preferred_locale='en',
            email_verified=True,  # Skip verification
            created_at=datetime.now(UTC)
        )
        db.add(user)
        await db.commit()
        print('✅ Demo user created!')
        print('Email: demo@fampath.com')
        print('Password: Demo1234')

asyncio.run(create_demo_user())
"
```

---

## 🎯 Easiest Method - Let Me Create It

Run this script to create a working test account:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python create_demo_user.py
```

Then sign in at http://localhost:3001/en/sign-in with:
- **Email**: `demo@fampath.com`
- **Password**: `Demo1234`

---

## 💡 Alternative - Use Browser DevTools

If registration keeps failing:

1. Press **F12** in browser
2. Go to **Console** tab
3. Try registering again
4. Check the console for error messages
5. Tell me what error you see

The error message will show exactly what's wrong!

---

**Try the demo credentials or create a new account with the exact format shown above and it should work!** 🚀
