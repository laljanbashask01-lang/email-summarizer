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

### 6. WebSocket (`from fastapi import WebSocket`)
- A persistent two-way connection between browser and server
- Why: Normal HTTP is request-response (browser asks, server answers). WebSocket lets the server PUSH data to the browser without the browser asking
- What it does: When a new email is processed, server instantly notifies the browser → shows toast notification

### 7. Uvicorn (`import uvicorn`)
- ASGI web server that runs FastAPI
- Why: FastAPI needs a server to handle incoming requests
- What it does: Listens on port 8000, routes requests to FastAPI

### 8. Pydantic (`from pydantic import BaseModel`)
- Data validation library
- Why: Ensures data has the right format/types
- What it does: Defines the structure of email documents

### 9. python-dotenv (`from dotenv import load_dotenv`)
- Loads environment variables from `.env` file
- Why: Keeps secrets (API keys, passwords) out of code
- What it does: Reads `.env` file → makes values available via `os.getenv()`

## Frontend (Vanilla JS)

- **fetch()** — Makes HTTP requests to our backend API
- **WebSocket** — Connects to server for real-time notifications
- **Notification API** — Shows browser desktop notifications
- **AudioContext** — Plays notification sound

## Infrastructure

| Component | Purpose |
|-----------|---------|
| MongoDB Atlas | Cloud database to store processed emails |
| GitHub | Store code, enable deployment |
| Render | Host the app online (like a cloud computer running your code) |
| Docker | Packages app + dependencies into a container for consistent deployment |

## Key Concepts

- **OAuth 2.0**: Industry standard for "Login with Google/Facebook/etc." — lets users grant limited access without sharing passwords
- **REST API**: Backend exposes endpoints (`/api/emails`, `/auth/login`) that the frontend calls
- **WebSocket**: Unlike HTTP (ask → answer), WebSocket stays open so server can push updates anytime
- **LLM/RAG**: We send email content to Gemini and get structured analysis back (summarization, classification)
- **Async/Await**: Python handles multiple requests simultaneously without blocking (important for web apps)
- **Environment Variables**: Secrets stored outside code so they're not exposed in GitHub

## File Purpose Summary

| File | Does what |
|------|-----------|
| `main.py` | Routes, auth flow, email processing, WebSocket |
| `gmail_service.py` | OAuth flow + fetches emails from Gmail API |
| `llm_service.py` | Sends email to Gemini, parses AI response |
| `database.py` | MongoDB connection setup |
| `app.js` | Frontend logic — fetch data, render cards, handle WebSocket |
| `style.css` | Dark theme UI styling |
| `Dockerfile` | Instructions for building the app container |
| `render.yaml` | Render deployment configuration |

## How to Swap Components

The core idea: you don't memorize every line — you understand what each piece does and why it exists. Then you can build similar apps by swapping parts:

- **Database**: MongoDB → PostgreSQL, MySQL, Firebase
- **LLM**: Gemini → OpenAI GPT, Claude, Llama
- **Frontend**: Vanilla JS → React, Vue, Svelte
- **Hosting**: Render → Vercel, Railway, AWS
- **Auth**: Google OAuth → Auth0, Firebase Auth, custom JWT
