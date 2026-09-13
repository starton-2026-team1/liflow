import { apiRequest } from './client'

export async function askAiChat({ conversationId, personId, question }) {
  return apiRequest('/ai-chat/messages', {
    method: 'POST',
    body: JSON.stringify({
      person_id: personId || null,
      question,
      conversation_id: conversationId || null,
    }),
  })
}
