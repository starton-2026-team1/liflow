import { apiRequest, clearAccessToken, getAccessToken, setAccessToken } from './client'

function saveAuth(auth) {
  setAccessToken(auth.access_token)
  return auth.user
}

export async function signUp(credentials) {
  return saveAuth(await apiRequest('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }))
}

export async function login(credentials) {
  return saveAuth(await apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }))
}

export async function getCurrentUser() {
  if (!getAccessToken()) return null
  return apiRequest('/auth/me')
}

export async function updateCurrentUser(account) {
  return apiRequest('/auth/me', {
    method: 'PATCH',
    body: JSON.stringify(account),
  })
}

export async function logout() {
  try {
    await apiRequest('/auth/logout', { method: 'POST' })
  } finally {
    clearAccessToken()
  }
}
