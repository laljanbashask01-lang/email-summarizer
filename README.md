# Email Summarizer

AI-powered email notification and summarization app using Gmail API + Gemini 2.5 Flash.

## Setup

### Prerequisites
- Python 3.10+
- MongoDB running locally (or MongoDB Atlas URI)
- Google Cloud project with Gmail API enabled
- Gemini API key

### 1. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable Gmail API
3. Create OAuth 2.0 credentials (Web application type)
4. Add `http://localhost:8000/auth/callback` as authorized redirect URI
5. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Install & Run

```bash
cd email-summarizer/backend
pip install -r requirements.txt

# Copy and fill in your credentials
cp .env.example .env
# Edit .env with your actual keys

# Run the app
python main.py
```

### 3. Use
1. Open `http://localhost:8000`
2. Click "Connect Gmail" to authenticate
3. Click "Fetch Emails" to process recent emails
4. New emails will appear with AI-generated summaries and importance levels
5. Real-time notifications via WebSocket when new emails arrive

## Deploy to Render

### 1. Database
Use [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier works) — get your connection URI.

### 2. Deploy
1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/) → New → Web Service
3. Connect your GitHub repo
4. Render will auto-detect the `render.yaml` blueprint, or configure manually:
   - **Root Directory:** `email-summarizer`
   - **Environment:** Docker
   - **Dockerfile Path:** `./Dockerfile`
5. Add environment variables in the Render dashboard:
   - `MONGODB_URI` — your MongoDB Atlas connection string
   - `GOOGLE_CLIENT_ID` — from Google Cloud Console
   - `GOOGLE_CLIENT_SECRET` — from Google Cloud Console
   - `GOOGLE_REDIRECT_URI` — `https://your-app-name.onrender.com/auth/callback`
   - `GEMINI_API_KEY` — from Google AI Studio

### 3. Update Google OAuth
Add your Render URL to Google Cloud Console → OAuth 2.0 → Authorized redirect URIs:
```
https://your-app-name.onrender.com/auth/callback
```

## Features
- Gmail OAuth2 authentication
- Automatic email polling (every 60s)
- AI summarization via Gemini 2.5 Flash
- Importance classification (high/medium/low)
- Category tagging (work, personal, urgent, etc.)
- Real-time WebSocket notifications
- Browser notifications
- Dark theme UI
