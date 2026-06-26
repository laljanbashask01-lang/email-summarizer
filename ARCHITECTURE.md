# Email Summarizer - Architecture & Concepts

## Application Flow

```
User opens app → Connects Gmail (OAuth) → App fetches emails → Sends to Gemini AI → Stores results in MongoDB → Shows in UI
                                                                                              ↓
                                                                     WebSocket pushes real-time notifications to browser
```

## Backend Libraries & Why

### 1. FastAPI (`from fastapi import FastAPI`)
- A Python web framework for building APIs
- Why: Fast, modern, supports async, easy to write REST endpoints
- What it does: Handles HTTP requests (login, fetch emails, serve pages)

### 2. Motor (`from motor.motor_asyncio import AsyncIOMotorClient`)
- Async MongoDB driver for Python
- Why: FastAPI is async, so we need an async database driver
- What it does: Reads/writes email data to MongoDB without blocking

### 3. Google Auth / OAuth (`from google_auth_oauthlib.flow import Flow`)
- Google's official library for OAuth 2.0 authentication
- Why: Gmail requires OAuth to access user emails (can't just use password)
- What it does: Redirects user to Google login → gets permission → returns access token

### 4. Google API Client (`from googleapiclient.discovery import build`)
- Library to call Google APIs (Gmail, Drive, etc.)
- Why: We need to fetch emails from Gmail's API
- What it does: Uses the OAuth token to call Gmail API → fetch inbox emails

### 5. Google Generative AI (`import google.generativeai as genai`)
- Library to call Gemini LLM
- Why: We want AI-powered summarization and analysis
- What it does: Sends email text to Gemini → gets back summary, sentiment, spam score
