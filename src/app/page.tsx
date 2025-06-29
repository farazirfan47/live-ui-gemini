'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User, Code, Loader2, Eye, ExternalLink, Maximize2, Minimize2, X } from 'lucide-react'
import { getApiUrl } from '../config'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  is_generated_ui?: boolean
}

interface ChatResponse {
  response: string
  conversation_id: string
  is_ui: boolean
  html_content?: string
  history: Message[]
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>('')
  const [generatedHtml, setGeneratedHtml] = useState<string>('')
  const [showPreview, setShowPreview] = useState(false)
  const [fullScreenPreview, setFullScreenPreview] = useState(false)
  const [viewMode, setViewMode] = useState<'code' | 'render'>('render')
  const [streamingText, setStreamingText] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const fullScreenIframeRef = useRef<HTMLIFrameElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Function to safely update iframe content
  const updateIframeContent = (iframe: HTMLIFrameElement | null, htmlContent: string) => {
    if (!iframe) return
    
    try {
      // Create a blob URL for the HTML content
      const blob = new Blob([htmlContent], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      
      // Set the src to the blob URL
      iframe.src = url
      
      // Clean up the blob URL after a short delay
      setTimeout(() => {
        URL.revokeObjectURL(url)
      }, 1000)
    } catch (error) {
      console.error('Error updating iframe:', error)
      // Fallback method
      try {
        const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document
        if (iframeDoc) {
          iframeDoc.open()
          iframeDoc.write(htmlContent)
          iframeDoc.close()
        }
      } catch (fallbackError) {
        console.error('Fallback iframe update failed:', fallbackError)
      }
    }
  }

  const sendMessage = async () => {
    if (!input.trim() || loading || isStreaming) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)
    setIsStreaming(true)
    setStreamingText('')

    try {
      // Debug: Log the backend URL being used
      console.log('Backend URL:', getApiUrl('/api/chat/stream'))
      
      const response = await fetch(getApiUrl('/api/chat/stream'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          conversation_id: conversationId || undefined,
          history: messages
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      let accumulatedText = ''
      let currentHtml = ''
      let finalConversationId = ''

      // Add streaming message placeholder
      const streamingMessageId = Date.now().toString()
      const streamingMessage: Message = {
        id: streamingMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        is_generated_ui: false
      }
      
      setMessages(prev => [...prev, streamingMessage])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'text_chunk') {
                accumulatedText = data.accumulated_text
                setStreamingText(accumulatedText)
                finalConversationId = data.conversation_id
                
                // Update the streaming message
                setMessages(prev => prev.map(msg => 
                  msg.id === streamingMessageId 
                    ? { ...msg, content: accumulatedText }
                    : msg
                ))
              }
              
              else if (data.type === 'html_chunk' || data.type === 'html_complete') {
                currentHtml = data.html_content
                setGeneratedHtml(currentHtml)
                setShowPreview(true)
                
                // Update iframes in real-time
                setTimeout(() => {
                  updateIframeContent(iframeRef.current, currentHtml)
                  updateIframeContent(fullScreenIframeRef.current, currentHtml)
                }, 50)
                
                // Mark message as UI generation
                setMessages(prev => prev.map(msg => 
                  msg.id === streamingMessageId 
                    ? { ...msg, is_generated_ui: true }
                    : msg
                ))
              }
              
              else if (data.type === 'complete') {
                // Final update
                setConversationId(data.conversation_id)
                setStreamingText('')
                
                if (data.html_content) {
                  setGeneratedHtml(data.html_content)
                  setShowPreview(true)
                  
                  setTimeout(() => {
                    updateIframeContent(iframeRef.current, data.html_content)
                    updateIframeContent(fullScreenIframeRef.current, data.html_content)
                  }, 100)
                }
                
                // Update final message
                setMessages(prev => prev.map(msg => 
                  msg.id === streamingMessageId 
                    ? { 
                        ...msg, 
                        content: data.final_text,
                        is_generated_ui: data.is_ui 
                      }
                    : msg
                ))
                
                break
              }
            } catch (parseError) {
              console.error('Error parsing SSE data:', parseError)
            }
          }
        }
      }
      
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend server is running on port 8000.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      setIsStreaming(false)
      setStreamingText('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const openInNewTab = () => {
    if (generatedHtml) {
      const blob = new Blob([generatedHtml], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    }
  }

  const downloadHtml = () => {
    if (generatedHtml) {
      const blob = new Blob([generatedHtml], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'generated-page.html'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const toggleFullScreenPreview = () => {
    setFullScreenPreview(!fullScreenPreview)
    if (!fullScreenPreview && generatedHtml) {
      // Update full screen iframe when opening
      setTimeout(() => {
        updateIframeContent(fullScreenIframeRef.current, generatedHtml)
      }, 100)
    }
  }

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                Live UI Gemini
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Generate beautiful HTML pages with AI-powered conversations
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Chat Interface */}
              <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-xl shadow-lg flex flex-col h-[600px]">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                    <Bot className="mr-2" size={24} />
                    AI Assistant
                  </h2>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.length === 0 ? (
                    <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
                      <Bot size={48} className="mx-auto mb-4 opacity-50" />
                      <p>Start a conversation to generate HTML pages!</p>
                      <p className="text-sm mt-2">Try: "Create a landing page" or "Build a contact form"</p>
                    </div>
                  ) : (
                    messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-xs px-4 py-2 rounded-lg ${
                            message.role === 'user'
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                          }`}
                        >
                          <div className="flex items-start space-x-2">
                            {message.role === 'assistant' && <Bot size={16} className="mt-1 flex-shrink-0" />}
                            {message.role === 'user' && <User size={16} className="mt-1 flex-shrink-0" />}
                            <div className="flex-1">
                              <p className="text-sm">{message.content}</p>
                              {message.is_generated_ui && (
                                <div className="mt-2 flex items-center text-xs opacity-75">
                                  <Code size={12} className="mr-1" />
                                  HTML Page Generated
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                  {(loading || isStreaming) && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 dark:bg-gray-700 px-4 py-2 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <Loader2 size={16} className="animate-spin" />
                          <span className="text-sm text-gray-600 dark:text-gray-300">
                            {isStreaming ? 'AI is streaming...' : 'AI is thinking...'}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Describe the HTML page you want to create..."
                      className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      disabled={loading || isStreaming}
                    />
                    <button
                      onClick={sendMessage}
                      disabled={loading || isStreaming || !input.trim()}
                      className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send size={20} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Live Preview */}
              <div className="lg:col-span-1 bg-white dark:bg-gray-800 rounded-xl shadow-lg flex flex-col h-[600px]">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center justify-between">
                    <div className="flex items-center">
                      <Eye className="mr-2" size={24} />
                      Live Preview
                    </div>
                    {generatedHtml && (
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={toggleFullScreenPreview}
                          className="px-3 py-1 text-sm bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded hover:bg-purple-200 dark:hover:bg-purple-800 flex items-center"
                        >
                          <Maximize2 size={14} className="mr-1" />
                          Full Screen
                        </button>
                        <button
                          onClick={() => copyToClipboard(generatedHtml)}
                          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                        >
                          Copy HTML
                        </button>
                        <button
                          onClick={downloadHtml}
                          className="px-3 py-1 text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-800"
                        >
                          Download
                        </button>
                        <button
                          onClick={openInNewTab}
                          className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center"
                        >
                          <ExternalLink size={14} className="mr-1" />
                          Open
                        </button>
                      </div>
                    )}
                  </h2>
                </div>

                <div className="flex-1 overflow-hidden relative">
                  {generatedHtml ? (
                    <>
                      <iframe
                        ref={iframeRef}
                        className="w-full h-full border-0"
                        title="Generated HTML Preview"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                      />
                      {isStreaming && (
                        <div className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs flex items-center">
                          <Loader2 size={12} className="animate-spin mr-1" />
                          Updating...
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center text-gray-500 dark:text-gray-400 mt-8 p-4">
                      <Eye size={48} className="mx-auto mb-4 opacity-50" />
                      <p>Generated HTML pages will appear here</p>
                      <p className="text-sm mt-2">Ask the AI to create a page to see it here!</p>
                      {isStreaming && (
                        <div className="mt-4 flex items-center justify-center text-blue-500">
                          <Loader2 size={16} className="animate-spin mr-2" />
                          <span className="text-sm">Generating page...</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>


          </div>
        </div>
      </div>

      {/* Full Screen Preview Modal */}
      {fullScreenPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-75 z-50 flex flex-col">
          {/* Header */}
          <div className="bg-white dark:bg-gray-800 p-4 flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Full Screen Preview</h3>
              
              {/* Toggle between code and render view */}
              <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('render')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'render'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Eye size={16} className="mr-2 inline" />
                  Render
                </button>
                <button
                  onClick={() => setViewMode('code')}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'code'
                      ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Code size={16} className="mr-2 inline" />
                  Code
                </button>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={openInNewTab}
                className="px-3 py-2 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center"
              >
                <ExternalLink size={16} className="mr-2" />
                Open in New Tab
              </button>
              <button
                onClick={toggleFullScreenPreview}
                className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center"
              >
                <X size={16} className="mr-2" />
                Close
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden">
            {viewMode === 'render' ? (
              <iframe
                ref={fullScreenIframeRef}
                className="w-full h-full border-0"
                title="Full Screen HTML Preview"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              />
            ) : (
              <div className="w-full h-full bg-gray-900 p-4 overflow-auto">
                <pre className="text-green-400 text-sm font-mono">
                  <code>{generatedHtml}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
} 