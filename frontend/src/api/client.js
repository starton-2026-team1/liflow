export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
const TOKEN_KEY = 'starton_access_token'

export const getAccessToken = () => window.sessionStorage.getItem(TOKEN_KEY)
export const setAccessToken = (token) => window.sessionStorage.setItem(TOKEN_KEY, token)
export const clearAccessToken = () => window.sessionStorage.removeItem(TOKEN_KEY)

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(getAccessToken() ? { Authorization: `Bearer ${getAccessToken()}` } : {}),
      ...options.headers,
    },
  })

  if (!response.ok) {
    let detail = '요청을 처리하지 못했어요.'
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // JSON 응답이 아닐 때 기본 메시지를 사용한다.
    }
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response.json()
}
