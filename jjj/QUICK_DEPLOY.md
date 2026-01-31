# 🚀 Quick Deployment Reference

## Fastest Way to Deploy (5 minutes)

### 1️⃣ Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/your-repo-name.git
git push -u origin main
```

### 2️⃣ Deploy on Render
1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click "New +" → "Web Service"
3. Select your repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment Variables**:
     ```
     WEATHER_API_KEY = your_key_from_weatherapi.com
     OPENAI_API_KEY = your_openai_key (optional)
     FLASK_ENV = production
     ```
5. Click "Create Web Service"
6. Wait 5-10 minutes → Your site is live! 🎉

---

## 🔑 Get API Keys

**Weather API (Required - FREE):**
- https://www.weatherapi.com/signup.aspx
- Free tier: 1M calls/month

**OpenAI API (Optional - Paid):**
- https://platform.openai.com/api-keys
- Only needed for AI-powered responses

---

## 🌐 Alternative Hosting Options

| Platform | Free Tier | Best For | Setup Time |
|----------|-----------|----------|------------|
| **Render** | ✅ Yes | Easy deployment | 5 mins |
| **Railway** | ✅ Yes | Great DX | 5 mins |
| **PythonAnywhere** | ✅ Yes | Python apps | 10 mins |
| **Vercel** | ✅ Yes | Serverless | 5 mins |
| **Heroku** | ❌ No longer free | Enterprise | - |

---

## ✅ Files Created for Deployment

- ✅ `Procfile` - Tells hosting how to run your app
- ✅ `runtime.txt` - Specifies Python version
- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `.env.example` - Template for environment variables
- ✅ `DEPLOYMENT_GUIDE.md` - Full instructions
- ✅ `deploy_setup.ps1` - Setup helper script

---

## 🐛 Common Issues

**"Application Error"**
- Check logs in deployment platform
- Verify environment variables are set
- Ensure PORT is configured

**"API Key Invalid"**
- Double-check API key from weatherapi.com
- No spaces before/after the key
- Key must be active

**"Site is sleeping"**
- Free tier apps sleep after 15 min inactivity
- First request wakes it up (~30 seconds)
- Use UptimeRobot to keep it awake

---

## 📞 Support

- **Full Guide**: See `DEPLOYMENT_GUIDE.md`
- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app

---

## 🎯 Quick Test After Deployment

Visit these URLs (replace with your domain):
```
https://your-app.onrender.com/
https://your-app.onrender.com/api/stats
https://your-app.onrender.com/api/weather?location=London
```

---

**Total Time: ~10 minutes from start to live website!** 🚀
