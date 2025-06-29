export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isGeneratedUI?: boolean
}

export interface ConversationHistory {
  id: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export interface GeminiResponse {
  text: string
  isUI?: boolean
  uiComponent?: string
}

export interface ChatRequest {
  message: string
  conversationId?: string
  history?: Message[]
}

export interface ChatResponse {
  response: string
  conversationId: string
  isUI: boolean
  uiComponent?: string
} 