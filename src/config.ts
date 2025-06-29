// Configuration for the application
export const config = {
  // Backend API URL - can be overridden by environment variable
  backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
  
  // API endpoints
  endpoints: {
    chatStream: '/api/chat/stream',
    chat: '/api/chat',
    health: '/api/health',
    conversations: '/api/conversations',
    render: '/api/render',
    renderHtml: '/api/render-html',
    html: '/api/html',
    htmlRaw: '/api/html-raw'
  }
}

// Helper function to get full API URL
export const getApiUrl = (endpoint: string) => {
  return `${config.backendUrl}${endpoint}`
} 