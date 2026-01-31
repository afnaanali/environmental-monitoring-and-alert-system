# AI Assistant Setup Guide

## 🤖 Enable Real AI Intelligence

Your AI assistant is currently using template-based responses (fallback mode). To enable REAL AI intelligence that can understand complex questions and provide accurate answers, follow these steps:

---

## Option 1: OpenAI GPT-4 (Recommended)

### Step 1: Get Your API Key
1. Go to **https://platform.openai.com/signup**
2. Create an account (or sign in)
3. Navigate to **https://platform.openai.com/api-keys**
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-proj-...`)

### Step 2: Add API Key to Your System

**Option A: Environment Variable (Recommended)**
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-proj-your-actual-key-here"

# Or add permanently:
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-your-actual-key-here', 'User')
```

**Option B: Direct in Code**
Open `app.py` and replace line 31:
```python
OPENAI_API_KEY = 'sk-proj-your-actual-key-here'  # Paste your key here
USE_AI_API = True  # Change to True
```

### Step 3: Restart the Server
```bash
python app.py
```

### Pricing (as of 2024)
- **GPT-4**: $0.03 per 1K tokens (~750 words)
- **GPT-3.5-Turbo**: $0.002 per 1K tokens (20x cheaper, faster)
- Each query costs approximately $0.01-0.05

---

## Option 2: Alternative AI APIs

### Anthropic Claude
1. Get API key: https://console.anthropic.com/
2. Modify the API call in `generate_ai_response_with_openai()` to use Claude API
3. Pricing: Similar to GPT-4

### Google Gemini (Free Tier Available!)
1. Get API key: https://makersuite.google.com/app/apikey
2. Free tier: 60 requests/minute
3. Modify code to use Gemini API endpoint

### Local AI Models (Free, No API Key)
If you want a FREE solution running locally:
- **Ollama** (https://ollama.ai/) - Run Llama 3, Mistral, etc.
- **LM Studio** (https://lmstudio.ai/) - Run open-source models
- Modify code to call local endpoint (usually http://localhost:11434)

---

## How It Works

### Without AI API (Current - Template Mode):
```
User: "How will be the weather in kochi after an hour"
System: [Checks keyword "after an hour"]
        [Selects "prediction" template]
        [Returns generic prediction data]
Result: ❌ Generic, often irrelevant
```

### With AI API (Intelligent Mode):
```
User: "How will be the weather in kochi after an hour"
AI Agent:
  1. Extracts location: "Kochi"
  2. Fetches real Kochi weather data
  3. Understands user wants FUTURE prediction
  4. Generates natural response:
     "In Kochi, the weather in the next hour is expected to be partly 
      cloudy with a temperature around 27°C. Humidity will remain high 
      at 85%, perfect beach weather! 🌴☁️"
Result: ✅ Accurate, contextual, natural
```

---

## Testing Your AI Agent

Once configured, try these queries:

1. **Complex Questions**:
   - "Is it safe to take my kids to the park in Mumbai right now?"
   - "Should I postpone my morning jog in Delhi due to pollution?"

2. **Predictions**:
   - "How will be the weather in Kochi after an hour?"
   - "Will air quality improve in the next hour in Beijing?"

3. **Comparisons**:
   - "Which city has better air quality: Mumbai or Delhi?"

4. **Contextual**:
   - "I have asthma. Can I go outside in London today?"

---

## Troubleshooting

### Error: "Invalid API key"
- Check if key starts with `sk-proj-` or `sk-`
- Verify key is active in OpenAI dashboard
- Check for extra spaces when copying

### Error: "Rate limit exceeded"
- You've hit API quota
- Wait a few minutes or upgrade your plan

### Error: "Model not found"
- Change model to `gpt-3.5-turbo` in app.py line 1653
- This model is available on free tier

### Still using templates?
- Verify `USE_AI_API = True` in app.py line 33
- Check console logs for "AI-powered: true" in responses
- Restart the server after changes

---

## Cost Management

To keep costs low:
1. Use `gpt-3.5-turbo` instead of `gpt-4` (20x cheaper)
2. Set `max_tokens: 300` instead of 500
3. Cache responses for repeated queries
4. Use local AI models (free!)

---

## Current Status

✅ **Fallback Mode Active**: Using template-based responses
❌ **AI Mode**: Disabled (no API key configured)

After adding your API key and setting `USE_AI_API = True`, you'll see:
```
🤖 AI Query: 'how will be the weather in kochi after an hour'
📍 Detected location: 'Kochi' | Using: 'Kochi'
✅ Fetched data for: Kochi
✅ AI Response generated for 'Kochi' [AI-POWERED]
```

---

**Need help?** Check the terminal logs for detailed error messages!
