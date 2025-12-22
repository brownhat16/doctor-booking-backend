# Doctor Booking Backend API

FastAPI backend for the doctor booking chatbot system.

## Features

- 🔌 REST API endpoints for chat, search, schedule, and booking
- 🤖 DeepSeek V3.1 LLM integration via NVIDIA API
- 🔍 Progressive search refinement with filter intent
- 📅 Doctor schedule viewing
- ✅ Appointment booking

## API Endpoints

### POST /api/chat
Main chat endpoint that handles all user messages.

**Request:**
```json
{
  "message": "I have fever",
  "history": [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": "Hello!"}
  ],
  "userLocation": {
    "lat": 18.5204,
    "lng": 73.8567
  }
}
```

**Response:**
```json
{
  "type": "search",
  "message": "I found 5 doctors...",
  "data": {
    "doctors": [...],
    "count": 5
  }
}
```

### GET /health
Health check endpoint.

### GET /
Service information.

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variable:
```bash
export NVIDIA_API_KEY="nvapi-..."
```

3. Run server:
```bash
python main.py
```

4. Test:
```bash
curl http://localhost:8000/health
```

## Deploy to Railway

1. Push code to GitHub
2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your backend repository
5. Add environment variable:
   - `NVIDIA_API_KEY`: Your NVIDIA API key
6. Deploy!

## Deploy to Render

1. Push code to GitHub
2. Go to https://render.com
3. Click "New" → "Web Service"
4. Connect GitHub repository
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable:
   - `NVIDIA_API_KEY`
7. Deploy!

## Environment Variables

- `NVIDIA_API_KEY`: Required. Your NVIDIA API key for DeepSeek
- `PORT`: Optional. Server port (default: 8000)

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── railway.json         # Railway configuration
├── agents/              # Copied from parent directory
│   ├── doctor_booking/
│   │   ├── agent.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── utils.py
│   └── llm_service.py
└── README.md
```

## Integration with Frontend

After deployment, update the Next.js frontend API route:

```typescript
// In doctor-booking-web/app/api/chat/route.ts
const BACKEND_URL = "https://your-backend.railway.app";

const response = await fetch(`${BACKEND_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
```

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **AI**: DeepSeek V3.1 via NVIDIA API
- **Client**: OpenAI SDK (for NVIDIA compatibility)
