import axios from 'axios';
import { AnalyzeResponse, ProcessingStatus, ValidationWarning } from '../types/catalog';
import { ChatRequest, ChatResponse } from '../types/chat';

const API_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export class ValidationWarningError extends Error {
  constructor(public warning: ValidationWarning) {
    super(warning.reason);
    this.name = 'ValidationWarningError';
  }
}

export async function* analyzeProductStream(
  images: File[],
  model?: string,
  overrideValidation?: boolean
): AsyncGenerator<ProcessingStatus | AnalyzeResponse> {
  const formData = new FormData();
  images.forEach((image) => {
    formData.append('images', image);
  });
  if (model) {
    formData.append('model', model);
  }
  if (overrideValidation) {
    formData.append('override_validation', 'true');
  }

  const response = await fetch(`${API_URL}/api/v1/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  let buffer = '';
  let currentEvent = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      // Skip empty lines
      if (!line.trim()) continue;

      if (line.startsWith('event:')) {
        currentEvent = line.substring(6).trim();
        continue;
      }

      if (line.startsWith('data:')) {
        const data = line.substring(5).trim();
        if (!data) continue;

        try {
          const parsed = JSON.parse(data);

          if (currentEvent === 'status' && parsed.step) {
            yield parsed as ProcessingStatus;
          } else if (currentEvent === 'complete' && parsed.status) {
            yield parsed as AnalyzeResponse;
            return;
          } else if (currentEvent === 'warning') {
            // Throw special warning error that can be caught and handled
            throw new ValidationWarningError(parsed as ValidationWarning);
          } else if (currentEvent === 'error') {
            throw new Error(parsed.message || 'Analysis failed');
          }
        } catch (e) {
          if (e instanceof SyntaxError) {
            console.error('Failed to parse SSE data:', data);
          } else {
            throw e;
          }
        }
      }
    }
  }
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/api/v1/chat', request);
  return response.data;
}

export async function checkHealth() {
  const response = await api.get('/api/v1/health');
  return response.data;
}

export async function getAvailableModels() {
  const response = await api.get('/api/v1/models');
  return response.data;
}

export async function regenerateSection(sessionId: string, section: string, userInstructions: string) {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('section', section);
  formData.append('user_instructions', userInstructions);

  const response = await fetch(`${API_URL}/api/v1/regenerate`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Regeneration failed: ${response.statusText}`);
  }

  return response.json();
}

export async function enhanceSEO(sessionId: string) {
  const formData = new FormData();
  formData.append('session_id', sessionId);

  const response = await fetch(`${API_URL}/api/v1/enhance-seo`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`SEO enhancement failed: ${response.statusText}`);
  }

  return response.json();
}
