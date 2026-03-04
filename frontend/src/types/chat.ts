export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  status: string;
  session_id: string;
  message: ChatMessage;
  processing_time_seconds: number;
}
