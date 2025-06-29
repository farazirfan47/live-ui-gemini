from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime
import uuid
import json
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Live UI Gemini API", description="AI-powered UI generation with Gemini", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://*.railway.app",
        "https://*.vercel.app",
        "https://*.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required. Please add it to backend/.env")

# Import Google GenAI
from google import genai
from google.genai import types

client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_ID = "gemini-2.5-flash-lite-preview-06-17"

# System instruction for dynamic UI generation with grounding
UI_SYSTEM_INSTRUCTION = """
CRITICAL: You are ONLY allowed to respond with HTML interfaces. Plain text responses are FORBIDDEN.

MANDATORY RESPONSE FORMAT:
You MUST ALWAYS start your response with exactly "HTML_PAGE:" followed by a complete HTML document.
NEVER provide plain text responses. NEVER explain things in text. ALWAYS create a visual interface.

EXAMPLES OF REQUIRED RESPONSES:
- Weather query → HTML_PAGE: <complete weather dashboard with current data>
- Product search → HTML_PAGE: <complete shopping comparison interface>
- Any question → HTML_PAGE: <complete interactive interface showing the answer>

GROUNDING INSTRUCTIONS:
- Use Google Search grounding to get real, current data
- Always integrate real data into your HTML interfaces
- Show data sources and timestamps in your UI

HTML REQUIREMENTS:
- Complete, self-contained HTML documents with DOCTYPE, html, head, body
- Embedded CSS in <style> tags in the <head>
- Embedded JavaScript in <script> tags before </body>
- Responsive, mobile-first design
- Modern UI with beautiful styling
- Interactive elements (buttons, forms, filters)
- Proper semantic HTML and accessibility

DESIGN STANDARDS:
- Use modern CSS (Flexbox, Grid, CSS Variables, animations)
- Beautiful color schemes and typography
- Data visualizations where appropriate
- Loading states and smooth transitions
- Professional, polished appearance

REMEMBER: NO PLAIN TEXT RESPONSES EVER. Every response MUST be "HTML_PAGE:" followed by complete HTML.
"""

# Pydantic models
class Message(BaseModel):
    id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    is_generated_ui: Optional[bool] = False

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    is_ui: bool
    html_content: Optional[str] = None
    history: List[Message]

# In-memory storage for conversations (use database in production)
conversations = {}

def safe_json_encode(data):
    """Safely encode data to JSON, handling problematic content"""
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        print(f"JSON encoding error: {e}")
        # Create a safe fallback
        safe_data = {
            "type": data.get("type", "error"),
            "content": "Content encoding error",
            "conversation_id": data.get("conversation_id", ""),
            "is_complete": data.get("is_complete", False)
        }
        return json.dumps(safe_data, ensure_ascii=False)





