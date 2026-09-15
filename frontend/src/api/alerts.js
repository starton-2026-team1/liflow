import { apiRequest } from './client'

export const toAlert = (alert) => ({
  id: alert.id,
  personId: alert.person_id,
  sensorId: alert.sensor_id,
  cause: alert.cause,
  severity: alert.severity,
  title: alert.title,
  description: alert.description,
  evidence: alert.evidence,
  source: alert.source,
  occurredAt: alert.occurred_at,
  readAt: alert.read_at,
  safetyConfirmedAt: alert.safety_confirmed_at,
  resolvedAt: alert.resolved_at,
  createdAt: alert.created_at,
})

export async function getAlerts(personId) {
  const query = personId ? `?person_id=${personId}` : ''
  const alerts = await apiRequest(`/alerts${query}`)
  return alerts.map(toAlert)
}

export async function confirmAlertSafety(alertId) {
  const alert = await apiRequest(`/alerts/${alertId}/safety-confirmations`, {
    method: 'POST',
  })
  return toAlert(alert)
}

export const confirmAllAlertSafety = () => apiRequest('/alerts/safety-confirmations', {
  method: 'POST',
})

export async function closeVisibleNotifications() {
  if (!('serviceWorker' in navigator)) return
  const registration = await navigator.serviceWorker.getRegistration()
  if (!registration?.getNotifications) return
  const notifications = await registration.getNotifications()
  notifications.forEach((notification) => notification.close())
}
