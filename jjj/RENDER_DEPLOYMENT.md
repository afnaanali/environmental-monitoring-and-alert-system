# 🚀 FastAPI Backend - Render Deployment Guide

## 📋 Deployment Checklist

### ✅ Requirements Met:
- [x] **FastAPI Entry Point**: `main.py` with `app = FastAPI()`
- [x] **Uvicorn Support**: Can run with `uvicorn main:app --host 0.0.0.0 --port 10000`
- [x] **requirements.txt**: Includes `fastapi`, `uvicorn`, `python-dotenv`, `openai`
- [x] **Environment Variables**: OpenAI API key loaded securely via `os.getenv("OPENAI_API_KEY")`
- [x] **.gitignore**: Contains `.env` and `__pycache__/`
- [x] **No Hardcoded Secrets**: All API keys loaded from environment variables

## 🌐 Render Deployment Configuration

### Build Command:
```
pip install -r backend/requirements.txt
```

### Start Command:
```
cd backend && uvicorn main:app --host 0.0.0.0 --port 10000
```

### Environment Variables:
```
OPENAI_API_KEY=your_openai_api_key_here
WEATHER_API_KEY=your_weatherapi_key_here
```

## 🔧 Local Development

### Install Dependencies:
```bash
pip install -r requirements.txt
```

### Run Locally:
```bash
uvicorn main:app --reload
```

### Access:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Frontend**: Open `index.html` in browser

## 📊 API Endpoints

- `GET /` - Serve frontend
- `GET /api/weather?location=London` - Get weather data
- `GET /api/weather/forecast?location=London&days=3` - Get forecast
- `POST /api/correlation/analyze` - Analyze correlations
- `POST /api/risk/calculate` - Calculate risk score
- `POST /api/alerts/contextual` - Generate alerts
- `POST /api/ai/assistant` - AI-powered assistant

## 🔒 Security Notes

- **Environment Variables**: Never commit API keys to code
- **.env File**: Local development only, excluded from Git
- **Production**: Set environment variables in Render dashboard
- **HTTPS**: Render provides automatic SSL certificates

## 🚀 Ready for Deployment!

Your FastAPI backend is fully configured for Render deployment. Simply:

1. Push code to GitHub
2. Create new Render Web Service
3. Connect GitHub repo
4. Set environment variables
5. Deploy!

**Estimated deployment time: 5-10 minutes** 🎉