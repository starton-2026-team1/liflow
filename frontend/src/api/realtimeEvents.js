import { API_BASE_URL, getAccessToken } from './client'
import { toSensorEvent } from './sensorEvents'

const MAX_RECONNECT_DELAY_MS = 30_000
const HEARTBEAT_INTERVAL_MS = 25_000
const NON_RETRYABLE_CLOSE_CODES = new Set([4401, 4403])

const createWebSocketUrl = () => {
  const url = new URL(API_BASE_URL, window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/ws/sensor-events`
  url.search = ''
  return url.toString()
}

export function connectSensorEventStream({ onEvent, onFatalError }) {
  let socket = null
  let heartbeatTimer = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let manuallyClosed = false

  const clearTimers = () => {
    window.clearInterval(heartbeatTimer)
    window.clearTimeout(reconnectTimer)
    heartbeatTimer = null
    reconnectTimer = null
  }

  const scheduleReconnect = () => {
    const delay = Math.min(1000 * (2 ** reconnectAttempts), MAX_RECONNECT_DELAY_MS)
    reconnectAttempts += 1
    reconnectTimer = window.setTimeout(connect, delay)
  }

  const connect = () => {
    const token = getAccessToken()
    if (!token) {
      onFatalError?.(new Error('로그인 정보가 없어 실시간 연결을 시작할 수 없어요.'))
      return
    }

    try {
      socket = new WebSocket(createWebSocketUrl())
    } catch {
      scheduleReconnect()
      return
    }

    socket.addEventListener('open', () => {
      socket.send(JSON.stringify({ type: 'authenticate', token }))
    })

    socket.addEventListener('message', (messageEvent) => {
      let message
      try {
        message = JSON.parse(messageEvent.data)
      } catch {
        socket.close(4400, 'Invalid server message')
        return
      }

      if (message.type === 'authenticated') {
        reconnectAttempts = 0
        heartbeatTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'ping' }))
          }
        }, HEARTBEAT_INTERVAL_MS)
        return
      }

      if (message.type === 'sensor_event.created' && message.data) {
        onEvent(toSensorEvent(message.data))
      }
    })

    socket.addEventListener('close', (closeEvent) => {
      window.clearInterval(heartbeatTimer)
      heartbeatTimer = null
      socket = null
      if (manuallyClosed) return
      if (NON_RETRYABLE_CLOSE_CODES.has(closeEvent.code)) {
        onFatalError?.(new Error('실시간 연결 인증에 실패했어요. 다시 로그인해 주세요.'))
        return
      }
      scheduleReconnect()
    })
  }

  connect()

  return () => {
    manuallyClosed = true
    clearTimers()
    socket?.close(1000, 'Page closed')
    socket = null
  }
}
