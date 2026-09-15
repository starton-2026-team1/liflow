import { API_BASE_URL, apiRequest } from './client'

export const createNfcTag = (data) => apiRequest('/nfc-tags', {
  method: 'POST',
  body: JSON.stringify({
    person_id: Number(data.personId),
    name: data.name,
    guardian_phone: data.guardianPhone,
    contact_reveal_enabled: true,
  }),
})

const publicRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const body = await response.json()
  if (!response.ok) throw new Error(body.detail || body.message || '요청을 처리하지 못했어요.')
  return body
}

export const getNfcHelp = (token) => publicRequest(`/nfc-help/${token}`)
export const sendNfcHelp = (token) => publicRequest(`/nfc-help/${token}/alerts`, { method: 'POST' })
export const getNfcHelpStatus = (eventId, finderToken) => publicRequest(`/nfc-help/events/${eventId}?finder_token=${encodeURIComponent(finderToken)}`)
export const revealNfcContact = (eventId, finderToken) => publicRequest(`/nfc-help/events/${eventId}/contact?finder_token=${encodeURIComponent(finderToken)}`, { method: 'POST' })