@app.get("/")
async def root():
    return {"message": "Live UI Gemini API with Grounding is running!", "model": MODEL_ID}

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for real-time UI generation with grounding"""
    try:
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = conversations.get(conversation_id, [])
        if request.history:
            conversation_history = [msg.dict() for msg in request.history]
        
        async def generate_stream():
            accumulated_text = ""
            is_ui_response = True  # Always generate UI
            
            try:
                # Prepare conversation history for Gemini
                contents = []
                
                # Add conversation history
                for msg in conversation_history:
                    contents.append(types.Content(
                        role='user' if msg['role'] == 'user' else 'model',
                        parts=[types.Part(text=msg['content'])]
                    ))
                
                # Add current message
                contents.append(types.Content(
                    role='user',
                    parts=[types.Part(text=request.message)]
                ))
                
                # Create config with grounding tools
                tools = []
                # Add Google Search grounding
                tools.append(types.Tool(google_search=types.GoogleSearch()))
                
                config = types.GenerateContentConfig(
                    system_instruction=UI_SYSTEM_INSTRUCTION,
                    temperature=0.7,
                    top_p=0.95,
                    top_k=20,
                    tools=tools
                )
                
                # Use non-streaming approach to avoid JSON parsing issues
                response = client.models.generate_content(
                    model=MODEL_ID,
                    contents=contents,
                    config=config
                )
                
                response_text = response.text if response.text else ""
                
                # Fast streaming by sending character chunks
                chunk_size = 25  # Characters per chunk
                for i in range(0, len(response_text), chunk_size):
                    chunk_text = response_text[i:i + chunk_size]
                    accumulated_text += chunk_text
                    
                    # Check if this is a UI generation response
                    if "HTML_PAGE:" in accumulated_text and not is_ui_response:
                        is_ui_response = True
                    
                    # If it's a UI response, send HTML content directly as we get it
                    if is_ui_response and "HTML_PAGE:" in accumulated_text:
                        html_match = accumulated_text.split("HTML_PAGE:", 1)
                        if len(html_match) > 1:
                            accumulated_html = html_match[1].strip()
                            
                            # Send HTML chunk if we have substantial content
                            if len(accumulated_html) > 150 and accumulated_html.count('<') > 5:
                                html_chunk_data = {
                                    "type": "html_chunk",
                                    "html_content": accumulated_html,
                                    "conversation_id": conversation_id,
                                    "is_complete": False
                                }
                                yield f"data: {safe_json_encode(html_chunk_data)}\n\n"
                    
                    # Send text chunk
                    chunk_data = {
                        "type": "text_chunk",
                        "content": chunk_text,
                        "accumulated_text": accumulated_text,
                        "conversation_id": conversation_id,
                        "is_complete": False
                    }
                    
                    yield f"data: {safe_json_encode(chunk_data)}\n\n"
                    await asyncio.sleep(0.01)  # Fast streaming
                
                # Send final completion
                final_html = None
                clean_text = "I've generated a dynamic UI for you!"
                
                if "HTML_PAGE:" in accumulated_text:
                    # Extract HTML content if properly formatted
                    html_match = accumulated_text.split("HTML_PAGE:", 1)
                    if len(html_match) > 1:
                        final_html = html_match[1].strip()
                else:
                    # Force HTML generation if model didn't follow instructions
                    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Response</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            max-width: 800px;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f8f9fa;
        }}
        
        .header h1 {{
            color: #333;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .content {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        .timestamp {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            display: inline-block;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Response</h1>
        </div>
        
        <div class="content">
{accumulated_text}
        </div>
        
        <div class="footer">
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </div>
</body>
</html>"""
                
                completion_data = {
                    "type": "complete",
                    "final_text": clean_text,
                    "html_content": final_html,
                    "is_ui": True,  # Always UI
                    "conversation_id": conversation_id,
                    "is_complete": True
                }
                yield f"data: {safe_json_encode(completion_data)}\n\n"
                
            except Exception as e:
                print(f"Error in generate_stream: {e}")
                # Send error message
                error_data = {
                    "type": "complete",
                    "final_text": f"Sorry, I encountered an error: {str(e)}. Please try again.",
                    "html_content": None,
                    "is_ui": False,
                    "conversation_id": conversation_id,
                    "is_complete": True
                }
                yield f"data: {safe_json_encode(error_data)}\n\n"
                accumulated_text = error_data["final_text"]
                is_ui_response = False
            
            # Update conversation history
            user_message = Message(
                id=str(uuid.uuid4()),
                role="user",
                content=request.message,
                timestamp=datetime.now()
            )
            
            assistant_message = Message(
                id=str(uuid.uuid4()),
                role="assistant",
                content=clean_text if 'clean_text' in locals() else accumulated_text,
                timestamp=datetime.now(),
                is_generated_ui=True  # Always UI
            )
            
            new_history = conversation_history + [user_message.dict(), assistant_message.dict()]
            conversations[conversation_id] = new_history
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        print(f"Error in streaming chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process streaming message: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate or use existing conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get conversation history
        conversation_history = conversations.get(conversation_id, [])
        if request.history:
            conversation_history = [msg.dict() for msg in request.history]
        
        # Convert our message history to Gemini's format
        gemini_history = []
        for msg in conversation_history:
            gemini_history.append(types.Content(
                role='user' if msg['role'] == 'user' else 'model',
                parts=[types.Part(text=msg['content'])]
            ))
        
        # Create tools for grounding
        tools = []
        tools.append(types.Tool(google_search=types.GoogleSearch()))
        
        # Create chat configuration with grounding
        chat_config = types.GenerateContentConfig(
            system_instruction=UI_SYSTEM_INSTRUCTION,
            temperature=0.7,
            top_p=0.95,
            top_k=20,
            tools=tools
        )
        
        # Create a new chat session with history
        chat = client.chats.create(
            model=MODEL_ID,
            config=chat_config,
            history=gemini_history
        )
        
        # Send the new message
        response = chat.send_message(request.message)
        response_text = response.text
        
        # Force UI generation - check if this is properly formatted
        html_content = None
        clean_text = "I've generated a dynamic UI for you!"
        
        if "HTML_PAGE:" in response_text:
            # Extract HTML content if properly formatted
            html_match = response_text.split("HTML_PAGE:", 1)
            if len(html_match) > 1:
                html_content = html_match[1].strip()
        else:
            # Force HTML generation if model didn't follow instructions
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dynamic Response</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            max-width: 800px;
            width: 100%;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f8f9fa;
        }}
        
        .header h1 {{
            color: #333;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .content {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        .timestamp {{
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            font-size: 0.8rem;
            display: inline-block;
            margin-top: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Response</h1>
        </div>
        
        <div class="content">
{response_text}
        </div>
        
        <div class="footer">
            <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </div>
</body>
</html>"""
        
        # Create new messages
        user_message = Message(
            id=str(uuid.uuid4()),
            role="user",
            content=request.message,
            timestamp=datetime.now()
        )
        
        assistant_message = Message(
            id=str(uuid.uuid4()),
            role="assistant",
            content=clean_text,
            timestamp=datetime.now(),
            is_generated_ui=True  # Always UI
        )
        
        # Update conversation history
        new_history = conversation_history + [user_message.dict(), assistant_message.dict()]
        conversations[conversation_id] = new_history
        
        return ChatResponse(
            response=clean_text,
            conversation_id=conversation_id,
            is_ui=True,  # Always UI
            html_content=html_content,
            history=[Message(**msg) for msg in new_history]
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history by ID"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = conversations[conversation_id]
    return {"conversation_id": conversation_id, "history": [Message(**msg) for msg in history]}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
    return {"message": "Conversation deleted"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": MODEL_ID, "grounding_enabled": True}

# Store HTML content separately to avoid JSON issues
html_storage = {}

@app.get("/api/html/{html_id}", response_class=HTMLResponse)
async def get_html_content(html_id: str):
    """Get HTML content by ID for fast rendering"""
    if html_id not in html_storage:
        raise HTTPException(status_code=404, detail="HTML content not found")
    
    response = HTMLResponse(content=html_storage[html_id])
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/api/html-raw/{html_id}")
async def get_html_raw(html_id: str):
    """Get raw HTML content as JSON for iframe rendering"""
    if html_id not in html_storage:
        raise HTTPException(status_code=404, detail="HTML content not found")
    return {"html_content": html_storage[html_id]}

@app.get("/api/render/{conversation_id}/{message_id}", response_class=HTMLResponse)
async def render_html(conversation_id: str, message_id: str):
    """Render HTML content for a specific message"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations[conversation_id]
    
    # Find the message with the HTML content
    for msg in conversation:
        if msg['id'] == message_id and msg.get('is_generated_ui'):
            # In the real implementation, we would store the HTML content
            # For now, return a demo HTML page
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Generated Page Preview</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }
                    
                    .container {
                        background: white;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                        max-width: 500px;
                        text-align: center;
                    }
                    
                    h1 {
                        color: #333;
                        margin-bottom: 1rem;
                    }
                    
                    p {
                        color: #666;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎉 HTML Page Generated!</h1>
                    <p>This is a preview of your generated HTML page.</p>
                    <p><strong>Message ID:</strong> {}</p>
                    <p>The full HTML content would be displayed here.</p>
                </div>
            </body>
            </html>
            """.format(message_id))
    
    raise HTTPException(status_code=404, detail="HTML content not found")

@app.post("/api/render-html", response_class=HTMLResponse)
async def render_html_content(request: dict):
    """Render HTML content directly"""
    html_content = request.get('html_content', '')
    if not html_content:
        raise HTTPException(status_code=400, detail="No HTML content provided")
    
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 