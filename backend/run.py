"""
Run script for the Live UI Gemini FastAPI server
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Live UI Gemini API server...")
    print("📝 Make sure to set your GOOGLE_API_KEY environment variable")
    print("🌐 Server will be available at http://localhost:8000")
    print("📖 API docs will be available at http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 