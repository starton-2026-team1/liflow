import { API_BASE_URL, getAccessToken } from './client'

const REQUEST_TIMEOUT_MS = 90_000

const createWebSocketUrl = () => {
  const url = new URL(API_BASE_URL, window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/ws/rpc`
  url.search = ''
  return url.toString()
}

export async function askAiChat({ conversationId, personId, question }) {
  const token = getAccessToken()
  if (!token) throw new Error('로그인 정보가 없어 AI 상담을 시작할 수 없어요.')

  return new Promise((resolve, reject) => {
    const socket = new WebSocket(createWebSocketUrl())
    // randomUUID is only available in secure contexts (HTTPS/localhost).
    // Keep chat usable when the app is opened over a plain HTTP LAN/Tailscale URL.
    const uuid = globalThis.crypto?.randomUUID?.() ??
      `${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}-${Math.random().toString(16).slice(2)}`
    const requestId = `ai_${Date.now()}_${uuid.replaceAll('-', '')}`
    let settled = false

    const finish = (callback, value) => {
      if (settled) return
      settled = true
      window.clearTimeout(timeout)
      callback(value)
      socket.close(1000, 'AI request completed')
    }
    const timeout = window.setTimeout(() => {
      finish(reject, new Error('AI 응답 시간이 초과됐어요. 다시 시도해 주세요.'))
    }, REQUEST_TIMEOUT_MS)

    socket.addEventListener('open', () => {
      socket.send(JSON.stringify({ type: 'authenticate', token }))
    })
    socket.addEventListener('message', (event) => {
      let message
      try {
        message = JSON.parse(event.data)
      } catch {
        finish(reject, new Error('AI 서버 응답을 확인할 수 없어요.'))
        return
      }
      if (message.type === 'authenticated') {
        socket.send(JSON.stringify({
          type: 'request',
          id: requestId,
          method: 'POST',
          path: '/ai-chat/messages',
          body: {
            person_id: personId || null,
            question,
            conversation_id: conversationId || null,
          },
        }))
        return
      }
      if (message.type !== 'response' || message.id !== requestId) return
      if (message.ok) finish(resolve, message.data)
      else finish(reject, new Error(message.error?.message || 'AI 답변을 불러오지 못했어요.'))
    })
    socket.addEventListener('error', () => {
      finish(reject, new Error('AI 상담 서버에 연결하지 못했어요.'))
    })
    socket.addEventListener('close', (event) => {
      if (!settled) finish(reject, new Error(
        event.code === 4401
          ? '로그인이 만료됐어요. 다시 로그인해 주세요.'
          : 'AI 상담 연결이 종료됐어요.',
      ))
    })
  })
}
