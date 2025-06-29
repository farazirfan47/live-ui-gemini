# Live UI Gemini

A powerful AI-powered UI generation tool that combines Google's Gemini AI with a multi-turn conversation interface. Generate beautiful React components through natural language conversations!

## Features

- 🤖 **Multi-turn conversations** with Gemini AI
- 🎨 **UI component generation** with React/TypeScript + Tailwind CSS
- 💬 **Chat interface** for natural interaction
- 📝 **Conversation history** maintained across sessions
- 🔄 **Real-time responses** with streaming support
- 📋 **Copy generated code** to clipboard
- 🎯 **Context-aware** AI that remembers previous messages

## Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **AI Model**: Google Gemini 2.5 Flash
- **Conversation Management**: In-memory storage (extensible to databases)

## Prerequisites

- Node.js 18+ 
- Python 3.8+
- Google Gemini API key (get it from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd live-ui-gemini
```

### 2. Backend Setup (Python FastAPI)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp backend/.env.example backend/.env

# Add your Gemini API key to backend/.env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Frontend Setup (Next.js)

```bash
# Install Node.js dependencies
npm install
```

### 4. Start the Application

#### Start the Backend Server

```bash
# From the root directory
cd backend
python run.py
```

The backend will start on `http://localhost:8000`
- API documentation available at `http://localhost:8000/docs`

#### Start the Frontend Development Server

```bash
# From the root directory (in a new terminal)
npm run dev
```

The frontend will start on `http://localhost:3000`

## Usage

1. **Open your browser** and navigate to `http://localhost:3000`
2. **Start chatting** with the AI about UI components you want to create
3. **View generated code** in the right panel
4. **Copy the code** and use it in your projects

### Example Prompts

- "Create a login form with email and password fields"
- "Build a dashboard with cards showing statistics"
- "Make a responsive navigation bar"
- "Design a contact form with validation"
- "Create a pricing table with three tiers"

## API Endpoints

### POST `/api/chat`
Send a message and get AI response with optional UI generation.

**Request:**
```json
{
  "message": "Create a login form",
  "conversation_id": "optional-uuid",
  "history": []
}
```

**Response:**
```json
{
  "response": "I've generated a UI component for you!",
  "conversation_id": "uuid",
  "is_ui": true,
  "ui_component": "React component code...",
  "history": [...]
}
```

### GET `/api/conversations/{conversation_id}`
Retrieve conversation history.

### DELETE `/api/conversations/{conversation_id}`
Delete a conversation.

### GET `/api/health`
Health check endpoint.

## Project Structure

```
live-ui-gemini/
├── backend/
│   ├── main.py              # FastAPI server
│   │   ├── run.py               # Server startup script
│   │   └── .env.example         # Environment variables template
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Next.js app layout
│   │   │   ├── page.tsx         # Main chat interface
│   │   │   └── globals.css      # Global styles
│   │   └── types/
│   │       └── conversation.ts  # TypeScript interfaces
│   ├── requirements.txt         # Python dependencies
│   ├── package.json            # Node.js dependencies
│   └── README.md              # This file
```

## Environment Variables

### Backend (.env)
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

## Development

### Backend Development
The FastAPI server uses hot reload. Any changes to Python files will automatically restart the server.

### Frontend Development
The Next.js development server supports hot reload. Changes to React components will be reflected immediately.

## Deployment

### Backend Deployment
- Deploy the FastAPI app to platforms like Railway, Render, or Google Cloud Run
- Set the `GOOGLE_API_KEY` environment variable
- Update CORS origins in `main.py` to match your frontend domain

### Frontend Deployment
- Deploy to Vercel, Netlify, or similar platforms
- Update the API endpoint URL in `src/app/page.tsx` to point to your deployed backend

## Troubleshooting

### Common Issues

1. **Backend server not starting:**
   - Check if Python dependencies are installed: `pip install -r requirements.txt`
   - Verify your Gemini API key is set in the environment

2. **Frontend can't connect to backend:**
   - Ensure the backend is running on port 8000
   - Check CORS settings in `backend/main.py`

3. **API key issues:**
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Make sure it's properly set in the `.env` file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google Gemini AI for powerful language model capabilities
- FastAPI for the excellent Python web framework
- Next.js for the React framework
- Tailwind CSS for styling utilities 