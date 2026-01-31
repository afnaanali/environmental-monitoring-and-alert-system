# 🚀 Deployment Guide - Environmental Monitoring System

This guide will help you deploy your Environmental Monitoring & Alert System to the web using **Render** (free tier available).

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Option 1: Deploy to Render (Recommended)](#option-1-deploy-to-render-recommended)
3. [Option 2: Deploy to Railway](#option-2-deploy-to-railway)
4. [Option 3: Deploy to PythonAnywhere](#option-3-deploy-to-pythonanywhere)
5. [Environment Variables](#environment-variables)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

Before deploying, ensure you have:
- ✅ GitHub account (free)
- ✅ Your Weather API key from [WeatherAPI.com](https://www.weatherapi.com/)
- ✅ OpenAI API key (optional, for AI features)
- ✅ All project files ready

---

## 🌐 Option 1: Deploy to Render (Recommended)

Render offers free hosting for web applications with automatic deployments from GitHub.

### Step 1: Push Code to GitHub

1. **Create a new GitHub repository:**
   - Go to [GitHub](https://github.com) and sign in
   - Click "New repository"
   - Name it: `environmental-monitoring-system`
   - Keep it Public (required for free tier)
   - Click "Create repository"

2. **Push your code to GitHub:**

   Open PowerShell in your project folder and run:

   ```powershell
   # Initialize git repository (if not already done)
   git init
   
   # Add all files
   git add .
   
   # Create first commit
   git commit -m "Initial commit - Environmental Monitoring System"
   
   # Link to your GitHub repository (replace YOUR_USERNAME)
   git remote add origin https://github.com/YOUR_USERNAME/environmental-monitoring-system.git
   
   # Push to GitHub
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Sign up for Render:**
   - Go to [render.com](https://render.com)
   - Click "Get Started for Free"
   - Sign up with your GitHub account

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select `environmental-monitoring-system`

3. **Configure the Service:**
   ```
   Name: environmental-monitoring-system
   Region: Choose closest to you (e.g., Oregon, Frankfurt, Singapore)
   Branch: main
   Root Directory: (leave blank)
   Runtime: Python 3
   Build Command: pip install -r backend/requirements.txt
   Start Command: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Set Environment Variables:**
   Click "Advanced" → "Add Environment Variable":
   
   ```
   WEATHER_API_KEY = your_actual_api_key_here
   OPENAI_API_KEY = your_openai_key_here
   FLASK_ENV = production
   PORT = 10000
   ```

5. **Choose Free Tier:**
   - Select "Free" plan (0 USD/month)
   - Click "Create Web Service"

6. **Wait for Deployment:**
   - Render will automatically build and deploy your app
   - This takes 5-10 minutes on first deploy
   - Watch the logs for any errors

7. **Access Your Website:**
   - Once deployed, you'll get a URL like: `https://environmental-monitoring-system.onrender.com`
   - Open it in your browser!

---

## 🚆 Option 2: Deploy to Railway

Railway is another excellent free hosting option with great developer experience.

### Step 1: Push Code to GitHub
Follow the GitHub steps from Option 1 above.

### Step 2: Deploy on Railway

1. **Sign up for Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Login with GitHub"
   
2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `environmental-monitoring-system` repository

3. **Configure Environment Variables:**
   - Click on your service
   - Go to "Variables" tab
   - Add:
     ```
     WEATHER_API_KEY=your_key_here
     OPENAI_API_KEY=your_key_here
     FLASK_ENV=production
     PORT=5000
     ```

4. **Add Domain:**
   - Go to "Settings"
   - Under "Domains", click "Generate Domain"
   - Your site will be available at: `https://your-app.up.railway.app`

---

## 🐍 Option 3: Deploy to PythonAnywhere

PythonAnywhere is perfect for Python web applications and has a free tier.

### Steps:

1. **Sign up:**
   - Go to [pythonanywhere.com](https://www.pythonanywhere.com)
   - Create a free "Beginner" account

2. **Upload Code:**
   - Click "Files" tab
   - Upload all your project files or clone from GitHub

3. **Install Dependencies:**
   - Go to "Consoles" tab
   - Start a Bash console
   - Run:
     ```bash
     cd ~/environmental-monitoring-system
     pip install --user -r requirements.txt
     ```

4. **Configure Web App:**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Flask" and Python 3.10
   - Set source code directory: `/home/yourusername/environmental-monitoring-system`
   - Set WSGI file to point to `app.py`

5. **Set Environment Variables:**
   - In the Web tab, scroll to "Environment Variables"
   - Add your API keys

6. **Reload:**
   - Click the big green "Reload" button
   - Access your site at: `https://yourusername.pythonanywhere.com`

---

## 🔑 Environment Variables

Your application needs these environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `WEATHER_API_KEY` | API key from weatherapi.com | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | ⚠️ Optional |
| `FLASK_ENV` | Set to `production` | ✅ Yes |
| `PORT` | Port number (usually auto-set) | 🔄 Auto |

### Getting API Keys:

**Weather API Key (Free):**
1. Go to [weatherapi.com](https://www.weatherapi.com/)
2. Sign up for free account
3. Get your API key from dashboard
4. Free tier: 1 million calls/month

**OpenAI API Key (Optional):**
1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up and add billing
3. Create an API key
4. Note: This costs money based on usage

---

## ✅ Post-Deployment

After deployment, verify everything works:

### 1. Test API Endpoints:
```
GET https://your-app-url.com/api/stats
GET https://your-app-url.com/api/weather?location=London
GET https://your-app-url.com/api/locations/monitored
```

### 2. Check Frontend:
- Open the main page
- Search for a location (e.g., "London")
- Verify data loads correctly
- Check the map shows markers

### 3. Monitor Logs:
- Check deployment platform logs for errors
- Look for any API failures
- Verify automatic data collection is running

---

## 🐛 Troubleshooting

### Issue: "Application Error" or "Bad Gateway"

**Solution:**
- Check logs in your deployment platform
- Verify all environment variables are set
- Ensure `Procfile` and `requirements.txt` are correct
- Check if PORT is properly configured

### Issue: API requests failing

**Solution:**
- Verify `WEATHER_API_KEY` is valid
- Check API key quotas on weatherapi.com
- Test API manually: `https://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=London`

### Issue: Database errors

**Solution:**
- SQLite database is automatically created
- Ensure write permissions in deployment environment
- For persistent storage, consider upgrading to PostgreSQL

### Issue: Static files not loading

**Solution:**
- Verify HTML/CSS/JS files are in the correct directory
- Check Flask static folder configuration
- Clear browser cache

### Issue: Render free tier sleeps after inactivity

**Solution:**
- Free tier apps sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- Consider upgrading for always-on service
- Or use a service like [UptimeRobot](https://uptimerobot.com/) to ping your app every 5 minutes

---

## 🎨 Customization After Deployment

### Update Monitored Locations:
Edit `app.py`, find this line:
```python
MONITORED_LOCATIONS = ['London', 'Mumbai', 'New Delhi', 'New York', 'Tokyo']
```
Add your cities, commit, and push to GitHub for automatic redeployment.

### Change Data Collection Frequency:
Find the scheduler configuration in `app.py`:
```python
scheduler.add_job(fetch_and_store_data, 'interval', minutes=15)
```

### Disable AI Features:
Set in `app.py`:
```python
USE_AI_API = False
```

---

## 📊 Monitoring Your App

### Render Dashboard:
- View real-time logs
- Monitor CPU/Memory usage
- Check deployment status
- Set up health checks

### Custom Health Check Endpoint:
Your app includes `/api/stats` for monitoring

---

## 🆙 Upgrading to Production

When ready to scale:

1. **Upgrade hosting plan** for always-on service
2. **Add custom domain** (e.g., `monitor.yourdomain.com`)
3. **Switch to PostgreSQL** database instead of SQLite
4. **Enable HTTPS** (usually automatic on most platforms)
5. **Set up monitoring** with alerts
6. **Configure CDN** for faster global access

---

## 🤝 Need Help?

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Flask Deployment Guide**: https://flask.palletsprojects.com/en/3.0.x/deploying/

---

## 📝 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Deployment platform account created
- [ ] Environment variables configured
- [ ] API keys obtained and set
- [ ] Application deployed successfully
- [ ] Frontend accessible via URL
- [ ] API endpoints tested
- [ ] Map showing location markers
- [ ] Data collection running automatically
- [ ] Logs checked for errors

---

## 🎉 Congratulations!

Your Environmental Monitoring System is now live on the web! 🌍

Share your deployment URL and help people monitor their environment! 

**Next Steps:**
- Share with friends
- Add more cities
- Customize the UI
- Set up custom domain
- Monitor usage and optimize

Happy monitoring! 🌤️📊🌱
